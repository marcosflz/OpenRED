# OpenRED — clean-machine smoke test (Windows).
#
# Validates the *installed* bundle without relying on any system Python:
#   * launches <install>\engine\python\python.exe -s -X utf8 -m openred_engine
#     with the OPENRED_* env vars (the wheels live in the runtime's own site-packages)
#   * opens the fixture workspace (contracts/fixtures/inputs)
#   * runs app.ping, workspace.set_dir, adiabatic.calculate and the reduced engine.calculate
#   * verifies that no python.exe outside <install>\engine is running
#   * verifies engine.lock against the shipped files
#
# Canonical validation is a pristine Windows Sandbox/VM (see .github/workflows/clean-machine.yml);
# this script is also the runner proxy used by CI. Exit code 0 = smoke green.
#
# Usage:
#   pwsh tests/clean-machine/smoke.ps1 -InstallDir "C:\Program Files\OpenRED"
#   pwsh tests/clean-machine/smoke.ps1 -Fixtures contracts/fixtures

[CmdletBinding()]
param(
    [string]$InstallDir = "",
    [string]$Fixtures = "",
    [string]$RepoRoot = "",
    [int]$TimeoutMs = 120000,
    [switch]$SkipLockVerify
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RepoRoot) { $RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path }
if (-not $Fixtures) { $Fixtures = Join-Path $RepoRoot "contracts\fixtures" }

function Find-InstallDir {
    $roots = @($env:ProgramFiles, ${env:ProgramFiles(x86)}, (Join-Path $env:LOCALAPPDATA "Programs"), $env:LOCALAPPDATA) |
        Where-Object { $_ -and (Test-Path $_) }
    foreach ($root in $roots) {
        $found = Get-ChildItem -LiteralPath $root -Directory -Recurse -Depth 4 -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -eq "openred_engine" -and (Test-Path (Join-Path $_.FullName "__init__.py")) } |
            Select-Object -First 1
        if ($found) { return (Split-Path -Parent (Split-Path -Parent $found.FullName)) }
    }
    return $null
}

if (-not $InstallDir) { $InstallDir = Find-InstallDir }
if (-not $InstallDir -or -not (Test-Path $InstallDir)) {
    throw "OpenRED installation not found; pass -InstallDir (searched Program Files / LocalAppData)"
}
$InstallDir = (Resolve-Path $InstallDir).Path
$engineDir = Join-Path $InstallDir "engine"
$pythonExe = Join-Path $engineDir "python\python.exe"
if (-not (Test-Path $pythonExe)) { $pythonExe = Join-Path $engineDir "python\bin\python3" }

Write-Host "[smoke] install dir : $InstallDir"
foreach ($required in @($pythonExe, (Join-Path $engineDir "openred_engine\__init__.py"))) {
    if (-not (Test-Path $required)) { throw "missing bundle item: $required" }
}
& $pythonExe -c "import numpy, scipy, matplotlib, serial" 2>$null
if ($LASTEXITCODE -ne 0) { throw "the bundled runtime cannot import numpy/scipy/matplotlib/pyserial" }

# -- fixture workspace ------------------------------------------------------
$work = Join-Path ([System.IO.Path]::GetTempPath()) ("openred-smoke-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
$dataDir = Join-Path $work "data"
$workDirRoot = Join-Path $work "workspace"
foreach ($dir in @($dataDir, $workDirRoot, (Join-Path $workDirRoot "Engines"), (Join-Path $workDirRoot "Nozzles"), (Join-Path $workDirRoot "Sketches"), (Join-Path $workDirRoot "Tests"))) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}
foreach ($name in @("KNSU-32-RT65.json")) {
    Copy-Item (Join-Path $Fixtures "inputs\$name") (Join-Path $workDirRoot "Engines\$name") -Force
}
Copy-Item (Join-Path $Fixtures "inputs\BN1.json") (Join-Path $workDirRoot "Nozzles\BN1.json") -Force
Copy-Item (Join-Path $Fixtures "inputs\config.json") $workDirRoot -Force
Copy-Item (Join-Path $Fixtures "inputs\database.db") (Join-Path $dataDir "database.db") -Force

