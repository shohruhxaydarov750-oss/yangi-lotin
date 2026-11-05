[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$venvRoot = Join-Path $projectRoot ".venv-build"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyLauncher) {
        & $pyLauncher.Source -3 -m venv $venvRoot
    }
    else {
        $systemPython = Get-Command python -ErrorAction Stop
        & $systemPython.Source -m venv $venvRoot
    }
}

Push-Location $projectRoot
try {
    & $venvPython -m pip install --disable-pip-version-check --quiet --upgrade pip
    & $venvPython -m pip install --disable-pip-version-check --quiet -r requirements-build.txt
    & $venvPython -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) {
        throw "Tests failed; executable was not built."
    }

    $entryPoint = Join-Path $projectRoot "app.py"
    $versionFile = Join-Path $projectRoot "packaging\version_info.txt"
    $iconFile = Join-Path $projectRoot "packaging\YangiLotin.ico"
    $distPath = Join-Path $projectRoot "dist"
    $workPath = Join-Path $projectRoot "build\pyinstaller"
    $specPath = Join-Path $projectRoot "build"
    $pyInstallerArgs = @(
        "--noconfirm",
        "--clean",
        "--noupx",
        "--onefile",
        "--windowed",
        "--name", "YangiLotin",
        "--hidden-import", "comtypes.stream",
        "--icon", $iconFile,
        "--add-data", "$iconFile;packaging",
        "--version-file", $versionFile,
        "--distpath", $distPath,
        "--workpath", $workPath,
        "--specpath", $specPath,
        $entryPoint
    )

    & $venvPython -m PyInstaller @pyInstallerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed."
    }

    Write-Host ""
    Write-Host "Ready: $distPath\YangiLotin.exe" -ForegroundColor Green
}
finally {
    Pop-Location
}
