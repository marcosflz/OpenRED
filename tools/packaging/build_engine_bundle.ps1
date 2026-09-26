# OpenRED — build the engine bundle (portable Python + sidecar + engine.lock).
#
# Assembles artifacts/engine-bundle/ with exactly the layout the Tauri resource
# directory expects (<install>/engine):
#
#   engine-bundle/
#   ├── python/                 # CPython 3.12 + site-packages (tools/python-portable)
#   ├── openred_engine/         # sidecar code + plugins
#   ├── requirements-core.lock  # wheel provenance
#   ├── engine.lock             # SHA-256 per file (integrity check at startup)
#   └── LICENSES/               # runtime + third-party licenses
#
# Prerequisites: run tools/python-portable/fetch_python.ps1 first.
#
# Usage:
#   pwsh tools/packaging/build_engine_bundle.ps1
#   pwsh tools/packaging/build_engine_bundle.ps1 -OutDir artifacts/engine-bundle -Force

[CmdletBinding()]
param(
    [string]$OutDir = "",
    [string]$EngineDir = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
if (-not $EngineDir) { $EngineDir = Join-Path $RepoRoot "engine" }
if (-not $OutDir) { $OutDir = Join-Path $RepoRoot "artifacts\engine-bundle" }

$pythonDir = Join-Path $EngineDir "python"
$sidecarDir = Join-Path $EngineDir "openred_engine"
if (-not (Test-Path (Join-Path $pythonDir "python.exe")) -and -not (Test-Path (Join-Path $pythonDir "bin/python3"))) {
    throw "portable runtime not found under $pythonDir — run tools/python-portable/fetch_python.ps1 first"
}
if (-not (Test-Path (Join-Path $sidecarDir "__init__.py"))) {
    throw "sidecar package not found under $sidecarDir"
}

if (Test-Path $OutDir) {
    Write-Host "[bundle] cleaning previous $OutDir"
    Remove-Item -LiteralPath $OutDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Copy-Tree {
    param([string]$Source, [string]$Destination)
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    if (Get-Command robocopy -ErrorAction SilentlyContinue) {
        # /E all subdirs, /XD excluded dirs, /XF excluded files, /NFL /NDL /NJH /NJS quiet
        & robocopy $Source $Destination /E /XD __pycache__ _downloads /XF *.pyc *.pyo /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }
    } else {
        Copy-Item -Path (Join-Path $Source "*") -Destination $Destination -Recurse -Force
        Get-ChildItem -Path $Destination -Recurse -Directory -Filter "__pycache__" |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "[bundle] copying portable runtime"
Copy-Tree -Source $pythonDir -Destination (Join-Path $OutDir "python")
Write-Host "[bundle] copying sidecar package"
Copy-Tree -Source $sidecarDir -Destination (Join-Path $OutDir "openred_engine")

Copy-Item -LiteralPath (Join-Path $EngineDir "requirements-core.lock") -Destination $OutDir -Force
Copy-Item -LiteralPath (Join-Path $EngineDir "requirements-core.txt") -Destination $OutDir -Force

# engine.lock is generated from the copied tree so the hashes match the shipped bytes.
Write-Host "[bundle] generating engine.lock"
$pythonExe = @(
    (Join-Path $EngineDir "python\python.exe"),
    (Join-Path $EngineDir "python\bin\python3"),
    (Join-Path $EngineDir ".venv\Scripts\python.exe"),
    "python"
) | Where-Object { $_ -eq "python" -or (Test-Path $_) } | Select-Object -First 1
& $pythonExe (Join-Path $ScriptDir "make_engine_lock.py") --root $OutDir --include python openred_engine --out (Join-Path $OutDir "engine.lock")
if ($LASTEXITCODE -ne 0) { throw "make_engine_lock.py failed with exit code $LASTEXITCODE" }

$licensesDir = Join-Path $OutDir "LICENSES"
New-Item -ItemType Directory -Force -Path $licensesDir | Out-Null
$runtimeLicense = Get-ChildItem -Path $pythonDir -Filter "LICENSE*" -File -ErrorAction SilentlyContinue | Select-Object -First 1
if ($runtimeLicense) {
    Copy-Item -LiteralPath $runtimeLicense.FullName -Destination (Join-Path $licensesDir "PYTHON-PSF.txt") -Force
}
Set-Content -LiteralPath (Join-Path $licensesDir "README.txt") -Encoding utf8 -Value @(
    "Third-party licenses for the bundled engine.",
    "",
    "CPython and python-build-standalone: see PYTHON-PSF.txt (PSF-2.0).",
    "Wheels installed from engine/requirements-core.lock: numpy/scipy (BSD-3-Clause),",
    "matplotlib (PSF-based), pyserial (BSD-3-Clause), pillow (HPND), and their transitive",
    "dependencies. Generate the full report with:",
    "  pip install pip-licenses && pip-licenses --with-license-file --format=markdown -o LICENSES/wheels.md"
)
if (Get-Command pip-licenses -ErrorAction SilentlyContinue) {
    & pip-licenses --with-license-file --format=markdown -o (Join-Path $licensesDir "wheels.md")
}

$size = (Get-ChildItem -Path $OutDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
Write-Host ("[bundle] done: {0} ({1:N1} MB, engine.lock {2} files)" -f $OutDir, ($size / 1MB), ((Get-Content (Join-Path $OutDir "engine.lock") -Raw | ConvertFrom-Json).file_count))
Write-Host "[bundle] copy this directory to <install>/engine (tauri.conf.json bundle.resources does it at build time)."
