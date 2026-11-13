"""
Eksperimen minimisasi DFA memakai DFA.minify() dari automata-lib pada dua kasus.

Kasus A : DFA kecil 8 state yang sengaja memuat jalur ganda, dipakai untuk
          menelusuri proses penggabungan state langkah demi langkah.
Kasus B : penggabungan enam aturan token sebuah scanner (INT, REAL, REAL_DOT,
          EXP_INT, EXP_REAL, EXP_REAL_DOT) memakai product construction
          (minify=False), lalu diminimalkan. Kasus ini sumber angka efisiensi.

Seluruh angka pada berkas hasil di folder hasil/ berasal dari eksekusi skrip ini.
"""

import json
import time
from itertools import product
from pathlib import Path

from automata.fa.dfa import DFA
from automata.fa.nfa import NFA

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "hasil"
OUT.mkdir(parents=True, exist_ok=True)
SIGMA = {"d", ".", "e", "+", "-"}
SIGMA_SORTED = sorted(SIGMA)


# ---------------------------------------------------------------- alat bantu
def label_state(state):
    """Nama state hasil minify, misalnya 'q2' atau 'q0+q6'."""
    if isinstance(state, frozenset):
        return "+".join(sorted(str(x) for x in state))
    return str(state)


def ukuran(dfa):
    entri = sum(len(v) for v in dfa.transitions.values())
    return {
        "states": len(dfa.states),
        "final_states": len(dfa.final_states),
        "transition_entries": entri,
        "matriks_penuh": len(dfa.states) * len(dfa.input_symbols),
        # tabel transisi padat 2 byte per sel (indeks state 16 bit)
        "bytes_tabel_padat": len(dfa.states) * len(dfa.input_symbols) * 2,
    }


def moore_partitions(dfa, batas=12):
    """Algoritma Moore sederhana sebagai pembanding hasil Hopcroft library."""
    states = sorted(dfa.states)
    kelas = {s: (0 if s in dfa.final_states else 1) for s in states}
    riwayat = [[sorted(s for s in states if s in dfa.final_states),
                sorted(s for s in states if s not in dfa.final_states)]]
    riwayat = [[g for g in riwayat[0] if g]]

    for _ in range(batas):
        tanda = {}
        baru = {}
        for s in states:
            sig = tuple(kelas.get(dfa.transitions[s].get(a), -1) for a in SIGMA_SORTED)
            kunci = (sig, s in dfa.final_states)
            if kunci not in tanda:
                tanda[kunci] = len(tanda)
            baru[s] = tanda[kunci]
        kelas = baru
        kelompok = {}
        for s in states:
            kelompok.setdefault(kelas[s], []).append(s)
        partisi = sorted((sorted(v) for v in kelompok.values()), key=lambda g: g[0])
        riwayat.append(partisi)
        if len(riwayat) >= 2 and riwayat[-1] == riwayat[-2]:
            break
    return riwayat


def uji(dfa, sampel):
    hasil = {}
    for s in sampel:
        try:
            hasil[s] = dfa.accepts_input(s)
        except Exception as exc:
            hasil[s] = f"error {type(exc).__name__}"
    return hasil


SAMPEL = [
    "d", "dd", "+d", "-dd", "d.d", "dd.dd", ".d", ".dd", "d.", ".", "+", "-",
    "e", "de", "dd+e", "dde+d", "dde-dd", "d.e", "+.d", "dd..d", "--d", "dde",
    ".d.", "+dd.dd", ".ded", "d.ded", "dde+", ".dd.e1",
]


# ---------------------------------------------------------------- Kasus A
# DFA 8 state dengan jalur ganda, seperti hasil konversi NFA ke DFA yang
# belum disederhanakan. q5 adalah salinan q2, q6 meniru perilaku q0.
dfa_a = DFA(
    states={"q0", "q1", "q2", "q3", "q4", "q5", "q6", "q7"},
    input_symbols=SIGMA,
    transitions={
        "q0": {"d": "q2", "+": "q1", "-": "q1", ".": "q7", "e": "q7"},
        "q1": {"d": "q2", "+": "q7", "-": "q7", ".": "q7", "e": "q7"},
        "q2": {"d": "q2", ".": "q3", "+": "q7", "-": "q7", "e": "q6"},
        "q5": {"d": "q2", ".": "q3", "+": "q7", "-": "q7", "e": "q6"},
        "q3": {"d": "q4", "+": "q7", "-": "q7", ".": "q7", "e": "q7"},
        "q4": {"d": "q4", "e": "q6", "+": "q7", "-": "q7", ".": "q7"},
        "q6": {"d": "q5", "+": "q1", "-": "q1", ".": "q7", "e": "q7"},
        "q7": {"d": "q7", "+": "q7", "-": "q7", ".": "q7", "e": "q7"},
    },
    initial_state="q0",
    final_states={"q2", "q4", "q5"},
)


# ---------------------------------------------------------------- Kasus B
ATURAN = {
    "INT": r"[+-]?d+",
    "REAL": r"[+-]?d+\.d+",
    "REAL_DOT": r"[+-]?\.d+",
    "EXP_INT": r"[+-]?d+(e[+-]?d+)",
    "EXP_REAL": r"[+-]?d+\.d+(e[+-]?d+)",
    "EXP_REAL_DOT": r"[+-]?\.d+(e[+-]?d+)",
}
REGEX_RUJUKAN = r"[+-]?(d+(\.d+)?(e[+-]?d+)?|\.d+(e[+-]?d+)?)"


def dari_regex(rx):
    return DFA.from_nfa(NFA.from_regex(rx, input_symbols=SIGMA))


