---
name: toolchain-management
description: Guide AI agents on detecting, explaining, and installing external mathematical and formal toolchains (Lean 4, elan, Lake, Julia, SageMath) to PATH according to the host OS (Windows, Linux, macOS), with mandatory user notification and explanation of why the toolchain is required.
---

# AXIOM Toolchain Management Skill

This skill governs how AI agents handle missing mathematical toolchains (such as **Lean 4 / elan**, **Lake**, **Julia**, or **SageMath**) when an operation requires heavy formal or numerical computation.

---

## 1. Golden Rules for Agents

### Rule 1: Mandatory User Notification & Justification
Agents must **NEVER** install software or modify system environment variables silently. Before invoking any package manager or install script, the agent **MUST** output a clear message to the user stating:
1. **Which toolchain is missing** (e.g., Lean 4 `elan`, Julia).
2. **Why it is required** for the requested task (e.g., *"To verify this theorem in Lean 4 without holes (`sorry`) and certify it with `formal-proof` guarantee, the interactive Lean 4 kernel is required"*).
3. **What command will be executed** according to the user's Operating System.

### Rule 2: Epistemic Fail-Closed Fallback
If the user declines installation, or if the environment cannot install the toolchain (e.g. no internet or restricted permissions), the agent must:
- Fall back cleanly to AXIOM's static/symbolic verifiers.
- Explicitly state in the response: *"Toolchain unavailable. Result classified under symbolic/heuristic guarantees; formal machine-checked proof could not be verified."*
- **Never fabricate** a `formal-proof` guarantee when the binary is absent.

---

## 2. OS-Specific Installation Matrix

The agent must inspect the host OS (`os.name`, `$env:OS`, or `uname -s`) and use the designated command:

### Windows (`os.name == "nt"`)

#### A. Lean 4 / elan & Lake
```powershell
# Option 1: Execute AXIOM's bundled installer script
powershell -ExecutionPolicy Bypass -File scripts\install_toolchains.ps1 -LeanOnly

# Option 2: Windows Package Manager (winget)
winget install --id Lean.Elan -e --accept-package-agreements --accept-source-agreements

# Option 3: Official PowerShell bootstrap
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/leanprover/elan/master/elan-init.ps1" -OutFile "$env:TEMP\elan-init.ps1"
powershell -ExecutionPolicy Bypass -File "$env:TEMP\elan-init.ps1" -y
```

**Adding to User PATH on Windows:**
The binary resides in `$HOME\.elan\bin`. To persist in user environment:
```powershell
$elanBin = "$HOME\.elan\bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$elanBin*") {
    [Environment]::SetEnvironmentVariable("Path", "$elanBin;$userPath", "User")
}
$env:PATH = "$elanBin;$env:PATH"
```

#### B. Julia
```powershell
winget install --id Julialang.Julia -e --accept-package-agreements --accept-source-agreements
```

---

### Linux (Ubuntu / Debian / RHEL)

#### A. Lean 4 / elan & Lake
```bash
# Execute AXIOM's bundled installer script
bash scripts/install_toolchains.sh

# Or official curl bootstrap
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y
export PATH="$HOME/.elan/bin:$PATH"
elan default stable
```

#### B. Julia
```bash
curl -fsSL https://install.julialang.org | sh -s -- -y
# Or via distro package manager
sudo apt-get update && sudo apt-get install -y julia
```

---

### macOS (Darwin)

#### A. Lean 4 / elan & Lake
```bash
# Via Homebrew
brew install elan-init
elan default stable

# Or via official curl bootstrap
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y
export PATH="$HOME/.elan/bin:$PATH"
```

#### B. Julia
```bash
brew install --cask julia
```

---

## 3. Post-Installation Verification Workflow

Immediately after installing a toolchain, the agent must:

1. **Verify Binary Availability**:
   ```bash
   # For Lean:
   lean --version && lake --version
   # For Julia:
   julia --version
   ```
2. **Execute AXIOM Diagnostics**:
   ```bash
   python -m axiom.cli doctor
   ```
   Confirm that the toolchain transitioned from `OPTIONAL / UNAVAILABLE` to `AVAILABLE`.
3. **Inform the User**:
   Notify the user that the toolchain is configured and proceed with the mathematical verification.
