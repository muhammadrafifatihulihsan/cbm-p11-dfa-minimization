"""
Menyusun laporan CBM Pertemuan 11 ke berkas .docx.

Format: kertas A4, margin atas 4 cm, kiri 4 cm, bawah 3 cm, kanan 3 cm,
huruf Times New Roman 12 pt, spasi 1,5.

Seluruh angka pada laporan diambil dari hasil_eksperimen.json.
"""

import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent
GAMBAR = OUT_DIR / "gambar"
DATA = json.loads((HERE / "hasil_eksperimen.json").read_text(encoding="utf-8"))

A = DATA["kasus_a"]
B = DATA["kasus_b"]
P = DATA["pemeriksaan"]
SIMBOL = ["d", ".", "e", "+", "-"]
NAMA_SIMBOL = {"d": "digit", ".": "titik", "e": "e", "+": "tanda +", "-": "tanda -"}


def pct(awal, akhir):
    """Persentase penurunan dari nilai awal ke nilai akhir."""
    if not awal:
        return "0"
    turun = (awal - akhir) / awal * 100
    teks = f"{turun:.1f}".rstrip("0").rstrip(".")
    return teks.replace(".", ",")


def peta_label_kasus_b(transisi):
    """Beri label pendek G1, G2, ... untuk state gabungan pada Kasus B.

    State tunggal tetap memakai s<angka>. State gabungan diberi nama G agar
    tidak melebar keluar lingkaran pada diagram. Fungsi menerima kamus
    transisi dan mengembalikan dua hal: peta dari nama asli ke label pendek,
    serta keterangan label pendek ke daftar state lama.
    """
    asli = set(transisi)
    for isi in transisi.values():
        asli.update(isi.values())

    def urut(nama):
        return tuple(sorted(nama.split("+"), key=lambda x: int(x)))

    kelompok = {}
    for nama in asli:
        kelompok.setdefault(urut(nama), []).append(nama)

    peta = {}
    keterangan = {}
    nomor = 0
    for kunci in sorted(kelompok, key=lambda k: (len(k) == 1, min(int(v) for v in k))):
        if len(kunci) == 1:
            label = "s" + kunci[0]
        else:
            nomor += 1
            label = f"G{nomor}"
            keterangan[label] = "+".join("s" + x for x in kunci)
        for nama in kelompok[kunci]:
            peta[nama] = label
    return peta, keterangan


PETA_B, KET_B = peta_label_kasus_b(B["transisi_sesudah"])


def angka(n):
    return f"{n:,}".replace(",", ".")


# --------------------------------------------------------------------- dokumen
doc = Document()

# gaya dasar: Times New Roman 12, spasi 1,5
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(0)
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.widow_control = True

for nama_gaya, ukuran, rata, spasi_before, spasi_after, kapital in [
    ("Heading 1", 12, WD_ALIGN_PARAGRAPH.CENTER, 12, 12, False),
    ("Heading 2", 12, WD_ALIGN_PARAGRAPH.LEFT, 12, 6, False),
    ("Heading 3", 12, WD_ALIGN_PARAGRAPH.LEFT, 10, 4, False),
]:
    st = doc.styles[nama_gaya]
    st.font.name = "Times New Roman"
    st.font.size = Pt(ukuran)
    for atribut in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        st.element.get_or_add_rPr().get_or_add_rFonts().set(qn(atribut), "Times New Roman")
    st.font.bold = True
    st.font.italic = False
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.paragraph_format.alignment = rata
    st.paragraph_format.line_spacing = 1.5
    st.paragraph_format.space_before = Pt(spasi_before)
    st.paragraph_format.space_after = Pt(spasi_after)
    st.paragraph_format.keep_with_next = True

section = doc.sections[0]
section.page_width = Cm(21.0)
section.page_height = Cm(29.7)
section.top_margin = Cm(4.0)
section.left_margin = Cm(4.0)
section.bottom_margin = Cm(3.0)
section.right_margin = Cm(3.0)
LEBAR_TEKS = Cm(21.0 - 4.0 - 3.0)


def par(teks="", *, rata=WD_ALIGN_PARAGRAPH.JUSTIFY, indentasi=True, tebal=False,
        miring=False, ukuran=12, spasi=1.5, before=0, after=0, gaya=None):
    p = doc.add_paragraph(style=gaya)
    p.alignment = rata
    p.paragraph_format.line_spacing = spasi
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    if indentasi:
        p.paragraph_format.first_line_indent = Cm(0.5)
    if teks:
        r = p.add_run(teks)
        r.font.name = "Times New Roman"
        r.font.size = Pt(ukuran)
        r.bold = tebal
        r.italic = miring
    return p


def h1(teks, halaman_baru=True):
    p = doc.add_heading(teks, level=1)
    if halaman_baru:
        p.paragraph_format.page_break_before = True
    return p


def h2(teks):
    return doc.add_heading(teks, level=2)


def h3(teks):
    return doc.add_heading(teks, level=3)


def daftar(butir, gaya="List Number"):
    """Menulis daftar. Untuk daftar bernomor, nomor ditulis manual supaya
    penomoran setiap daftar selalu mulai dari 1 (gaya List Number Word
    melanjutkan nomor antar daftar yang berbeda)."""
    for i, b in enumerate(butir, start=1):
        teks = f"{i}. {b}" if gaya == "List Number" else f"\u2022 {b}"
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.left_indent = Cm(0)
        p.paragraph_format.first_line_indent = Cm(0)
        r = p.add_run(teks)
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)


def beri_border(sel):
    tcPr = sel._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for sisi in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{sisi}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tcPr.append(borders)


def beri_abu(sel, warna="EFEFEF"):
    tcPr = sel._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), warna)
    tcPr.append(shd)


