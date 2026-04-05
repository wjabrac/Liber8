# Hyper-V Guest Isolation Setup Checklist

To use the `hyperv` isolation backend, the host machine must be configured as follows:

## 1. Host Requirements
- [ ] Windows 10/11 Pro, Enterprise, or Education (Hyper-V is not available on Home).
- [ ] Hyper-V feature enabled (`Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All`).
- [ ] PowerShell execution policy allows running local scripts (`Set-ExecutionPolicy RemoteSigned`).

## 2. Network Configuration
- [ ] A Virtual Switch must exist. For isolated execution, an "Internal" switch is recommended.
  ```powershell
  New-VMSwitch -Name "LIBR8-Internal" -SwitchType Internal
  ```

## 3. Guest VM Configuration
- [ ] A VM must be created and named (e.g., `LIBR8-Worker-01`).
- [ ] The VM must have an OS installed (Windows or Linux with Integration Services).
- [ ] **PowerShell Direct** must be functional (requires Windows 10/Server 2016 or later guest).
- [ ] A local user account with administrative privileges must exist in the guest for `Invoke-Command`.

## 4. LIBR8 Configuration
- [ ] Set the environment variable `LIBR8_EXECUTION_ISOLATION_BACKEND=hyperv`.
- [ ] Set the environment variable `LIBR8_HYPERV_VM_NAME=LIBR8-Worker-01`.
- [ ] (Future) Provide guest credentials via a secure secret store.

## 5. Verification
Run the following to check host readiness:
```bash
python -c "from src.execution.hyperv import HyperVIsolationBoundary; print(HyperVIsolationBoundary('LIBR8-Worker-01').check_ready())"
```
