"""FileDocs - conversor e manipulador de PDF local para Windows.

Uso:
  pythonw filedocs.py [arquivos...]            abre a interface
  pythonw filedocs.py --op compress arq.pdf    executa uma operação direto
  python  filedocs.py --install | --uninstall  menu de contexto do Explorer
"""
import os, re, shutil, subprocess, sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
TESS_DIR = Path(r"C:\Program Files\Tesseract-OCR")
os.environ["TESSDATA_PREFIX"] = str(HERE / "tessdata")
if TESS_DIR.exists():
    os.environ["PATH"] = str(TESS_DIR) + os.pathsep + os.environ["PATH"]

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".heic", ".gif"}
OFFICE_EXT = {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".rtf", ".txt"}


# ---------- utilidades ----------
def out_path(src, suffix, ext=None):
    """arquivo_suffix.ext ao lado do original, sem sobrescrever."""
    src = Path(src)
    p = src.with_name(f"{src.stem}_{suffix}{ext or src.suffix}")
    n = 2
    while p.exists():
        p = src.with_name(f"{src.stem}_{suffix}_{n}{ext or src.suffix}")
        n += 1
    return p


def parse_pages(spec, total):
    """'1-3,5,8-' -> [0,1,2,4,7..total-1] (índices base 0)."""
    pages = []
    for part in spec.replace(" ", "").split(","):
        if not part:
            continue
        m = re.fullmatch(r"(\d*)-(\d*)", part)
        if m:
            a = int(m[1] or 1); b = int(m[2] or total)
        elif part.isdigit():
            a = b = int(part)
        else:
            raise ValueError(f"Intervalo inválido: {part}")
        if not (1 <= a <= b <= total):
            raise ValueError(f"Páginas fora do intervalo 1-{total}: {part}")
        pages += range(a - 1, b)
    if not pages:
        raise ValueError("Nenhuma página informada")
    return pages


def soffice():
    for p in (shutil.which("soffice"), r"C:\Program Files\LibreOffice\program\soffice.exe"):
        if p and Path(p).exists():
            return p


# ---------- operações: (arquivos, parâmetro) -> lista de saídas ----------
def op_merge(files, _=""):
    out = pymupdf.open()
    for f in files:
        if Path(f).suffix.lower() in IMG_EXT:
            img = pymupdf.open(f)
            out.insert_pdf(pymupdf.open("pdf", img.convert_to_pdf()))
        else:
            out.insert_pdf(pymupdf.open(f))
    dst = out_path(files[0], "unido", ".pdf")
    out.save(dst, garbage=3, deflate=True)
    return [dst]


def op_split(files, _=""):
    res = []
    for f in files:
        doc = pymupdf.open(f)
        folder = out_path(f, "paginas", "")
        folder.mkdir()
        for i in range(doc.page_count):
            one = pymupdf.open(); one.insert_pdf(doc, from_page=i, to_page=i)
            one.save(folder / f"{Path(f).stem}_p{i + 1:03}.pdf")
        res.append(folder)
    return res


def op_extract(files, spec):
    res = []
    for f in files:
        doc = pymupdf.open(f)
        doc.select(parse_pages(spec, doc.page_count))
        dst = out_path(f, "extraido"); doc.save(dst, garbage=3, deflate=True); res.append(dst)
    return res


def op_delete(files, spec):
    res = []
    for f in files:
        doc = pymupdf.open(f)
        drop = set(parse_pages(spec, doc.page_count))
        doc.select([i for i in range(doc.page_count) if i not in drop])
        dst = out_path(f, "editado"); doc.save(dst, garbage=3, deflate=True); res.append(dst)
    return res


def op_rotate(files, angle="90"):
    res = []
    for f in files:
        doc = pymupdf.open(f)
        for p in doc:
            p.set_rotation((p.rotation + int(angle or 90)) % 360)
        dst = out_path(f, "girado"); doc.save(dst, garbage=3, deflate=True); res.append(dst)
    return res