def tabel(baris, header=None, lebar=None, ukuran=12, kapsi=None, rata_kolom=None):
    if kapsi:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_before = Pt(8)
        cap.paragraph_format.space_after = Pt(4)
        cap.paragraph_format.line_spacing = 1.5
        r = cap.add_run(kapsi)
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
        r.bold = False
        cap.paragraph_format.keep_with_next = True

    jumlah_kolom = len(header) if header else len(baris[0])
    t = doc.add_table(rows=0, cols=jumlah_kolom)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False

    # buang baris data yang isinya sama dengan judul kolom (baris ganda)
    if header and baris and [str(x).strip().lower() for x in baris[0]] == [str(x).strip().lower() for x in header]:
        baris = baris[1:]

    semua = ([header] if header else []) + baris
    for i, isi in enumerate(semua):
        if i == 0 and header:
            pass
        row = t.add_row()
        for j, nilai in enumerate(isi):
            sel = row.cells[j]
            sel.text = ""
            p = sel.paragraphs[0]
            rata = WD_ALIGN_PARAGRAPH.CENTER
            if rata_kolom and j < len(rata_kolom):
                rata = rata_kolom[j]
            p.alignment = rata
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            r = p.add_run(str(nilai))
            r.font.name = "Times New Roman"
            r.font.size = Pt(ukuran)
            r.bold = bool(header and i == 0)
            if lebar:
                sel.width = lebar[j]
            beri_border(sel)

    if lebar:
        for j, w in enumerate(lebar):
            for row in t.rows:
                row.cells[j].width = w

    # baris tabel tidak boleh terpotong di tengah halaman
    for row in t.rows:
        trPr_baris = row._tr.get_or_add_trPr()
        pecah = OxmlElement("w:cantSplit")
        pecah.set(qn("w:val"), "true")
        trPr_baris.append(pecah)

    if header:
        trPr = t.rows[0]._tr.get_or_add_trPr()
        ulang = OxmlElement("w:tblHeader")
        ulang.set(qn("w:val"), "true")
        trPr.append(ulang)

    # tabel panjang boleh terpecah antar halaman, tetapi baris judul selalu
    # menempel pada baris data pertama agar tidak berdiri sendiri di dasar halaman
    for sel in t.rows[0].cells:
        for par_sel in sel.paragraphs:
            par_sel.paragraph_format.keep_with_next = True

    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def gambar(nama, kapsi, lebar_cm=12.8, tinggi_maks=9.3):
    path = GAMBAR / nama
    from PIL import Image as _Im
    w, h = _Im.open(path).size
    lebar_cm = min(lebar_cm, tinggi_maks * w / h)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(lebar_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(10)
    cap.paragraph_format.line_spacing = 1.5
    r = cap.add_run(kapsi)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.italic = False


def nomor_halaman_footer():
    """Nomor halaman di tengah bawah memakai field PAGE Word."""
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    isi = OxmlElement("w:r")
    teks = OxmlElement("w:t")
    teks.text = "1"
    isi.append(teks)
    fld.append(isi)
    p._p.append(fld)


section.different_first_page_header_footer = True


# ----------------------------------------------------------------------- COVER
def cover_baris(teks, tebal=False, ukuran=12, after=0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(teks)
    r.font.name = "Times New Roman"
    r.font.size = Pt(ukuran)
    r.bold = tebal
    return p


cover_baris("LAPORAN CASE BASED METHOD (CBM)", tebal=True, ukuran=14, after=2)
cover_baris("PERTEMUAN KE-11", tebal=True, ukuran=14, after=18)
cover_baris("MINIMISASI DFA DAN PEMBUKTIAN EKIVALENSI STATE", tebal=True, ukuran=14, after=2)
cover_baris("Analisis Kode DFA.minify() pada Pustaka automata-lib", ukuran=12, after=54)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(46)
p.add_run().add_picture(str(GAMBAR / "logo_unp.png"), width=Cm(4.2))

cover_baris("Dosen Pengampu:", tebal=True, after=2)
cover_baris("Dr. Resmi Darni, S.Kom, M.Kom.", after=44)

cover_baris("Oleh:", tebal=True, after=2)
cover_baris("Muhammad Rafi Fatihul Ihsan  (24343016)", after=64)

cover_baris("PROGRAM STUDI INFORMATIKA", tebal=True, after=0)
cover_baris("DEPARTEMEN TEKNIK ELEKTRONIKA", tebal=True, after=0)
cover_baris("FAKULTAS TEKNIK", tebal=True, after=0)
cover_baris("UNIVERSITAS NEGERI PADANG", tebal=True, after=0)
cover_baris("2026", tebal=True, after=0)

# gaya daftar isi: rapat agar tidak menyisakan halaman setengah kosong
from docx.enum.style import WD_STYLE_TYPE

for nama_toc in ("toc 1", "toc 2", "TOC 11", "TOC 21", "TOC 1", "TOC 2"):
    try:
        st_toc = doc.styles[nama_toc]
    except KeyError:
        st_toc = doc.styles.add_style(nama_toc, WD_STYLE_TYPE.PARAGRAPH)
    st_toc.font.name = "Times New Roman"
    st_toc.font.size = Pt(12)
    st_toc.paragraph_format.line_spacing = 1.0
    st_toc.paragraph_format.space_before = Pt(0)
    st_toc.paragraph_format.space_after = Pt(0)

# ------------------------------------------------------- TAUTAN BERKAS PROGRAM
h1("TAUTAN BERKAS PROGRAM")
par("Seluruh kode program, berkas hasil eksekusi, dan gambar pendukung laporan ini dikemas dalam satu "
    "berkas zip. Berkas tersebut diunggah ke Google Drive, lalu tautannya dicantumkan pada ruang di "
    "bawah ini.")
par("Tautan Google Drive:", rata=WD_ALIGN_PARAGRAPH.LEFT)
par("https://drive.google.com/" + "…" * 14, indentasi=False, rata=WD_ALIGN_PARAGRAPH.LEFT)
par("Isi berkas zip:", rata=WD_ALIGN_PARAGRAPH.LEFT, tebal=True, before=6)
tabel(
    [
        ["kode/01_eksperimen_minify.py", "Skrip verifikasi: membangun dua kasus DFA, menjalankan minify(), mengukur ukuran, dan menguji ekuivalensi"],
        ["kode/02_buat_gambar_kode.py", "Pembuat tangkapan layar kode sumber"],
        ["kode/03_diagram_dfa.py", "Pembuat diagram DFA dan grafik perbandingan"],
        ["kode/04_buat_laporan_docx.py", "Penyusun laporan ini"],
        ["kode/05_docx_ke_pdf.py", "Pengubah laporan menjadi PDF"],
        ["kode/hasil_eksperimen.json", "Seluruh angka hasil eksekusi yang dipakai laporan"],
        ["kode/output_eksperimen.txt", "Keluaran teks skrip verifikasi"],
        ["kode/kutipan/", "Potongan kode sumber yang dikutip beserta nomor baris"],
        ["gambar/", "Tangkapan layar kode, diagram DFA, dan grafik"],
    ],
    header=["Berkas", "Isi"],
    lebar=[Cm(6.4), Cm(7.6)],
    kapsi="Isi berkas zip kode program",
    rata_kolom=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT],
)
par("Cara memeriksa: unduh zip, ekstrak, pasang pustaka automata-lib, lalu jalankan skrip "
    "01_eksperimen_minify.py memakai Python 3.13. Skrip itu menulis ulang seluruh angka pada laporan.")


# ------------------------------------------------------------------ DAFTAR ISI
_h_isi = h1("DAFTAR ISI")
_h_isi.paragraph_format.page_break_before = True
p = doc.add_paragraph()
p.paragraph_format.line_spacing = 1.5
fld_sederhana = OxmlElement("w:fldSimple")
fld_sederhana.set(qn("w:instr"), r'TOC \o "1-2" \z \u')
isi_fld = OxmlElement("w:r")
teks_isi = OxmlElement("w:t")
teks_isi.text = "Daftar isi sedang disiapkan."
isi_fld.append(teks_isi)
fld_sederhana.append(isi_fld)
p._p.append(fld_sederhana)

# ---------------------------------------------------------------------- BAB I
_awal_bab = h1("BAB I PENDAHULUAN")
_awal_bab.paragraph_format.page_break_before = True

h2("A. Latar Belakang")
par("Mata kuliah Teori Bahasa dan Automata membahas cara sebuah mesin abstrak mengenali "
    "bahasa. Salah satu mesin yang paling banyak dipakai di dunia nyata adalah Deterministic "
    "Finite Automaton (DFA). Kelas DFA dipakai pada lexer atau scanner kompilator, validasi "
    "format masukan, sampai pengenalan pola pada perangkat lunak.")
par("Persoalan penting pada DFA bukan hanya apakah mesin tersebut menerima bahasa yang benar, "
    "tetapi juga berapa besar mesin itu dibuat. Hasil konversi dari sebuah ekspresi reguler "
    "sering menghasilkan DFA yang berlebihan. Ada dua state yang perilakunya persis sama, ada "
    "state yang tidak pernah dicapai, dan ada state jebakan yang tidak berguna. DFA yang "
    "berlebihan berarti tabel transisi yang lebih besar, kebutuhan memori yang lebih tinggi, dan "
    "proses pencarian yang lebih lambat.")
par("Minimisasi DFA menyelesaikan persoalan tersebut. Prinsipnya sederhana, yaitu menggabungkan "
    "semua state yang tidak dapat dibedakan. Dua state disebut tidak dapat dibedakan bila untuk "
    "setiap string masukan, keduanya selalu berakhir pada hasil yang sama, sama-sama menerima "
    "atau sama-sama menolak.")
par("Laporan ini memakai pendekatan case based method. Objek yang dibedah bukan kode buatan "
    "sendiri, melainkan kode nyata pada pustaka terbuka automata-lib, khususnya fungsi "
    "DFA.minify(). Fungsi tersebut menerapkan algoritma Hopcroft dengan bantuan struktur data "
    "PartitionRefinement. Setelah kode dibedah, minimisasi juga dijalankan pada dua kasus uji, "
    "yaitu DFA kecil 8 state dan DFA gabungan aturan token sebuah scanner, sehingga terlihat "
    "dampaknya terhadap jumlah state dan ukuran tabel transisi.")

h2("B. Rumusan Masalah")
daftar([
    "Bagaimana konsep DFA, tabel transisi, dan state yang tidak dapat dibedakan dirumuskan secara formal?",
    "Bagaimana algoritma minimisasi DFA diimplementasikan pada fungsi DFA.minify() di pustaka automata-lib?",
    "Bagian kode mana yang berperan sebagai state, transisi, alfabet, dan state akhir?",
    "Berapa besar pengurangan jumlah state dan ukuran tabel transisi setelah minimisasi dijalankan?",
], gaya="List Number")

h2("C. Tujuan Penulisan")
daftar([
    "Menjelaskan landasan teori minimisasi DFA dan teknik indistinguishability.",
    "Membaca dan menjelaskan alur kode DFA.minify() beserta struktur data pendukungnya.",
    "Menyusun tabel pemetaan dari konsep teori ke variabel dan fungsi pada kode.",
    "Mengukur pengaruh minimisasi terhadap ukuran tabel transisi pada kasus DFA kecil dan pada kasus scanner.",
], gaya="List Number")

h2("D. Manfaat Penulisan")
par("Secara teori, laporan ini memperlihatkan hubungan langsung antara definisi formal DFA dan "
    "implementasinya di bahasa pemrograman. Secara praktik, hasil pengukuran memberi gambaran "
    "bahwa minimisasi bukan sekadar latihan di kertas, tetapi langkah yang menghemat memori pada "
    "program yang benar-benar dipakai.")

h2("E. Batasan Pembahasan")
par("Objek yang dibedah terbatas pada modul automata/fa/dfa.py dan automata/base/utils.py dari "
    "pustaka automata-lib versi " + DATA["versi_library"] + " dengan lisensi MIT. Model mesin "
    "dibatasi pada DFA. Sesuai instruksi tugas, tidak ada aplikasi baru yang dibuat. Skrip yang "
    "dilampirkan hanyalah alat verifikasi untuk menjalankan fungsi pustaka dan mengukur hasilnya.")

# --------------------------------------------------------------------- BAB II
h1("BAB II LANDASAN TEORI")

h2("A. Deterministic Finite Automaton")
par("DFA didefinisikan sebagai lima komponen M = (Q, Σ, δ, q0, F). Q adalah himpunan state, Σ "
    "adalah alfabet, δ adalah fungsi transisi δ : Q x Σ menuju Q, q0 adalah state awal, dan F "
    "adalah himpunan state akhir. Mesin bersifat deterministik karena untuk setiap pasangan state "
    "dan simbol, hanya ada satu tujuan.")
par("Sebuah mesin membaca string satu simbol demi satu. Fungsi transisi diperluas menjadi δ* "
    "yang bekerja pada rangkaian simbol. String w diterima bila δ*(q0, w) termasuk anggota F. "
    "Pada kode, fungsi δ* ini dijalankan sebagai perulangan sederhana, dan di pustaka automata-lib "
    "bentuknya bisa dilihat pada fungsi read_input_stepwise().")

h2("B. Tabel Transisi dan Biaya Memori")
par("Implementasi DFA menyimpan fungsi transisi sebagai tabel. Bila disimpan sebagai matriks "
    "padat, ukurannya adalah jumlah state dikali jumlah simbol. Tabel jenis ini cepat diakses "
    "karena indeks baris dan kolom dapat dihitung langsung, tetapi memakan memori paling besar. "
    "Bentuk lain adalah tabel jarang, yaitu hanya menyimpan pasangan yang benar-benar ada.")
par("Semakin banyak state, semakin besar tabel. Karena itu, setiap state yang sebetulnya bisa "
    "digabung berarti pemborosan yang ikut terbawa ke seluruh tabel, termasuk ke cache prosesor. "
    "Pada scanner kompilator yang dijalankan untuk setiap karakter berkas sumber, pemborosan ini "
    "terasa langsung.")

h2("C. State yang Tidak Dapat Dibedakan")
par("Dua state p dan q disebut tidak dapat dibedakan (indistinguishable) bila untuk setiap string "
    "w, keadaan δ*(p, w) termasuk F tepat ketika δ*(q, w) juga termasuk F. Sebaliknya, keduanya "
    "dapat dibedakan bila ada satu string penanda yang membuat salah satunya berakhir di state "
    "akhir dan yang lain tidak.")
par("Relasi tidak dapat dibedakan bersifat ekuivalen, sehingga himpunan state terpecah menjadi "
    "kelas-kelas ekuivalensi. DFA minimal dibentuk dengan mengganti setiap kelas menjadi satu "
    "state tunggal. Bila DFA sudah minimal, tidak ada lagi kelas yang berisi lebih dari satu "
    "state, kecuali bila ada state jebakan.")

h2("D. Algoritma Minimisasi: Moore dan Hopcroft")
par("Algoritma Moore bekerja dengan memperhalus partisi secara berulang. Langkah awalnya membagi "
    "state menjadi dua kelompok, yaitu state akhir dan bukan state akhir. Pada setiap iterasi, "
    "setiap kelompok dipecah lagi bila anggotanya memiliki pola transisi yang berbeda terhadap "
    "kelompok saat ini. Perulangan berhenti ketika partisi tidak berubah lagi.")
par("Algoritma Hopcroft memakai ide yang sama tetapi lebih hemat. Alih-alih memeriksa semua "
    "kelompok setiap putaran, algoritma ini menyimpan antrean pemecah (splitter) dan hanya "
    "memproses kelompok yang benar-benar dipisahkan. Kompleksitasnya O(k n log n), dengan n jumlah "
    "state dan k ukuran alfabet, sehingga jauh lebih cepat pada automaton besar.")
par("Keduanya menghasilkan partisi akhir yang sama, sebab keduanya menghitung relasi tidak dapat "
    "dibedakan secara lengkap. Perbedaan hanya pada urutan kerja dan biaya waktunya.")

h2("E. Peran Minimisasi pada Scanner")
par("Scanner bekerja dengan membaca karakter dan berpindah state sesuai tabel transisi. Setiap "
    "token dijelaskan oleh sebuah ekspresi reguler, lalu seluruh ekspresi digabung menjadi satu "
    "DFA. Penggabungan itulah yang biasanya menghasilkan state berlebih, karena setiap aturan "
    "dibangun terpisah lalu ditempel. Minimisasi menyatukan state yang berperilaku sama sehingga "
    "tabel kembali ringkas tanpa mengubah bahasa yang dikenali.")

# -------------------------------------------------------------------- BAB III
h1("BAB III BEDAH KODE PROGRAM")

h2("A. Profil Pustaka yang Dianalisis")
par("automata-lib adalah pustaka Python untuk membangun dan mengolah finite automata, pushdown "
    "automata, dan Turing machine. Pustaka ini ditulis oleh Caleb Evans, memakai lisensi MIT, dan "
    "tersedia di PyPI dengan nama paket automata-lib. Versi yang dipakai pada laporan ini adalah "
    "versi " + DATA["versi_library"] + ".")
tabel(
    [
        ["automata/fa/dfa.py", "Kelas DFA: atribut, pembacaan string, minify(), _minify(), operasi himpunan"],
        ["automata/fa/fa.py", "Kelas dasar automaton: validasi state, simbol, dan state akhir"],
        ["automata/base/utils.py", "PartitionRefinement, algoritma bantu untuk memperhalus partisi"],
        ["automata/fa/nfa.py", "Kelas NFA dan from_regex(), dipakai sebagai sumber DFA pada Kasus B"],
    ],
    header=["Berkas", "Peran"],
    lebar=[Cm(5.2), Cm(8.8)],
    kapsi="Tabel 1. Berkas pustaka yang dibedah",
    rata_kolom=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT],
)

