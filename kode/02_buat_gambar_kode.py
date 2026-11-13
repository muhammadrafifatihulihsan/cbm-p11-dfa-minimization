"""
Merender potongan kode asli menjadi gambar PNG (tangkapan layar kode).

Sumber yang digambar:
  1. automata/fa/dfa.py          -> DFA.minify()
  2. automata/fa/dfa.py          -> DFA._minify() bagian awal
  3. automata/fa/dfa.py          -> DFA._minify() bagian partisi
  4. automata/fa/dfa.py          -> DFA._minify() bagian pembentukan DFA baru
  5. automata/base/utils.py      -> PartitionRefinement.refine()
  6. 01_eksperimen_minify.py     -> DFA kasus A

Teks yang digambar diambil langsung dari file, jadi tidak ada kode yang
diketik ulang secara manual.
"""

import ast
import io
import sys
import tokenize
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PAKET = Path(r"C:\Users\Pongo\AppData\Local\Programs\Python\Python313\Lib\site-packages\automata")
SKRIP = Path(__file__).resolve().parent / "01_eksperimen_minify.py"
OUT = Path(__file__).resolve().parent.parent / "gambar"
KUTIPAN = Path(__file__).resolve().parent / "kutipan"
OUT.mkdir(parents=True, exist_ok=True)
KUTIPAN.mkdir(parents=True, exist_ok=True)

FONT = r"C:\Windows\Fonts\consola.ttf"
FONT_BOLD = r"C:\Windows\Fonts\consolab.ttf"
UKURAN = 16
BARIS_TINGGI = 23
MARGIN = 18

WARNA = {
    "bg": (252, 252, 253),
    "bar": (32, 41, 56),
    "bar_text": (226, 232, 240),
    "nomor": (150, 158, 170),
    "kode": (30, 34, 42),
    "kata_kunci": (156, 39, 176),
    "def": (21, 101, 192),
    "string": (46, 125, 50),
    "komentar": (120, 144, 130),
    "angka": (183, 92, 0),
    "self": (198, 40, 40),
}

KATA_KUNCI = {
    "def", "class", "return", "if", "else", "elif", "for", "while", "in", "not",
    "and", "or", "is", "None", "True", "False", "import", "from", "as", "with",
    "try", "except", "raise", "yield", "lambda", "continue", "break", "pass",
    "while", "global", "nonlocal", "assert", "del", "async", "await",
}


def token_warna(baris: str):
    """Warnai satu baris kode memakai modul tokenize bawaan Python."""
    hasil = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(baris + "\n").readline))
    except Exception:
        return [(baris, WARNA["kode"])]
    posisi = 0
    for tok in tokens:
        if tok.type in (tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE,
                        tokenize.NL, tokenize.INDENT, tokenize.DEDENT):
            continue
        mulai, akhir = tok.start[1], tok.end[1]
        if mulai > posisi:
            hasil.append((baris[posisi:mulai], WARNA["kode"]))
        teks = baris[mulai:akhir]
        if not teks:
            continue
        if tok.type == tokenize.COMMENT:
            w = WARNA["komentar"]
        elif tok.type == tokenize.STRING:
            w = WARNA["string"]
        elif tok.type == tokenize.NUMBER:
            w = WARNA["angka"]
        elif tok.type == tokenize.NAME and teks in KATA_KUNCI:
            w = WARNA["kata_kunci"]
        elif tok.type == tokenize.NAME and teks in ("self", "cls"):
            w = WARNA["self"]
        elif tok.type == tokenize.NAME:
            w = WARNA["kode"]
        else:
            w = WARNA["kode"]
        hasil.append((teks, w))
        posisi = akhir
    if posisi < len(baris):
        hasil.append((baris[posisi:], WARNA["kode"]))
    return hasil


def potong(sumber: Path, mulai: int, akhir: int):
    baris = sumber.read_text(encoding="utf-8").splitlines()
    return baris[mulai - 1:akhir]


