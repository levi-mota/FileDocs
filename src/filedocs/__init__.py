"""FileDocs: caminhos e ambiente compartilhados (dev e .exe)."""
import os
import sys
from pathlib import Path

__version__ = "1.0.0"
APP = "FileDocs"

FROZEN = getattr(sys, "frozen", False)
# No .exe (PyInstaller onedir) os dados ficam em _internal; em dev, na raiz do repo.
BASE = Path(sys._MEIPASS) if FROZEN else Path(__file__).resolve().parents[2]
ASSETS = BASE / "assets"
VENDOR = BASE / "vendor"

_tess = VENDOR / "tesseract"
if not (_tess / "tesseract.exe").exists():
    _tess = Path(r"C:\Program Files\Tesseract-OCR")
os.environ["PATH"] = str(_tess) + os.pathsep + os.environ.get("PATH", "")
os.environ["TESSDATA_PREFIX"] = str(VENDOR / "tessdata")