def op_compress(files, quality=""):
    """Recomprime imagens (JPEG, ~150 dpi) e limpa objetos. Sem Ghostscript."""
    q = int(quality or 60)
    res = []
    for f in files:
        doc = pymupdf.open(f)
        doc.rewrite_images(dpi_threshold=160, dpi_target=150, quality=q, lossy=True, lossless=True, bitonal=True, color=True, gray=True)
        dst = out_path(f, "comprimido")
        doc.save(dst, garbage=4, deflate=True, clean=True, use_objstms=True)
        if dst.stat().st_size >= Path(f).stat().st_size:  # não piorar
            shutil.copyfile(f, dst)
        res.append(dst)
    return res


def op_ocr(files, lang=""):
    import ocrmypdf
    res = []
    for f in files:
        dst = out_path(f, "ocr", ".pdf")
        src = f
        if Path(f).suffix.lower() in IMG_EXT:  # imagem -> pdf antes
            src = op_img2pdf([f])[0]
        ocrmypdf.ocr(src, dst, language=(lang or "por+eng").split("+"), skip_text=True,
                     output_type="pdf", rotate_pages=True, deskew=False, progress_bar=False)
        if src != f:
            Path(src).unlink()
        res.append(dst)
    return res


def op_img2pdf(files, _=""):
    out = pymupdf.open()
    for f in files:
        out.insert_pdf(pymupdf.open("pdf", pymupdf.open(f).convert_to_pdf()))
    dst = out_path(files[0], "imagens" if len(files) > 1 else "pdf", ".pdf")
    out.save(dst, garbage=3, deflate=True)
    return [dst]


def op_pdf2img(files, fmt="png"):
    fmt = (fmt or "png").lower().lstrip(".")
    res = []
    for f in files:
        doc = pymupdf.open(f)
        folder = out_path(f, "imagens", ""); folder.mkdir()
        for i, p in enumerate(doc):
            p.get_pixmap(dpi=150).save(folder / f"{Path(f).stem}_p{i + 1:03}.{fmt}")
        res.append(folder)
    return res


def op_convert_img(files, fmt="jpg"):
    from PIL import Image
    try:
        import pillow_heif; pillow_heif.register_heif_opener()
    except ImportError:
        pass
    fmt = (fmt or "jpg").lower().lstrip(".")
    res = []
    for f in files:
        im = Image.open(f)
        if fmt in ("jpg", "jpeg", "bmp") and im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        dst = out_path(f, "convertido", "." + fmt)
        im.save(dst, quality=90) if fmt in ("jpg", "jpeg", "webp") else im.save(dst)
        res.append(dst)
    return res


def op_office2pdf(files, _=""):
    exe = soffice()
    if not exe:
        raise RuntimeError("LibreOffice não encontrado. Instale com: winget install TheDocumentFoundation.LibreOffice")
    res = []
    for f in files:
        f = Path(f)
        subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", str(f.parent), str(f)],
                       check=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=300)
        res.append(f.with_suffix(".pdf"))
    return res


# nome: (rótulo, função, dica do parâmetro ou None)
OPS = {
    "merge":    ("Juntar PDFs/imagens (na ordem da lista)", op_merge, None),
    "split":    ("Dividir PDF (uma página por arquivo)", op_split, None),
    "extract":  ("Extrair páginas", op_extract, "Páginas, ex.: 1-3,5,8-"),
    "delete":   ("Remover páginas", op_delete, "Páginas, ex.: 2,4-6"),
    "rotate":   ("Girar páginas", op_rotate, "Graus: 90, 180 ou 270"),
    "compress": ("Comprimir PDF", op_compress, "Qualidade JPEG 1-100 (padrão 60)"),
    "ocr":      ("OCR (tornar PDF pesquisável)", op_ocr, "Idiomas (padrão por+eng)"),
    "img2pdf":  ("Imagens → PDF", op_img2pdf, None),
    "pdf2img":  ("PDF → imagens", op_pdf2img, "Formato: png ou jpg"),
    "convimg":  ("Converter imagem", op_convert_img, "Formato: jpg, png, webp, bmp, tif, ico"),
    "office2pdf": ("Office/Texto → PDF (LibreOffice)", op_office2pdf, None),
}


