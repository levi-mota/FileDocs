"""Operações. Cada uma recebe (arquivos, parâmetro) e devolve a lista de saídas."""
import re
import shutil
import subprocess
from pathlib import Path

import pymupdf

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".heic", ".gif"}
OFFICE_EXT = {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".rtf", ".txt"}


def out_path(src, suffix, ext=None):
    """arquivo_suffix.ext ao lado do original, sem sobrescrever."""
    src = Path(src)
    p = src.with_name(f"{src.stem}_{suffix}{ext if ext is not None else src.suffix}")
    n = 2
    while p.exists():
        p = src.with_name(f"{src.stem}_{suffix}_{n}{ext if ext is not None else src.suffix}")
        n += 1
    return p


def parse_pages(spec, total):
    """'1-3,5,8-' -> [0,1,2,4,7..total-1] (base 0)."""
    pages = []
    for part in (spec or "").replace(" ", "").split(","):
        if not part:
            continue
        m = re.fullmatch(r"(\d*)-(\d*)", part)
        if m:
            a, b = int(m[1] or 1), int(m[2] or total)
        elif part.isdigit():
            a = b = int(part)
        else:
            raise ValueError(f"Intervalo inválido: {part}")
        if not 1 <= a <= b <= total:
            raise ValueError(f"Páginas fora do intervalo 1-{total}: {part}")
        pages += range(a - 1, b)
    if not pages:
        raise ValueError("Informe as páginas, ex.: 1-3,5")
    return pages


def _as_pdf(f):
    """Abre PDF; imagens viram PDF de uma página."""
    if Path(f).suffix.lower() in IMG_EXT:
        return pymupdf.open("pdf", pymupdf.open(f).convert_to_pdf())
    return pymupdf.open(f)


def _save(doc, dst):
    doc.save(dst, garbage=3, deflate=True)
    return dst


def op_merge(files, _=""):
    out = pymupdf.open()
    for f in files:
        out.insert_pdf(_as_pdf(f))
    return [_save(out, out_path(files[0], "unido", ".pdf"))]


def op_split(files, _=""):
    res = []
    for f in files:
        doc = pymupdf.open(f)
        folder = out_path(f, "paginas", "")
        folder.mkdir()
        for i in range(doc.page_count):
            one = pymupdf.open()
            one.insert_pdf(doc, from_page=i, to_page=i)
            one.save(folder / f"{Path(f).stem}_p{i + 1:03}.pdf")
        res.append(folder)
    return res


def op_extract(files, spec):
    res = []
    for f in files:
        doc = pymupdf.open(f)
        doc.select(parse_pages(spec, doc.page_count))
        res.append(_save(doc, out_path(f, "extraido")))
    return res


def op_delete(files, spec):
    res = []
    for f in files:
        doc = pymupdf.open(f)
        drop = set(parse_pages(spec, doc.page_count))
        if len(drop) == doc.page_count:
            raise ValueError("Não é possível remover todas as páginas")
        doc.select([i for i in range(doc.page_count) if i not in drop])
        res.append(_save(doc, out_path(f, "editado")))
    return res


def op_rotate(files, angle="90"):
    angle = int(angle or 90)
    if angle % 90:
        raise ValueError("Use 90, 180 ou 270")
    res = []
    for f in files:
        doc = pymupdf.open(f)
        for p in doc:
            p.set_rotation((p.rotation + angle) % 360)
        res.append(_save(doc, out_path(f, "girado")))
    return res


def op_compress(files, quality=""):
    """Recomprime imagens (JPEG ~150 dpi) e limpa objetos."""
    q = max(1, min(100, int(quality or 60)))
    res = []
    for f in files:
        doc = pymupdf.open(f)
        doc.rewrite_images(dpi_threshold=160, dpi_target=150, quality=q,
                           lossy=True, lossless=True, bitonal=True, color=True, gray=True)
        dst = out_path(f, "comprimido")
        doc.save(dst, garbage=4, deflate=True, clean=True, use_objstms=True)
        if dst.stat().st_size >= Path(f).stat().st_size:  # nunca entregar maior
            shutil.copyfile(f, dst)
        res.append(dst)
    return res


