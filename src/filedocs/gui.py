"""Interface (PySide6). Segue o tema claro/escuro e a cor de destaque do Windows."""
import os
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QDir, QFileInfo, QLockFile, QRectF, QSettings, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QFontMetrics, QIcon, QImage, QKeySequence, QPainter, QPainterPath, \
    QPalette, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QFileDialog, QFileIconProvider, QFrame,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QProgressBar, QPushButton, QSizePolicy, QStackedWidget, QStyle,
                               QStyledItemDelegate, QVBoxLayout, QWidget)

from . import APP, ASSETS, __version__
from .ops import IMG_EXT, OFFICE_EXT, OPS, run

# Ícones da fonte Segoe Fluent Icons (nativa do Windows 11; MDL2 no Windows 10)
GLYPH = {"merge": "", "split": "", "extract": "", "delete": "", "rotate": "",
         "compress": "", "ocr": "", "pdf2img": "", "img2pdf": "", "convimg": "",
         "office2pdf": ""}
G_ADD, G_UP, G_DOWN, G_CLEAR, G_FOLDER, G_DROP, G_OK, G_ERR = \
    "", "", "", "", "", "", "", ""
ICON_FONTS = ["Segoe Fluent Icons", "Segoe MDL2 Assets"]
PER_FILE = set(OPS) - {"merge", "img2pdf"}  # processadas arquivo a arquivo (permite progresso)

LIGHT = dict(bg="#F3F3F3", card="#FFFFFF", input="#FFFFFF", border="#E5E5E5", strong="#C8C8C8", text="#1B1B1B",
             muted="#5D5D5D", hover="#EAEAEA", select="#E6E6E6", ok="#0F7B0F", ok_bg="#DFF6DD",
             err="#C42B1C", err_bg="#FDE7E9")
DARK = dict(bg="#202020", card="#2B2B2B", input="#1F1F1F", border="#383838", strong="#4D4D4D", text="#F5F5F5",
            muted="#A8A8A8", hover="#2D2D2D", select="#363636", ok="#6CCB5F", ok_bg="#2A3A27",
            err="#FF99A4", err_bg="#442726")
T = dict(LIGHT)  # cores em uso


def settings():
    return QSettings(APP, APP)


def icon_font(pt):
    f = QFont(); f.setFamilies(ICON_FONTS); f.setPointSizeF(pt)
    return f


def system_accent():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM") as k:
            v = winreg.QueryValueEx(k, "AccentColor")[0]  # ABGR
        return QColor(v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF)
    except OSError:
        return QColor("#0067C0")


def apply_theme(app):
    dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    T.clear(); T.update(DARK if dark else LIGHT)
    acc = system_accent()
    if dark:  # o Windows usa a variação clara do destaque no tema escuro
        acc = acc.lighter(150) if acc.lightnessF() < 0.55 else acc
    else:
        acc = acc.darker(115) if acc.lightnessF() > 0.55 else acc
    T["accent"] = acc.name()
    T["accent_hover"] = (acc.lighter(112) if dark else acc.darker(112)).name()
    T["on_accent"] = "#000000" if acc.lightnessF() > 0.6 else "#FFFFFF"
    a = acc
    T["tint"] = f"rgba({a.red()},{a.green()},{a.blue()},{40 if dark else 28})"

    pal = QPalette()
    for role, key in ((QPalette.Window, "bg"), (QPalette.Base, "card"), (QPalette.AlternateBase, "bg"),
                      (QPalette.Text, "text"), (QPalette.WindowText, "text"), (QPalette.Button, "card"),
                      (QPalette.ButtonText, "text"), (QPalette.ToolTipBase, "card"), (QPalette.ToolTipText, "text"),
                      (QPalette.PlaceholderText, "muted"), (QPalette.Highlight, "accent"),
                      (QPalette.HighlightedText, "on_accent")):
        pal.setColor(role, QColor(T[key]))
    app.setPalette(pal)
    app.setStyleSheet(QSS.format(**T))
    for w in app.topLevelWidgets():
        w.update()