h2("B. Struktur Data yang Mewakili DFA")
par("Kelas DFA menyimpan lima komponen formal sebagai atribut biasa. Nama atributnya bahkan "
    "mengikuti notasi teori, yaitu states, input_symbols, transitions, initial_state, dan "
    "final_states. Karena itu, pemetaan antara definisi dan kode hampir satu banding satu.")
gambar("kode_0_struktur_dfa.png",
       "Gambar 1. Atribut dan konstruktor kelas DFA (automata/fa/dfa.py baris 88 sampai 117)")
par("Atribut transitions bertipe kamus bertingkat. Kunci tingkat pertama adalah nama state, "
    "nilainya kamus kedua yang memetakan simbol ke state tujuan. Bentuk ini setara dengan fungsi "
    "δ pada definisi formal, hanya saja ditulis sebagai pemetaan, bukan fungsi matematika. State "
    "akhir disimpan terpisah pada final_states, sehingga pengecekan penerimaan cukup dilakukan "
    "dengan operasi keanggotaan himpunan.")

h2("C. Alur Penelusuran String")
par("Pembacaan string dilakukan per simbol. Fungsi _get_next_current_state() mengambil tujuan "
    "transisi dari kamus. Bila simbol tidak punya transisi, fungsi mengembalikan None, yang berarti "
    "mesin mati atau langsung menolak string. Setelah seluruh simbol habis, fungsi "
    "_check_for_input_rejection() memeriksa apakah state terakhir ada di final_states.")
