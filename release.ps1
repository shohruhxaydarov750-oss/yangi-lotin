[CmdletBinding()]
param(
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $projectRoot "release"
}
$releaseRoot = [System.IO.Path]::GetFullPath($OutputDirectory)

$projectFile = Get-Content -LiteralPath (Join-Path $projectRoot "pyproject.toml") -Raw
$packageFile = Get-Content -LiteralPath (Join-Path $projectRoot "yangi_lotin\__init__.py") -Raw
$versionFile = Get-Content -LiteralPath (Join-Path $projectRoot "packaging\version_info.txt") -Raw
$projectMatch = [regex]::Match($projectFile, '(?m)^version = "([0-9]+\.[0-9]+\.[0-9]+)"$')
$packageMatch = [regex]::Match($packageFile, '(?m)^__version__ = "([0-9]+\.[0-9]+\.[0-9]+)"$')
if (-not $projectMatch.Success -or -not $packageMatch.Success) {
    throw "Cannot read the project version."
}
$version = $projectMatch.Groups[1].Value
if ($packageMatch.Groups[1].Value -ne $version -or
    -not $versionFile.Contains(('ProductVersion", "{0}"' -f $version))) {
    throw "Version values in project files do not agree."
}

$expectedNames = @(
    "YangiLotin-v$version.exe",
    "YangiLotin-portable-x64-v$version.zip",
    "YangiLotin-source-v$version.zip"
)
foreach ($name in $expectedNames) {
    if (Test-Path -LiteralPath (Join-Path $releaseRoot $name)) {
        throw "Release file already exists: $name"
    }
}

& (Join-Path $projectRoot "build.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "Build failed."
}
$builtExe = Join-Path $projectRoot "dist\YangiLotin.exe"
if ((Get-Item -LiteralPath $builtExe).VersionInfo.ProductVersion -ne $version) {
    throw "The EXE version does not match the source version."
}

$stageRoot = Join-Path $projectRoot ("build\release-v" + $version + "-" + [guid]::NewGuid().ToString("N"))
$sourceStage = Join-Path $stageRoot "source"
$portableStage = Join-Path $stageRoot "portable"
New-Item -ItemType Directory -Path $sourceStage, $portableStage, $releaseRoot -Force | Out-Null

@("app.py", "build.ps1", "release.ps1", "README.md", "CHANGELOG.md", "LICENSE", "pyproject.toml", "requirements-build.txt", ".gitignore") |
    ForEach-Object { Copy-Item -LiteralPath (Join-Path $projectRoot $_) -Destination $sourceStage }
foreach ($subdir in @("yangi_lotin", "tests", "packaging")) {
    $destination = Join-Path $sourceStage $subdir
    New-Item -ItemType Directory -Path $destination | Out-Null
    $filter = if ($subdir -eq "packaging") { "*.txt" } else { "*.py" }
    Get-ChildItem -LiteralPath (Join-Path $projectRoot $subdir) -File -Filter $filter |
        Copy-Item -Destination $destination
}
Copy-Item -LiteralPath (Join-Path $projectRoot "packaging\YangiLotin.ico") -Destination (Join-Path $sourceStage "packaging")
Copy-Item -LiteralPath (Join-Path $projectRoot "packaging\make_icon.py") -Destination (Join-Path $sourceStage "packaging")
Copy-Item -LiteralPath (Join-Path $projectRoot ".github") -Destination $sourceStage -Recurse

Copy-Item -LiteralPath $builtExe -Destination (Join-Path $portableStage "YangiLotin.exe")
Copy-Item -LiteralPath (Join-Path $projectRoot "README.md") -Destination $portableStage
Copy-Item -LiteralPath (Join-Path $projectRoot "LICENSE") -Destination $portableStage

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
function New-ReleaseZip([string]$sourceDirectory, [string]$zipPath) {
    $stream = [System.IO.File]::Create($zipPath)
    try {
        $archive = [System.IO.Compression.ZipArchive]::new(
            $stream, [System.IO.Compression.ZipArchiveMode]::Create, $false
        )
        try {
            foreach ($file in Get-ChildItem -LiteralPath $sourceDirectory -Recurse -File) {
                $relative = $file.FullName.Substring($sourceDirectory.Length + 1).Replace('\', '/')
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                    $archive,
                    $file.FullName,
                    $relative,
                    [System.IO.Compression.CompressionLevel]::Optimal
                ) | Out-Null
            }
        }
        finally {
            $archive.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}
New-ReleaseZip $sourceStage (Join-Path $releaseRoot "YangiLotin-source-v$version.zip")
New-ReleaseZip $portableStage (Join-Path $releaseRoot "YangiLotin-portable-x64-v$version.zip")
Copy-Item -LiteralPath $builtExe -Destination (Join-Path $releaseRoot "YangiLotin-v$version.exe")
Copy-Item -LiteralPath $builtExe -Destination (Join-Path $releaseRoot "YangiLotin.exe") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "README.md") -Destination $releaseRoot -Force

$hashNames = @("YangiLotin.exe") + $expectedNames
$lines = foreach ($name in $hashNames) {
    $hash = (Get-FileHash -LiteralPath (Join-Path $releaseRoot $name) -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $name"
}
[System.IO.File]::WriteAllText(
    (Join-Path $releaseRoot "SHA256SUMS.txt"),
    (($lines -join "`n") + "`n"),
    (New-Object System.Text.UTF8Encoding($false))
)

Write-Host "Ready: $releaseRoot" -ForegroundColor Green