# -- sidecar ----------------------------------------------------------------
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonExe
$psi.Arguments = "-s -X utf8 -m openred_engine"
$psi.WorkingDirectory = $engineDir
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$env_vars = @{
    PYTHONNOUSERSITE        = "1"
    PYTHONUTF8              = "1"
    PYTHONDONTWRITEBYTECODE = "1"
    MPLBACKEND              = "Agg"
    MPLCONFIGDIR            = (Join-Path $dataDir "mpl-data")
    OPENRED_DATA_DIR        = $dataDir
    OPENRED_RESOURCE_DIR    = $engineDir
    OPENRED_WORKDIR         = $workDirRoot
    PYTHONPATH              = $engineDir
}
foreach ($key in $env_vars.Keys) { $psi.EnvironmentVariables[$key] = $env_vars[$key] }

$process = [System.Diagnostics.Process]::Start($psi)
$stderrTask = $process.StandardError.ReadToEndAsync()
$nextId = 1
$consoleLines = New-Object System.Collections.Generic.List[string]
$records = New-Object System.Collections.Generic.List[object]

function Read-Line-WithTimeout {
    param([int]$Timeout)
    $task = $process.StandardOutput.ReadLineAsync()
    if (-not $task.Wait($Timeout)) { throw "timeout waiting for sidecar stdout (is the engine stuck?)" }
    return $task.Result
}

function Invoke-Rpc {
    param([string]$Method, $Params, [int]$Timeout = $TimeoutMs)
    $id = $script:nextId
    $script:nextId += 1
    $request = @{ id = $id; method = $Method; params = $Params } | ConvertTo-Json -Depth 30 -Compress
    $process.StandardInput.WriteLine($request)
    $process.StandardInput.Flush()
    $deadline = [DateTime]::UtcNow.AddMilliseconds($Timeout)
    while ([DateTime]::UtcNow -lt $deadline) {
        $remaining = [int]([Math]::Max(1, ($deadline - [DateTime]::UtcNow).TotalMilliseconds))
        $line = Read-Line-WithTimeout -Timeout $remaining
        if (-not $line) { throw "sidecar closed stdout while waiting for $Method" }
        $message = $line | ConvertFrom-Json
        if ($message.PSObject.Properties.Name -contains "method" -and $message.method -eq "event") {
            switch ($message.params.name) {
                "console" { $script:consoleLines.Add([string]$message.params.line) }
                "record" { $script:records.Add($message.params) }
                "job_done" { }
                default { }
            }
            continue
        }
        if ($message.id -eq $id) {
            if ($message.PSObject.Properties.Name -contains "error") {
                throw "RPC $Method failed: $($message.error | ConvertTo-Json -Compress)"
            }
            return $message.result
        }
    }
    throw "timeout waiting for RPC $Method"
}

function Assert-Close {
    param([double]$Actual, [double]$Expected, [string]$Label, [double]$Rel = 1e-9)
    $diff = [Math]::Abs($Actual - $Expected)
    $tolerance = [Math]::Max([Math]::Abs($Expected) * $Rel, 1e-12)
    if ($diff -gt $tolerance) { throw "$Label mismatch: expected $Expected, got $Actual (diff $diff)" }
}

