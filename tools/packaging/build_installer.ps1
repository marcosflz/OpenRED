# OpenRED — build the installers (MSI/NSIS/DMG/AppImage-deb) and collect them in artifacts/.
#
# Steps (documented and executable):
#   1. (optional) build the engine bundle -> artifacts/engine-bundle
#   2. npm ci + tauri build in apps/desktop
#   3. copy the produced installers into artifacts/
#
# Prerequisites: Node.js 20+, Rust stable, platform bundler toolchain (WiX/NSIS on Windows,
# Xcode CLT on macOS, webkit2gtk + appindicator on Linux).
#
# NOTE (coordination A2/A9): wiring artifacts/engine-bundle into the Tauri resources
# (tauri.conf.json "bundle.resources" + updater config) is a shared change owned by A9 with
# A2 review. Until it lands, pass -BuildEngineBundle to produce the payload ready to copy.
#
# Usage:
#   pwsh tools/packaging/build_installer.ps1
#   pwsh tools/packaging/build_installer.ps1 -BuildEngineBundle -Bundles msi,nsis
#   pwsh tools/packaging/build_installer.ps1 -SkipNpm

[CmdletBinding()]
param(
    [string]$AppDir = "",
    [string]$OutDir = "",
    [string[]]$Bundles = @("msi", "nsis", "dmg", "appimage", "deb"),
    [switch]$BuildEngineBundle,
    [switch]$SkipNpm
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
if (-not $AppDir) { $AppDir = Join-Path $RepoRoot "apps\desktop" }
if (-not $OutDir) { $OutDir = Join-Path $RepoRoot "artifacts" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if ($BuildEngineBundle) {
    Write-Host "[installer] step 1/3: engine bundle"
    & pwsh -NoProfile -File (Join-Path $ScriptDir "build_engine_bundle.ps1")
    if ($LASTEXITCODE -ne 0) { throw "build_engine_bundle.ps1 failed with exit code $LASTEXITCODE" }
} else {
    Write-Host "[installer] step 1/3: engine bundle skipped (pass -BuildEngineBundle to build it)"
}

if (-not $SkipNpm) {
    Write-Host "[installer] step 2/3: npm ci"
    Push-Location $AppDir
    try {
        & npm ci
        if ($LASTEXITCODE -ne 0) { throw "npm ci failed with exit code $LASTEXITCODE" }
        Write-Host "[installer] step 2/3: tauri build ($($Bundles -join ', '))"
        $bundleFlag = "--bundles", ($Bundles -join ",")
        & npx tauri build @bundleFlag
        if ($LASTEXITCODE -ne 0) { throw "tauri build failed with exit code $LASTEXITCODE" }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "[installer] step 2/3: npm/tauri build skipped"
}

Write-Host "[installer] step 3/3: collecting installers"
$bundleRoot = Join-Path $AppDir "src-tauri\target\release\bundle"
$patterns = @("*.msi", "*.exe", "*.dmg", "*.AppImage", "*.deb", "*.rpm", "*.tar.gz")
$collected = @()
if (Test-Path $bundleRoot) {
    foreach ($pattern in $patterns) {
        foreach ($file in Get-ChildItem -Path $bundleRoot -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue) {
            $target = Join-Path $OutDir $file.Name
            Copy-Item -LiteralPath $file.FullName -Destination $target -Force
            $collected += $target
        }
    }
}
if ($collected.Count -eq 0) {
    Write-Warning "[installer] no installers found under $bundleRoot (did the build run?)"
} else {
    foreach ($file in $collected) {
        Write-Host ("[installer]   {0}  ({1:N1} MB)" -f (Split-Path -Leaf $file), ((Get-Item $file).Length / 1MB))
    }
}

# Updater manifest template: tauri-action generates the real latest.json during releases;
# this placeholder documents the required shape for manual/offline builds.
$latestTemplate = Join-Path $OutDir "latest.json.template"
@'
{
  "version": "<package version, e.g. 0.2.0>",
  "notes": "<release notes>",
  "pub_date": "<RFC3339 UTC, e.g. 2026-09-25T12:00:00Z>",
  "platforms": {
    "windows-x86_64": { "signature": "<minisign signature>", "url": "https://github.com/<owner>/<repo>/releases/download/v<ver>/OpenRED_<ver>_x64-setup.exe" },
    "darwin-aarch64": { "signature": "<minisign signature>", "url": "https://github.com/<owner>/<repo>/releases/download/v<ver>/OpenRED_<ver>_aarch64.dmg" },
    "linux-x86_64":  { "signature": "<minisign signature>", "url": "https://github.com/<owner>/<repo>/releases/download/v<ver>/OpenRED_<ver>_amd64.AppImage" }
  }
}
'@ | Set-Content -LiteralPath $latestTemplate -Encoding utf8
Write-Host "[installer] updater template: $latestTemplate"
Write-Host "[installer] done: $OutDir"
