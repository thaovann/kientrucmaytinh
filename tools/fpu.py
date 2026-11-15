#!/usr/bin/env python3
"""Mo hinh khoi FPU (giong circuit "FPU" trong modules/riscv_modules.circ): so thuc single precision
theo phan mo rong RISC-V Zfinx (so thuc nam trong thanh ghi x, opcode OP-FP = 0x53, fmt = S).

funct5 = Instr[31:27]  lenh                       ket qua
 00000  fadd.s  rd, rs1, rs2                      rs1 + rs2
 00001  fsub.s                                    rs1 - rs2
 00010  fmul.s                                    rs1 * rs2
 00011  fdiv.s                                    rs1 / rs2
 01011  fsqrt.s rd, rs1                           sqrt(rs1)
 00100  fsgnj.s / fsgnjn.s / fsgnjx.s (f3 0/1/2)  {dau, rs1[30:0]}
 00101  fmin.s / fmax.s (f3 0/1)
 10100  fle.s / flt.s / feq.s (f3 0/1/2)          0 hoac 1
 11000  fcvt.w.s / fcvt.wu.s rd, rs1[, rm]         so nguyen (lam tron theo rm)
 11010  fcvt.s.w / fcvt.s.wu rd, rs1 (rs2 = 0/1)   so thuc
Phep toan so hoc luon lam tron ve gan nhat, chan (RNE); truong rm chi dung cho fcvt.w[u].s:
 rm = 0 RNE, 1 RTZ, 2 RDN, 3 RUP; rm >= 4 (ke ca DYN = 7) -> RNE.
Gioi han (do khoi Logisim): fmin/fmax tra NaN neu co NaN; fcvt.w[u].s khi tran/NaN khong bao hoa
nhu chuan (lay 32 bit thap cua so nguyen 64 bit); khong co co ngoai le (fflags) va fclass.
"""
import math, struct
M = 0xFFFFFFFF
QNAN = 0x7FC00000
OP_FP = 0x53

def b2f(b): return struct.unpack("<f", struct.pack("<I", b & M))[0]
def f2b(x):
    """double -> float32 (RNE); NaN -> NaN chuan 0x7FC00000."""
    if math.isnan(x): return QNAN
    try: return struct.unpack("<I", struct.pack("<f", x))[0]
    except OverflowError: return 0xFF800000 if x < 0 else 0x7F800000

def _div(a, b):
    if b == 0.0:
        if a == 0.0 or math.isnan(a): return math.nan
        neg = (math.copysign(1, a) < 0) != (math.copysign(1, b) < 0)
        return -math.inf if neg else math.inf
    return a / b
def _minmax(a, b, want_max):
    if math.isnan(a) or math.isnan(b): return math.nan
    if a == b == 0.0:                                     # -0 < +0 (giong Math.min/max cua Java)
        neg_a, neg_b = math.copysign(1, a) < 0, math.copysign(1, b) < 0
        if want_max: return a if not neg_a else b
        return a if neg_a else b
    return max(a, b) if want_max else min(a, b)
def _to_int(x, mode):
    """Giong khoi FPToInt: lam tron (rint/truncate/floor/ceil) roi d2l (bao hoa 64 bit), lay 32 bit thap."""
    if math.isnan(x): v = 0
    elif math.isinf(x): v = (1 << 63) - 1 if x > 0 else -(1 << 63)
    else:
        v = [round, math.trunc, math.floor, math.ceil][mode](x)   # round() cua Python = lam tron chan
        v = max(-(1 << 63), min((1 << 63) - 1, int(v)))
    return v & M

def is_fp(ins): return (ins & 0x7F) == OP_FP

def fpu(ins, a_bits, b_bits):
    """Ket qua 32 bit cua lenh FP 'ins' voi toan hang rs1 = a_bits, rs2 = b_bits."""
    f5, f3, r2 = (ins >> 27) & 31, (ins >> 12) & 7, (ins >> 20) & 1
    a, b = b2f(a_bits), b2f(b_bits)
    if f5 == 0b00000: return f2b(a + b)
    if f5 == 0b00001: return f2b(a - b)
    if f5 == 0b00010: return f2b(a * b)
    if f5 == 0b00011: return f2b(_div(a, b))
    if f5 == 0b01011: return f2b(math.nan if a < 0 else math.sqrt(a))
    if f5 == 0b00100:
        a31, b31 = (a_bits >> 31) & 1, (b_bits >> 31) & 1
        s = b31 ^ (f3 & 1) ^ ((f3 >> 1) & a31)
        return (a_bits & 0x7FFFFFFF) | (s << 31)
    if f5 == 0b00101: return f2b(_minmax(a, b, f3 & 1))
    if f5 == 0b10100:
        eq, lt = int(a == b), int(a < b)                  # NaN -> ca hai = 0
        return [eq | lt, lt, eq, 0][f3 & 3]               # f3: 0 fle, 1 flt, 2 feq
    if f5 == 0b11000: return _to_int(a, 0 if f3 & 4 else f3 & 3)
    if f5 == 0b11010:
        v = a_bits & M
        if not r2 and v & 0x80000000: v -= 1 << 32
        return f2b(float(v))
    return 0
