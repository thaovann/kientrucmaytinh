#!/usr/bin/env python3
"""Bang so sanh hieu nang cac phien ban CPU (tu mo hinh da kiem chung khop phan cung tung chu ky).
    python tools/compare.py "asm/t[1-6]_*.s" --md report/so_sanh.md
Cot: so lenh that (khong tinh nop) / so chu ky cua tung phien ban (chuong trinh chay DUNG o phien ban do)."""
import argparse, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rvsim, pipesim

CONFIGS = [  # (ten, lab, pad, pad_load, pad_ctl[, nocache])
    ("Lab 8 (+3 nop/lenh)", 8, 3, 0, 0),
    ("Lab 9 forwarding (+nop sau lw, nhay)", 9, 0, 1, 2),
    ("Lab 10 +stall (+nop sau nhay)", 10, 0, 0, 2),
    ("Lab 11 day du (khong nop)", 11, 0, 0, 0),
    ("Lab 16 du doan nhanh", 16, 0, 0, 0),
    ("Khong cache, bo nho 5 chu ky/lan (uoc tinh)", 17, 0, 0, 0, True),
    ("Lab 17 + cache (miss = 8 chu ky)", 17, 0, 0, 0),
]
def cycles(path, lab, pad, pl, pc, nocache=False):
    w = rvsim.load_words(path, pad, pl, pc); sw, rx = rvsim.parse_sw(path), rvsim.parse_rx(path)
    ref, n, halted = rvsim.run_to_halt(w, sw=sw, rx=rx)
    if not halted: return None, False
    p, recs = pipesim.run(w, lab, 20 * n + 200, ref.pc, sw=sw, rx=rx, nocache=nocache)
    if lab >= 17 and not nocache: CACHE_STATS[path] = (p.ic.misses, p.ic.misses + p.ic.accesses, p.dc.misses, p.dc.misses + p.dc.accesses, p.cstalls)
    return len(recs), (p.x == ref.x and p.mem == ref.mem)
CACHE_STATS = {}

ap = argparse.ArgumentParser(); ap.add_argument("progs", nargs="+"); ap.add_argument("--md")
a = ap.parse_args()
progs = list(dict.fromkeys(p for pat in a.progs for p in (sorted(glob.glob(pat)) or [pat])))
head = ["Chuong trinh", "So lenh", "Single-cycle (chu ky)"] + [c[0] for c in CONFIGS] + ["CPI Lab 17"]
rows = []
for p in progs:
    ref, n, halted = rvsim.run_to_halt(rvsim.load_words(p), sw=rvsim.parse_sw(p), rx=rvsim.parse_rx(p))
    if not halted: continue
    cells = [os.path.basename(p), str(n), str(n)]
    last = None
    for name, lab, pad, pl, pc, *nc in CONFIGS:
        c, ok = cycles(p, lab, pad, pl, pc, *nc)
        cells.append(f"{c}" if ok else "sai")
        last = c if ok else None
    cells.append(f"{last / n:.2f}" if last else "-")
    rows.append(cells)
out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(r) + " |" for r in rows]
note = ("\n\nGhi chu: CPU single-cycle co 1 chu ky/lenh nhung chu ky rat dai (bang tong tre ca 5 tang); "
        "pipeline co chu ky ngan hon ~5 lan (bang tre tang cham nhat). CPI Lab 17 (co cache) gom ca chu ky dong bang khi cache miss va vai chu ky nap/xa pipeline ban dau.\n")
pct = lambda m, n: f"{100 * m / n:.1f}%" if n else "-"
ch = ["Chuong trinh", "I-cache miss / doc lenh", "Ti le miss I", "D-cache miss / doc du lieu", "Ti le miss D",
      "Chu ky dong bang", "Khong cache -> co cache (chu ky)", "Tang toc"]
crow = []
for p in progs:
    if p not in CACHE_STATS: continue
    im, ia, dm, dac, fz = CACHE_STATS[p]
    r = next(r for r in rows if r[0] == os.path.basename(p))
    sp = f"{int(r[-3]) / int(r[-2]):.2f}x" if r[-3].isdigit() and r[-2].isdigit() else "-"
    crow.append([os.path.basename(p), f"{im} / {ia}", pct(im, ia), f"{dm} / {dac}", pct(dm, dac), str(fz), f"{r[-3]} -> {r[-2]}", sp])
cout = ["| " + " | ".join(ch) + " |", "|" + "---|" * len(ch)] + ["| " + " | ".join(r) + " |" for r in crow]
cnote = ("\n\nCache (Lab 17): I-cache va D-cache rieng, moi cache direct-mapped 16 dong x 4 word (256 byte), "
         "D-cache write-through, khong cap phat dong khi ghi miss. Moi lan miss CPU dong bang 8 chu ky de nap 1 dong "
         "(gia lap bo nho chinh cham: cho 4 chu ky + 4 word). Lab 16 gia dinh bo nho chinh tra ket qua trong 1 chu ky "
         "(khong thuc te). Cot 'Khong cache' la uoc tinh tren mo hinh: cung bo nho chinh do (4 chu ky cho + 1 chu ky "
         "truyen = 5 chu ky moi lan doc lenh/doc du lieu), khong co mach tuong ung.\n")
print("\n".join(out)); print(); print("\n".join(cout))
if a.md:
    if os.path.dirname(a.md): os.makedirs(os.path.dirname(a.md), exist_ok=True)
    open(a.md, "w", encoding="utf-8", newline="\n").write("## So sanh hieu nang\n\n" + "\n".join(out) + note
                                                         + "\n## Cache\n\n" + "\n".join(cout) + cnote)
    print("Da ghi", a.md)
