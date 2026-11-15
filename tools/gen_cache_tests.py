#!/usr/bin/env python3
# Sinh tests/cache.txt cho circuit "Cache" (tuan tu), theo mo hinh tools/cache.py
#   python tools/gen_cache_tests.py      (chay tu thu muc goc project)
import random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cache import Cache, M
random.seed(17)
H = lambda v: f"0x{v & M:08X}"
mem = lambda a: (a * 2654435761 + 12345) & M          # noi dung "bo nho chinh"

rows = []
class T:
    def __init__(s, sid): s.c = Cache(); s.set = sid; s.seq = 0
    def cycle(s, a, req, we=0, wd=0):
        md = mem(s.c.fill_addr(a))                      # MemData giu nguyen ca 2 dong cua chu ky
        for clk in (0, 1):
            if clk: s.c.edge(a, req, md, we, wd)
            s.seq += 1
            rows.append((s.set, s.seq, clk, a, req, md, we, wd, s.c.rdata(a, req), s.c.stall(a, req), s.c.fill_addr(a)))
    def access(s, a, req=1, we=0, wd=0):
        """Giu yeu cau toi khi het Stall (miss: 8 chu ky nap) roi them 1 chu ky hit."""
        n = 0
        while s.c.stall(a, req):
            s.cycle(a, req, we, wd); n += 1
            assert n <= 8
        s.cycle(a, req, we, wd)

t = T(1)                                    # Set 1: doc - miss, hit trong dong, xung dot chi so
for a in (0x0, 0x4, 0x8, 0xC, 0x10, 0x3C, 0x0, 0x100, 0x104, 0x0, 0x100, 0x7FFFFFF4, 0x80000000, 0xFFC):
    t.access(a)
t = T(2)                                    # Set 2: ghi write-through (hit: cap nhat, miss: khong cap phat), Req = 0
t.access(0x20)                              # nap dong 2
t.access(0x24, req=0, we=1, wd=0xDEADBEEF)  # ghi hit
t.access(0x24); t.access(0x20)
t.access(0x2C, req=0, we=1, wd=0x12345678); t.access(0x2C)
t.access(0x40, req=0, we=1, wd=0x55555555)  # ghi miss: khong stall, khong nap
t.access(0x40)                              # doc: miss -> nap tu bo nho chinh
t.cycle(0x80, 0); t.cycle(0x84, 0, 1, 7)    # Req = 0: khong stall
t = T(3)                                    # Set 3: ngau nhien tren 2 KB (nhieu xung dot)
for _ in range(150):
    a = random.randrange(512) * 4
    if random.random() < 0.3: t.access(a, req=0, we=1, wd=random.getrandbits(32))
    else: t.access(a)

with open("tests/cache.txt", "w", newline="\n") as f:
    f.write("# Test vector circuit Cache (tuan tu): direct-mapped 16 dong x 4 word, miss = 8 chu ky nap\n")
    f.write("<set> <seq> clk Addr[32] Req MemData[32] WE WData[32] RData[32] Stall FillAddr[32]\n")
    for st, sq, c, a, rq, md, we, wd, rd, sl, fa in rows:
        f.write(f"{st} {sq} {c} {H(a)} {rq} {H(md)} {we} {H(wd)} {H(rd)} {sl} {H(fa)}\n")
print(f"cache: {len(rows)} dong")
