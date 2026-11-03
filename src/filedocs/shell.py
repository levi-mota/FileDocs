"""Menu de contexto do Explorer (HKCU, não precisa de admin)."""
import sys
import winreg as w
from pathlib import Path

from . import ASSETS, FROZEN
from .ops import IMG_EXT, OFFICE_EXT

# grupo -> (extensões, [(id, rótulo, op, parâmetro)])
MENU = {
    "pdf": ([".pdf"], [("open", "Abrir no FileDocs", None, None),
                       ("compress", "Comprimir", "compress", ""),
                       ("ocr", "OCR (tornar pesquisável)", "ocr", ""),
                       ("pdf2img", "Converter para PNG", "pdf2img", "png")]),
    "img": (sorted(IMG_EXT), [("open", "Abrir no FileDocs", None, None),
                              ("img2pdf", "Converter para PDF", "img2pdf", ""),
                              ("jpg", "Converter para JPG", "convimg", "jpg"),
                              ("png", "Converter para PNG", "convimg", "png"),
                              ("ocr", "OCR → PDF pesquisável", "ocr", "")]),
    "office": (sorted(OFFICE_EXT), [("open", "Abrir no FileDocs", None, None),
                                    ("pdf", "Converter para PDF", "office2pdf", "")]),
}


def _launcher():
    if FROZEN:
        return f'"{sys.executable}"'
    pyw = Path(sys.executable).with_name("pythonw.exe")
    return f'"{pyw}" "{Path(__file__).resolve().parents[1] / "main.py"}"'


def _key(ext):
    return rf"Software\Classes\SystemFileAssociations\{ext}\shell\FileDocs"


def install():
    icon = str(ASSETS / "filedocs.ico")
    for exts, items in MENU.values():
        for ext in exts:
            with w.CreateKey(w.HKEY_CURRENT_USER, _key(ext)) as k:
                w.SetValueEx(k, "MUIVerb", 0, w.REG_SZ, "FileDocs")
                w.SetValueEx(k, "SubCommands", 0, w.REG_SZ, "")
                w.SetValueEx(k, "Icon", 0, w.REG_SZ, icon)
            for i, (cid, label, op, param) in enumerate(items):
                key = rf"{_key(ext)}\shell\{i:02}{cid}"
                args = "" if op is None else f'--op {op} --param "{param}" '
                with w.CreateKey(w.HKEY_CURRENT_USER, key) as k:
                    w.SetValueEx(k, "MUIVerb", 0, w.REG_SZ, label)
                    w.SetValueEx(k, "MultiSelectModel", 0, w.REG_SZ, "Player")
                with w.CreateKey(w.HKEY_CURRENT_USER, key + r"\command") as k:
                    w.SetValueEx(k, "", 0, w.REG_SZ, f'{_launcher()} {args}"%1"')


def _rm(path):
    try:
        with w.OpenKey(w.HKEY_CURRENT_USER, path) as k:
            subs = []
            i = 0
            while True:
                try:
                    subs.append(w.EnumKey(k, i)); i += 1
                except OSError:
                    break
        for s in subs:
            _rm(path + "\\" + s)
        w.DeleteKey(w.HKEY_CURRENT_USER, path)
    except FileNotFoundError:
        pass


def uninstall():
    for exts, _ in MENU.values():
        for ext in exts:
            _rm(_key(ext))
