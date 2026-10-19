# Chronokairo AXIOM — Quick PowerShell Setup Launcher
# Usage:
#   .\setup.ps1 -Min
#   .\setup.ps1 -Full
#   .\setup.ps1 -Check

param(
    [switch]$Min,
    [switch]$Full,
    [switch]$Check,
    [switch]$SkipToolchains
)

$argsList = @()
if ($Min) { $argsList += "--min" }
if ($Full) { $argsList += "--full" }
if ($Check) { $argsList += "--check" }
if ($SkipToolchains) { $argsList += "--skip-toolchains" }

python setup_env.py $argsList