QSS = """
QWidget#root, QWidget#quick {{ background: {bg}; }}
QLabel {{ background: transparent; }}
QLabel#brand {{ font-size: 12pt; font-weight: 600; }}
QLabel#group {{ color: {muted}; font-size: 9pt; padding: 14px 12px 4px 12px; }}
QLabel#title {{ font-size: 20pt; font-weight: 600; }}
QLabel#muted, QLabel#small {{ color: {muted}; }}
QLabel#small {{ font-size: 9pt; }}
QLabel#glyph {{ color: {accent}; }}
QLabel#fieldLabel {{ color: {text}; font-weight: 600; }}

QPushButton#nav {{ text-align: left; border: none; border-left: 3px solid transparent; border-radius: 4px;
                   padding: 8px 10px 8px 9px; background: transparent; }}
QPushButton#nav:hover {{ background: {hover}; }}
QPushButton#nav:checked {{ background: {select}; border-left: 3px solid {accent}; font-weight: 600; }}

QPushButton {{ background: {card}; border: 1px solid {border}; border-bottom-color: {strong};
               border-radius: 4px; padding: 6px 14px; min-height: 20px; }}
QPushButton:hover {{ background: {hover}; }}
QPushButton:pressed {{ color: {muted}; }}
QPushButton:disabled {{ color: {muted}; }}
QPushButton#icon {{ padding: 6px; min-width: 22px; }}
QPushButton#primary {{ background: {accent}; color: {on_accent}; border: 1px solid {accent}; font-weight: 600;
                       padding: 8px 22px; }}
QPushButton#primary:hover {{ background: {accent_hover}; border-color: {accent_hover}; }}
QPushButton#primary:disabled {{ background: {strong}; border-color: {strong}; color: {card}; }}
QPushButton#link {{ border: none; background: transparent; color: {accent}; padding: 2px 4px; }}
QPushButton#link:hover {{ text-decoration: underline; }}
QPushButton#chip {{ padding: 5px 14px; }}
QPushButton#chip:checked {{ background: {tint}; border: 1px solid {accent}; color: {text}; }}

QFrame#card {{ background: {card}; border: 1px solid {border}; border-radius: 8px; }}
QFrame#drop {{ background: {card}; border: 1px dashed {strong}; border-radius: 8px; }}
QFrame#drop[hover="true"] {{ border: 1px solid {accent}; background: {tint}; }}
QFrame#sep {{ background: {border}; max-height: 1px; border: none; }}

QLineEdit {{ background: {input}; border: 1px solid {border}; border-bottom: 1px solid {strong}; border-radius: 4px;
             padding: 6px 8px; selection-background-color: {accent}; }}
QLineEdit:focus {{ border-bottom: 2px solid {accent}; }}

QListWidget {{ background: transparent; border: none; outline: 0; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {strong}; border-radius: 3px; min-height: 30px; margin: 0 2px; }}
QScrollBar::handle:vertical:hover {{ background: {muted}; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ height: 0; background: none; }}

QProgressBar {{ background: {border}; border: none; border-radius: 2px; max-height: 4px; min-height: 4px; }}
QProgressBar::chunk {{ background: {accent}; border-radius: 2px; }}

QFrame#result {{ border-radius: 6px; }}
QFrame#result[ok="true"] {{ background: {ok_bg}; }}
QFrame#result[ok="false"] {{ background: {err_bg}; }}
QLabel#okGlyph {{ color: {ok}; }}
QLabel#errGlyph {{ color: {err}; }}
QToolTip {{ background: {card}; color: {text}; border: 1px solid {border}; padding: 4px 6px; }}
QMenu {{ background: {card}; border: 1px solid {border}; padding: 4px; }}
QMenu::item {{ padding: 6px 24px 6px 12px; border-radius: 4px; }}
QMenu::item:selected {{ background: {hover}; }}
"""


# ---------- utilidades ----------
def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}".replace(".", ",")
        n /= 1024
    return f"{n:.1f} TB"


def size_of(p):
    p = Path(p)
    if p.is_dir():
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    return p.stat().st_size if p.exists() else 0


def reveal(path):
    subprocess.Popen(["explorer", "/select,", str(Path(path))])


def friendly(e):
    msg = str(e) or type(e).__name__
    name = type(e).__name__
    if "Encrypted" in name or "password" in msg.lower():
        return "O PDF está protegido por senha."
    if "FileDataError" in name or "cannot open" in msg.lower():
        return "Não foi possível abrir o arquivo (corrompido ou formato inválido)."
    if isinstance(e, PermissionError):
        return "Sem permissão para salvar. O arquivo pode estar aberto em outro programa."
    return msg


def summary(op, files, outs):
    """Texto do resultado: nomes e, na compressão, quanto reduziu."""
    names = [Path(o).name for o in outs]
    text = names[0] if len(names) == 1 else f"{len(names)} arquivos gerados"
    if op == "compress" and outs:
        before, after = sum(size_of(f) for f in files), sum(size_of(o) for o in outs)
        pct = round(100 * (1 - after / before)) if before else 0
        text += f"  ·  {human(before)} → {human(after)} (-{pct}%)" if pct > 0 else "  ·  já estava otimizado"
    return text


