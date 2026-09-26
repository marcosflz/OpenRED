# OpenRED — fetch and verify the portable Python runtime (Windows / CI).
#
# Downloads the pinned python-build-standalone release from tools/python-portable/python.lock,
# verifies its SHA-256, extracts it to engine/python/ and installs the locked wheels *into*
# that runtime (Lib/site-packages) with uv when available (pip fallback). Idempotent:
# re-running with the same lock is a no-op unless -Force is passed.
#
# The sidecar can then run without PYTHONPATH; the Tauri supervisor still exports the engine
# directory (see apps/desktop/src-tauri/README.md and tests/clean-machine/smoke.ps1).
#
# Usage:
#   pwsh tools/python-portable/fetch_python.ps1
#   pwsh tools/python-portable/fetch_python.ps1 -Flavor x86_64-unknown-linux-gnu -Force

[CmdletBinding()]
param(
    [string]$Flavor = "",
    [string]$LockFile = "",
    [switch]$Force,
    [switch]$SkipDeps
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$EngineDir = Join-Path $RepoRoot "engine"
if (-not $LockFile) { $LockFile = Join-Path $ScriptDir "python.lock" }
if (-not (Test-Path $LockFile)) { throw "python.lock not found: $LockFile" }
$lock = Get-Content -LiteralPath $LockFile -Raw | ConvertFrom-Json

function Get-DefaultFlavor {
    $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        if ($arch -eq "Arm64") { return "aarch64-pc-windows-msvc" }
        return "x86_64-pc-windows-msvc"
    }
    if ($IsMacOS) {
        if ($arch -eq "Arm64") { return "aarch64-apple-darwin" }
        return "x86_64-apple-darwin"
    }
    if ($arch -eq "Arm64") { return "aarch64-unknown-linux-gnu" }
    return "x86_64-unknown-linux-gnu"
}

if (-not $Flavor) { $Flavor = Get-DefaultFlavor }
$entry = $lock.flavors.$Flavor
if (-not $entry) {
    throw "flavor '$Flavor' is not present in $LockFile (available: $($lock.flavors.PSObject.Properties.Name -join ', '))"
}

$pythonDir = Join-Path $EngineDir "python"
$marker = Join-Path $pythonDir ".openred-runtime.json"
if ((Test-Path $marker) -and -not $Force) {
    $current = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    if ($current.asset -eq $entry.asset -and $current.sha256 -eq $entry.sha256) {
        Write-Host "[fetch_python] runtime already present and matches $($entry.asset) — nothing to do"
        exit 0
    }
    Write-Host "[fetch_python] runtime present but does not match the lock; reinstalling"
}

$cacheDir = Join-Path ([System.IO.Path]::GetTempPath()) "openred-python-cache"
New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
$archive = Join-Path $cacheDir $entry.asset
if (-not (Test-Path $archive)) {
    Write-Host "[fetch_python] downloading $($entry.url)"
    Invoke-WebRequest -Uri $entry.url -OutFile $archive -UseBasicParsing
}
$actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $entry.sha256) {
    Remove-Item -LiteralPath $archive -Force
    throw "[fetch_python] SHA256 mismatch for $($entry.asset): expected $($entry.sha256), got $actual; archive removed"
}
Write-Host "[fetch_python] SHA256 OK: $actual"

$staging = Join-Path ([System.IO.Path]::GetTempPath()) ("openred-python-staging-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force -Path $staging | Out-Null
try {
    Push-Location $staging
    try {
        tar -xzf $archive
        if ($LASTEXITCODE -ne 0) { throw "tar failed with exit code $LASTEXITCODE" }
    } finally {
        Pop-Location
    }
    $extracted = Join-Path $staging $entry.extract_dir
    if (-not (Test-Path $extracted)) { throw "expected a '$($entry.extract_dir)/' directory inside $($entry.asset)" }
    if (Test-Path $pythonDir) { Remove-Item -LiteralPath $pythonDir -Recurse -Force }
    Move-Item -LiteralPath $extracted -Destination $pythonDir
} finally {
    Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
}

$pythonExe = Join-Path $pythonDir "python.exe"
if (-not (Test-Path $pythonExe)) { $pythonExe = Join-Path $pythonDir "bin/python3" }
if (-not (Test-Path $pythonExe)) { throw "python executable not found under $pythonDir" }

if (-not $SkipDeps) {
    # Dependencies are installed *into* the portable runtime (Lib/site-packages), so the
    # sidecar works without PYTHONPATH. uv is preferred when available (portable copy in
    # tools/uv or on PATH); pip inside the runtime is the fallback.
    $uvExe = @(
        (Join-Path $RepoRoot "tools\uv\uv.exe"),
        (Join-Path $RepoRoot "tools\uv\uv")
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $uvExe) {
        $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
        if ($uvCommand) { $uvExe = $uvCommand.Source }
    }
    $lockPath = Join-Path $EngineDir "requirements-core.lock"
    if ($uvExe) {
        Write-Host "[fetch_python] installing locked wheels with uv ($uvExe)"
        & $uvExe pip install --system --python $pythonExe --requirement $lockPath `
            --only-binary :all: --no-progress
        if ($LASTEXITCODE -ne 0) { throw "[fetch_python] uv pip install failed with exit code $LASTEXITCODE" }
    } else {
        Write-Host "[fetch_python] uv not found; falling back to the runtime pip"
        & $pythonExe -m pip --version *> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[fetch_python] pip missing; bootstrapping with ensurepip"
            & $pythonExe -m ensurepip --upgrade
        }
        & $pythonExe -m pip install --requirement $lockPath `
            --only-binary :all: --no-warn-script-location --disable-pip-version-check
        if ($LASTEXITCODE -ne 0) { throw "[fetch_python] pip install failed with exit code $LASTEXITCODE" }
    }

    & $pythonExe -c "import numpy, scipy, matplotlib, serial; print('[fetch_python] runtime OK:', numpy.__version__, scipy.__version__, matplotlib.__version__, serial.__version__)"
    if ($LASTEXITCODE -ne 0) { throw "[fetch_python] runtime import check failed" }
}

$markerPayload = [ordered]@{
    asset          = $entry.asset
    sha256         = $entry.sha256
    release_tag    = $lock.release_tag
    python_version = $lock.python_version
    flavor         = $Flavor
}
$markerPayload | ConvertTo-Json | Set-Content -LiteralPath $marker -Encoding utf8
Write-Host "[fetch_python] done: $pythonDir"