def gambar(judul: str, baris: list, keluar: Path, nomor_awal: int = 1):
    font = ImageFont.truetype(FONT, UKURAN)
    font_bold = ImageFont.truetype(FONT_BOLD, UKURAN)
    nomor_akhir = nomor_awal + len(baris) - 1
    lebar_nomor = max(len(str(nomor_awal)), len(str(nomor_akhir))) + 1
    lebar_teks = max(
        font.getlength("  " * lebar_nomor + b.replace("\t", "    ")) for b in baris
    )
    lebar = int(lebar_teks) + 2 * MARGIN + 20
    tinggi_bar = 34
    tinggi = tinggi_bar + MARGIN + len(baris) * BARIS_TINGGI + MARGIN

    img = Image.new("RGB", (lebar, tinggi), WARNA["bg"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, lebar, tinggi_bar], fill=WARNA["bar"])
    d.text((MARGIN, 9), judul, font=font_bold, fill=WARNA["bar_text"])
    d.line([0, tinggi_bar, lebar, tinggi_bar], fill=(60, 70, 88), width=1)

    y = tinggi_bar + 10
    for nomor, teks in enumerate(baris, start=nomor_awal):
        teks = teks.replace("\t", "    ")
        d.text((MARGIN, y), str(nomor).rjust(lebar_nomor), font=font, fill=WARNA["nomor"])
        x = MARGIN + font.getlength("  " * lebar_nomor) + 6
        for bagian, warna in token_warna(teks):
            d.text((x, y), bagian, font=font, fill=warna)
            x += font.getlength(bagian)
        y += BARIS_TINGGI

    img.save(keluar)
    print("tulis", keluar.name, img.size)


TARGET = [
    ("kode_0_struktur_dfa.png", PAKET / "fa" / "dfa.py", 88, 117,
     "automata/fa/dfa.py  baris 88-117  ::  atribut dan konstruktor class DFA"),
    ("kode_1a_minify_judul.png", PAKET / "fa" / "dfa.py", 558, 577,
     "automata/fa/dfa.py  baris 558-577  ::  judul dan dokumentasi DFA.minify()"),
    ("kode_1b_minify_badan.png", PAKET / "fa" / "dfa.py", 578, 605,
     "automata/fa/dfa.py  baris 578-605  ::  badan DFA.minify()"),
    ("kode_2_minify_awal.png", PAKET / "fa" / "dfa.py", 623, 657,
     "automata/fa/dfa.py  baris 623-657  ::  DFA._minify() tahap persiapan"),
    ("kode_3_minify_partisi.png", PAKET / "fa" / "dfa.py", 658, 693,
     "automata/fa/dfa.py  baris 658-693  ::  DFA._minify() loop partisi"),
    ("kode_4a_minify_hasil.png", PAKET / "fa" / "dfa.py", 694, 718,
     "automata/fa/dfa.py  baris 694-718  ::  DFA._minify() pemetaan state baru"),
    ("kode_4b_minify_transisi.png", PAKET / "fa" / "dfa.py", 719, 744,
     "automata/fa/dfa.py  baris 719-744  ::  DFA._minify() tabel transisi baru"),
    ("kode_5a_partition_refinement.png", PAKET / "base" / "utils.py", 155, 187,
     "automata/base/utils.py  baris 155-187  ::  PartitionRefinement (struktur)"),
    ("kode_5b_partition_refine.png", PAKET / "base" / "utils.py", 189, 216,
     "automata/base/utils.py  baris 189-216  ::  PartitionRefinement.refine()"),
    ("kode_6_studi_kasus.png", SKRIP, 91, 109,
     "01_eksperimen_minify.py  baris 91-115  ::  DFA Kasus A"),
    ("kode_7_penelusuran.png", PAKET / "fa" / "dfa.py", 472, 493,
     "automata/fa/dfa.py  baris 472-493  ::  penelusuran transisi dan penolakan input"),
]

for nama, sumber, mulai, akhir, judul in TARGET:
    baris = potong(sumber, mulai, akhir)
    (KUTIPAN / (nama.replace(".png", ".txt"))).write_text(
        "\n".join(f"{mulai + i:>5}| {b}" for i, b in enumerate(baris)),
        encoding="utf-8",
    )
    gambar(judul, baris, OUT / nama, nomor_awal=mulai)

# keluaran nyata skrip eksperimen, dirender sebagai gambar bukti eksekusi
keluaran = (SKRIP.parent / "output_eksperimen.txt").read_text(encoding="utf-8").splitlines()
for i in range(0, len(keluaran), 9):
    bagian = keluaran[i:i + 9]
    gambar(f"keluaran 01_eksperimen_minify.py  (bagian {i // 9 + 1})", bagian,
           OUT / f"output_eksperimen_{i // 9 + 1}.png")