def thumbnail(path):
    """(QPixmap, info) para a lista."""
    p, ext = Path(path), Path(path).suffix.lower()
    info = human(p.stat().st_size)
    try:
        if ext == ".pdf":
            import pymupdf
            doc = pymupdf.open(p)
            page = doc[0]
            zoom = 96 / max(page.rect.width, page.rect.height)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
            n = doc.page_count
            return QPixmap.fromImage(img), f"{info}  ·  {n} página{'s' if n > 1 else ''}"
        if ext in IMG_EXT:
            img = QImage(str(p))
            if not img.isNull():
                return QPixmap.fromImage(img.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)), \
                    f"{info}  ·  {img.width()}×{img.height()}"
    except Exception:
        info += "  ·  não foi possível ler"
    return QFileIconProvider().icon(QFileInfo(str(p))).pixmap(48, 48), info


# ---------- trabalho em segundo plano ----------
class Worker(QThread):
    progress = Signal(int, int, str)  # feitos, total, arquivo atual
    done = Signal(list, str)          # saídas, erro

    def __init__(self, op, files, param, dest):
        super().__init__()
        self.op, self.files, self.param, self.dest = op, files, param, dest

    def run(self):
        groups = [[f] for f in self.files] if self.op in PER_FILE else [self.files]
        outs = []
        for i, g in enumerate(groups):
            self.progress.emit(i, len(groups), Path(g[0]).name)
            try:
                outs += [str(o) for o in run(self.op, g, self.param, self.dest)]
            except Exception as e:
                prefix = f"{Path(g[0]).name}: " if len(groups) > 1 else ""
                return self.done.emit(outs, prefix + friendly(e))
        self.progress.emit(len(groups), len(groups), "")
        self.done.emit(outs, "")


def close_when_idle(widget, event):
    """Fechar no meio do processamento derrubaria o app: esconde e sai quando terminar."""
    w = getattr(widget, "worker", None)
    if w and w.isRunning():
        widget.hide(); w.finished.connect(QApplication.quit); event.ignore()
    else:
        event.accept()


def dest_folder():
    s = settings()
    return s.value("dest") if s.value("dest_mode", "same") == "custom" and s.value("dest") else None


# ---------- componentes ----------
class FileDelegate(QStyledItemDelegate):
    H = 60

    def sizeHint(self, opt, idx):
        return QSize(0, self.H)

    def paint(self, p, opt, idx):
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(opt.rect).adjusted(2, 2, -2, -2)
        if opt.state & QStyle.State_Selected:
            p.setBrush(QColor(T["select"])); p.setPen(Qt.NoPen); p.drawRoundedRect(r, 4, 4)
        elif opt.state & QStyle.State_MouseOver:
            p.setBrush(QColor(T["hover"])); p.setPen(Qt.NoPen); p.drawRoundedRect(r, 4, 4)

        bad = idx.data(Qt.UserRole + 2)
        p.setOpacity(0.45 if bad else 1)
        # miniatura
        pix = idx.data(Qt.DecorationRole)
        box = QRectF(r.left() + 12, r.top() + 6, 36, r.height() - 12)
        if pix and not pix.isNull():
            s = pix.size().scaled(box.size().toSize(), Qt.KeepAspectRatio)
            tr = QRectF(0, 0, s.width(), s.height()); tr.moveCenter(box.center())
            path = QPainterPath(); path.addRoundedRect(tr, 2, 2)
            p.setClipPath(path); p.drawPixmap(tr.toRect(), pix); p.setClipping(False)
            p.setPen(QColor(T["border"])); p.setBrush(Qt.NoBrush); p.drawRoundedRect(tr, 2, 2)
        # textos
        num = f"{idx.row() + 1}"
        f = QFont(opt.font); fm = QFontMetrics(f)
        right = r.right() - 14 - fm.horizontalAdvance(num)
        x = box.right() + 14
        bold = QFont(f); bold.setWeight(QFont.DemiBold)
        p.setFont(bold); p.setPen(QColor(T["text"]))
        name = QFontMetrics(bold).elidedText(idx.data(Qt.DisplayRole), Qt.ElideMiddle, int(right - x - 12))
        p.drawText(QRectF(x, r.top() + 10, right - x, 20), Qt.AlignLeft | Qt.AlignVCenter, name)
        small = QFont(f); small.setPointSizeF(f.pointSizeF() - 1)
        p.setFont(small)
        p.setPen(QColor(T["err"] if bad else T["muted"]))
        meta = "Formato não aceito nesta ferramenta" if bad else idx.data(Qt.UserRole + 1)
        p.drawText(QRectF(x, r.top() + 30, right - x, 18), Qt.AlignLeft | Qt.AlignVCenter, meta)
        p.setFont(f); p.setPen(QColor(T["muted"]))
        p.drawText(QRectF(right, r.top(), r.right() - right - 10, r.height()), Qt.AlignRight | Qt.AlignVCenter, num)
        p.restore()


