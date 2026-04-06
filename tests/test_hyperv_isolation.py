import unittest
from unittest.mock import MagicMock, patch
from src.execution.hyperv import HyperVIsolationBoundary, HyperVManager
from src.execution.isolation import IsolationRequest, IsolationResult

class TestHyperVIsolation(unittest.TestCase):
    def setUp(self):
        self.vm_name = "test-vm"
        self.boundary = HyperVIsolationBoundary(vm_name=self.vm_name)
        self.request = IsolationRequest(tool_name="shell", arguments={"command": "whoami"})

    @patch("src.execution.hyperv.HyperVManager.run_ps")
    def test_check_ready_success(self, mock_run_ps):
        # Mocking multiple calls to run_ps
        # 1. Get-Service vmms
        # 2. Get-Module
        # 3. Get-VM
        # 4. Get-VMSwitch
        # 5. Get-VM -Name (for state)
        
        mock_svc = MagicMock()
        mock_svc.stdout = "Running"
        mock_svc.returncode = 0
        
        mock_mod = MagicMock()
        mock_mod.stdout = "Hyper-V module"
        mock_mod.returncode = 0
        
        mock_vms = MagicMock()
        mock_vms.stdout = '[{"Name": "test-vm", "State": "Running"}]'
        mock_vms.returncode = 0
        
        mock_sw = MagicMock()
        mock_sw.stdout = "[]"
        mock_sw.returncode = 0
        
        mock_state = MagicMock()
        mock_state.stdout = "Running"
        mock_state.returncode = 0
        
        mock_run_ps.side_effect = [mock_svc, mock_mod, mock_vms, mock_sw, mock_state]
        
        ready = self.boundary.check_ready()
        self.assertTrue(ready["ready"])
        self.assertTrue(ready["vm_exists"])
        self.assertEqual(ready["vm_state"], "Running")

    @patch("src.execution.hyperv.HyperVIsolationBoundary.check_ready")
    @patch("src.execution.hyperv.HyperVManager.invoke_guest_command")
    def test_execute_shell_success(self, mock_invoke, mock_check_ready):
        mock_check_ready.return_value = {
            "ready": True,
            "vm_exists": True,
            "vm_state": "Running"
        }
        mock_invoke.return_value = {
            "status": "success",
            "output": "guest-user",
            "duration": 0.5
        }
        
        result = self.boundary.execute(self.request, lambda x: x)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.output, "guest-user")
        self.assertEqual(result.backend, "hyperv")

    @patch("src.execution.hyperv.HyperVIsolationBoundary.check_ready")
    def test_execute_vm_not_found(self, mock_check_ready):
        mock_check_ready.return_value = {
            "ready": True,
            "vm_exists": False
        }
        
        result = self.boundary.execute(self.request, lambda x: x)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error_class, "configuration_error")
        self.assertIn("not found", result.output)

if __name__ == "__main__":
    unittest.main()