gambar("kode_7_penelusuran.png",
       "Gambar 2. Penelusuran transisi dan pemeriksaan penolakan (baris 472 sampai 493)")
par("Perilaku ini sesuai definisi δ*. Perbedaannya hanya pada penanganan DFA parsial: bila "
    "transisi tidak tersedia, pustaka tidak menganggap state sebagai jebakan implisit, "
    "melainkan mengembalikan None dan menolak string.")

h2("D. Fungsi DFA.minify(): Dua Jalur Masuk")
par("Fungsi minify() adalah pintu masuk publik. Ia menerima parameter retain_names yang "
    "menentukan apakah nama state lama dipertahankan setelah penggabungan. Nilai False membuat "
    "state hasil penomoran baru dari 0, nilai True membuat state hasil berupa himpunan nama lama, "
    "misalnya frozenset berisi q2 dan q5. Bentuk kedua inilah yang dipakai pada laporan ini agar "
    "penggabungan mudah ditunjukkan.")
gambar("kode_1a_minify_judul.png",
       "Gambar 3. Judul dan dokumentasi fungsi DFA.minify() (baris 558 sampai 577)")
gambar("kode_1b_minify_badan.png",
       "Gambar 4. Badan fungsi DFA.minify() dengan dua cabang perlakuan (baris 578 sampai 605)")
par("Baris 578 sampai 588 menangani DFA parsial, yaitu DFA yang tidak semua state punya transisi "
    "untuk setiap simbol. Pada cabang ini pustaka lebih dulu membuang state mati dan state "
    "jebakan, karena keduanya tidak akan pernah membantu menerima string. Cabang kedua, baris 589 "
    "sampai 594, dipakai untuk DFA lengkap dan hanya menghitung state yang dapat dicapai dari "
    "state awal melalui penelusuran BFS.")
par("Kedua cabang bertemu pada baris 596 sampai 605, yaitu pemanggilan _minify() dengan parameter "
    "berupa himpunan state yang dapat dicapai, alfabet, tabel transisi, state awal, himpunan state "
    "akhir yang dapat dicapai, dan retain_names. Perhatikan bahwa state yang tidak dapat dicapai "
    "sudah dibuang sebelum minimisasi. Ini penting, sebab state yang tidak dicapai tidak punya arti "
    "bagi bahasa yang dikenali.")

h2("E. Tahap Persiapan: Peta Balik dan State Jebakan")
par("Bagian kedua, yaitu _minify(), bekerja dengan peta balik transisi. Untuk setiap simbol, "
    "pustaka membangun kamus yang memetakan state tujuan ke daftar state asal. Peta ini adalah "
    "kunci efisiensi algoritma Hopcroft, karena pertanyaan yang muncul saat pemecahan kelompok "
    "adalah siapa saja state yang berpindah ke kelompok tertentu, bukan sebaliknya.")
gambar("kode_2_minify_awal.png",
       "Gambar 5. Pembentukan peta balik transisi dan penambahan state jebakan (baris 623 sampai 657)")
par("Baris 633 sampai 656 mengisi peta balik. Bila ditemukan transisi menuju state yang tidak ada "
    "pada himpunan state yang dapat dicapai, pustaka membuat satu state jebakan tiruan dan "
    "mengarahkan seluruh transisi semacam itu ke sana. State jebakan ini hanya dipakai selama "
    "perhitungan partisi, lalu dibuang lagi pada tahap akhir. Tujuannya agar dua state yang "
    "berbeda hanya karena penanganan transisi kosong tetap terbaca sebagai sama.")

h2("F. Inti Algoritma: Memperhalus Partisi")
par("Baris 659 sampai 693 adalah jantung minimisasi. Mula-mula seluruh state dimasukkan ke satu "
    "kelompok besar, lalu langsung dipecah menjadi kelompok state akhir dan kelompok bukan state "
    "akhir pada baris 660. Setelah itu dibuat antrean proses yang berisi kelompok state akhir.")
gambar("kode_3_minify_partisi.png",
       "Gambar 6. Loop pemecahan partisi dengan antrean pemecah (baris 658 sampai 693)")
par("Pada setiap putaran, satu kelompok diambil dari antrean sebagai pemecah. Untuk setiap simbol, "
    "dikumpulkan semua state yang bertransisi masuk ke kelompok pemecah tersebut. Himpunan itu lalu "
    "dipakai untuk memecah kelompok lain menjadi dua bagian, yaitu bagian yang masuk ke pemecah dan "
    "bagian yang tidak. Baris 682 sampai 692 memilih salah satu dari dua bagian baru untuk dimasukkan "
    "ke antrean, dengan aturan bagian yang lebih kecil yang dipilih. Inilah pemilihan splitter khas "
    "Hopcroft yang membuat algoritma tetap hemat waktu.")
par("Perulangan berhenti ketika antrean kosong, yang berarti tidak ada lagi kelompok yang dapat "
    "dipecah. Hasilnya adalah partisi final, yaitu kelas-kelas ekuivalensi atau himpunan state yang "
    "tidak dapat dibedakan.")

h2("G. Menyusun DFA Baru dari Partisi")
par("Tahap terakhir mengubah partisi menjadi DFA utuh. Setiap kelas diganti menjadi satu state, "
    "lalu tabel transisi dibangun ulang dengan mengambil satu state wakil dari setiap kelas.")
gambar("kode_4a_minify_hasil.png",
       "Gambar 7. Pemberian nama state hasil dan peta balik nama baru (baris 694 sampai 718)")
gambar("kode_4b_minify_transisi.png",
       "Gambar 8. Pembentukan tabel transisi baru dan pengembalian objek DFA (baris 719 sampai 744)")
par("Baris 695 sampai 699 memberi nama pada setiap kelas. Bila retain_names bernilai False, nama "
    "diambil dari nomor urut. Bila True, nama berupa frozenset berisi state lama, sehingga jejak "
    "penggabungan tetap terlihat. Baris 720 sampai 732 lalu membangun kamus transisi baru, dan "
    "kelas yang memuat state jebakan dilewati agar tidak ikut menjadi state pada DFA hasil. Baris "
    "734 sampai 744 memeriksa apakah DFA hasil bersifat parsial dan mengembalikan objek DFA yang "
    "baru, sehingga DFA asal tidak berubah.")

h2("H. Peran PartitionRefinement")
par("Seluruh proses pemecahan kelompok dititipkan pada kelas PartitionRefinement di "
    "automata/base/utils.py. Kelas ini menyimpan dua hal, yaitu kamus dari id kelompok ke himpunan "
    "anggotanya, dan kamus dari anggota ke id kelompoknya. Dengan dua kamus ini, operasi "
    "\"pecah kelompok berdasarkan himpunan tertentu\" dapat dilakukan tanpa memeriksa seluruh state.")
gambar("kode_5a_partition_refinement.png",
       "Gambar 9. Struktur kelas PartitionRefinement (automata/base/utils.py baris 155 sampai 187)")
gambar("kode_5b_partition_refine.png",
       "Gambar 10. Metode refine() yang memecah kelompok menjadi dua (baris 189 sampai 216)")
par("Metode refine() mengelompokkan anggota masukan berdasarkan kelompok asalnya, lalu memotong "
    "kelompok yang terkena. Kelompok yang lebih kecil memperoleh id baru, sementara sisanya tetap "
    "memakai id lama. Karena pemotongan dilakukan dengan operasi himpunan, biaya waktunya sebanding "
    "dengan ukuran masukan, bukan ukuran seluruh DFA. Komentar pada baris 157 sampai 158 menyatakan "
    "hal ini secara eksplisit, yaitu ruang O(n) dan waktu sebanding ukuran argumen.")