class DropZone(QFrame):
    dropped = Signal(list)
    browse = Signal()

    def __init__(self):
        super().__init__(objectName="drop")
        self.setAcceptDrops(True)
        g = QLabel(G_DROP, objectName="glyph", alignment=Qt.AlignCenter); g.setFont(icon_font(26))
        t = QLabel("Arraste os arquivos para cá", alignment=Qt.AlignCenter)
        t.setStyleSheet("font-size: 12pt; font-weight: 600;")
        self.accepts = QLabel(objectName="muted", alignment=Qt.AlignCenter)
        b = QPushButton("Selecionar arquivos"); b.clicked.connect(self.browse)
        lay = QVBoxLayout(self); lay.setSpacing(8)
        lay.addStretch(); lay.addWidget(g); lay.addWidget(t); lay.addWidget(self.accepts)
        lay.addSpacing(6); lay.addWidget(b, 0, Qt.AlignCenter); lay.addStretch()

    def _hover(self, on):
        self.setProperty("hover", on); self.style().unpolish(self); self.style().polish(self)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction(); self._hover(True)

    def dragLeaveEvent(self, e):
        self._hover(False)

    def dropEvent(self, e):
        self._hover(False)
        self.dropped.emit([u.toLocalFile() for u in e.mimeData().urls()])


class Chips(QWidget):
    """Grupo de opções exclusivas (botões lado a lado)."""
    changed = Signal(str)

    def __init__(self, options, value):
        super().__init__()
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        self.group = QButtonGroup(self)
        for label, v in options:
            b = QPushButton(label, objectName="chip", checkable=True); b.setProperty("v", v)
            b.setCursor(Qt.PointingHandCursor)
            b.setChecked(v == value); self.group.addButton(b); lay.addWidget(b)
        lay.addStretch()
        self.group.buttonClicked.connect(lambda b: self.changed.emit(b.property("v")))

    def value(self):
        b = self.group.checkedButton()
        return b.property("v") if b else ""


def accept_text(exts):
    kinds = []
    if ".pdf" in exts:
        kinds.append("PDF")
    if exts & IMG_EXT:
        kinds.append("imagens (JPG, PNG, HEIC…)")
    if exts & OFFICE_EXT:
        kinds.append("Word, Excel, PowerPoint")
    return "Aceita " + " e ".join(kinds)


def file_filter(exts):
    pats = " ".join(f"*{e}" for e in sorted(exts))
    return f"Arquivos aceitos ({pats});;Todos os arquivos (*.*)"


