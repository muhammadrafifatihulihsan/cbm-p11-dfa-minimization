"""
Menggambar diagram DFA (tata letak berlapis) dan grafik perbandingan
dari hasil/hasil_eksperimen.json.

Keluaran:
  dfa_kasus_a_sebelum.png, dfa_kasus_a_sesudah.png, dfa_kasus_b_sesudah.png,
  alur_scanner.png, grafik_kasus_b.png
"""

import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "gambar"
HASIL = HERE.parent / "hasil"
OUT.mkdir(parents=True, exist_ok=True)
DATA = json.loads((HASIL / "hasil_eksperimen.json").read_text(encoding="utf-8"))

URUT_SIMBOL = ["d", ".", "e", "+", "-"]
TINTA = "#111827"
AKSEN = "#1d4ed8"
AKSEN2 = "#b91c1c"
ABU = "#6b7280"
ISI_NODE = "#e8eeff"
ISI_FINAL = "#fde68a"


def gabung_label(labels):
    urut = [s for s in URUT_SIMBOL if s in labels]
    urut += sorted(set(labels) - set(URUT_SIMBOL))
    return " , ".join(urut)


def teks_node(nama):
    bagian = nama.split("+")
    if len(bagian) == 1:
        return nama
    tengah = (len(bagian) + 1) // 2
    return "+".join(bagian[:tengah]) + "\n+" + "+".join(bagian[tengah:])


def posisi_berlapis(transisi, awal):
    """State disusun per lapis (jarak dari state awal), bukan melingkar."""
    level = {awal: 0}
    antre = [awal]
    while antre:
        u = antre.pop(0)
        for v in transisi.get(u, {}).values():
            if v not in level:
                level[v] = level[u] + 1
                antre.append(v)

    semua = set(transisi) | {v for isi in transisi.values() for v in isi.values()}
    for n in semua:
        if n not in level:
            level[n] = max(level.values()) + 1 if level else 0

    kelompok = defaultdict(list)
    for n, lv in level.items():
        kelompok[lv].append(n)

    pos = {}
    for lv in sorted(kelompok):
        anggota = sorted(kelompok[lv])
        n = len(anggota)
        for i, node in enumerate(anggota):
            pos[node] = (lv * 3.1, ((n - 1) / 2 - i) * 2.55)
    return pos


