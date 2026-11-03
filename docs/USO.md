# Guia de uso

O FileDocs segue o tema claro ou escuro e a cor de destaque do Windows automaticamente.

## Pela janela

1. Abra o FileDocs (atalho na Área de Trabalho ou no Menu Iniciar).
2. Escolha a ferramenta na barra da esquerda.
3. Arraste arquivos (ou uma pasta inteira) para a janela, ou clique em **Selecionar arquivos**.
4. Ajuste as opções da ferramenta, como nível de compressão, idioma do OCR ou formato.
5. Em **Salvar em**, escolha **Mesma pasta do original** ou **Outra pasta**. A escolha fica memorizada.
6. Clique no botão azul com o nome da ferramenta (atalho: `Ctrl+Enter`).

Ao terminar, aparecem os botões **Mostrar na pasta** e **Abrir**. Na compressão, o app mostra quanto o arquivo diminuiu.

### Lista de arquivos

- **Juntar PDF:** a ordem da lista é a ordem do arquivo final. Arraste os itens ou use as setas para reordenar.
- Arquivos que a ferramenta não aceita ficam apagados, com um aviso, e o botão só libera depois de removê-los.
- Clique direito num item para abrir, mostrar na pasta ou remover; `Delete` também remove.
- Ao soltar arquivos com a lista vazia, o app escolhe sozinho uma ferramenta compatível (por exemplo, fotos vão para **Imagem para PDF**).

### Campos de páginas

`1-3, 5, 8-` = páginas de 1 a 3, a página 5 e da 8 até o fim.

## Pelo clique direito

Clique com o botão direito no arquivo → **Mostrar mais opções** → **FileDocs**.

| Arquivo | Sempre | Só com um arquivo selecionado |
|---|---|---|
| PDF | Abrir no FileDocs, Juntar PDFs…, Comprimir, OCR, Converter para imagens PNG | Dividir em páginas, Girar 90°, Extrair páginas…, Remover páginas… |
| Imagem | Abrir no FileDocs, Converter para PDF (um por imagem), Juntar em um PDF…, Converter para JPG/PNG, OCR | — |
| Word/Excel/PPT | Abrir no FileDocs, Converter para PDF | — |

- Itens com **…** abrem a janela do FileDocs já na ferramenta certa. Em **Juntar**, os arquivos chegam em ordem de nome e dá para reordenar antes de executar.
- Os demais abrem uma janelinha com o progresso. Com vários arquivos selecionados, todos são processados juntos numa única janela.
- Se der erro, o botão **Abrir no FileDocs** leva os arquivos para a janela completa.

## Word, Excel e PowerPoint para PDF

Se o computador tiver o Microsoft Office, o FileDocs usa o próprio Office (resultado idêntico ao "Salvar como PDF").
Se não tiver, o instalador oferece baixar o **LibreOffice** do site oficial durante a instalação (cerca de 360 MB).
Para ativar depois, basta executar o instalador de novo e marcar essa opção.

## Onde ficam os resultados

Na pasta escolhida em **Salvar em** (padrão: ao lado do original), com sufixo: `contrato_comprimido.pdf`, `contrato_ocr.pdf`, `contrato_unido.pdf`.
Dividir e PDF para imagem criam uma pasta. O original nunca é alterado nem sobrescrito.

## Desinstalar

Configurações do Windows → Aplicativos → FileDocs → Desinstalar. O menu de contexto sai junto.