# --------------------------------------------------------------------- BAB IV
h1("BAB IV PEMETAAN KONSEP, STUDI KASUS, DAN PENGUKURAN")

h2("A. Pemetaan Konsep Teori ke Kode")
par("Tabel berikut memetakan unsur formal automata ke variabel dan fungsi yang benar-benar ada pada "
    "kode, bukan pada kode rekaan.")
tabel(
    [
        ["Q (himpunan state)", "atribut states bertipe set", "Setiap nama state berupa string atau objek hashable"],
        ["Σ (alfabet)", "atribut input_symbols", "Setiap simbol berupa string satu karakter"],
        ["δ (fungsi transisi)", "atribut transitions, kamus dua tingkat", "transitions[asal][simbol] berisi state tujuan"],
        ["q0 (state awal)", "atribut initial_state", "Titik mulai pembacaan, juga dasar BFS pada minify()"],
        ["F (state akhir)", "atribut final_states yang bertipe set", "Penerimaan diperiksa dengan operasi keanggotaan"],
        ["δ* (transisi lanjut)", "_get_next_current_state() dan read_input_stepwise()", "Menelusuri string simbol demi simbol"],
        ["Kelas ekuivalensi", "objek kelompok pada PartitionRefinement", "Satu kelompok sama dengan satu state hasil"],
        ["State jebakan", "variabel trap_state pada _minify()", "Dibuat sementara, dibuang pada tahap akhir"],
        ["Peta balik transisi", "variabel transition_back_map", "Kamus simbol ke daftar state asal"],
        ["Antrean pemecah", "variabel processing pada _minify()", "Berisi id kelompok yang akan dipakai memecah"],
    ],
    header=["Konsep", "Bentuk pada kode", "Keterangan"],
    lebar=[Cm(3.6), Cm(5.4), Cm(5.0)],
    kapsi="Tabel 2. Pemetaan unsur automata ke variabel dan fungsi pada automata-lib",
    rata_kolom=[WD_ALIGN_PARAGRAPH.LEFT] * 3,
    ukuran=12,
)

h2("B. Kasus A: DFA Kecil dengan Jalur Ganda")
par("Kasus pertama adalah DFA 8 state yang sengaja memuat dua jalur ganda, meniru hasil konversi "
    "NFA ke DFA yang belum disederhanakan. Alfabetnya Σ = {d, ., e, +, -} dengan d mewakili satu "
    "digit. State q5 dibuat sebagai salinan q2, sedangkan q6 meniru perilaku q0. State q7 adalah "
    "jebakan yang menampung semua simbol yang tidak diharapkan.")
gambar("kode_6_studi_kasus.png",
       "Gambar 11. Definisi DFA Kasus A pada skrip verifikasi (01_eksperimen_minify.py baris 91 sampai 115)")

par("Tabel transisi sebelum minimisasi ditampilkan berikut. Baris adalah state, kolom adalah simbol "
    "alfabet. State akhir ditandai tanda bintang.")
baris_a = []
for state in sorted(A["transisi_sebelum"]):
    isi = A["transisi_sebelum"][state]
    nama = state + ("*" if state in A["final_sebelum"] else "")
    baris_a.append([nama] + [isi.get(s, "-") for s in SIMBOL])
tabel(baris_a, header=["State"] + SIMBOL,
      lebar=[Cm(2.0)] + [Cm(2.4)] * 5,
      kapsi="Tabel 3. Tabel transisi DFA Kasus A sebelum minimisasi (8 state, 40 entri)")
gambar("dfa_kasus_a_sebelum.png",
       "Gambar 12. Diagram DFA Kasus A sebelum minimisasi")

par("Algoritma Moore dijalankan sebagai pembanding hasil Hopcroft pada pustaka. Setiap iterasi "
    "memecah kelompok berdasarkan tanda transisi terhadap partisi sebelumnya. Partisi akhirnya "
    "sama dengan hasil DFA.minify(), yaitu enam kelompok, dan dua di antaranya berisi lebih dari "
    "satu state.")
partisi = A["partisi_moore"][:-1] if A["partisi_moore"][-1] == A["partisi_moore"][-2] else A["partisi_moore"]
baris_partisi = []
for i, part in enumerate(partisi):
    label = "Awal" if i == 0 else f"Iterasi {i}"
    baris_partisi.append([label] + ["{" + ", ".join(g) + "}" for g in part] +
                         [""] * (6 - len(part)))
tabel(baris_partisi, header=["Tahap", "K1", "K2", "K3", "K4", "K5", "K6"],
      lebar=[Cm(2.0)] + [Cm(2.0)] * 6,
      kapsi="Tabel 4. Riwayat pemecahan partisi pada Kasus A (algoritma Moore)",
      ukuran=12)

par("Pasangan yang digabung adalah q0 dengan q6, serta q2 dengan q5. Alasan q2 dan q5 "
    "indistinguishable dapat diperiksa langsung pada Tabel 3. Keduanya sama-sama state akhir, "
    "sama-sama berpindah ke dirinya sendiri saat menerima d, sama-sama menuju q3 saat menerima "
    "titik, sama-sama menuju q6 saat menerima e, dan sama-sama menuju q7 saat menerima tanda. "
    "Karena tanda tangan transisinya identik dan status akhirnya sama, tidak ada string yang dapat "
    "memisahkan keduanya.")
par("Pasangan q0 dan q6 juga berakhir serupa karena q6 menyalin perilaku q0 lewat perantara q5. "
    "Setelah q2 dan q5 digabung, perbedaan q0 dan q6 hilang. Inilah ciri minimisasi yang bekerja "
    "bertahap, yaitu penggabungan satu pasangan dapat membuka penggabungan pasangan lain.")

par("Hasil minimisasi pada Kasus A memperlihatkan penurunan jumlah state dan ukuran tabel.")
baris_a2 = []
for state in sorted(A["transisi_sesudah"]):
    isi = A["transisi_sesudah"][state]
    nama = state + ("*" if state in A["final_sesudah"] else "")
    baris_a2.append([nama] + [isi.get(s, "-") for s in SIMBOL])
tabel(baris_a2, header=["State baru"] + SIMBOL,
      lebar=[Cm(2.6)] + [Cm(2.3)] * 5,
      kapsi="Tabel 5. Tabel transisi DFA Kasus A sesudah minimisasi (6 state, 30 entri)",
      ukuran=12)
gambar("dfa_kasus_a_sesudah.png",
       "Gambar 13. Diagram DFA Kasus A sesudah minimisasi")
tabel(
    [
        ["Jumlah state", str(A["sebelum"]["states"]), str(A["sesudah"]["states"]),
         pct(A["sebelum"]["states"], A["sesudah"]["states"]) + "%"],
        ["State akhir", str(A["sebelum"]["final_states"]), str(A["sesudah"]["final_states"]),
         pct(A["sebelum"]["final_states"], A["sesudah"]["final_states"]) + "%"],
        ["Entri tabel transisi", str(A["sebelum"]["transition_entries"]),
         str(A["sesudah"]["transition_entries"]),
         pct(A["sebelum"]["transition_entries"], A["sesudah"]["transition_entries"]) + "%"],
        ["Sel matriks padat", str(A["sebelum"]["matriks_penuh"]), str(A["sesudah"]["matriks_penuh"]),
         pct(A["sebelum"]["matriks_penuh"], A["sesudah"]["matriks_penuh"]) + "%"],
        ["Perkiraan memori tabel (2 byte per sel)", str(A["sebelum"]["bytes_tabel_padat"]) + " byte",
         str(A["sesudah"]["bytes_tabel_padat"]) + " byte",
         pct(A["sebelum"]["bytes_tabel_padat"], A["sesudah"]["bytes_tabel_padat"]) + "%"],
    ],
    header=["Ukuran", "Sebelum", "Sesudah", "Penurunan"],
    lebar=[Cm(6.0), Cm(2.6), Cm(2.6), Cm(2.8)],
    kapsi="Tabel 6. Perbandingan ukuran DFA Kasus A",
    rata_kolom=[WD_ALIGN_PARAGRAPH.LEFT] + [WD_ALIGN_PARAGRAPH.CENTER] * 3,
)