# ---------- menu de contexto (HKCU, sem admin) ----------
MENU = {  # extensões -> [(id, rótulo, op, param)]
    "pdf": [("open", "Abrir no FileDocs", None, None), ("compress", "Comprimir", "compress", ""),
            ("ocr", "OCR (pesquisável)", "ocr", ""), ("pdf2img", "Converter para PNG", "pdf2img", "png")],
    "img": [("open", "Abrir no FileDocs", None, None), ("img2pdf", "Converter para PDF", "img2pdf", ""),
            ("jpg", "Converter para JPG", "convimg", "jpg"), ("png", "Converter para PNG", "convimg", "png"),
            ("ocr", "OCR → PDF pesquisável", "ocr", "")],
    "office": [("open", "Abrir no FileDocs", None, None), ("pdf", "Converter para PDF", "office2pdf", "")],
}


def _exts(group):
    return {"pdf": [".pdf"], "img": sorted(IMG_EXT), "office": sorted(OFFICE_EXT)}[group]


def install():
    import winreg as w
    pyw = Path(sys.executable).with_name("pythonw.exe")
    icon = str(HERE / "filedocs.ico") if (HERE / "filedocs.ico").exists() else str(pyw)
    for group, items in MENU.items():
        for ext in _exts(group):
            base = rf"Software\Classes\SystemFileAssociations\{ext}\shell\FileDocs"
            with w.CreateKey(w.HKEY_CURRENT_USER, base) as k:
                w.SetValueEx(k, "MUIVerb", 0, w.REG_SZ, "FileDocs")
                w.SetValueEx(k, "SubCommands", 0, w.REG_SZ, "")
                w.SetValueEx(k, "Icon", 0, w.REG_SZ, icon)
            for i, (cid, label, op, param) in enumerate(items):
                key = rf"{base}\shell\{i:02}{cid}"
                args = "" if op is None else f'--op {op} --param "{param}" '
                with w.CreateKey(w.HKEY_CURRENT_USER, key) as k:
                    w.SetValueEx(k, "MUIVerb", 0, w.REG_SZ, label)
                    # Várias seleções: o Explorer passa todos os arquivos de uma vez
                    w.SetValueEx(k, "MultiSelectModel", 0, w.REG_SZ, "Player")
                with w.CreateKey(w.HKEY_CURRENT_USER, key + r"\command") as k:
                    w.SetValueEx(k, "", 0, w.REG_SZ, f'"{pyw}" "{HERE / "filedocs.py"}" {args}"%1"')
    print("Menu de contexto instalado (Windows 11: clique direito > Mostrar mais opções).")


def uninstall():
    import winreg as w

    def rm(root, path):
        try:
            with w.OpenKey(root, path) as k:
                while True:
                    try:
                        rm(root, path + "\\" + w.EnumKey(k, 0))
                    except OSError:
                        break
            w.DeleteKey(root, path)
        except FileNotFoundError:
            pass
    for group in MENU:
        for ext in _exts(group):
            rm(w.HKEY_CURRENT_USER, rf"Software\Classes\SystemFileAssociations\{ext}\shell\FileDocs")
    print("Menu de contexto removido.")


