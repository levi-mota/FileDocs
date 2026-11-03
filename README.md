# FileDocs

Conversor e manipulador de PDF 100% local para Windows (tipo iLovePDF, mas sem enviar nada para a internet).

**PDF:** juntar, dividir, extrair/remover páginas, girar, comprimir, OCR (português + inglês), PDF → imagens.
**Imagens:** converter entre JPG/PNG/WEBP/HEIC/BMP/TIF, imagens → PDF, OCR de imagem.
**Office:** DOCX/XLSX/PPTX → PDF (requer LibreOffice: `winget install TheDocumentFoundation.LibreOffice`).

## Instalação

1. Baixe/clone esta pasta para um lugar fixo (ex.: `C:\FileDocs`).
2. Clique direito em `install.ps1` → **Executar com PowerShell**.

Isso instala Python e Tesseract (se faltarem), as bibliotecas, o menu de contexto e um atalho na Área de Trabalho.

## Uso

- **Clique direito** num PDF/imagem → *Mostrar mais opções* → **FileDocs** → Comprimir, OCR, Converter…
- **Abrir no FileDocs** (ou o atalho): janela onde se arrasta arquivos, ordena e escolhe a operação.
- Os resultados ficam ao lado do original (`arquivo_comprimido.pdf`, `arquivo_ocr.pdf`…); nada é sobrescrito.

Remover o menu: `.venv\Scripts\python filedocs.py --uninstall`
Teste: `.venv\Scripts\python test_filedocs.py`