per_aturan = {}
gabungan = None
for nama, rx in ATURAN.items():
    d = dari_regex(rx)
    per_aturan[nama] = {"regex": rx, **ukuran(d)}
    gabungan = d if gabungan is None else gabungan.union(d, minify=False)

nfa_b = NFA.from_regex(REGEX_RUJUKAN, input_symbols=SIGMA)
dfa_b = DFA.from_nfa(nfa_b)


def jalankan_kasus(dfa, nama, sampel, dengan_moore=True):
    mini_bernama = dfa.minify(retain_names=True)
    mini = dfa.minify()

    t0 = time.perf_counter()
    for _ in range(50):
        dfa.minify()
    waktu = (time.perf_counter() - t0) * 1000 / 50

    grup = []
    for state in mini_bernama.states:
        anggota = sorted(str(x) for x in state) if isinstance(state, frozenset) else [str(state)]
        grup.append(sorted(anggota))

    partisi = moore_partitions(dfa) if dengan_moore else None

    return {
        "nama": nama,
        "sebelum": ukuran(dfa),
        "sesudah": ukuran(mini),
        "waktu_minify_ms": round(waktu, 3),
        "ekuivalen_library": dfa == mini,
        "uji_sama": uji(dfa, sampel) == uji(mini, sampel),
        "uji": uji(mini, sampel),
        "uji_sebelum": uji(dfa, sampel),
        "uji_sesudah": uji(mini, sampel),
        "grup_gabungan": [g for g in grup if len(g) > 1],
        "jumlah_grup": len(grup),
        "partisi_moore": partisi,
        "partisi_moore_akhir": partisi[-1] if partisi else None,
        "jumlah_iterasi_moore": len(partisi) if partisi else None,
        "transisi_sesudah": {label_state(k): {sym: label_state(v) for sym, v in t.items()}
                             for k, t in mini_bernama.transitions.items()},
        "final_sesudah": sorted(label_state(f) for f in mini_bernama.final_states),
        "awal_sesudah": label_state(mini_bernama.initial_state),
        "transisi_sebelum": {str(k): dict(v) for k, v in dfa.transitions.items()},
        "final_sebelum": sorted(str(f) for f in dfa.final_states),
        "awal_sebelum": str(dfa.initial_state),
    }


kasus_a = jalankan_kasus(dfa_a, "Kasus A: DFA kecil dengan jalur ganda", SAMPEL)
kasus_b = jalankan_kasus(gabungan, "Kasus B: gabungan enam aturan token", SAMPEL)

# ------------------------------------------------- pemeriksaan menyeluruh
# Seluruh string atas alfabet sampai panjang 6 diuji ke tiga DFA sekaligus.
dfa_rujukan = dari_regex(REGEX_RUJUKAN)
mini_b = gabungan.minify()
total = 0
beda_minify = []
beda_rujukan = []
diterima = 0
for panjang in range(0, 7):
    for tup in product(SIGMA_SORTED, repeat=panjang):
        s = "".join(tup)
        total += 1
        a = gabungan.accepts_input(s)
        b = mini_b.accepts_input(s)
        c = dfa_rujukan.accepts_input(s)
        diterima += 1 if b else 0
        if a != b:
            beda_minify.append(s)
        if b != c:
            beda_rujukan.append(s)

hasil = {
    "versi_library": __import__("importlib.metadata", fromlist=["version"]).version("automata-lib"),
    "alphabet": SIGMA_SORTED,
    "kasus_a": kasus_a,
    "kasus_b": kasus_b,
    "per_aturan": per_aturan,
    "regex_rujukan": REGEX_RUJUKAN,
    "nfa_state": len(nfa_b.states),
    "nfa_transisi": sum(len(v) for v in nfa_b.transitions.values()),
    "dfa_rujukan": ukuran(dfa_rujukan),
    "pemeriksaan": {
        "jumlah_string": total,
        "panjang_maks": 6,
        "beda_minify": beda_minify[:10],
        "jumlah_beda_minify": len(beda_minify),
        "beda_rujukan": beda_rujukan[:10],
        "jumlah_beda_rujukan": len(beda_rujukan),
        "minify_ekuivalen_rujukan": mini_b == dfa_rujukan,
        "jumlah_diterima": diterima,
    },
}

(OUT / "hasil_eksperimen.json").write_text(
    json.dumps(hasil, indent=2, ensure_ascii=False), encoding="utf-8"
)

for k in ("kasus_a", "kasus_b"):
    h = hasil[k]
    s0, s1 = h["sebelum"], h["sesudah"]
    print(f"== {k} ==")
    print(f"   state          : {s0['states']} -> {s1['states']}")
    print(f"   final state    : {s0['final_states']} -> {s1['final_states']}")
    print(f"   entri transisi : {s0['transition_entries']} -> {s1['transition_entries']}")
    print(f"   ekuivalen      : {h['ekuivalen_library']} | uji 28 string sama: {h['uji_sama']}")
    print(f"   grup gabungan  : {h['grup_gabungan']}")
    print(f"   partisi Moore  : {h['partisi_moore_akhir']} ({h['jumlah_iterasi_moore']} iterasi)")
    print(f"   waktu minify   : {h['waktu_minify_ms']} ms")
p = hasil["pemeriksaan"]
print("== pemeriksaan menyeluruh ==")
print(f"   string diuji   : {p['jumlah_string']} (panjang 0 sampai {p['panjang_maks']})")
print(f"   string diterima: {p['jumlah_diterima']}")
print(f"   beda sebelum/sesudah minify : {p['jumlah_beda_minify']}")
print(f"   beda terhadap regex rujukan : {p['jumlah_beda_rujukan']}")
print(f"   alur Kasus B : {hasil['nfa_state']} state NFA -> {hasil['dfa_rujukan']['states']} state DFA minimal")
