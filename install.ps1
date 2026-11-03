# Instala o FileDocs para o usuário atual (sem admin, exceto o Tesseract via winget).
# Uso: clique direito > Executar com PowerShell   (ou: powershell -ExecutionPolicy Bypass -File install.ps1)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
}
if (-not (Test-Path "C:\Program Files\Tesseract-OCR\tesseract.exe")) {
    winget install -e --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements
}

py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -q -r requirements.txt
.\.venv\Scripts\python filedocs.py --install

# atalho na Área de Trabalho
$s = (New-Object -ComObject WScript.Shell).CreateShortcut("$env:USERPROFILE\Desktop\FileDocs.lnk")
$s.TargetPath = "$PSScriptRoot\.venv\Scripts\pythonw.exe"
$s.Arguments = "`"$PSScriptRoot\filedocs.py`""
$s.WorkingDirectory = $PSScriptRoot
$s.Save()
Write-Host "Pronto. Atalho criado na Área de Trabalho."
