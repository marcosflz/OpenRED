# OpenRED — refresh tools/python-portable/python.lock from the real upstream release.
#
# Queries the GitHub API for the most recent astral-sh/python-build-standalone release that
# ships CPython 3.12 `install_only` tarballs, downloads its SHA256SUMS asset and rewrites the
# lock with the tag, version and hashes. Review the diff before committing (the runtime pin is
# part of the release supply chain).
#
# Usage:
#   pwsh tools/python-portable/refresh_python_lock.ps1
#   pwsh tools/python-portable/refresh_python_lock.ps1 -ReleaseTag 20260924

[CmdletBinding()]
param(
    [string]$ReleaseTag = "",
    [string]$PythonSeries = "3.12",
    [string]$OutFile = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $OutFile) { $OutFile = Join-Path $ScriptDir "python.lock" }
$headers = @{ "User-Agent" = "OpenRED-python-lock"; "Accept" = "application/vnd.github+json" }

$flavorNames = @(
    "x86_64-pc-windows-msvc",
    "aarch64-pc-windows-msvc",
    "aarch64-apple-darwin",
    "x86_64-apple-darwin",
    "x86_64-unknown-linux-gnu",
    "aarch64-unknown-linux-gnu"
)

function Get-ReleaseWithAssets {
    param([string]$Tag)
    if ($Tag) {
        return Invoke-RestMethod -Uri "https://api.github.com/repos/astral-sh/python-build-standalone/releases/tags/$Tag" -Headers $headers
    }
    $releases = Invoke-RestMethod -Uri "https://api.github.com/repos/astral-sh/python-build-standalone/releases?per_page=30" -Headers $headers
    foreach ($release in $releases) {
        $probe = $release.assets | Where-Object { $_.name -like "*${PythonSeries}*install_only.tar.gz" -and $_.name -notlike "*sha256*" }
        if ($probe) { return $release }
    }
    throw "no release with ${PythonSeries} install_only assets found"
}

$release = Get-ReleaseWithAssets -Tag $ReleaseTag
$sumsAsset = $release.assets | Where-Object { $_.name -eq "SHA256SUMS" }
if (-not $sumsAsset) { throw "release $($release.tag_name) has no SHA256SUMS asset" }
Write-Host "[refresh_python_lock] release $($release.tag_name) ($($release.published_at))"

$response = Invoke-WebRequest -Uri $sumsAsset.browser_download_url -UseBasicParsing -Headers $headers
$sumsText = if ($response.Content -is [byte[]]) { [System.Text.Encoding]::UTF8.GetString($response.Content) } else { [string]$response.Content }
$sums = @{}
foreach ($line in ($sumsText -split "`r?`n")) {
    if ($line -match '^\s*([0-9a-fA-F]{64})\s+\*?(.+?)\s*$') { $sums[$Matches[2]] = $Matches[1].ToLowerInvariant() }
}

$flavors = [ordered]@{}
$pythonVersion = ""
foreach ($flavor in $flavorNames) {
    $asset = $release.assets | Where-Object { $_.name -like "cpython-${PythonSeries}.*-${flavor}-install_only.tar.gz" } | Select-Object -First 1
    if (-not $asset) { Write-Warning "flavor $flavor not available in $($release.tag_name); skipped"; continue }
    if (-not $pythonVersion -and $asset.name -match "cpython-(${PythonSeries}\.\d+)") { $pythonVersion = $Matches[1] }
    $hash = $sums[$asset.name]
    if (-not $hash) { throw "no SHA256SUMS entry for $($asset.name)" }
    $flavors[$flavor] = [ordered]@{
        asset       = $asset.name
        sha256      = $hash
        url         = $asset.browser_download_url -replace '\+', '%2B'
        extract_dir = "python"
    }
}
if ($flavors.Count -eq 0) { throw "no matching flavors found" }

$lock = [ordered]@{
    format         = 1
    description    = "Pinned python-build-standalone runtime for the OpenRED engine bundle. Regenerate with tools/python-portable/refresh_python_lock.ps1 after reviewing the release."
    source         = "https://github.com/astral-sh/python-build-standalone"
    release_tag    = $release.tag_name
    python_version = $pythonVersion
    install_only   = $true
    flavors        = $flavors
}
$lock | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutFile -Encoding utf8
Write-Host "[refresh_python_lock] wrote $OutFile (tag $($release.tag_name), python $pythonVersion, $($flavors.Count) flavors)"
