#!/usr/bin/env python3
# Sinh tests/fpu.txt cho circuit "FPU" (to hop), theo mo hinh tools/fpu.py
#   python tools/gen_fpu_tests.py      (chay tu thu muc goc project)
import random, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fpu import fpu, f2b, OP_FP, M
random.seed(20)
H = lambda v: f"0x{v & M:08X}"
enc = lambda f5, f3=7, r2=0: (f5 << 27) | (r2 << 20) | (f3 << 12) | OP_FP

SPECIAL = [0x00000000, 0x80000000, 0x3F800000, 0xBF800000, 0x7F800000, 0xFF800000, 0x7F7FFFFF, 0x00000001,
           0x00800000, 0x007FFFFF, 0x40490FDB, 0x3EAAAAAB, 0x4B000000, 0xCF000000]
def rnd():
    r = random.random()
    if r < 0.15: return random.choice(SPECIAL)
    if r < 0.6: return f2b(random.choice([-1, 1]) * random.uniform(0, 1000))
    if r < 0.8: return f2b(random.choice([-1, 1]) * random.randrange(1 << 20) / 4)   # so co phan .25/.5/.75
    return random.getrandbits(32) & 0x7F7FFFFF | (random.getrandbits(1) << 31)      # bat ky, khong NaN

OPS = [(0, (7,), 0), (1, (7,), 0), (2, (7,), 0), (3, (7,), 0), (11, (7,), 0), (4, (0, 1, 2), 0),
       (5, (0, 1), 0), (20, (0, 1, 2), 0), (24, (0, 1, 2, 3, 7), 0), (24, (1,), 1), (26, (7,), 0), (26, (7,), 1)]
rows = []
for f5, f3s, r2 in OPS:
    for _ in range(60):
        f3 = random.choice(f3s)
        a, b = rnd(), rnd()
        if f5 == 24:                                    # fcvt.w[u].s: chi kiem trong pham vi so nguyen 32 bit
            a = f2b(random.choice([-1, 1]) * random.choice([random.uniform(0, 3e5), random.randrange(64) / 2]))
            if r2: a &= 0x7FFFFFFF
        if f5 == 26: a = random.getrandbits(32) if random.random() < 0.7 else random.choice([0, 1, M, 0x80000000, 0x7FFFFFFF, 16777217])
        rows.append((a, b, enc(f5, f3, r2)))
# NaN (chi cac phep ma khoi Logisim cho ket qua dung chuan): +,-,*,/, so sanh
for f5, f3 in [(0, 7), (1, 7), (2, 7), (3, 7), (20, 0), (20, 1), (20, 2)]:
    for a, b in [(0x7FC00000, 0x3F800000), (0x3F800000, 0x7FC00000), (0x7F800000, 0xFF800000), (0, 0)]:
        rows.append((a, b, enc(f5, f3)))
rows.append((0x3F800000, 0x3F800000, 0x00B50533))             # add a0,a0,a1 (khong phai FP): IsFP = 0
with open("tests/fpu.txt", "w", newline="\n") as f:
    f.write("# Test vector circuit FPU (to hop): Zfinx single precision, xem tools/fpu.py\n")
    f.write("A[32] B[32] Instr[32] Result[32] IsFP\n")
    for a, b, ins in rows:
        res = fpu(ins, a, b) if (ins & 0x7F) == OP_FP else "<DC>"
        f.write(f"{H(a)} {H(b)} {H(ins)} {res if isinstance(res, str) else H(res)} {int((ins & 0x7F) == OP_FP)}\n")
print(f"fpu: {len(rows)} dong")
