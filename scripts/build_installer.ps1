$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

if (-not $env:BEBRALAND_BUILD_VERSION) {
    $projectVersion = Select-String -Path "pyproject.toml" -Pattern '^\s*version\s*=\s*"([^"]+)"' |
        Select-Object -First 1
    if ($projectVersion) {
        $env:BEBRALAND_BUILD_VERSION = $projectVersion.Matches[0].Groups[1].Value
    }
}

$versionNumbers = [regex]::Matches($env:BEBRALAND_BUILD_VERSION, '\d+') |
    Select-Object -First 4 |
    ForEach-Object { [int]$_.Value }
while ($versionNumbers.Count -lt 4) {
    $versionNumbers += 0
}
$env:BEBRALAND_WINDOWS_FILE_VERSION = $versionNumbers -join "."

& (Join-Path $ProjectRoot "build_frontend.bat")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$iscc = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
$isccPath = if ($iscc) { $iscc.Source } else { $null }
if (-not $iscc) {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            $isccPath = (Get-Item -LiteralPath $candidate).FullName
            break
        }
    }
}

if (-not $isccPath) {
    throw "ISCC.exe not found. Install Inno Setup 6 or add ISCC.exe to PATH."
}

& $isccPath "installer\BebraLandLauncher.iss"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Done: $ProjectRoot\dist\BebraLand-Launcher-Setup-$env:BEBRALAND_BUILD_VERSION.exe"
