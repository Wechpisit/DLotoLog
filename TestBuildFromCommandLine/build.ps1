# Syncs D-Loto.py from the project root (single source of truth) into this
# build folder, then runs PyInstaller against the spec file here.
#
# Usage: run from anywhere, e.g.:
#   powershell -File "TestBuildFromCommandLine/build.ps1"

$ErrorActionPreference = "Stop"

$BuildDir = $PSScriptRoot
$RootDir = Split-Path $BuildDir -Parent
$SourceFile = Join-Path $RootDir "D-Loto.py"
$DestFile = Join-Path $BuildDir "D-Loto.py"

Write-Host "Syncing D-Loto.py from root into TestBuildFromCommandLine..."
Copy-Item -Path $SourceFile -Destination $DestFile -Force

Write-Host "Remember to set ENV = 'prod' in D-Loto.py (root) before building for production."

Push-Location $BuildDir
try {
    pyinstaller D-Loto.spec
} finally {
    Pop-Location
}
