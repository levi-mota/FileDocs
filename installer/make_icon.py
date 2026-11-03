"""Gera assets/logo.png e assets/filedocs.ico a partir de assets/logo.svg."""
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

assets = Path(__file__).resolve().parents[1] / "assets"
app = QGuiApplication([])
img = QImage(512, 512, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
QSvgRenderer(str(assets / "logo.svg")).render(p)
p.end()
img.save(str(assets / "logo.png"))
Image.open(assets / "logo.png").save(assets / "filedocs.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
print("ok")
