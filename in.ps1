# in.ps1 -- set this repository up on Windows. The PowerShell twin of in.sh (#82 A, 2026-10-22).
#
#     .\in.ps1
#
# Makes .venv here if there is none (Python 3.13, through the py launcher),
# then installs the app's packages and its test tools into it, from the same
# two files in.sh reads. in.sh's apt-get lines have no Windows counterpart:
# PyQt6's Windows wheel carries Qt itself. Run it again after a round that
# moves a pin. It never touches anything outside this folder's .venv.

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

$onWindows = ($PSVersionTable.PSEdition -eq 'Desktop') -or $IsWindows
$venvPython = if ($onWindows) { Join-Path '.venv' 'Scripts\python.exe' } else { Join-Path '.venv' 'bin/python' }
$activate = if ($onWindows) { '.\.venv\Scripts\Activate.ps1' } else { '. .venv/bin/activate' }

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host 'Making .venv with Python 3.13 ...'
    if ($onWindows) { py -3.13 -m venv .venv } else { python3.13 -m venv .venv }
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $venvPython)) {
        throw 'Could not make .venv with Python 3.13. Install it (winget install -e --id Python.Python.3.13), open a new terminal, and run .\in.ps1 again.'
    }
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip could not upgrade itself; nothing else was installed.' }

& $venvPython -m pip install -r requirements.txt -r tests/requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'pip install failed. .venv is left as it is; read the error above, then run .\in.ps1 again.' }

Write-Host ''
Write-Host 'Ready. To work in this terminal, activate the venv:'
Write-Host "    $activate"
