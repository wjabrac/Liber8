"""Hyper-V based execution isolation boundary."""

from __future__ import annotations

import subprocess
import json
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
            
            return {
                "ready": service_running and module_available,
                "service_running": service_running,
                "module_available": module_available,
                "vm_configured": bool(self.vm_name),
                "vm_exists": vm_exists,
                "vm_count": len(vms),
                "switch_count": len(switches),
            }
        except Exception as e:
            return {"ready": False, "error": str(e)}

    def execute(self, request: IsolationRequest, func: Callable[..., Any]) -> IsolationResult:
        # Enforce boundary existence and readiness
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

        # Implementation Note: 
        # Actual guest orchestration will use:
        # 1. Start-VM (if not running)
        # 2. Invoke-Command -VMName ... (PowerShell Direct)
        # 3. Copy-Item -ToSession ... (for payload injection)

        return IsolationResult(
            status="error",
            output="Hyper-V guest execution (PowerShell Direct) not yet implemented",
            error_class="not_implemented",
            backend=self.backend_name
        )