h2("C. Kasus B: DFA Gabungan Aturan Token Scanner")
par("Kasus kedua meniru pekerjaan scanner. Enam aturan token ditulis sebagai ekspresi reguler, "
    "masing-masing mengenali bentuk bilangan yang berbeda. Setiap aturan diubah menjadi NFA, lalu "
    "menjadi DFA. Seluruh DFA kemudian digabung memakai operasi union dengan parameter minify "
    "dimatikan, sehingga hasil gabungannya masih berisi state berlebih. Setelah itu minimisasi "
    "dijalankan.")
gambar("alur_scanner.png",
       "Gambar 14. Alur pembentukan DFA scanner pada Kasus B", lebar_cm=12.4)
baris_aturan = []
for nama, info in DATA["per_aturan"].items():
    baris_aturan.append([nama, info["regex"], str(info["states"]),
                         str(info["transition_entries"])])
tabel(baris_aturan, header=["Aturan", "Ekspresi reguler", "State", "Entri"],
      lebar=[Cm(3.4), Cm(6.6), Cm(1.9), Cm(1.9)],
      kapsi="Tabel 7. Enam aturan token pada Kasus B dan ukuran DFA tiap aturan",
      rata_kolom=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT,
                  WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.CENTER],
      ukuran=12)
par("Penggabungan enam aturan menghasilkan DFA dengan " + str(B["sebelum"]["states"]) + " state, "
    + str(B["sebelum"]["transition_entries"]) + " entri transisi, dan "
    + str(B["sebelum"]["final_states"]) + " state akhir. Angka ini jauh lebih besar daripada DFA "
    "minimal bahasa yang sama, yaitu " + str(DATA["dfa_rujukan"]["states"]) + " state. Kelebihan "
    "itu muncul karena operasi union menyusun produk silang antar aturan, sehingga banyak state "
    "berperilaku sama tetap disimpan terpisah.")
par("Minimisasi menyatukan state-state tersebut. Sebanyak " + str(len(B["grup_gabungan"]))
    + " kelompok berisi lebih dari satu state, dan setelah digabung ukuran DFA turun menjadi "
    + str(B["sesudah"]["states"]) + " state dengan " + str(B["sesudah"]["transition_entries"])
    + " entri transisi.")
baris_gabung = []
for grup in sorted(B["grup_gabungan"], key=lambda g: min(int(x) for x in g)):
    kunci = "+".join(grup)
    baris_gabung.append([PETA_B[kunci],
                         "s" + ", s".join(sorted(grup, key=lambda x: int(x))),
                         str(len(grup))])
tabel(baris_gabung, header=["Label baru", "State lama yang digabung", "Jumlah"],
      lebar=[Cm(2.4), Cm(7.0), Cm(2.4)],
      kapsi="Tabel 8. Kelompok state yang digabung pada Kasus B",
      rata_kolom=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER],
      ukuran=12)
par("Nama state asli pada Kasus B berupa angka karena berasal dari hasil konversi NFA. Agar mudah "
    "dibaca, state tunggal ditulis s diikuti angkanya, sedangkan state hasil penggabungan diberi "
    "label pendek G1 sampai G" + str(len(KET_B)) + ". Arti setiap label ada pada Tabel 8, dan "
    "penulisan seperti G2 berarti beberapa state lama digabung menjadi satu state baru.")
def nama_b(label):
    return PETA_B[str(label)]


baris_b = []
for state in sorted(B["transisi_sesudah"], key=lambda x: min(int(v) for v in x.split("+"))):
    isi = B["transisi_sesudah"][state]
    label = nama_b(state)
    label += "*" if state in B["final_sesudah"] else ""
    baris_b.append([label] + [nama_b(isi[s]) if s in isi else "-" for s in SIMBOL])
tabel(baris_b, header=["State baru"] + SIMBOL,
      lebar=[Cm(3.4)] + [Cm(2.1)] * 5,
      kapsi="Tabel 9. Tabel transisi DFA Kasus B sesudah minimisasi (8 state, " + str(B["sesudah"]["transition_entries"]) + " entri)",
      ukuran=12)
gambar("dfa_kasus_b_sesudah.png",
       "Gambar 15. Diagram DFA Kasus B sesudah minimisasi", lebar_cm=12.4)
gambar("grafik_kasus_b.png",
       "Gambar 16. Perbandingan ukuran DFA Kasus B sebelum dan sesudah minimisasi", lebar_cm=11.8)
tabel(
    [
        ["Jumlah state", str(B["sebelum"]["states"]), str(B["sesudah"]["states"]),
         pct(B["sebelum"]["states"], B["sesudah"]["states"]) + "%"],
        ["State akhir", str(B["sebelum"]["final_states"]), str(B["sesudah"]["final_states"]),
         pct(B["sebelum"]["final_states"], B["sesudah"]["final_states"]) + "%"],
        ["Entri tabel transisi", str(B["sebelum"]["transition_entries"]),
         str(B["sesudah"]["transition_entries"]),
         pct(B["sebelum"]["transition_entries"], B["sesudah"]["transition_entries"]) + "%"],
        ["Sel matriks padat", str(B["sebelum"]["matriks_penuh"]), str(B["sesudah"]["matriks_penuh"]),
         pct(B["sebelum"]["matriks_penuh"], B["sesudah"]["matriks_penuh"]) + "%"],
        ["Perkiraan memori tabel (2 byte per sel)", str(B["sebelum"]["bytes_tabel_padat"]) + " byte",
         str(B["sesudah"]["bytes_tabel_padat"]) + " byte",
         pct(B["sebelum"]["bytes_tabel_padat"], B["sesudah"]["bytes_tabel_padat"]) + "%"],
    ],
    header=["Ukuran", "Sebelum", "Sesudah", "Penurunan"],
    lebar=[Cm(6.0), Cm(2.6), Cm(2.6), Cm(2.8)],
    kapsi="Tabel 10. Perbandingan ukuran DFA Kasus B",
    rata_kolom=[WD_ALIGN_PARAGRAPH.LEFT] + [WD_ALIGN_PARAGRAPH.CENTER] * 3,
)

h2("D. Verifikasi Hasil Minimisasi")
par("Minimisasi hanya sah bila bahasa yang dikenali tidak berubah. Verifikasi dilakukan dengan "
    "tiga cara. Cara pertama memakai pembanding bawaan pustaka, yaitu operasi kesamaan antar DFA "
    "yang di dalamnya memakai versi optimisasi algoritma Hopcroft-Karp untuk menguji ekuivalensi "
    "dua automaton. Hasilnya Kasus A "
    + ("ekuivalen" if A["ekuivalen_library"] else "tidak ekuivalen")
    + " dan Kasus B "
    + ("ekuivalen" if B["ekuivalen_library"] else "tidak ekuivalen") + ".")
par("Cara kedua menguji " + str(len(A["uji"])) + " string contoh pada DFA sebelum dan sesudah "
    "minimisasi. Seluruh hasilnya sama. Tabel berikut memperlihatkan sebagian hasil uji.")
baris_uji = []
for teks_uji, hasil_sebelum in A["uji_sebelum"].items():
    hasil_sesudah = A["uji_sesudah"][teks_uji]
    baris_uji.append([
        teks_uji,
        "diterima" if hasil_sebelum else "ditolak",
        "diterima" if hasil_sesudah else "ditolak",
        "sama" if hasil_sebelum == hasil_sesudah else "beda",
    ])
tabel(baris_uji, header=["String uji", "DFA sebelum", "DFA sesudah", "Kesimpulan"],
      lebar=[Cm(4.0), Cm(3.0), Cm(3.0), Cm(3.2)],
      kapsi="Tabel 11. Hasil uji string pada Kasus A sebelum dan sesudah minimisasi",
      rata_kolom=[WD_ALIGN_PARAGRAPH.LEFT] + [WD_ALIGN_PARAGRAPH.CENTER] * 3,
      ukuran=12)