def op_ocr(files, lang=""):
    import ocrmypdf
    res = []
    for f in files:
        dst = out_path(f, "ocr", ".pdf")
        src = f
        if Path(f).suffix.lower() in IMG_EXT:
            src = op_img2pdf([f])[0]
        try:
            # use_threads: evita multiprocessing, que não combina com o .exe
            ocrmypdf.ocr(src, dst, language=(lang or "por+eng").split("+"), skip_text=True,
                         output_type="pdf", rotate_pages=True, progress_bar=False, use_threads=True)
        finally:
            if src != f:
                Path(src).unlink(missing_ok=True)
        res.append(dst)
    return res


def op_img2pdf(files, _=""):
    out = pymupdf.open()
    for f in files:
        out.insert_pdf(_as_pdf(f))
    return [_save(out, out_path(files[0], "imagens" if len(files) > 1 else "pdf", ".pdf"))]


def op_pdf2img(files, fmt="png"):
    fmt = (fmt or "png").lower().lstrip(".")
    res = []
    for f in files:
        doc = pymupdf.open(f)
        folder = out_path(f, "imagens", "")
        folder.mkdir()
        for i, p in enumerate(doc):
            p.get_pixmap(dpi=150).save(folder / f"{Path(f).stem}_p{i + 1:03}.{fmt}")
        res.append(folder)
    return res


def op_convert_img(files, fmt="jpg"):
    from PIL import Image
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    fmt = (fmt or "jpg").lower().lstrip(".")
    res = []
    for f in files:
        im = Image.open(f)
        if fmt in ("jpg", "jpeg", "bmp") and im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        dst = out_path(f, "convertido", "." + fmt)
        if fmt in ("jpg", "jpeg", "webp"):
            im.save(dst, quality=90)
        else:
            im.save(dst)
        res.append(dst)
    return res


def soffice():
    for p in (shutil.which("soffice"), r"C:\Program Files\LibreOffice\program\soffice.exe"):
        if p and Path(p).exists():
            return p


def op_office2pdf(files, _=""):
    exe = soffice()
    if not exe:
        raise RuntimeError("LibreOffice não encontrado. Instale com:\nwinget install TheDocumentFoundation.LibreOffice")
    res = []
    for f in map(Path, files):
        subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", str(f.parent), str(f)],
                       check=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=300)
        res.append(f.with_suffix(".pdf"))
    return res


# id: (grupo, título, descrição, função, dica do parâmetro, valor padrão)
OPS = {
    "merge":    ("PDF", "Juntar", "Une PDFs e imagens na ordem da lista", op_merge, None, ""),
    "split":    ("PDF", "Dividir", "Uma página por arquivo", op_split, None, ""),
    "extract":  ("PDF", "Extrair páginas", "Gera um PDF só com as páginas escolhidas", op_extract, "Páginas (ex.: 1-3,5,8-)", ""),
    "delete":   ("PDF", "Remover páginas", "Tira páginas do PDF", op_delete, "Páginas (ex.: 2,4-6)", ""),
    "rotate":   ("PDF", "Girar", "Gira todas as páginas", op_rotate, "Graus (90, 180, 270)", "90"),
    "compress": ("PDF", "Comprimir", "Reduz o tamanho recomprimindo imagens", op_compress, "Qualidade 1-100", "60"),
    "ocr":      ("PDF", "OCR", "Torna PDFs e imagens pesquisáveis", op_ocr, "Idiomas", "por+eng"),
    "pdf2img":  ("Converter", "PDF → Imagens", "Cada página vira uma imagem", op_pdf2img, "Formato (png, jpg)", "png"),
    "img2pdf":  ("Converter", "Imagens → PDF", "Junta imagens num PDF", op_img2pdf, None, ""),
    "convimg":  ("Converter", "Converter imagem", "JPG, PNG, WEBP, HEIC, BMP, TIF, ICO", op_convert_img, "Formato de saída", "jpg"),
    "office2pdf": ("Converter", "Office → PDF", "Word, Excel, PowerPoint (requer LibreOffice)", op_office2pdf, None, ""),
}


def run(op, files, param=""):
    return OPS[op][3](files, param)
