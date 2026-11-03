# Desenvolvimento

## Preparar o ambiente

```powershell
winget install -e --id Python.Python.3.12
winget install -e --id UB-Mannheim.TesseractOCR   # o build copia o executável dele
winget install -e --id JRSoftware.InnoSetup       # só para gerar o instalador
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Rodar

```powershell
.venv\Scripts\python src\main.py                        # interface
.venv\Scripts\python src\main.py --cli --op merge a.pdf b.pdf
.venv\Scripts\python tests\test_ops.py                  # teste das operações
```

## Gerar o instalador

```powershell
powershell -ExecutionPolicy Bypass -File installer\build.ps1
```

Gera `dist\FileDocs-Setup-<versão>.exe`, que:

- instala em `%LOCALAPPDATA%\Programs\FileDocs` sem pedir administrador;
- já leva Python, Qt, PyMuPDF, OCRmyPDF, Tesseract e os idiomas: o usuário não instala nada à parte;
- cria os atalhos e registra o menu de contexto (`FileDocs.exe --install-menu`); a desinstalação remove tudo.

A versão fica em `src/filedocs/__init__.py` (`__version__`).

## Arquitetura

| Arquivo | Papel |
|---|---|
| `src/main.py` | argumentos: interface, `--op` (janela rápida do menu), `--cli`, `--install-menu` |
| `filedocs/ops.py` | operações; cada uma é `f(arquivos, parâmetro) -> [saídas]`, registradas em `OPS` |
| `filedocs/gui.py` | janela principal + janela rápida; instância única via `QLocalServer` |
| `filedocs/shell.py` | chaves em `HKCU\Software\Classes\SystemFileAssociations\<ext>\shell\FileDocs` |
| `filedocs/__init__.py` | caminhos (dev ou .exe) e `PATH`/`TESSDATA_PREFIX` do Tesseract |

**Nova operação:** escreva `op_x(files, param)` em `ops.py` e adicione a entrada em `OPS`. A interface mostra a ferramenta automaticamente. Para aparecer no clique direito, adicione também em `MENU` (`shell.py`).

## Bibliotecas

| Uso | Biblioteca | Licença |
|---|---|---|
| PDF, imagens, compressão | PyMuPDF | AGPL |
| OCR | OCRmyPDF + Tesseract | MPL / Apache |
| Interface | PySide6 (Qt) | LGPL |
| Imagens/HEIC | Pillow, pillow-heif | MIT-CMU / BSD |