$failures = New-Object System.Collections.Generic.List[string]
try {
    Write-Host "[smoke] app.ping"
    $ping = Invoke-Rpc -Method "app.ping" -Params @{}
    if (-not $ping.version) { $failures.Add("app.ping returned no version") }
    if ((Resolve-Path $ping.resourceDir).Path -ne $engineDir) { $failures.Add("app.ping resourceDir=$($ping.resourceDir) expected $engineDir") }

    Write-Host "[smoke] workspace.set_dir"
    $workspace = Invoke-Rpc -Method "workspace.set_dir" -Params @{ path = $workDirRoot }
    if (-not $workspace.hasConfig) { $failures.Add("workspace.set_dir did not load config.json") }

    Write-Host "[smoke] adiabatic.calculate"
    $adiabaticFixture = Get-Content (Join-Path $Fixtures "adiabatic_knsu.json") -Raw | ConvertFrom-Json
    $adiabatic = Invoke-Rpc -Method "adiabatic.calculate" -Params $adiabaticFixture.rpc.params
    foreach ($key in @("tSol", "gamma", "cChar")) {
        Assert-Close -Actual ([double]$adiabatic.$key) -Expected ([double]$adiabaticFixture.outputs.$key) -Label "adiabatic.$key"
    }

    Write-Host "[smoke] engine.calculate (reduced)"
    $engineFixture = Get-Content (Join-Path $Fixtures "engine_knsu_smoke.json") -Raw | ConvertFrom-Json
    $engineResult = Invoke-Rpc -Method "engine.calculate" -Params $engineFixture.rpc.params -Timeout 300000
    $expectedCount = $engineFixture.arrays.time.Count
    $actualCount = $engineResult.arrays.time.Count
    if ($actualCount -ne $expectedCount) { $failures.Add("engine.calculate samples: expected $expectedCount, got $actualCount") }
    $lastIndex = [Math]::Min($actualCount, $expectedCount) - 1
    if ($lastIndex -ge 0) {
        Assert-Close -Actual ([double]$engineResult.arrays.pressure[$lastIndex]) -Expected ([double]$engineFixture.arrays.pressure[$lastIndex]) -Label "engine.pressure[last]"
        Assert-Close -Actual ([double]$engineResult.arrays.mass[$lastIndex]) -Expected ([double]$engineFixture.arrays.mass[$lastIndex]) -Label "engine.mass[last]"
    }
    Write-Host ("[smoke] console lines: {0} (fixture {1})" -f $consoleLines.Count, $engineFixture.console.Count)
} catch {
    $failures.Add($_.Exception.Message)
} finally {
    try { Invoke-Rpc -Method "app.shutdown" -Params @{} -Timeout 15000 | Out-Null } catch { }
    if (-not $process.WaitForExit(5000)) { $process.Kill() }
    $stderr = $stderrTask.Result
    if ($stderr) { Write-Host "[smoke] sidecar stderr tail:`n$(($stderr -split "`n" | Select-Object -Last 10) -join "`n")" }
}

# -- no python outside the install -----------------------------------------
$outside = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='python3.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ExecutablePath -and ($_.ExecutablePath -notlike "$InstallDir*") }
if ($outside) {
    $failures.Add("python outside the install dir: $($outside.ExecutablePath -join ', ')")
}

# -- engine.lock ------------------------------------------------------------
if (-not $SkipLockVerify) {
    $lockPath = Join-Path $engineDir "engine.lock"
    if (-not (Test-Path $lockPath)) {
        $failures.Add("engine.lock missing at $lockPath")
    } else {
        $verifyScript = Join-Path $RepoRoot "tools\packaging\make_engine_lock.py"
        if (Test-Path $verifyScript) {
            & $pythonExe $verifyScript --root $engineDir --include python openred_engine --verify $lockPath
            if ($LASTEXITCODE -ne 0) { $failures.Add("engine.lock verification failed") }
        } else {
            Write-Warning "[smoke] make_engine_lock.py not found; skipping lock verification"
        }
    }
}

Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue

if ($failures.Count -gt 0) {
    Write-Host "[smoke] FAIL ($($failures.Count) issue(s))"
    foreach ($failure in $failures) { Write-Host "  - $failure" }
    exit 1
}
Write-Host "[smoke] PASS: bundle self-sufficient, fixture workspace and T0/T1 parity spot-checks OK"
exit 0
