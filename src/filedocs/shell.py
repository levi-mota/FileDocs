"""Menu de contexto do Explorer (HKCU, não precisa de admin).

Itens com seleção "one" somem quando há mais de um arquivo selecionado (MultiSelectModel=Single).
O registro não permite o contrário (item só para vários arquivos), por isso "Juntar" abre a janela,
onde dá para acrescentar arquivos e ajustar a ordem.
"""
import sys
import winreg as w
from pathlib import Path

from . import ASSETS, FROZEN
from .ops import IMG_EXT, OFFICE_EXT

# Ação: ("open", ferramenta) abre a janela nessa ferramenta | ("run", op, parâmetro) executa direto
# grupo -> (extensões, [(id, rótulo, ação, seleção "any"|"one")])
MENU = {
    "pdf": ([".pdf"], [
        ("open", "Abrir no FileDocs", ("open", ""), "any"),
        ("merge", "Juntar PDFs…", ("open", "merge"), "any"),
        ("compress", "Comprimir", ("run", "compress", ""), "any"),
        ("ocr", "OCR (tornar pesquisável)", ("run", "ocr", ""), "any"),
        ("png", "Converter para imagens PNG", ("run", "pdf2img", "png"), "any"),
        ("split", "Dividir em páginas", ("run", "split", ""), "one"),
        ("rotate", "Girar 90° à direita", ("run", "rotate", "90"), "one"),
        ("extract", "Extrair páginas…", ("open", "extract"), "one"),
        ("delete", "Remover páginas…", ("open", "delete"), "one"),
    ]),
    "img": (sorted(IMG_EXT), [
        ("open", "Abrir no FileDocs", ("open", ""), "any"),
        ("pdf", "Converter para PDF", ("run", "img2pdf", "each"), "any"),
        ("merge", "Juntar em um PDF…", ("open", "img2pdf"), "any"),
        ("jpg", "Converter para JPG", ("run", "convimg", "jpg"), "any"),
        ("png", "Converter para PNG", ("run", "convimg", "png"), "any"),
        ("ocr", "OCR → PDF pesquisável", ("run", "ocr", ""), "any"),
    ]),
    "office": (sorted(OFFICE_EXT), [
        ("open", "Abrir no FileDocs", ("open", ""), "any"),
        ("pdf", "Converter para PDF", ("run", "office2pdf", ""), "any"),
    ]),
}


def _launcher():
    if FROZEN:
        return f'"{sys.executable}"'
    pyw = Path(sys.executable).with_name("pythonw.exe")
    return f'"{pyw}" "{Path(__file__).resolve().parents[1] / "main.py"}"'


def _key(ext):
    return rf"Software\Classes\SystemFileAssociations\{ext}\shell\FileDocs"


def _args(action):
    if action[0] == "open":
        return f"--tool {action[1]} " if action[1] else ""
    return f'--op {action[1]} --param "{action[2]}" '


def install():
    uninstall()  # remove itens de versões anteriores
    icon = str(ASSETS / "filedocs.ico")
    for exts, items in MENU.values():
        for ext in exts:
            with w.CreateKey(w.HKEY_CURRENT_USER, _key(ext)) as k:
                w.SetValueEx(k, "MUIVerb", 0, w.REG_SZ, "FileDocs")
                w.SetValueEx(k, "SubCommands", 0, w.REG_SZ, "")
                w.SetValueEx(k, "Icon", 0, w.REG_SZ, icon)
                w.SetValueEx(k, "MultiSelectModel", 0, w.REG_SZ, "Player")
            for i, (cid, label, action, sel) in enumerate(items):
                key = rf"{_key(ext)}\shell\{i:02}{cid}"
                with w.CreateKey(w.HKEY_CURRENT_USER, key) as k:
                    w.SetValueEx(k, "MUIVerb", 0, w.REG_SZ, label)
                    w.SetValueEx(k, "MultiSelectModel", 0, w.REG_SZ, "Single" if sel == "one" else "Player")
                with w.CreateKey(w.HKEY_CURRENT_USER, key + r"\command") as k:
                    w.SetValueEx(k, "", 0, w.REG_SZ, f'{_launcher()} {_args(action)}"%1"')


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