# ---------- janela principal ----------
class Main(QWidget):
    def __init__(self):
        super().__init__(objectName="root")
        self.setWindowTitle(APP)
        self.resize(1040, 700); self.setMinimumSize(860, 600)
        self.setAcceptDrops(True)
        self.worker = None
        self.outputs = []

        # barra lateral
        side = QWidget(); side.setFixedWidth(232)
        sl = QVBoxLayout(side); sl.setContentsMargins(10, 14, 6, 12); sl.setSpacing(2)
        brand = QHBoxLayout(); brand.setContentsMargins(8, 0, 0, 6)
        logo = QLabel(); logo.setPixmap(QIcon(str(ASSETS / "logo.png")).pixmap(24, 24))
        brand.addWidget(logo); brand.addSpacing(6); brand.addWidget(QLabel(APP, objectName="brand")); brand.addStretch()
        sl.addLayout(brand)
        self.nav = QButtonGroup(self)
        group = None
        for key, (grp, title, *_r) in OPS.items():
            if grp != group:
                sl.addWidget(QLabel(grp, objectName="group")); group = grp
            b = QPushButton(f"{GLYPH[key]}    {title}", objectName="nav", checkable=True)
            b.setProperty("op", key); b.setCursor(Qt.PointingHandCursor)
            self.nav.addButton(b); sl.addWidget(b)
        sl.addStretch()
        sl.addWidget(QLabel(f"   Versão {__version__}", objectName="small"))
        self.nav.buttonClicked.connect(lambda *_: self.select_op())

        # cabeçalho
        self.title = QLabel(objectName="title")
        self.desc = QLabel(objectName="muted")

        # arquivos
        self.drop = DropZone()
        self.drop.dropped.connect(self.add); self.drop.browse.connect(self.browse)
        self.list = QListWidget()
        self.list.setItemDelegate(FileDelegate(self.list))
        self.list.setDragDropMode(QAbstractItemView.InternalMove)
        self.list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list.setMouseTracking(True)
        self.list.setContextMenuPolicy(Qt.ActionsContextMenu)
        for text, key, fn in (("Abrir", None, self.open_selected), ("Mostrar na pasta", None, self.reveal_selected),
                              ("Remover da lista", QKeySequence.Delete, self.remove)):
            a = QAction(text, self.list)
            if key:
                a.setShortcut(key); a.setShortcutContext(Qt.WidgetShortcut)
            a.triggered.connect(fn); self.list.addAction(a)
        self.list.itemDoubleClicked.connect(lambda *_: self.open_selected())
        self.list.model().rowsMoved.connect(lambda *_: self.list.viewport().update())

        files_card = QFrame(objectName="card")
        fc = QVBoxLayout(files_card); fc.setContentsMargins(6, 6, 6, 6); fc.setSpacing(4)
        fc.addWidget(self.list, 1)
        sep = QFrame(objectName="sep"); fc.addWidget(sep)
        tb = QHBoxLayout(); tb.setContentsMargins(6, 2, 6, 2); tb.setSpacing(6)
        add = QPushButton(f"{G_ADD}  Adicionar"); add.clicked.connect(self.browse)
        tb.addWidget(add)
        for g, tip, fn in ((G_UP, "Mover para cima", lambda: self.move(-1)),
                           (G_DOWN, "Mover para baixo", lambda: self.move(1)),
                           (G_CLEAR, "Remover selecionados (Delete)", self.remove)):
            b = QPushButton(g, objectName="icon"); b.setToolTip(tip); b.setFont(icon_font(10)); b.clicked.connect(fn)
            tb.addWidget(b)
        clear = QPushButton("Limpar lista", objectName="link"); clear.clicked.connect(self.clear)
        tb.addWidget(clear); tb.addStretch()
        self.count = QLabel(objectName="muted"); tb.addWidget(self.count)
        fc.addLayout(tb)

        self.stack = QStackedWidget(); self.stack.addWidget(self.drop); self.stack.addWidget(files_card)

        # opções
        opts = QFrame(objectName="card")
        self.grid = QGridLayout(opts); self.grid.setContentsMargins(16, 12, 16, 12)
        self.grid.setHorizontalSpacing(16); self.grid.setVerticalSpacing(10); self.grid.setColumnStretch(1, 1)
        self.param_label = QLabel(objectName="fieldLabel")
        self.param_box = QHBoxLayout(); self.param_box.setContentsMargins(0, 0, 0, 0)
        self.param_widget = None
        self.grid.addWidget(self.param_label, 0, 0); self.grid.addLayout(self.param_box, 0, 1)
        self.grid.addWidget(QLabel("Salvar em", objectName="fieldLabel"), 1, 0)
        drow = QHBoxLayout(); drow.setSpacing(10)
        s = settings()
        self.dest_chips = Chips([("Mesma pasta do original", "same"), ("Outra pasta", "custom")],
                                s.value("dest_mode", "same"))
        self.dest_chips.changed.connect(self.dest_changed)
        self.dest_label = QLabel(objectName="muted")
        self.dest_change = QPushButton("Alterar…", objectName="link"); self.dest_change.clicked.connect(self.pick_dest)
        drow.addWidget(self.dest_chips, 0); drow.addWidget(self.dest_label, 1); drow.addWidget(self.dest_change)
        self.grid.addLayout(drow, 1, 1)

        # rodapé: progresso/resultado + ação
        self.status = QLabel(objectName="muted")
        self.progress = QProgressBar(); self.progress.setTextVisible(False); self.progress.hide()
        self.result = QFrame(objectName="result"); self.result.hide()
        rl = QHBoxLayout(self.result); rl.setContentsMargins(12, 8, 8, 8); rl.setSpacing(10)
        self.result_glyph = QLabel(); self.result_glyph.setFont(icon_font(13))
        self.result_text = QLabel(wordWrap=True); self.result_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.result_open = QPushButton("Abrir"); self.result_open.clicked.connect(lambda: os.startfile(self.outputs[0]))
        self.result_show = QPushButton(f"{G_FOLDER}  Mostrar na pasta")
        self.result_show.clicked.connect(lambda: reveal(self.outputs[0]))
        rl.addWidget(self.result_glyph); rl.addWidget(self.result_text, 1)
        rl.addWidget(self.result_show); rl.addWidget(self.result_open)

        self.btn = QPushButton(objectName="primary"); self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(self.execute); self.btn.setShortcut(QKeySequence("Ctrl+Return"))
        foot = QHBoxLayout(); foot.setSpacing(16)
        left = QVBoxLayout(); left.setSpacing(6); left.addWidget(self.status); left.addWidget(self.progress)
        foot.addLayout(left, 1); foot.addWidget(self.btn, 0, Qt.AlignVCenter)

        main = QVBoxLayout(); main.setContentsMargins(28, 22, 28, 20); main.setSpacing(12)
        main.addWidget(self.title); main.addWidget(self.desc); main.addSpacing(4)
        main.addWidget(self.stack, 1); main.addWidget(opts); main.addWidget(self.result); main.addLayout(foot)

        root = QHBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(side); root.addLayout(main, 1)

        last = s.value("op", "merge")
        for b in self.nav.buttons():
            b.setChecked(b.property("op") == last)
        if not self.nav.checkedButton():
            self.nav.buttons()[0].setChecked(True)
        self.select_op(); self.dest_changed(s.value("dest_mode", "same"), ask=False)
        self.refresh()

    # ----- arquivos
    def files(self):
        return [self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())]

    def add(self, paths):
        was_empty = self.list.count() == 0
        have = set(self.files())
        new = []
        for p in paths:
            p = str(Path(p))
            if Path(p).is_dir():
                paths.extend(str(c) for c in sorted(Path(p).iterdir()) if c.is_file())
                continue
            if p in have or not Path(p).is_file():
                continue
            have.add(p); new.append(p)
            pix, info = thumbnail(p)
            it = QListWidgetItem(Path(p).name)
            it.setData(Qt.UserRole, p); it.setData(Qt.UserRole + 1, info); it.setData(Qt.DecorationRole, pix)
            it.setToolTip(p)
            self.list.addItem(it)
        if was_empty and new:
            self.auto_select(new)
        self.refresh()

    def auto_select(self, files):
        """Escolhe uma ferramenta compatível quando a atual não aceita os arquivos."""
        exts = {Path(f).suffix.lower() for f in files}
        if exts <= OPS[self.op()][5]:
            return
        for key in (["img2pdf"] if exts <= IMG_EXT else ["office2pdf"] if exts <= OFFICE_EXT else ["merge"]):
            for b in self.nav.buttons():
                if b.property("op") == key:
                    b.setChecked(True); self.select_op()

    def browse(self):
        s = settings()
        fs, _ = QFileDialog.getOpenFileNames(self, "Selecionar arquivos", s.value("last_dir", ""),
                                             file_filter(OPS[self.op()][5]))
        if fs:
            s.setValue("last_dir", str(Path(fs[0]).parent)); self.add(fs)

    def remove(self):
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))
        self.refresh()

    def clear(self):
        self.list.clear(); self.refresh()

    def move(self, d):
        r = self.list.currentRow(); t = r + d
        if 0 <= r < self.list.count() and 0 <= t < self.list.count():
            self.list.insertItem(t, self.list.takeItem(r)); self.list.setCurrentRow(t)

    def selected_path(self):
        it = self.list.currentItem()
        return it.data(Qt.UserRole) if it else None

    def open_selected(self):
        if p := self.selected_path():
            os.startfile(p)

    def reveal_selected(self):
        if p := self.selected_path():
            reveal(p)

    def refresh(self):
        accepted = OPS[self.op()][5]
        bad = 0
        for i in range(self.list.count()):
            it = self.list.item(i)
            is_bad = Path(it.data(Qt.UserRole)).suffix.lower() not in accepted
            it.setData(Qt.UserRole + 2, is_bad); bad += is_bad
        n = self.list.count()
        self.stack.setCurrentIndex(1 if n else 0)
        self.count.setText(f"{n} arquivo{'s' if n != 1 else ''}" if n else "")
        self.btn.setEnabled(n > 0 and not bad and not (self.worker and self.worker.isRunning()))
        if self.worker and self.worker.isRunning():
            return
        if bad:
            self.status.setText(f"{bad} arquivo(s) não são aceitos por esta ferramenta. Remova-os ou troque de ferramenta.")
        elif not n:
            self.status.setText("Adicione arquivos para começar.")
        elif self.op() == "merge":
            self.status.setText("Arraste os itens da lista para mudar a ordem.")
        else:
            self.status.setText("Pronto para executar.")
        self.list.viewport().update()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.add([u.toLocalFile() for u in e.mimeData().urls()])

    # ----- ferramenta e opções
    def op(self):
        return self.nav.checkedButton().property("op")

    def select_op(self):
        op = self.op()
        _, title, desc, _, spec, exts = OPS[op]
        settings().setValue("op", op)
        self.title.setText(title); self.desc.setText(desc)
        self.btn.setText(title)
        self.drop.accepts.setText(accept_text(exts))
        if self.param_widget:
            self.param_widget.hide(); self.param_widget.deleteLater(); self.param_widget = None
        self.param_label.setVisible(bool(spec))
        if spec:
            self.param_label.setText(spec[1])
            if spec[0] == "text":
                self.param_widget = QLineEdit(placeholderText=spec[2])
                self.param_widget.returnPressed.connect(self.execute)
            else:
                saved = settings().value(f"param/{op}", spec[3])
                self.param_widget = Chips(spec[2], saved)
                self.param_widget.changed.connect(lambda v, op=op: settings().setValue(f"param/{op}", v))
            self.param_box.addWidget(self.param_widget)
        self.result.hide()
        self.refresh()

    def param(self):
        w = self.param_widget
        return "" if w is None else w.text().strip() if isinstance(w, QLineEdit) else w.value()

    def dest_changed(self, mode, ask=True):
        s = settings()
        if mode == "custom" and (ask and not s.value("dest")):
            if not self.pick_dest():
                mode = "same"
                for b in self.dest_chips.group.buttons():
                    b.setChecked(b.property("v") == "same")
        s.setValue("dest_mode", mode)
        custom = mode == "custom" and bool(s.value("dest"))
        self.dest_label.setText(s.value("dest") if custom else "")
        self.dest_label.setToolTip(s.value("dest") or "")
        self.dest_change.setVisible(custom)

    def pick_dest(self):
        s = settings()
        d = QFileDialog.getExistingDirectory(self, "Salvar resultados em", s.value("dest", ""))
        if d:
            s.setValue("dest", str(Path(d))); s.setValue("dest_mode", "custom")
            self.dest_label.setText(str(Path(d))); self.dest_change.setVisible(True)
        return bool(d)

    # ----- execução
    def execute(self):
        fs = self.files()
        if not fs or not self.btn.isEnabled():
            return
        spec = OPS[self.op()][4]
        if spec and spec[0] == "text" and not self.param():
            self.param_widget.setFocus()
            return self.show_result([], f"Preencha o campo “{spec[1]}”.")
        self.result.hide()
        self.worker = Worker(self.op(), fs, self.param(), dest_folder())
        self.worker.progress.connect(self.on_progress)
        self.worker.done.connect(self.finished)
        self.btn.setEnabled(False); self.btn.setText("Processando…")
        self.progress.setRange(0, 0); self.progress.show()
        self.worker.start()

    def on_progress(self, done, total, name):
        if total > 1:
            self.progress.setRange(0, total); self.progress.setValue(done)
            self.status.setText(f"Processando {min(done + 1, total)} de {total}  ·  {name}" if name else "Finalizando…")
        else:
            self.status.setText(f"Processando {name}…" if name else "Finalizando…")

    def finished(self, outs, err):
        self.progress.hide()
        self.btn.setText(OPS[self.op()][1])
        self.show_result(outs, err)
        self.refresh()

    def closeEvent(self, e):
        close_when_idle(self, e)

    def show_result(self, outs, err):
        self.outputs = outs
        ok = not err
        self.result.setProperty("ok", ok); self.result.style().unpolish(self.result); self.result.style().polish(self.result)
        self.result_glyph.setText(G_OK if ok else G_ERR)
        self.result_glyph.setObjectName("okGlyph" if ok else "errGlyph")
        self.result_glyph.style().unpolish(self.result_glyph); self.result_glyph.style().polish(self.result_glyph)
        self.result_text.setText(summary(self.op(), self.files(), outs) if ok else err)
        self.result_open.setVisible(bool(outs)); self.result_show.setVisible(bool(outs))
        self.result.show()


