# Prepara o LibreOffice portátil a partir do MSI oficial (baixado pelo instalador do FileDocs).
# Extrai sem instalar no sistema, junta o runtime do Visual C++ e as fontes, e tira o que não serve para converter.
#   libreoffice.ps1 -Msi <arquivo.msi> -Target <pasta>
param([Parameter(Mandatory)][string]$Msi, [Parameter(Mandatory)][string]$Target)
$ErrorActionPreference = "Stop"

$tmp = Join-Path $env:TEMP "filedocs-lo-$PID"
Start-Process msiexec.exe -ArgumentList "/a `"$Msi`" /qn TARGETDIR=`"$tmp`"" -Wait
if (-not (Test-Path "$tmp\program\soffice.exe")) { throw "Falha ao extrair o LibreOffice" }

Remove-Item $Target -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $Target | Out-Null
foreach ($p in "program", "share", "presets") { Move-Item "$tmp\$p" $Target }
Move-Item "$tmp\LICENSE.html", "$tmp\NOTICE" $Target
Copy-Item "$tmp\System64\*.dll" "$Target\program" -Force   # runtime do Visual C++
$fonts = "$Target\share\fonts\truetype"; New-Item -ItemType Directory -Force $fonts | Out-Null
Get-ChildItem "$tmp\Fonts" | Where-Object Name -match '^(Carlito|Caladea|Liberation|DejaVu|opens___)' |
    Copy-Item -Destination $fonts   # compatíveis com Calibri/Cambria/Arial/Times + marcadores
Remove-Item $tmp -Recurse -Force

foreach ($p in "share\gallery", "share\template", "share\wizards", "share\extensions", "program\classes") {
    Remove-Item "$Target\$p" -Recurse -Force -ErrorAction SilentlyContinue
}
Get-ChildItem "$Target\program\resource" -Directory | Where-Object Name -notin "pt_BR", "pt" | Remove-Item -Recurse -Force
Get-ChildItem "$Target\share\registry\res" -File | Where-Object Name -notmatch '_(en-US|pt-BR|pt)\.xcd$' | Remove-Item -Force
Get-ChildItem "$Target\share\config" -Filter "images_*.zip" | Where-Object Name -ne "images_colibre.zip" | Remove-Item -Force
