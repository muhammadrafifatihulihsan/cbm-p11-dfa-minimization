# Analisis dan Simulasi Minimisasi DFA pada automata-lib

Berkas pendukung tugas Case Based Method pertemuan 11, mata kuliah Teori Bahasa dan
Automata, Program Studi Informatika, Universitas Negeri Padang.

Objek yang dibedah adalah fungsi `DFA.minify()` pada pustaka Python `automata-lib` versi
9.2.0. Isinya kode verifikasi, data hasil eksekusi, dan gambar pendukung laporan.

## Hasil singkat

| Kasus | Sebelum | Sesudah | Penurunan |
|---|---|---|---|
| A, DFA kecil dengan jalur ganda | 8 state, 40 entri | 6 state, 30 entri | 25 persen |
| B, DFA gabungan enam aturan token | 16 state, 30 entri | 8 state, 17 entri | 50 persen |

Verifikasi ekuivalensi memakai tiga cara: pembanding DFA bawaan pustaka, uji string
contoh, dan pengujian menyeluruh 19.531 string dengan panjang 0 sampai 5. Tidak ada satu
string pun yang hasilnya berbeda sesudah minimisasi, sehingga bahasa yang dikenali tetap
sama.

## Isi folder

```
kode/01_eksperimen_minify.py     skrip verifikasi utama, menulis hasil_eksperimen.json
kode/02_buat_gambar_kode.py      pembuat tangkapan layar kode sumber
kode/03_diagram_dfa.py           pembuat diagram DFA dan grafik perbandingan
kode/04_buat_laporan_docx.py     penyusun laporan .docx
kode/05_docx_ke_pdf.py           pengubah laporan menjadi PDF memakai Word
kode/hasil_eksperimen.json       seluruh angka yang dipakai laporan
kode/output_eksperimen.txt       keluaran teks skrip verifikasi
kode/kutipan/                    potongan kode sumber yang dikutip, dengan nomor baris
gambar/                          tangkapan layar kode, diagram DFA, dan grafik
```

## Cara menjalankan

Pasang pustaka yang dibutuhkan:

```bash
pip install -r requirements.txt
```

Jalankan skrip verifikasi:

```bash
python kode/01_eksperimen_minify.py
```

Skrip ini membangun dua kasus DFA, menjalankan `minify()`, mengukur jumlah state dan entri
transisi, lalu menguji ekuivalensi bahasa sebelum dan sesudah minimisasi. Hasilnya ditulis
ulang ke `kode/hasil_eksperimen.json` dan `kode/output_eksperimen.txt`.

Pembuatan gambar dan laporan dijalankan berurutan:

```bash
python kode/02_buat_gambar_kode.py
python kode/03_diagram_dfa.py
python kode/04_buat_laporan_docx.py
python kode/05_docx_ke_pdf.py
```

Skrip `05_docx_ke_pdf.py` memakai otomasi COM, jadi hanya berjalan di Windows yang
memiliki Microsoft Word.

## Lingkungan

- Python 3.13
- automata-lib 9.2.0
- matplotlib, networkx, Pillow untuk gambar
- python-docx untuk laporan
- pywin32 dan Microsoft Word untuk ekspor PDF

## Catatan

Tidak ada aplikasi baru yang dibuat pada tugas ini. Seluruh skrip berfungsi sebagai alat
verifikasi untuk menjalankan fungsi pustaka, mengukur hasilnya, dan menyusun laporan.
