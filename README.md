<p align="center"><img src="assets/logo.png" width="96" alt="FileDocs"></p>

# FileDocs

Conversor e editor de PDF **100% local** para Windows, no estilo do iLovePDF, mas sem enviar nenhum arquivo para a internet.
Funciona pelo **clique direito** no Explorer e tem **interface própria**.

| PDF | Converter |
|---|---|
| Juntar, dividir, extrair e remover páginas | PDF → imagens (PNG/JPG) |
| Girar páginas | Imagens → PDF |
| Comprimir | Converter imagens (JPG, PNG, WEBP, HEIC, BMP, TIF, ICO) |
| OCR em português e inglês (PDF pesquisável) | Word/Excel/PowerPoint → PDF* |

\* Office → PDF exige o LibreOffice instalado (`winget install TheDocumentFoundation.LibreOffice`).

## Instalar (usuários)

1. Baixe `FileDocs-Setup-x.y.z.exe` na página **Releases** do GitHub.
2. Execute e avance. Não precisa ser administrador nem instalar mais nada.

Veja o [guia de uso](docs/USO.md).

## Desenvolver

```
src/
  main.py              ponto de entrada (argumentos de linha de comando)
  filedocs/
    __init__.py        versão, caminhos e ambiente (Tesseract)
    ops.py             operações (juntar, OCR, comprimir...)
    gui.py             interface PySide6
    shell.py           menu de contexto do Explorer
assets/                logo (SVG/PNG/ICO)
vendor/tessdata/       idiomas do OCR (por, eng, osd)
installer/             build.ps1, FileDocs.iss (Inno Setup), make_icon.py
tests/test_ops.py      teste das operações
docs/                  documentação
```

Detalhes em [docs/DESENVOLVIMENTO.md](docs/DESENVOLVIMENTO.md).
