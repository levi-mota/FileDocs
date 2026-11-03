"""Interface (PySide6)."""
import os
import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMessageBox, QProgressBar, QPushButton, QStackedWidget, QVBoxLayout,
                               QWidget, QFileIconProvider)
from PySide6.QtCore import QFileInfo

from . import APP, ASSETS, __version__
from .ops import OPS, run

ACCENT = "#4F46E5"
QSS = f"""
* {{ font-family: 'Segoe UI'; font-size: 10pt; color: #1F2937; }}
QWidget#root {{ background: #F5F6FA; }}
QFrame#side {{ background: #FFFFFF; border-right: 1px solid #E5E7EB; }}
QLabel#brand {{ font-size: 15pt; font-weight: 600; }}
QLabel#group {{ color: #9CA3AF; font-size: 8pt; font-weight: 600; letter-spacing: 1px; padding: 12px 12px 4px; }}
QPushButton#tool {{ text-align: left; border: none; border-radius: 8px; padding: 8px 12px; background: transparent; }}
QPushButton#tool:hover {{ background: #F3F4F6; }}
QPushButton#tool:checked {{ background: #EEF2FF; color: {ACCENT}; font-weight: 600; }}
QLabel#title {{ font-size: 18pt; font-weight: 600; }}
QLabel#subtitle {{ color: #6B7280; }}
QFrame#drop {{ border: 2px dashed #C7D2FE; border-radius: 14px; background: #FFFFFF; }}
QFrame#drop[hover="true"] {{ border-color: {ACCENT}; background: #EEF2FF; }}
QLabel#dropText {{ color: #6B7280; font-size: 11pt; }}
QListWidget {{ border: 1px solid #E5E7EB; border-radius: 12px; background: #FFFFFF; padding: 4px; outline: 0; }}
QListWidget::item {{ padding: 6px; border-radius: 6px; }}
QListWidget::item:selected {{ background: #EEF2FF; color: #1F2937; }}
QPushButton {{ border: 1px solid #E5E7EB; border-radius: 8px; padding: 6px 12px; background: #FFFFFF; }}
QPushButton:hover {{ border-color: #C7D2FE; background: #F9FAFB; }}
QPushButton#primary {{ background: {ACCENT}; color: white; border: none; font-weight: 600; padding: 10px 28px; font-size: 11pt; }}
QPushButton#primary:hover {{ background: #4338CA; }}
QPushButton#primary:disabled {{ background: #A5B4FC; }}
QLineEdit {{ border: 1px solid #E5E7EB; border-radius: 8px; padding: 7px 10px; background: #FFFFFF; }}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QProgressBar {{ border: none; background: #E5E7EB; border-radius: 3px; max-height: 6px; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 3px; }}
QFrame#result {{ border-radius: 10px; padding: 4px; }}
QFrame#result[ok="true"] {{ background: #ECFDF5; border: 1px solid #A7F3D0; }}
QFrame#result[ok="false"] {{ background: #FEF2F2; border: 1px solid #FECACA; }}
"""


class Worker(QThread):
    done = Signal(list, str)  # saídas, erro

    def __init__(self, op, files, param):
        super().__init__()
        self.args = (op, files, param)

    def run(self):
        try:
            self.done.emit([str(o) for o in run(*self.args)], "")
        except Exception as e:  # mostrado ao usuário
            self.done.emit([], str(e) or type(e).__name__)


def open_location(path):
    p = Path(path)
    if p.is_dir():
        os.startfile(p)
    else:
        os.system(f'explorer /select,"{p}"')


def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


class Drop(QFrame):
    dropped = Signal(list)
    clicked = Signal()

    def __init__(self):
        super().__init__(objectName="drop")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(self)
        icon = QLabel(alignment=Qt.AlignCenter)
        icon.setPixmap(QIcon(str(ASSETS / "logo.png")).pixmap(56, 56))
        lay.addStretch(); lay.addWidget(icon)
        lay.addWidget(QLabel("Arraste arquivos aqui ou clique para escolher", objectName="dropText",
                             alignment=Qt.AlignCenter))
        lay.addStretch()

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

    def mouseReleaseEvent(self, e):
        self.clicked.emit()