par("Cara ketiga adalah pengujian menyeluruh. Seluruh string atas alfabet dengan panjang 0 sampai "
    + str(P["panjang_maks"]) + " dibangkitkan dan diuji pada tiga mesin sekaligus, yaitu DFA "
    "gabungan sebelum minimisasi, DFA hasil minimisasi, dan DFA rujukan yang dibangun langsung "
    "dari satu ekspresi reguler setara. Jumlah string yang diuji sebanyak "
    + angka(P["jumlah_string"]) + " buah, dan jumlah string yang diterima sebanyak "
    + angka(P["jumlah_diterima"]) + " buah.")
tabel(
    [
        ["Jumlah string yang diuji (panjang maksimum " + str(P["panjang_maks"]) + ")",
         angka(P["jumlah_string"])],
        ["String yang diterima DFA hasil minimisasi", angka(P["jumlah_diterima"])],
        ["Perbedaan sebelum dan sesudah minimisasi", str(P["jumlah_beda_minify"])],
        ["Perbedaan terhadap DFA rujukan", str(P["jumlah_beda_rujukan"])],
        ["Hasil pembandingan objek DFA (minify vs rujukan)",
         "ekuivalen" if P["minify_ekuivalen_rujukan"] else "tidak ekuivalen"],
        ["Rata-rata waktu eksekusi minify, Kasus A", str(A["waktu_minify_ms"]) + " ms"],
        ["Rata-rata waktu eksekusi minify, Kasus B", str(B["waktu_minify_ms"]) + " ms"],
    ],
    header=["Pemeriksaan", "Hasil"],
    lebar=[Cm(9.5), Cm(3.7)],
    kapsi="Tabel 12. Ringkasan pemeriksaan ekuivalensi",
    rata_kolom=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER],
    ukuran=12,
)
par("Tidak ada satu pun string yang hasilnya berbeda. Artinya, DFA hasil minimisasi menerima "
    "bahasa yang persis sama dengan DFA sebelumnya. Pemeriksaan menyeluruh ini juga berguna "
    "sebagai penjaga kesalahan penulisan ekspresi reguler, karena perbedaan kecil pada pola akan "
    "langsung terlihat sebagai selisih hasil uji.")
par("Bukti eksekusi ditampilkan berikut, diambil langsung dari keluaran skrip verifikasi.")
gambar("output_eksperimen_1.png",
       "Gambar 17. Keluaran skrip verifikasi, bagian 1 (Kasus A)", lebar_cm=12.4)
gambar("output_eksperimen_2.png",
       "Gambar 18. Keluaran skrip verifikasi, bagian 2 (Kasus B)", lebar_cm=12.8)
gambar("output_eksperimen_3.png",
       "Gambar 19. Keluaran skrip verifikasi, bagian 3 (pemeriksaan menyeluruh)", lebar_cm=10.5)

h2("E. Dampak terhadap Efisiensi Memori")
par("Tabel berikut merangkum pengaruh minimisasi terhadap ukuran tabel transisi pada kedua kasus. "
    "Perkiraan memori dihitung dengan asumsi tabel disimpan sebagai matriks padat berisi indeks "
    "state 16 bit, yaitu dua byte per sel. Angka ini adalah perkiraan kasar untuk memberi gambaran "
    "skala, bukan ukuran memori sebenarnya pada Python, yang menyimpan kamus dengan tambahan "
    "overhead.")
tabel(
    [
        ["Kasus", "State", "Entri transisi", "Sel matriks", "Perkiraan memori"],
        ["A sebelum", str(A["sebelum"]["states"]), str(A["sebelum"]["transition_entries"]),
         str(A["sebelum"]["matriks_penuh"]), str(A["sebelum"]["bytes_tabel_padat"]) + " byte"],
        ["A sesudah", str(A["sesudah"]["states"]), str(A["sesudah"]["transition_entries"]),
         str(A["sesudah"]["matriks_penuh"]), str(A["sesudah"]["bytes_tabel_padat"]) + " byte"],
        ["B sebelum", str(B["sebelum"]["states"]), str(B["sebelum"]["transition_entries"]),
         str(B["sebelum"]["matriks_penuh"]), str(B["sebelum"]["bytes_tabel_padat"]) + " byte"],
        ["B sesudah", str(B["sesudah"]["states"]), str(B["sesudah"]["transition_entries"]),
         str(B["sesudah"]["matriks_penuh"]), str(B["sesudah"]["bytes_tabel_padat"]) + " byte"],
    ],
    header=["Kasus", "State", "Entri transisi", "Sel matriks", "Perkiraan memori"],
    lebar=[Cm(2.8), Cm(1.9), Cm(3.1), Cm(2.7), Cm(3.2)],
    kapsi="Tabel 13. Ringkasan ukuran tabel transisi pada kedua kasus",
    ukuran=12,
)
par("Pada Kasus A, jumlah state turun " + pct(A["sebelum"]["states"], A["sesudah"]["states"])
    + " persen dan entri transisi turun " + pct(A["sebelum"]["transition_entries"], A["sesudah"]["transition_entries"])
    + " persen. Pada Kasus B, jumlah state turun " + pct(B["sebelum"]["states"], B["sesudah"]["states"])
    + " persen dan entri transisi turun " + pct(B["sebelum"]["transition_entries"], B["sesudah"]["transition_entries"])
    + " persen. Penurunan pada Kasus B hampir dua kali lipat Kasus A karena DFA gabungan hasil "
    "operasi union memang menyimpan banyak state kembar.")
par("Bagi scanner, angka ini berdampak pada tiga hal. Pertama, tabel transisi yang lebih kecil "
    "lebih mudah dimuat sepenuhnya ke dalam cache prosesor, sehingga perpindahan state menjadi lebih "
    "cepat ketika berkas sumber berukuran besar dipindai. Kedua, proses pembuatan tabel tidak perlu "
    "mengalokasikan ruang untuk state yang sama sekali tidak menambah kemampuan mengenali token. "
    "Ketiga, biaya perawatan kode turun, karena jumlah state yang harus diperiksa manual saat "
    "mencari kesalahan aturan token menjadi lebih sedikit.")

# ---------------------------------------------------------------------- BAB V
h1("BAB V PENUTUP")

h2("A. Kesimpulan")
daftar([
    "DFA pada pustaka automata-lib disimpan sebagai lima atribut yang mengikuti notasi formal, "
    "yaitu states, input_symbols, transitions, initial_state, dan final_states, sehingga pemetaan "
    "antara teori dan kode dapat dilakukan hampir satu banding satu.",
    "Minimisasi diimplementasikan dalam dua lapis. Fungsi minify() membuang state yang tidak dapat "
    "dicapai dan menangani DFA parsial, sedangkan _minify() menjalankan algoritma Hopcroft memakai "
    "peta balik transisi dan antrean pemecah.",
    "Struktur data PartitionRefinement menyimpan kelompok dan keanggotaannya secara dua arah, "
    "sehingga pemecahan kelompok hanya memakan waktu sebanding ukuran masukan, sesuai klaim O(n) "
    "pada dokumen kode.",
    "Pada Kasus A, minimisasi menurunkan jumlah state dari " + str(A["sebelum"]["states"]) + " menjadi "
    + str(A["sesudah"]["states"]) + " dan entri transisi dari " + str(A["sebelum"]["transition_entries"])
    + " menjadi " + str(A["sesudah"]["transition_entries"]) + ".",
    "Pada Kasus B, minimisasi menurunkan jumlah state dari " + str(B["sebelum"]["states"]) + " menjadi "
    + str(B["sesudah"]["states"]) + " dan entri transisi dari " + str(B["sebelum"]["transition_entries"])
    + " menjadi " + str(B["sesudah"]["transition_entries"]) + ", dengan bahasa yang dikenali tetap sama "
    "berdasarkan pengujian " + angka(P["jumlah_string"]) + " string dan pembandingan DFA bawaan pustaka.",
], gaya="List Number")

