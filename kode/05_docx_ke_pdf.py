"""
Mengubah laporan .docx menjadi .pdf memakai Microsoft Word (COM).

Sebelum diekspor, daftar isi (field TOC) diperbarui supaya nomor halaman terisi.
"""

import os
import sys
from pathlib import Path

import win32com.client as win32

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent
DOCX = OUT_DIR / "Laporan_CBM_P11_Minimisasi_DFA.docx"
PDF = OUT_DIR / "Laporan_CBM_P11_Minimisasi_DFA.pdf"

word = win32.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0

try:
    dokumen = word.Documents.Open(str(DOCX), ReadOnly=False)

    # perbarui daftar isi dan seluruh field (nomor halaman)
    for i in range(1, dokumen.TablesOfContents.Count + 1):
        dokumen.TablesOfContents(i).Update()
    dokumen.Fields.Update()
    for i in range(1, dokumen.TablesOfContents.Count + 1):
        dokumen.TablesOfContents(i).Update()

    dokumen.Repaginate()
    halaman = dokumen.ComputeStatistics(2)  # 2 = wdStatisticPages
    dokumen.Save()
    dokumen.ExportAsFixedFormat(
        OutputFileName=str(PDF),
        ExportFormat=17,  # wdExportFormatPDF
        OpenAfterExport=False,
        OptimizeFor=0,
        CreateBookmarks=1,
        DocStructureTags=True,
    )
    dokumen.Close(SaveChanges=0)
    print("PDF ditulis:", PDF)
    print("jumlah halaman:", halaman)
finally:
    word.Quit()

print("ukuran PDF:", round(os.path.getsize(PDF) / 1024 / 1024, 2), "MB")