# ---------- janelinha do clique direito ----------
class Quick(QWidget):
    def __init__(self, op, files, param):
        super().__init__(objectName="quick")
        self.op, self.files, self.param = op, list(files), param
        title = OPS[op][1]
        self.setWindowTitle(f"{title} – {APP}")
        self.setFixedWidth(480)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)

        self.glyph = QLabel(GLYPH[op], objectName="glyph"); self.glyph.setFont(icon_font(20))
        self.glyph.setFixedWidth(36); self.glyph.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.head = QLabel(title); self.head.setStyleSheet("font-size: 12pt; font-weight: 600;")
        self.sub = QLabel(objectName="muted"); self.sub.setWordWrap(True)
        self.progress = QProgressBar(); self.progress.setTextVisible(False); self.progress.setRange(0, 0)

        self.btn_show = QPushButton(f"{G_FOLDER}  Mostrar na pasta"); self.btn_show.hide()
        self.btn_open = QPushButton("Abrir"); self.btn_open.hide()
        self.btn_main = QPushButton("Abrir no FileDocs"); self.btn_main.hide()
        self.btn_close = QPushButton("Fechar", objectName="primary"); self.btn_close.hide()
        self.btn_close.clicked.connect(self.close)
        self.btn_show.clicked.connect(lambda: (reveal(self.outs[0]), self.close()))
        self.btn_open.clicked.connect(lambda: (os.startfile(self.outs[0]), self.close()))
        self.btn_main.clicked.connect(self.open_main)

        text = QVBoxLayout(); text.setSpacing(4)
        text.addWidget(self.head); text.addWidget(self.sub); text.addSpacing(8); text.addWidget(self.progress)
        top = QHBoxLayout(); top.setSpacing(12); top.addWidget(self.glyph); top.addLayout(text, 1)
        bl = QHBoxLayout(); bl.setSpacing(8)
        bl.addWidget(self.btn_main); bl.addStretch()
        bl.addWidget(self.btn_show); bl.addWidget(self.btn_open); bl.addWidget(self.btn_close)
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 18, 20, 16); lay.setSpacing(14)
        lay.addLayout(top); lay.addLayout(bl)
        self.update_sub()
        # espera um instante: o Explorer manda os outros arquivos selecionados em processos separados
        QTimer.singleShot(500, self.start)

    def add(self, files):
        if hasattr(self, "worker"):
            return False
        self.files += [f for f in files if f not in self.files]; self.update_sub()
        return True

    def update_sub(self):
        n = len(self.files)
        self.sub.setText(Path(self.files[0]).name if n == 1 else f"{n} arquivos")

    def start(self):
        self.worker = Worker(self.op, self.files, self.param, dest_folder())
        self.worker.progress.connect(self.on_progress)
        self.worker.done.connect(self.finished)
        self.worker.start()

    def on_progress(self, done, total, name):
        if total > 1:
            self.progress.setRange(0, total); self.progress.setValue(done)
            self.sub.setText(f"{min(done + 1, total)} de {total}  ·  {name}" if name else "Finalizando…")

    def finished(self, outs, err):
        self.outs = outs
        self.progress.hide()
        if err:
            self.head.setText("Não foi possível concluir")
            self.glyph.setText(G_ERR); self.glyph.setObjectName("errGlyph")
            self.sub.setText(err)
            self.btn_main.show()
        else:
            self.head.setText("Concluído")
            self.glyph.setText(G_OK); self.glyph.setObjectName("okGlyph")
            self.sub.setText(summary(self.op, self.files, outs))
            self.btn_show.setVisible(bool(outs)); self.btn_open.setVisible(len(outs) == 1)
        self.glyph.style().unpolish(self.glyph); self.glyph.style().polish(self.glyph)
        self.btn_close.show()
        self.activateWindow()

    def closeEvent(self, e):
        close_when_idle(self, e)

    def open_main(self):
        exe = [sys.executable] if getattr(sys, "frozen", False) else \
            [sys.executable, str(Path(__file__).resolve().parents[1] / "main.py")]
        subprocess.Popen(exe + self.files)
        self.close()


