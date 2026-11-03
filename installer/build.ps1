# Gera dist\FileDocs-Setup-<versão>.exe
# Requisitos só na máquina de build: Python 3.12, Tesseract (UB-Mannheim) e Inno Setup 6.
#   winget install -e --id UB-Mannheim.TesseractOCR
#   winget install -e --id JRSoftware.InnoSetup
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Set-Location $root

if (-not (Test-Path .venv)) { py -3.12 -m venv .venv }
.\.venv\Scripts\python -m pip install -q -r requirements.txt pyinstaller

# 1. Tesseract: só o executável e as DLLs (idiomas já estão em vendor\tessdata)
$tess = "C:\Program Files\Tesseract-OCR"
New-Item -ItemType Directory -Force vendor\tesseract | Out-Null
Copy-Item "$tess\tesseract.exe", "$tess\*.dll" vendor\tesseract -Force

# 2. Ícone e executável
.\.venv\Scripts\python installer\make_icon.py
.\.venv\Scripts\pyinstaller --noconfirm --clean --windowed --name FileDocs `
    --icon "$root\assets\filedocs.ico" --paths "$root\src" `
    --add-data "$root\assets;assets" --add-data "$root\vendor\tessdata;vendor\tessdata" `
    --collect-all ocrmypdf --copy-metadata pikepdf `
    --distpath dist --workpath build --specpath build `
    src\main.py
if ($LASTEXITCODE) { throw "PyInstaller falhou" }
# Tesseract copiado depois: via --add-data o PyInstaller duplica as DLLs na raiz
Copy-Item vendor\tesseract dist\FileDocs\_internal\vendor\tesseract -Recurse -Force
Remove-Item dist\FileDocs\_internal\PySide6\opengl32sw.dll -ErrorAction SilentlyContinue  # GL por software, não usado

# 3. Instalador
$version = (Select-String -Path src\filedocs\__init__.py -Pattern '__version__ = "(.+)"').Matches[0].Groups[1].Value
# antivírus às vezes trava o arquivo ao gravar o ícone: tenta de novo
foreach ($i in 1..3) {
    & "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" /Q "/DAppVersion=$version" installer\FileDocs.iss
    if (-not $LASTEXITCODE) { break }
    if ($i -eq 3) { throw "Inno Setup falhou" }
    Start-Sleep 3
}
Write-Host "Instalador: dist\FileDocs-Setup-$version.exe"
