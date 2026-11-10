[CmdletBinding()]
param(
    [ValidateSet('CampaignOpening','ScriptedObservation','FiveTurnGameplay')][string]$Scenario = 'CampaignOpening',
    [ValidateSet('Deterministic','Live','ScriptedGameplay')][string]$Mode = 'Deterministic',
    [switch]$AuthorizeLiveProvider,
    [switch]$CaptureResponse,
    [switch]$Latest,
    [ValidateRange(0,65535)][int]$Port = 0,
    [ValidateSet('success','truncation','invalid_json','envelope','semantic','safe_nonresolution','exception','admission','empty','incomplete')][string]$FixtureResponse = 'success',
    [string]$PythonExecutable
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$previousPath = $env:PYTHONPATH
try {
    if (-not $PythonExecutable) {
        $localPython = Join-Path $repo '.venv/Scripts/python.exe'
        if (Test-Path -LiteralPath $localPython) {
            & $localPython --version 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { $PythonExecutable = $localPython }
        }
        if (-not $PythonExecutable) {
            $bundledPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
            if (Test-Path -LiteralPath $bundledPython) {
                $PythonExecutable = $bundledPython
                $env:PYTHONPATH = (Join-Path $repo '.venv/Lib/site-packages') + [IO.Path]::PathSeparator + $previousPath
            } else { throw 'Python environment unavailable. Install requirements.txt in .venv or pass -PythonExecutable.' }
        }
    }
    $env:PYTHONPATH = $repo + [IO.Path]::PathSeparator + $env:PYTHONPATH
    $arguments = @('-m','tools.playtest.runner','--scenario',$Scenario,'--mode',$Mode,'--port',"$Port",'--fixture-response',$FixtureResponse)
    if ($AuthorizeLiveProvider) { $arguments += '--authorize-live-provider' }
    if ($CaptureResponse) { $arguments += '--capture-response' }
    if ($Latest) { $arguments += '--latest' }
    & $PythonExecutable @arguments
    $playtestExit = $LASTEXITCODE
} finally {
    $env:PYTHONPATH = $previousPath
}
exit $playtestExit