def _deliver(name, payload):
    """Entrega os arquivos à instância aberta: 'ok', 'busy' (já processando) ou None (não há)."""
    sock = QLocalSocket(); sock.connectToServer(name)
    if not sock.waitForConnected(200):
        return None
    sock.write("\n".join(payload).encode()); sock.waitForBytesWritten(1000)
    sock.waitForReadyRead(1500)
    return bytes(sock.readAll()).decode() or None


def _claim(name, files):
    """O primeiro processo fica com a trava e abre a janela; os demais entregam os arquivos a ele.
    Devolve a trava (este processo abre a janela) ou None (arquivos entregues)."""
    lock = QLockFile(str(Path(QDir.tempPath()) / f"{name}.lock"))
    for _ in range(40):
        if lock.tryLock(0):
            return lock
        r = _deliver(name, files)
        if r == "ok":
            return None
        if r == "busy":
            return lock  # quem tem a trava já começou: abre janela própria (sem trava)
        time.sleep(0.05)
    return lock


def _serve(name, parent, on_files):
    """on_files(lista) -> True se aceitou."""
    server = QLocalServer(parent)
    QLocalServer.removeServer(name); server.listen(name)

    def incoming():
        s = server.nextPendingConnection()
        s.waitForReadyRead(1000)
        ok = on_files(bytes(s.readAll()).decode().splitlines())
        s.write(b"ok" if ok else b"busy"); s.flush(); s.waitForBytesWritten(500)
    server.newConnection.connect(incoming)
    return server


def start(files, quick=None):
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    f = QFont(); f.setFamilies(["Segoe UI Variable Text", "Segoe UI", *ICON_FONTS]); f.setPointSizeF(10)
    app.setFont(f)
    app.setWindowIcon(QIcon(str(ASSETS / "filedocs.ico")))

    if quick:
        name = f"{APP}-{quick[0]}-{quick[1]}"
        lock = _claim(name, files)
        if lock is None:
            return 0
        apply_theme(app)
        app.styleHints().colorSchemeChanged.connect(lambda *_: apply_theme(app))
        w = Quick(quick[0], files, quick[1])
        if lock.isLocked():
            _serve(name, w, w.add)
        w.show()
        return app.exec()

    lock = _claim(APP, files)
    if lock is None:
        return 0
    apply_theme(app)
    app.styleHints().colorSchemeChanged.connect(lambda *_: apply_theme(app))
    win = Main()

    def incoming(fs):
        win.add(fs); win.showNormal(); win.raise_(); win.activateWindow()
        return True
    _serve(APP, win, incoming)
    win.add(files); win.show()
    return app.exec()
