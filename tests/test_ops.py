"""Teste rápido das operações: python tests/test_ops.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pymupdf
from filedocs import ops as fd

tmp = Path(tempfile.mkdtemp())


def make_pdf(name, pages):
    d = pymupdf.open()
    for i in range(pages):
        d.new_page().insert_text((72, 72), f"Pagina {i + 1} contrato social", fontsize=24)
    p = tmp / name; d.save(p); return p


a, b = make_pdf("a.pdf", 3), make_pdf("b.pdf", 2)
assert fd.parse_pages("1-2,5-", 6) == [0, 1, 4, 5]

assert pymupdf.open(fd.op_merge([a, b])[0]).page_count == 5
assert len(list(fd.op_split([a])[0].iterdir())) == 3
assert pymupdf.open(fd.op_extract([a], "2-3")[0]).page_count == 2
assert pymupdf.open(fd.op_delete([a], "1")[0]).page_count == 2
assert pymupdf.open(fd.op_rotate([a], "90")[0])[0].rotation == 90
assert fd.op_compress([a])[0].exists()

imgs = fd.op_pdf2img([a], "png")[0]
png = sorted(imgs.iterdir())[0]
assert fd.op_convert_img([png], "jpg")[0].suffix == ".jpg"
scan = fd.op_img2pdf([png])[0]
assert pymupdf.open(scan)[0].get_text().strip() == ""          # imagem, sem texto
ocr = fd.op_ocr([scan])[0]
assert "contrato" in pymupdf.open(ocr)[0].get_text().lower()   # OCR achou o texto

assert len(fd.op_img2pdf([png, png], "each")) == 2                 # um PDF por imagem

rtf = tmp / "carta.rtf"; rtf.write_text(r"{\rtf1 Declaracao de residencia}")
engines = ([""] if fd.has_msoffice() else []) + (["libreoffice"] if fd.soffice() else [])
for engine in engines:  # Microsoft Office e/ou LibreOffice, o que houver
    assert "Declaracao" in pymupdf.open(fd.op_office2pdf([rtf], engine)[0])[0].get_text(), engine

dest = tmp / "saida"; dest.mkdir()
assert fd.run("merge", [a, b], "", dest)[0].parent == dest     # pasta de destino escolhida
assert fd.run("merge", [a, b], "", dest)[0].name == "a_unido_2.pdf"  # não sobrescreve
print("OK", tmp)
