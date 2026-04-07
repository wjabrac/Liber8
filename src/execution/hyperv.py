"""Hyper-V based execution isolation boundary."""

from __future__ import annotations

import subprocess
import json
import time
import textwrap
import base64
from typing import Any, Callable, Dict, List, Optional
from .isolation import IsolationRequest, IsolationResult, ExecutionIsolationBoundary


class HyperVManager:
    """Orchestrates Hyper-V VMs via PowerShell on the host."""

    def run_ps(self, command: str) -> subprocess.CompletedProcess:
        """Runs a PowerShell command and returns the result."""
        full_cmd = f"powershell.exe -NoProfile -NonInteractive -Command \"{command}\""
        return subprocess.run(full_cmd, shell=True, capture_output=True, text=True)

    @staticmethod
    def _b64_utf16le(payload: str) -> str:
        return base64.b64encode(payload.encode("utf-16le")).decode("ascii")

    def get_vms(self) -> List[Dict[str, Any]]:
        """Returns a list of VMs on the host."""
        # Using ConvertTo-Json for easier parsing
        cmd = "Get-VM | Select-Object Name, State, Status | ConvertTo-Json"
        res = self.run_ps(cmd)
        if res.returncode != 0 or not res.stdout.strip():
            return []
        try:
            data = json.loads(res.stdout)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            return []

    def get_switches(self) -> List[Dict[str, Any]]:
        """Returns a list of VM switches on the host."""
        cmd = "Get-VMSwitch | Select-Object Name, SwitchType | ConvertTo-Json"
        res = self.run_ps(cmd)
        if res.returncode != 0 or not res.stdout.strip():
            return []
        try:
            data = json.loads(res.stdout)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            return []

    def get_vm_state(self, vm_name: str) -> str:
        """Returns the state of a specific VM (e.g., Running, Off)."""
        cmd = f"Get-VM -Name '{vm_name}' | Select-Object -ExpandProperty State"
        res = self.run_ps(cmd)
        return res.stdout.strip()

    def start_vm(self, vm_name: str) -> bool:
        """Starts a VM if it is not already running."""
        state = self.get_vm_state(vm_name)
        if state == "Running":
            return True
        res = self.run_ps(f"Start-VM -Name '{vm_name}'")
        return res.returncode == 0

    def wait_for_vm_running(self, vm_name: str, timeout: int = 30, poll_interval: float = 1.0) -> bool:
        """Waits until a VM reports Running state."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.get_vm_state(vm_name) == "Running":
                return True
            time.sleep(poll_interval)
        return False

    def invoke_guest_payload(self, vm_name: str, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """Executes a payload in a guest over PowerShell Direct with timeout/result capture."""
        payload_json = json.dumps(payload)
        encoded_payload = self._b64_utf16le(payload_json)
        wrapped_script = textwrap.dedent(
            """
            $payload = [System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('{encoded_payload}')) | ConvertFrom-Json
            $job = Start-Job -ScriptBlock {{
                param($cmd)
                $stdout = @()
                try {{
                    $stdout = & cmd.exe /c $cmd 2>&1
                    $exitCode = $LASTEXITCODE
                    if ($null -eq $exitCode) {{ $exitCode = 0 }}
                    [PSCustomObject]@{{
                        status = "success"
                        stdout = ($stdout -join "`n")
                        stderr = ""
                        exit_code = [int]$exitCode
                    }}
                }} catch {{
                    [PSCustomObject]@{{
                        status = "error"
                        stdout = ""
                        stderr = $_.Exception.Message
                        exit_code = 1
                    }}
                }}
            }} -ArgumentList $payload.command

            if (-not (Wait-Job -Job $job -Timeout {timeout})) {{
                Stop-Job -Job $job -Force
                Receive-Job -Job $job -ErrorAction SilentlyContinue | Out-Null
                [PSCustomObject]@{{
                    status = "timeout"
                    stdout = ""
                    stderr = "Guest command timed out after {timeout}s"
                    exit_code = -1
                }} | ConvertTo-Json -Compress
                exit 124
            }}

            $result = Receive-Job -Job $job
            $result | ConvertTo-Json -Compress
            """
        ).format(encoded_payload=encoded_payload, timeout=timeout)
        encoded_script = self._b64_utf16le(wrapped_script)
        cmd = (
            f"Invoke-Command -VMName '{vm_name}' "
            f"-ScriptBlock {{ powershell.exe -NoProfile -NonInteractive -EncodedCommand {encoded_script} }}"
        )

        started = time.monotonic()
        res = self.run_ps(cmd)
        duration = time.monotonic() - started
        if res.returncode != 0 and not res.stdout.strip():
            return {
                "status": "error",
                "stdout": res.stdout,
                "stderr": res.stderr,
                "exit_code": res.returncode,
                "duration": duration,
            }

        parsed: Dict[str, Any]
        try:
            parsed = json.loads(res.stdout) if res.stdout.strip() else {}
        except json.JSONDecodeError:
            parsed = {"status": "error", "stdout": "", "stderr": f"Invalid guest JSON: {res.stdout.strip()}", "exit_code": 1}
        parsed["duration"] = duration
        return parsed

    def check_ps_direct(self, vm_name: str) -> bool:
        """Checks that PowerShell Direct can execute a trivial command."""
        probe = self.run_ps(f"Invoke-Command -VMName '{vm_name}' -ScriptBlock {{ 'ready' }}")
        return probe.returncode == 0 and "ready" in probe.stdout


class HyperVIsolationBoundary:
    backend_name = "hyperv"

    def __init__(self, vm_name: str | None = None) -> None:
        self.vm_name = vm_name
        self.manager = HyperVManager()
        self.default_timeout_seconds = 30

    def check_ready(self) -> Dict[str, Any]:
        """Check if Hyper-V orchestration is available and configured."""
        try:
            # 1. Check Service
            svc_res = self.manager.run_ps("Get-Service vmms | Select-Object -ExpandProperty Status")
            service_running = svc_res.stdout.strip() == "Running"
            
            # 2. Check Module
            mod_res = self.manager.run_ps("Get-Module -ListAvailable Hyper-V")
            module_available = bool(mod_res.stdout.strip())
            
            # 3. Check Inventory
            vms = self.manager.get_vms()
            switches = self.manager.get_switches()
            
            vm_exists = any(v.get("Name") == self.vm_name for v in vms) if self.vm_name else False
            vm_state = self.manager.get_vm_state(self.vm_name) if vm_exists and self.vm_name else "Unknown"
            
            return {
                "ready": service_running and module_available,
                "service_running": service_running,
                "module_available": module_available,
                "vm_configured": bool(self.vm_name),
                "vm_exists": vm_exists,
                "vm_state": vm_state,
                "vm_count": len(vms),
                "switch_count": len(switches),
            }
        except Exception as e:
            return {"ready": False, "error": str(e)}

    def execute(self, request: IsolationRequest, func: Callable[..., Any]) -> IsolationResult:
        # Enforce boundary existence and readiness
        if not self.vm_name:
            return IsolationResult(
                status="error",
                output="Hyper-V VM name not configured",
                error_class="configuration_error",
                backend=self.backend_name
            )

        ready_status = self.check_ready()
        if not ready_status["ready"]:
            return IsolationResult(
                status="error",
                output=f"Hyper-V backend not ready: {ready_status}",
                error_class="isolation_backend_unavailable",
                backend=self.backend_name
            )

        if not ready_status["vm_exists"]:
            return IsolationResult(
                status="error",
                output=f"Hyper-V VM '{self.vm_name}' not found on host",
                error_class="configuration_error",
                backend=self.backend_name
            )

        # 1. Ensure VM is running
        if ready_status["vm_state"] != "Running":
            started = self.manager.start_vm(self.vm_name)
            if not started:
                return IsolationResult(
                    status="error",
                    output=f"Failed to start Hyper-V VM '{self.vm_name}'",
                    error_class="vm_start_error",
                    backend=self.backend_name
                )
            if not self.manager.wait_for_vm_running(self.vm_name, timeout=30):
                return IsolationResult(
                    status="degraded",
                    output=f"Hyper-V VM '{self.vm_name}' start requested but VM did not reach Running state in time",
                    error_class="vm_state_timeout",
                    backend=self.backend_name,
                )

        # 2. Ensure PowerShell Direct is actually available before execution
        if not self.manager.check_ps_direct(self.vm_name):
            return IsolationResult(
                status="degraded",
                output=f"VM '{self.vm_name}' is running but PowerShell Direct is unavailable",
                error_class="ps_direct_unavailable",
                backend=self.backend_name,
            )

        # 3. Prepare payload injection
        # Support open_interpreter path (plus shell alias for compatibility)
        if request.tool_name in {"open_interpreter", "shell"}:
            command = request.arguments.get("command", "")
            timeout = int(request.arguments.get("timeout", self.default_timeout_seconds))
            if not command:
                return IsolationResult(
                    status="error",
                    output="Shell command missing from arguments",
                    error_class="argument_error",
                    backend=self.backend_name
                )
            
            payload = {"tool": request.tool_name, "command": command}
            res = self.manager.invoke_guest_payload(self.vm_name, payload, timeout=timeout)
            if res.get("status") == "success":
                return IsolationResult(
                    status="success",
                    output={
                        "stdout": res.get("stdout", ""),
                        "stderr": res.get("stderr", ""),
                        "exit_code": res.get("exit_code", 0),
                        "duration": res.get("duration"),
                    },
                    backend=self.backend_name,
                )
            if res.get("status") == "timeout":
                return IsolationResult(
                    status="degraded",
                    output=res.get("stderr") or f"Guest command timed out after {timeout}s",
                    error_class="guest_execution_timeout",
                    backend=self.backend_name,
                )
            return IsolationResult(
                    status="error",
                    output=res.get("stderr") or res.get("stdout") or "Unknown guest error",
                    error_class="guest_execution_error",
                    backend=self.backend_name,
                )

        return IsolationResult(
            status="error",
            output=f"Hyper-V guest execution for tool '{request.tool_name}' not yet fully implemented",
            error_class="not_implemented",
            backend=self.backend_name
        )