h2("B. Refleksi")
par("Pembacaan kode memberi dua pelajaran yang tidak terlihat dari buku teks. Pertama, hal yang "
    "paling menentukan performa justru pembalikan arah peta transisi. Peta balik memungkinkan "
    "pertanyaan siapa yang masuk ke kelompok ini dijawab dalam satu langkah, dan inilah yang "
    "membuat hopcroft tetap cepat. Kedua, penanganan state jebakan menunjukkan bahwa implementasi "
    "nyata harus peduli pada kasus pinggiran. DFA parsial, transisi yang tidak ada, dan state yang "
    "tidak dicapai ditangani lebih dulu, baru partisi dijalankan.")
par("Hal menarik berikutnya adalah hasil Kasus A dan Kasus B berbeda besarnya. Konversi langsung "
    "dari ekspresi reguler ke DFA pada pustaka ini ternyata sudah menghasilkan DFA minimal, "
    "sedangkan operasi gabungan menghasilkan DFA yang jauh dari minimal. Artinya, sumber "
    "pemborosan state paling sering adalah cara DFA dibangun, bukan algoritma minimisasinya. "
    "Kesadaran ini berguna saat merancang aturan token pada scanner, misalnya dengan menghindari "
    "penggabungan aturan yang sebenarnya saling tumpang tindih.")
par("Keterbatasan yang perlu dicatat adalah perkiraan memori pada laporan ini masih kasar, karena "
    "Python menyimpan kamus dengan overhead tambahan yang tidak diperhitungkan. Di samping itu, "
    "pengujian menyeluruh hanya dilakukan sampai panjang string " + str(P["panjang_maks"])
    + ", sehingga kesamaan bahasa secara umum tetap bertumpu pada pembandingan DFA bawaan pustaka.")

h2("C. Saran")
daftar([
    "Untuk tugas lanjutan, pengukuran dapat dilengkapi dengan pengukuran waktu pemindaian "
    "sebenarnya pada berkas sumber, bukan hanya ukuran tabel.",
    "Perbandingan dapat diperluas dengan algoritma Moore buatan sendiri untuk melihat selisih "
    "waktu pada automaton yang lebih besar.",
    "Pada perancangan scanner, gunakan satu DFA gabungan untuk seluruh token, lalu jalankan "
    "minimisasi sekali di akhir, bukan minimisasi pada setiap aturan secara terpisah.",
], gaya="List Number")

# --------------------------------------------------------------- DAFTAR PUSTAKA
h1("DAFTAR PUSTAKA")
pustaka = [
    "Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2007). Compilers: Principles, techniques, "
    "and tools (2nd ed.). Pearson Addison-Wesley.",
    "Evans, C. (2024). automata: A Python library for simulating finite automata, pushdown automata, "
    "and Turing machines (versi " + DATA["versi_library"] + ") [Perangkat lunak]. "
    "https://github.com/caleb531/automata",
    "Eppstein, D. (2008). PartitionRefinement: A data structure for maintaining a partition of a set "
    "[Kode sumber]. University of California, Irvine. "
    "https://www.ics.uci.edu/~eppstein/PADS/PartitionRefinement.py",
    "Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2006). Introduction to automata theory, "
    "languages, and computation (3rd ed.). Addison-Wesley.",
    "Linz, P. (2016). An introduction to formal languages and automata (6th ed.). Jones & Bartlett "
    "Learning.",
    "Sipser, M. (2012). Introduction to the theory of computation (3rd ed.). Cengage Learning.",
]
for p_ in pustaka:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.left_indent = Cm(1.27)
    p.paragraph_format.first_line_indent = Cm(-1.27)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(p_)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)

# ------------------------------------------------------------------- LAMPIRAN
h1("LAMPIRAN: BERKAS PENDUKUNG")
par("Seluruh berkas pendukung disimpan pada folder output pekerjaan ini, dengan susunan sebagai berikut.")
tabel(
    [
        ["kode/01_eksperimen_minify.py", "Skrip verifikasi: membangun dua kasus DFA, menjalankan minify(), "
                                         "mengukur ukuran, dan menguji ekuivalensi"],
        ["kode/02_buat_gambar_kode.py", "Skrip pembuat tangkapan layar kode sumber"],
        ["kode/03_diagram_dfa.py", "Skrip pembuat diagram DFA dan grafik perbandingan"],
        ["kode/04_buat_laporan_docx.py", "Skrip penyusun laporan ini"],
        ["kode/05_docx_ke_pdf.py", "Skrip pengubah laporan menjadi PDF memakai Microsoft Word"],
        ["kode/hasil_eksperimen.json", "Seluruh angka hasil eksekusi yang dipakai pada laporan"],
        ["kode/output_eksperimen.txt", "Keluaran teks skrip verifikasi"],
        ["kode/kutipan/", "Potongan kode sumber yang dikutip, disertai nomor baris aslinya"],
        ["gambar/", "Tangkapan layar kode, diagram DFA, dan grafik"],
    ],
    header=["Berkas", "Isi"],
    lebar=[Cm(6.4), Cm(7.6)],
    kapsi="Tabel 14. Berkas pendukung pada folder output",
    rata_kolom=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT],
    ukuran=12,
)
par("Cara menjalankan ulang: pasang pustaka dengan perintah pip install automata-lib, lalu jalankan "
    "skrip 01_eksperimen_minify.py memakai Python 3.13. Skrip akan menulis ulang berkas "
    "hasil_eksperimen.json, sehingga angka pada laporan dapat diperiksa kembali. Pembuatan gambar "
    "dan laporan dijalankan berurutan dengan skrip 02, 03, dan 04.")

# ------------------------------------------------------------- LAMPIRAN KODE
h1("LAMPIRAN KODE PROGRAM")
par("Dua potongan kode berikut adalah bagian yang paling menentukan hasil laporan, ditampilkan sebagai "
    "tangkapan layar kode sumber beserta nomor barisnya. Berkas lengkap tersedia pada tautan di halaman 2.")

def _kode(nama, mulai, akhir, kapsi):
    """Tampilkan potongan kode beserta nomor baris aslinya."""
    berkas = HERE / nama
    semua = berkas.read_text(encoding="utf-8").splitlines()[mulai - 1:akhir]
    par(kapsi + f" (baris {mulai} sampai {akhir})", indentasi=False, tebal=True, before=8, after=4)
    for nomor, isi in enumerate(semua, start=mulai):
        if not isi.strip():
            continue
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.first_line_indent = Cm(0)
        r = p.add_run(f"{nomor:>3}  " + isi.replace("	", "    "))
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)

gambar("lampiran_kode_1.png", "Kode 1. Fungsi ukuran() dan moore_partitions(), baris 34 sampai 62", lebar_cm=13.0, tinggi_maks=11.2)
_p_kode2 = par("Fungsi ukuran() menghitung jumlah state dan entri transisi, sedangkan moore_partitions() menjalankan "
    "pembanding algoritma Moore. Fungsi gambar_dfa() berikut dipakai untuk menggambar diagram DFA sebelum dan "
    "sesudah minimisasi, termasuk penanda state awal dan state akhir.")
_p_kode2.paragraph_format.page_break_before = True
gambar("lampiran_kode_2.png", "Kode 2. Fungsi gambar_dfa(), baris 76 sampai 104", lebar_cm=13.0, tinggi_maks=10.6)

nomor_halaman_footer()

def _sapu_font():
    """Paksa seluruh run memakai Times New Roman 12 pt."""
    def proses(par):
        for r in par.runs:
            if not r.text.strip():
                continue
            r.font.name = "Times New Roman"
            rf = r._element.get_or_add_rPr().get_or_add_rFonts()
            for atribut in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                rf.set(qn(atribut), "Times New Roman")
            if r.font.size is None:
                r.font.size = Pt(12)
    for par in doc.paragraphs:
        proses(par)
    for t in doc.tables:
        for row in t.rows:
            for sel in row.cells:
                for par in sel.paragraphs:
                    proses(par)
    for sek in doc.sections:
        for par in list(sek.footer.paragraphs) + list(sek.header.paragraphs):
            proses(par)


_sapu_font()
keluaran = OUT_DIR / "Laporan_CBM_P11_Minimisasi_DFA.docx"
doc.save(keluaran)
print("laporan ditulis:", keluaran)
print("jumlah paragraf:", len(doc.paragraphs), "| jumlah tabel:", len(doc.tables))