def gambar_dfa(transisi, awal, final, judul, keluar, radius_node=0.34, belok=0.32,
               buang_trap=None):
    if buang_trap:
        # Panah ke state jebakan dihilangkan agar gambar terbaca; disebutkan di judul.
        transisi = {k: {s: v for s, v in isi.items() if v != buang_trap}
                    for k, isi in transisi.items() if k != buang_trap}

    tepi = defaultdict(list)
    for asal, isi in transisi.items():
        for simbol, tujuan in isi.items():
            tepi[(asal, tujuan)].append(simbol)

    nodes = sorted({n for (a, b) in tepi for n in (a, b)})
    if awal not in nodes:
        nodes.append(awal)

    pos = posisi_berlapis(transisi, awal)
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    pad = radius_node * 2.4
    xlim = (min(xs) - pad - 0.7, max(xs) + pad + 0.2)
    ylim = (min(ys) - pad - 0.2, max(ys) + pad + 0.5)
    rasio = (xlim[1] - xlim[0]) / (ylim[1] - ylim[0])
    tinggi = 3.5
    tinggi_skala = max(1.0, (ylim[1] - ylim[0]) / 4.2)
    fig, ax = plt.subplots(figsize=(min(7.2, max(4.6, tinggi * rasio)), tinggi * tinggi_skala),
                           dpi=220)
    ax.set_axis_off()
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")

    for n in nodes:
        x, y = pos[n]
        ax.add_patch(plt.Circle((x, y), radius_node,
                                facecolor=ISI_FINAL if n in final else ISI_NODE,
                                edgecolor=TINTA, linewidth=1.7, zorder=3))
        if n in final:
            ax.add_patch(plt.Circle((x, y), radius_node * 0.80, facecolor="none",
                                    edgecolor=TINTA, linewidth=1.1, zorder=4))
        ax.text(x, y, teks_node(n), ha="center", va="center",
                fontsize=11.0 if len(n) <= 6 else 9.6, color=TINTA, zorder=6,
                linespacing=1.05)

    x, y = pos[awal]
    ax.annotate("", xy=(x - radius_node, y), xytext=(x - radius_node - 0.62, y),
                arrowprops=dict(arrowstyle="-|>", color=AKSEN, lw=2.0), zorder=2)

    for (asal, tujuan), simbol in tepi.items():
        label = gabung_label(simbol)
        xa, ya = pos[asal]
        xb, yb = pos[tujuan]

        if asal == tujuan:
            ax.annotate("", xy=(xa + 0.14, ya + radius_node + 0.18),
                        xytext=(xa - 0.14, ya + radius_node + 0.18),
                        arrowprops=dict(arrowstyle="-|>", color=AKSEN2, lw=1.4,
                                        connectionstyle="arc3,rad=-1.6"), zorder=2)
            ax.text(xa, ya + radius_node + 0.55, label, fontsize=10.0, color=AKSEN2,
                    ha="center", va="bottom")
            continue

        maju = xb > xa + 1e-9
        rad = 0.0 if maju else belok
        warna = ABU if asal in teks_trap(tujuan) else TINTA
        ax.annotate("", xy=(xb, yb), xytext=(xa, ya),
                    arrowprops=dict(arrowstyle="-|>", color=warna, lw=1.2,
                                    shrinkA=radius_node * 68, shrinkB=radius_node * 68,
                                    connectionstyle=f"arc3,rad={rad}"), zorder=1)

        t = 0.45
        mx, my = xa + (xb - xa) * t, ya + (yb - ya) * t
        vx, vy = xb - xa, yb - ya
        panjang = math.hypot(vx, vy) or 1.0
        ox, oy = -vy / panjang, vx / panjang
        geser = 0.26 if maju else 0.38
        ax.text(mx + ox * geser, my + oy * geser, label, fontsize=9.8, color=warna,
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.13", fc="white", ec="none", alpha=0.95),
                zorder=5)

    ax.set_title(judul, fontsize=12.5, color=TINTA, pad=10, linespacing=1.35)
    fig.savefig(keluar, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("tulis", keluar.name)


def teks_trap(tujuan):
    """Penanda untuk mewarnai panah yang menuju state jebakan (q7)."""
    return "q7" if tujuan in {"q7"} else ""


# ------------------------------------------------------------------ Kasus A
a = DATA["kasus_a"]
gambar_dfa(a["transisi_sebelum"], a["awal_sebelum"], set(a["final_sebelum"]),
           "DFA Kasus A sebelum minimisasi: 8 state, 40 entri transisi.\n"
           "Panah ke state jebakan q7 tidak digambar supaya terbaca.",
           OUT / "dfa_kasus_a_sebelum.png", buang_trap="q7", radius_node=0.42)
gambar_dfa(a["transisi_sesudah"], a["awal_sesudah"], set(a["final_sesudah"]),
           "DFA Kasus A sesudah minimisasi: 6 state, 30 entri transisi.\n"
           "State gabungan ditulis q0+q6 dan q2+q5.",
           OUT / "dfa_kasus_a_sesudah.png", buang_trap="q7", radius_node=0.56)


# ------------------------------------------------------------------ Kasus B
b = DATA["kasus_b"]


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


peta_b, ket_b = peta_label_kasus_b(b["transisi_sesudah"])
b_transisi = {peta_b[str(k)]: {sim: peta_b[str(v)] for sim, v in isi.items()}
              for k, isi in b["transisi_sesudah"].items()}
gambar_dfa(b_transisi, peta_b[str(b["awal_sesudah"])],
           {peta_b[str(f)] for f in b["final_sesudah"]},
           "DFA Kasus B sesudah minimisasi: 8 state, "
           + str(b["sesudah"]["transition_entries"]) + " entri transisi.\n"
           "G1 sampai G" + str(len(ket_b)) + " adalah state gabungan pada Tabel 8.",
           OUT / "dfa_kasus_b_sesudah.png", radius_node=0.62)


# ------------------------------------------------------------- alur scanner
fig, ax = plt.subplots(figsize=(7.6, 2.1), dpi=200)
ax.set_axis_off()
ax.set_xlim(0, 10)
ax.set_ylim(0, 3)
kotak = [
    ("6 aturan\ntoken regex", 0.9),
    ("NFA gabungan\n{} state".format(DATA["nfa_state"]), 3.3),
    ("DFA gabungan\n{} state".format(b["sebelum"]["states"]), 5.7),
    ("DFA minimal\n{} state".format(b["sesudah"]["states"]), 8.1),
]
for teks, x in kotak:
    ax.add_patch(plt.Rectangle((x - 0.95, 1.05), 1.9, 0.95, facecolor="#e8eeff",
                               edgecolor=TINTA, linewidth=1.4))
    ax.text(x, 1.52, teks, ha="center", va="center", fontsize=8.6, color=TINTA,
            linespacing=1.3)
for x0 in (1.85, 4.25, 6.65):
    ax.annotate("", xy=(x0 + 0.55, 1.52), xytext=(x0, 1.52),
                arrowprops=dict(arrowstyle="-|>", color=AKSEN, lw=1.7))
ax.text(3.05, 0.62, "konstruksi Thompson", fontsize=7.6, color=AKSEN, ha="center")
ax.text(5.45, 0.62, "subset construction", fontsize=7.6, color=AKSEN, ha="center")
ax.text(7.85, 0.62, "minimisasi Hopcroft", fontsize=7.6, color=AKSEN, ha="center")
ax.set_title("Alur pembentukan DFA scanner pada Kasus B", fontsize=10.5, color=TINTA)
fig.savefig(OUT / "alur_scanner.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("tulis alur_scanner.png")


# --------------------------------------------------------- grafik kasus B
label = ["Jumlah state", "Entri tabel\ntransisi", "Sel matriks state\nx simbol"]
sebelum = [b["sebelum"]["states"], b["sebelum"]["transition_entries"], b["sebelum"]["matriks_penuh"]]
sesudah = [b["sesudah"]["states"], b["sesudah"]["transition_entries"], b["sesudah"]["matriks_penuh"]]

x = list(range(len(label)))
lebar = 0.34
fig, ax = plt.subplots(figsize=(6.6, 3.2), dpi=200)
b1 = ax.bar([i - lebar / 2 for i in x], sebelum, lebar, label="Sebelum minimisasi",
            color="#93c5fd", edgecolor=TINTA, linewidth=0.8)
b2 = ax.bar([i + lebar / 2 for i in x], sesudah, lebar, label="Sesudah minimisasi",
            color="#1d4ed8", edgecolor=TINTA, linewidth=0.8)
for batang in (b1, b2):
    for r in batang:
        ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 1.3,
                f"{int(r.get_height())}", ha="center", fontsize=9, color=TINTA)
ax.set_xticks(x)
ax.set_xticklabels(label, fontsize=8.8)
ax.set_ylabel("jumlah", fontsize=9)
ax.set_ylim(0, max(sebelum) * 1.2)
ax.legend(fontsize=8.4, frameon=False)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Ukuran DFA Kasus B sebelum dan sesudah minimisasi", fontsize=10.5, color=TINTA)
fig.savefig(OUT / "grafik_kasus_b.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("tulis grafik_kasus_b.png")
