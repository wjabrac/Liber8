"""Hyper-V based execution isolation boundary."""

from __future__ import annotations

import subprocess
import json
import time
from typing import Any, Callable, Dict, List, Optional
from .isolation import IsolationRequest, IsolationResult, ExecutionIsolationBoundary


class HyperVManager:
    """Orchestrates Hyper-V VMs via PowerShell on the host."""

    def run_ps(self, command: str) -> subprocess.CompletedProcess:
        """Runs a PowerShell command and returns the result."""
        full_cmd = f"powershell.exe -NoProfile -NonInteractive -Command \"{command}\""
        return subprocess.run(full_cmd, shell=True, capture_output=True, text=True)

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

    def invoke_guest_command(self, vm_name: str, script_block: str, timeout: int = 30) -> Dict[str, Any]:
        """Executes a command inside the guest via PowerShell Direct."""
        # PowerShell Direct uses Invoke-Command -VMName
        # Escaping quotes for the shell command
        escaped_script = script_block.replace("\"", "\\\"")
        cmd = f"Invoke-Command -VMName '{vm_name}' -ScriptBlock {{ {escaped_script} }} | ConvertTo-Json"
        
        start_time = time.monotonic()
        res = self.run_ps(cmd)
        duration = time.monotonic() - start_time
        
        if res.returncode != 0:
            return {
                "status": "error",
                "stdout": res.stdout,
                "stderr": res.stderr,
                "exit_code": res.returncode,
                "duration": duration
            }
            
        try:
            output = json.loads(res.stdout) if res.stdout.strip() else None
            return {
                "status": "success",
                "output": output,
                "duration": duration
            }
        except json.JSONDecodeError:
            return {
                "status": "success",
                "output": res.stdout.strip(),
                "duration": duration
            }


class HyperVIsolationBoundary:
    backend_name = "hyperv"

    def __init__(self, vm_name: str | None = None) -> None:
        self.vm_name = vm_name
        self.manager = HyperVManager()

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
            # Wait a moment for Integration Services to be ready (minimal wait)
            time.sleep(2)

        # 2. Prepare payload injection
        # Support 'shell' tool specifically via PowerShell Direct
        if request.tool_name == "shell":
            command = request.arguments.get("command")
            if not command:
                return IsolationResult(
                    status="error",
                    output="Shell command missing from arguments",
                    error_class="argument_error",
                    backend=self.backend_name
                )
            
            res = self.manager.invoke_guest_command(self.vm_name, command)
            if res["status"] == "success":
                return IsolationResult(
                    status="success",
                    output=res["output"],
                    backend=self.backend_name
                )
            else:
                return IsolationResult(
                    status="error",
                    output=res.get("stderr") or res.get("stdout") or "Unknown guest error",
                    error_class="guest_execution_error",
                    backend=self.backend_name
                )

        return IsolationResult(
            status="error",
            output=f"Hyper-V guest execution for tool '{request.tool_name}' not yet fully implemented",
            error_class="not_implemented",
            backend=self.backend_name
        )
