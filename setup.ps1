# Chronokairo AXIOM — Quick PowerShell Setup Launcher
# Usage:
#   .\setup.ps1 -Min
#   .\setup.ps1 -Full
#   .\setup.ps1 -Custom
#   .\setup.ps1 -Select "cas,docs,lean"
#   .\setup.ps1 -Check

param(
    [switch]$Min,
    [switch]$Full,
    [switch]$Custom,
    [string]$Select,
    [switch]$Check,
    [switch]$SkipToolchains
)

$argsList = @()
if ($Min) { $argsList += "--min" }
if ($Full) { $argsList += "--full" }
if ($Custom) { $argsList += "--custom" }
if ($Select) { $argsList += "--select", $Select }
if ($Check) { $argsList += "--check" }
if ($SkipToolchains) { $argsList += "--skip-toolchains" }

python setup_env.py @argsList