class Main(QWidget):
    def __init__(self):
        super().__init__(objectName="root")
        self.setWindowTitle(APP)
        self.setWindowIcon(QIcon(str(ASSETS / "filedocs.ico")))
        self.resize(980, 640)
        self.setAcceptDrops(True)
        self.icons = QFileIconProvider()
        self.worker = None

        # barra lateral
        side = QFrame(objectName="side"); side.setFixedWidth(230)
        sl = QVBoxLayout(side); sl.setContentsMargins(12, 16, 12, 12); sl.setSpacing(2)
        brand = QHBoxLayout()
        logo = QLabel(); logo.setPixmap(QIcon(str(ASSETS / "logo.png")).pixmap(32, 32))
        brand.addWidget(logo); brand.addWidget(QLabel(APP, objectName="brand")); brand.addStretch()
        sl.addLayout(brand); sl.addSpacing(8)
        self.tools = QButtonGroup(self)
        group = None
        for key, (grp, title, *_rest) in OPS.items():
            if grp != group:
                sl.addWidget(QLabel(grp.upper(), objectName="group")); group = grp
            b = QPushButton(title, objectName="tool", checkable=True)
            b.setProperty("op", key); b.setCursor(Qt.PointingHandCursor)
            self.tools.addButton(b); sl.addWidget(b)
        sl.addStretch()
        sl.addWidget(QLabel(f"v{__version__} · 100% offline", objectName="subtitle"))
        self.tools.buttonClicked.connect(self.select_op)

        # área principal
        self.title = QLabel(objectName="title")
        self.subtitle = QLabel(objectName="subtitle")
        self.drop = Drop()
        self.drop.dropped.connect(self.add); self.drop.clicked.connect(self.browse)
        self.list = QListWidget()
        self.list.setDragDropMode(QAbstractItemView.InternalMove)
        self.list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list.setIconSize(QSize(28, 28))
        self.stack = QStackedWidget(); self.stack.addWidget(self.drop); self.stack.addWidget(self.list)

        bar = QHBoxLayout()
        self.count = QLabel(objectName="subtitle")
        for text, fn in (("+ Adicionar", self.browse), ("Remover", self.remove),
                         ("▲", lambda: self.move(-1)), ("▼", lambda: self.move(1)), ("Limpar", self.clear)):
            b = QPushButton(text); b.clicked.connect(fn); bar.addWidget(b)
        bar.addStretch(); bar.addWidget(self.count)

        self.hint = QLabel(objectName="subtitle")
        self.param = QLineEdit()
        self.btn = QPushButton("Executar", objectName="primary"); self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(self.execute)
        self.progress = QProgressBar(); self.progress.setRange(0, 0); self.progress.hide()

        self.result = QFrame(objectName="result"); self.result.hide()
        rl = QHBoxLayout(self.result)
        self.result_text = QLabel(wordWrap=True, textInteractionFlags=Qt.TextSelectableByMouse)
        self.result_open = QPushButton("Abrir local")
        self.result_open.clicked.connect(lambda: open_location(self.outputs[0]))
        rl.addWidget(self.result_text, 1); rl.addWidget(self.result_open)

        action = QHBoxLayout()
        pcol = QVBoxLayout(); pcol.addWidget(self.hint); pcol.addWidget(self.param)
        action.addLayout(pcol, 1); action.addWidget(self.btn, 0, Qt.AlignBottom)

        main = QVBoxLayout(); main.setContentsMargins(28, 24, 28, 24); main.setSpacing(12)
        main.addWidget(self.title); main.addWidget(self.subtitle)
        main.addWidget(self.stack, 1); main.addLayout(bar); main.addLayout(action)
        main.addWidget(self.progress); main.addWidget(self.result)

        root = QHBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(side); root.addLayout(main, 1)

        self.tools.buttons()[0].setChecked(True); self.select_op()
        self.refresh()

    # ----- arquivos
    def files(self):
        return [self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())]

    def add(self, paths):
        have = set(self.files())
        for p in paths:
            p = str(Path(p))
            if p in have or not Path(p).is_file():
                continue
            have.add(p)
            info = human(Path(p).stat().st_size)
            if p.lower().endswith(".pdf"):
                try:
                    import pymupdf
                    info += f" · {pymupdf.open(p).page_count} pág."
                except Exception:
                    info += " · PDF inválido"
            it = QListWidgetItem(self.icons.icon(QFileInfo(p)), f"{Path(p).name}\n{info}")
            it.setData(Qt.UserRole, p); it.setToolTip(p)
            self.list.addItem(it)
        self.refresh()

    def browse(self):
        self.add(QFileDialog.getOpenFileNames(self, "Escolher arquivos")[0])

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

    def refresh(self):
        n = self.list.count()
        self.stack.setCurrentIndex(1 if n else 0)
        self.count.setText(f"{n} arquivo(s)" if n else "")

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.add([u.toLocalFile() for u in e.mimeData().urls()])

    # ----- operação
    def op(self):
        return self.tools.checkedButton().property("op")

    def select_op(self, *_):
        _, title, desc, _, hint, default = OPS[self.op()]
        self.title.setText(title); self.subtitle.setText(desc)
        self.hint.setText(hint or ""); self.hint.setVisible(bool(hint))
        self.param.setVisible(bool(hint)); self.param.setText(default)
        self.result.hide()

    def execute(self):
        fs = self.files()
        if not fs:
            return self.browse()
        self.btn.setEnabled(False); self.progress.show(); self.result.hide()
        self.worker = Worker(self.op(), fs, self.param.text().strip())
        self.worker.done.connect(self.finished)
        self.worker.start()

    def finished(self, outs, err):
        self.btn.setEnabled(True); self.progress.hide()
        self.outputs = outs
        ok = not err
        self.result.setProperty("ok", ok); self.result.style().unpolish(self.result); self.result.style().polish(self.result)
        self.result_text.setText(("✔ Pronto: " + ", ".join(Path(o).name for o in outs)) if ok else "✖ " + err)
        self.result_open.setVisible(ok and bool(outs))
        self.result.show()