# ---------- interface ----------
def gui(initial, quick=None):
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFileDialog, QHBoxLayout,
                                   QLabel, QLineEdit, QListWidget, QMessageBox, QPlainTextEdit, QPushButton,
                                   QVBoxLayout, QWidget)

    app = QApplication(sys.argv)

    # Explorer abre um processo por arquivo: junta tudo numa só janela
    if quick is None:
        sock = QLocalSocket(); sock.connectToServer("FileDocs")
        if sock.waitForConnected(300):
            sock.write("\n".join(initial).encode()); sock.waitForBytesWritten(1000)
            return

    class Worker(QThread):
        done = Signal(str, bool)

        def __init__(self, op, files, param):
            super().__init__(); self.op, self.files, self.param = op, files, param

        def run(self):
            try:
                outs = OPS[self.op][1](self.files, self.param)
                self.done.emit("Pronto:\n" + "\n".join(map(str, outs)), True)
            except Exception as e:
                self.done.emit(f"Erro: {e}", False)

    if quick:  # operação direta do menu de contexto, só mostra o resultado
        op, param = quick
        w = Worker(op, initial, param)
        w.done.connect(lambda msg, ok: (QMessageBox.information(None, "FileDocs", msg) if ok
                                        else QMessageBox.critical(None, "FileDocs", msg), app.quit()))
        w.start(); app.exec(); return

    win = QWidget(); win.setWindowTitle("FileDocs"); win.resize(720, 520); win.setAcceptDrops(True)
    lst = QListWidget(); lst.setDragDropMode(QAbstractItemView.InternalMove)
    lst.setSelectionMode(QAbstractItemView.ExtendedSelection)
    combo = QComboBox()
    for k, (label, _, _) in OPS.items():
        combo.addItem(label, k)
    param = QLineEdit(); hint = QLabel()
    log = QPlainTextEdit(readOnly=True)
    b_add, b_rm, b_up, b_dn, b_clear, b_run = (QPushButton(t) for t in
        ("Adicionar…", "Remover", "▲", "▼", "Limpar", "Executar"))
    b_run.setDefault(True)

    def add(paths):
        have = {lst.item(i).text() for i in range(lst.count())}
        for p in paths:
            if p and p not in have and Path(p).is_file():
                lst.addItem(p); have.add(p)

    def files():
        return [lst.item(i).text() for i in range(lst.count())]

    def move(d):
        r = lst.currentRow(); t = r + d
        if 0 <= r < lst.count() and 0 <= t < lst.count():
            lst.insertItem(t, lst.takeItem(r)); lst.setCurrentRow(t)

    def on_op():
        h = OPS[combo.currentData()][2]
        param.setVisible(bool(h)); hint.setVisible(bool(h)); hint.setText(h or ""); param.clear()

    def run():
        fs = files()
        if not fs:
            return QMessageBox.warning(win, "FileDocs", "Adicione arquivos primeiro.")
        b_run.setEnabled(False); log.appendPlainText(f"▶ {combo.currentText()} ({len(fs)} arquivo(s))…")
        win._w = Worker(combo.currentData(), fs, param.text().strip())
        win._w.done.connect(lambda msg, ok: (log.appendPlainText(msg + "\n"), b_run.setEnabled(True)))
        win._w.start()

    b_add.clicked.connect(lambda: add(QFileDialog.getOpenFileNames(win, "Arquivos")[0]))
    b_rm.clicked.connect(lambda: [lst.takeItem(lst.row(i)) for i in lst.selectedItems()])
    b_up.clicked.connect(lambda: move(-1)); b_dn.clicked.connect(lambda: move(1))
    b_clear.clicked.connect(lst.clear); b_run.clicked.connect(run)
    combo.currentIndexChanged.connect(on_op)

    win.dragEnterEvent = lambda e: e.acceptProposedAction() if e.mimeData().hasUrls() else None
    win.dropEvent = lambda e: add([u.toLocalFile() for u in e.mimeData().urls()])

    bar = QHBoxLayout()
    for b in (b_add, b_rm, b_up, b_dn, b_clear):
        bar.addWidget(b)
    bar.addStretch()
    lay = QVBoxLayout(win)
    lay.addWidget(QLabel("Arraste arquivos para cá (a ordem da lista vale para Juntar):"))
    lay.addWidget(lst, 3); lay.addLayout(bar)
    lay.addWidget(combo); lay.addWidget(hint); lay.addWidget(param); lay.addWidget(b_run)
    lay.addWidget(log, 2)
    on_op(); add(initial)

    server = QLocalServer(); QLocalServer.removeServer("FileDocs"); server.listen("FileDocs")

    def incoming():
        s = server.nextPendingConnection()
        s.waitForReadyRead(1000)
        add(bytes(s.readAll()).decode().splitlines())
        win.raise_(); win.activateWindow()
    server.newConnection.connect(incoming)

    win.show(); app.exec()


def main(argv):
    if "--install" in argv:
        return install()
    if "--uninstall" in argv:
        return uninstall()
    op = param = None
    if "--op" in argv:
        i = argv.index("--op"); op = argv[i + 1]; del argv[i:i + 2]
    if "--param" in argv:
        i = argv.index("--param"); param = argv[i + 1]; del argv[i:i + 2]
    cli = "--cli" in argv
    files = [str(Path(a).resolve()) for a in argv if a != "--cli"]
    if op and cli:  # modo texto, para scripts e testes
        for o in OPS[op][1](files, param or ""):
            print(o)
        return
    gui(files, (op, param or "") if op else None)


if __name__ == "__main__":
    main(sys.argv[1:])
