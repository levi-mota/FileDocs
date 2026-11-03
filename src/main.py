"""Ponto de entrada do FileDocs.

  FileDocs.exe [arquivos...]                 abre a interface
  FileDocs.exe --op compress [--param 60] a.pdf   operação direta (menu de contexto)
  FileDocs.exe --cli --op merge a.pdf b.pdf  modo texto
  FileDocs.exe --install-menu | --uninstall-menu
"""
import argparse
import sys
from pathlib import Path

from filedocs import ops, shell


def main():
    ap = argparse.ArgumentParser(prog="FileDocs")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--op", choices=ops.OPS)
    ap.add_argument("--param", default="")
    ap.add_argument("--cli", action="store_true")
    ap.add_argument("--install-menu", action="store_true")
    ap.add_argument("--uninstall-menu", action="store_true")
    a = ap.parse_args()

    if a.install_menu:
        return shell.install()
    if a.uninstall_menu:
        return shell.uninstall()
    files = [str(Path(f).resolve()) for f in a.files]
    if a.cli:
        for o in ops.run(a.op, files, a.param):
            print(o)
        return
    from filedocs import gui
    gui.start(files, (a.op, a.param) if a.op else None)


if __name__ == "__main__":
    sys.exit(main())