class Quick(QWidget):
    """Janela pequena para operações do menu de contexto."""

    def __init__(self, op, files, param):
        super().__init__(objectName="root")
        self.setWindowTitle(APP); self.setWindowIcon(QIcon(str(ASSETS / "filedocs.ico")))
        self.setFixedWidth(420)
        self.text = QLabel(f"{OPS[op][1]}: {', '.join(Path(f).name for f in files)}", wordWrap=True)
        self.progress = QProgressBar(); self.progress.setRange(0, 0)
        self.btn_open = QPushButton("Abrir local"); self.btn_open.hide()
        self.btn_close = QPushButton("Fechar", objectName="primary"); self.btn_close.hide()
        self.btn_close.clicked.connect(self.close)
        bl = QHBoxLayout(); bl.addStretch(); bl.addWidget(self.btn_open); bl.addWidget(self.btn_close)
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 18, 20, 18)
        lay.addWidget(self.text); lay.addWidget(self.progress); lay.addLayout(bl)
        self.worker = Worker(op, files, param)
        self.worker.done.connect(self.finished); self.worker.start()

    def finished(self, outs, err):
        self.progress.hide()
        if err:
            self.text.setText("✖ " + err)
        else:
            self.text.setText("✔ Pronto: " + ", ".join(Path(o).name for o in outs))
            self.btn_open.clicked.connect(lambda: open_location(outs[0])); self.btn_open.show()
        self.btn_close.show()


def start(files, quick=None):
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.setWindowIcon(QIcon(str(ASSETS / "filedocs.ico")))

    if quick:
        w = Quick(quick[0], files, quick[1]); w.show()
        return app.exec()

    # O Explorer abre um processo por arquivo: os seguintes entregam à janela já aberta.
    sock = QLocalSocket(); sock.connectToServer(APP)
    if sock.waitForConnected(300):
        sock.write("\n".join(files).encode()); sock.waitForBytesWritten(1000)
        return 0

    win = Main()
    server = QLocalServer(win)
    QLocalServer.removeServer(APP); server.listen(APP)

    def incoming():
        s = server.nextPendingConnection()
        s.waitForReadyRead(1000)
        win.add(bytes(s.readAll()).decode().splitlines())
        win.showNormal(); win.raise_(); win.activateWindow()
    server.newConnection.connect(incoming)

    win.add(files); win.show()
    return app.exec()
