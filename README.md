# Minimisasi DFA dengan automata-lib

Eksperimen tugas Case Based Method pertemuan 11, mata kuliah Teori Bahasa dan Automata,
Program Studi Informatika, Universitas Negeri Padang.

Objek yang diuji adalah fungsi `DFA.minify()` pada pustaka Python `automata-lib` versi
9.2.0. Repositori ini berisi kode eksperimen, data hasil pengukuran, dan gambar diagram
DFA sebelum dan sesudah minimisasi.

## Dasar pemikiran

DFA dinyatakan sebagai lima komponen M = (Q, Σ, δ, q0, F). Pada implementasi, δ disimpan
sebagai tabel berisi pasangan state dan simbol. Karena tabel itu tumbuh sebanding jumlah
state, setiap state yang perilakunya sama menambah beban memori dan waktu pencarian.

Dua state disebut tidak dapat dibedakan bila untuk setiap string masukan keduanya berakhir
pada hasil yang sama, sama sama menerima atau sama sama menolak. Relasi ini membentuk kelas
ekuivalensi, dan setiap kelas boleh diganti dengan satu state. Pekerjaan itulah yang
dilakukan minimisasi. Pustaka automata-lib memakai algoritma Hopcroft dengan peta balik
transisi dan antrean pemecah, lalu memakai `PartitionRefinement` untuk memecah kelompok
state.

## Yang diuji

Ada dua kasus, keduanya dijalankan oleh `src/eksperimen_minify.py`.

Kasus A adalah DFA kecil 8 state dengan alfabet Σ = {d, ., e, +, -} yang sengaja memuat
dua jalur ganda. State q5 dibuat meniru q2, sedangkan q6 meniru q0. Kasus ini dipakai untuk
melihat proses penggabungan langkah demi langkah.

Kasus B meniru pekerjaan scanner. Enam aturan token ditulis sebagai ekspresi reguler, lalu
masing masing dibangun menjadi NFA dan DFA. Semua aturan digabung memakai operasi union
dengan `minify=False`, sehingga hasil gabungannya masih memuat state kembar. Setelah itu
minimisasi dijalankan.

## Cara menjalankan

```bash
pip install -r requirements.txt
python src/eksperimen_minify.py
python src/diagram_hasil.py
```

Skrip pertama menulis ulang `hasil/hasil_eksperimen.json` dan mencetak ringkasan ke layar.
Skrip kedua menggambar diagram DFA dan grafik perbandingan ke folder `gambar/`.

## Hasil pengukuran

| Kasus | State sebelum | State sesudah | Entri sebelum | Entri sesudah | Penurunan state | Penurunan entri |
|---|---|---|---|---|---|---|
| A, DFA kecil jalur ganda | 8 | 6 | 40 | 30 | 25 persen | 25 persen |
| B, gabungan enam aturan token | 16 | 8 | 30 | 17 | 50 persen | 43,3 persen |

Jumlah state akhir ikut turun, dari 3 menjadi 2 pada Kasus A dan dari 6 menjadi 3 pada
Kasus B. Pada Kasus B, alur pembentukannya adalah 36 state NFA menjadi 16 state DFA
gabungan, lalu 8 state setelah minimisasi, sama dengan DFA rujukan yang dibangun langsung
dari satu ekspresi reguler.

State yang digabung pada Kasus A ada dua pasangan, yaitu q0 dengan q6 dan q2 dengan q5.
Pada Kasus B ada lima kelompok, yaitu 10 dengan 11 dan 4, lalu 6 dengan 9, 12 dengan 14 dan
7, 13 dengan 15 dan 8, serta 3 dengan 5.

Algoritma Moore yang dijalankan sebagai pembanding menghasilkan partisi yang sama.
Kasus A memerlukan 5 iterasi dan Kasus B memerlukan 4 iterasi.

## Verifikasi ekuivalensi

Minimisasi hanya sah bila bahasa yang dikenali tidak berubah. Pemeriksaan dilakukan tiga
cara, dan ketiganya sepakat.

| Pemeriksaan | Kasus A | Kasus B |
|---|---|---|
| Pembanding DFA bawaan pustaka | ekuivalen | ekuivalen |
| Uji 28 string contoh sebelum dan sesudah | seluruhnya sama | seluruhnya sama |
| Pengujian menyeluruh | 0 perbedaan | 0 perbedaan |

Pengujian menyeluruh membangkitkan seluruh string atas alfabet sampai panjang 6, sebanyak
19.531 string. Sebanyak 127 string diterima, dan tidak ada satu string pun yang hasilnya
berbeda antara DFA sebelum minimisasi, DFA sesudah minimisasi, dan DFA rujukan.

## Analisis

Penurunan pada kedua kasus berbeda besar, dan penyebabnya bukan algoritma minimisasi,
melainkan cara DFA dibentuk. Kasus A hanya kehilangan seperempat state karena memang hanya
memuat dua pasangan state kembar. Kasus B kehilangan setengah state karena operasi union
menyusun produk silang antar aturan, sehingga banyak state berperilaku sama tetap disimpan
terpisah. Konversi langsung dari satu ekspresi reguler ke DFA, seperti pada DFA rujukan,
ternyata sudah menghasilkan bentuk minimal.

Waktu eksekusi `minify()` sendiri sangat kecil, yaitu 0,079 ms pada Kasus A dan 0,115 ms
pada Kasus B, karena kedua mesin berukuran kecil. Karena itu, manfaat minimisasi pada
eksperimen ini lebih tepat dibaca sebagai penghematan ukuran tabel, bukan penghematan waktu
proses. Hopcroft baru terasa keunggulannya pada automaton berukuran besar. Untuk mengukur
dampak waktu, pengujian perlu diperluas ke DFA dengan ratusan atau ribuan state.

## Batas eksperimen

- Ukuran mesin kecil, sehingga waktu eksekusi belum menggambarkan perilaku algoritma pada
  automaton besar.
- Pengujian menyeluruh hanya sampai panjang string 6, sehingga kesamaan bahasa secara umum
  bertumpu pada pembanding DFA bawaan pustaka.
- Perkiraan memori pada hasil pengukuran memakai asumsi tabel matriks padat 2 byte per sel,
  bukan ukuran memori sebenarnya di Python.

## Struktur repositori

```
src/eksperimen_minify.py     eksperimen utama, menulis hasil/hasil_eksperimen.json
src/diagram_hasil.py         penggambar diagram DFA dan grafik perbandingan
hasil/hasil_eksperimen.json  seluruh angka hasil pengukuran
hasil/output_eksperimen.txt  keluaran teks saat eksperimen dijalankan
gambar/                      diagram DFA sebelum dan sesudah, alur scanner, grafik
```

## Lingkungan

- Python 3.13
- automata-lib 9.2.0
- matplotlib untuk diagram dan grafik
