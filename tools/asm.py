#!/usr/bin/env python3
# Dung: python asm.py prog.s -o prog.hex
import sys, re

REGS = {f"x{i}": i for i in range(32)}
ABI = "zero ra sp gp tp t0 t1 t2 s0 s1 a0 a1 a2 a3 a4 a5 a6 a7 s2 s3 s4 s5 s6 s7 s8 s9 s10 s11 t3 t4 t5 t6".split()
REGS.update({n: i for i, n in enumerate(ABI)}); REGS["fp"] = 8

R  = {'add':(0,0),'sub':(0x20,0),'sll':(0,1),'slt':(0,2),'sltu':(0,3),
      'xor':(0,4),'srl':(0,5),'sra':(0x20,5),'or':(0,6),'and':(0,7),
      # M-extension (Lab 14): funct7 = 0000001
      'mul':(1,0),'mulh':(1,1),'mulhsu':(1,2),'mulhu':(1,3),'div':(1,4),'divu':(1,5),'rem':(1,6),'remu':(1,7)}
I  = {'addi':0,'slti':2,'sltiu':3,'xori':4,'ori':6,'andi':7}
SH = {'slli':(0,1),'srli':(0,5),'srai':(0x20,5)}
LD = {'lb':0,'lh':1,'lw':2,'lbu':4,'lhu':5}
ST = {'sb':0,'sh':1,'sw':2}
BR = {'beq':0,'bne':1,'blt':4,'bge':5,'bltu':6,'bgeu':7}
# So thuc Zfinx (opcode 0x53, toan hang la thanh ghi x): ten -> (funct5, funct3 co dinh hoac None = rm, rs2 co dinh hoac None)
FP = {'fadd.s':(0,None,None), 'fsub.s':(1,None,None), 'fmul.s':(2,None,None), 'fdiv.s':(3,None,None),
      'fsqrt.s':(11,None,0), 'fsgnj.s':(4,0,None), 'fsgnjn.s':(4,1,None), 'fsgnjx.s':(4,2,None),
      'fmin.s':(5,0,None), 'fmax.s':(5,1,None), 'fle.s':(20,0,None), 'flt.s':(20,1,None), 'feq.s':(20,2,None),
      'fcvt.w.s':(24,None,0), 'fcvt.wu.s':(24,None,1), 'fcvt.s.w':(26,None,0), 'fcvt.s.wu':(26,None,1)}
RM = {'rne':0, 'rtz':1, 'rdn':2, 'rup':3, 'rmm':4, 'dyn':7}

def float_bits(s):
    """'3.25f', '-1e-3f', 'inf' ... -> bit cua so thuc 32 bit; khong phai so thuc -> None"""
    t = s.lower()
    if t.endswith('f') and not t.lstrip('+-').startswith('0x') and any(c in t for c in '.e'):
        t = t[:-1]
    elif t.lstrip('+-') not in ('inf', 'nan'):
        return None
    import struct, math
    v = float(t)
    if math.isnan(v): return 0x7FC00000
    try: return struct.unpack('<I', struct.pack('<f', v))[0]
    except OverflowError: return 0xFF800000 if v < 0 else 0x7F800000

def enc_r(f7,rs2,rs1,f3,rd,op): return (f7<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|op
def enc_i(imm,rs1,f3,rd,op):    return ((imm&0xfff)<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|op
def enc_s(imm,rs2,rs1,f3,op):
    imm&=0xfff; return ((imm>>5)<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|((imm&0x1f)<<7)|op
def enc_b(imm,rs2,rs1,f3,op):
    imm&=0x1fff
    return (((imm>>12)&1)<<31)|(((imm>>5)&0x3f)<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|(((imm>>1)&0xf)<<8)|(((imm>>11)&1)<<7)|op
def enc_u(imm,rd,op): return ((imm&0xfffff)<<12)|(rd<<7)|op
def enc_j(imm,rd,op):
    imm&=0x1fffff
    return (((imm>>20)&1)<<31)|(((imm>>1)&0x3ff)<<21)|(((imm>>11)&1)<<20)|(((imm>>12)&0xff)<<12)|(rd<<7)|op

def num(s): return int(s, 0)

def expand(m, o):
    if m=='nop':  return [('addi',['x0','x0','0'])]
    if m=='mv':   return [('addi',[o[0],o[1],'0'])]
    if m=='j':    return [('jal',['x0',o[0]])]
    if m=='jr':   return [('jalr',['x0',o[0],'0'])]
    if m=='ret':  return [('jalr',['x0','ra','0'])]
    if m=='iret': return [('jalr',['x0','tp','-4'])]      # thoat trinh phuc vu ngat (tp = PC bi ngat + 4)
    if m=='beqz': return [('beq',[o[0],'x0',o[1]])]
    if m=='bnez': return [('bne',[o[0],'x0',o[1]])]
    if m=='jal' and len(o)==1: return [('jal',['ra',o[0]])]
    if m=='fmv.s':  return [('fsgnj.s', [o[0], o[1], o[1]])]
    if m=='fneg.s': return [('fsgnjn.s',[o[0], o[1], o[1]])]
    if m=='fabs.s': return [('fsgnjx.s',[o[0], o[1], o[1]])]
    if m=='fgt.s':  return [('flt.s',   [o[0], o[2], o[1]])]
    if m=='fge.s':  return [('fle.s',   [o[0], o[2], o[1]])]
    if m=='li':
        fb = float_bits(o[1])
        v = fb if fb is not None else num(o[1])
        if fb is not None and fb & 0x80000000: v = fb - (1 << 32)
        if -2048 <= v < 2048: return [('addi',[o[0],'x0',str(v)])]
        v &= 0xffffffff; lo = v & 0xfff
        if lo >= 0x800: lo -= 0x1000
        hi = ((v - lo) >> 12) & 0xfffff
        return [('lui',[o[0],str(hi)]), ('addi',[o[0],o[0],str(lo)])]
    return [(m,o)]

def encode(m, o, pc, labels):
    reg = lambda x: REGS[x]
    tgt = lambda x: labels[x]-pc if x in labels else num(x)
    def memop(s):
        g = re.match(r'\s*(-?\w*)\((\w+)\)', s).groups()
        return (num(g[0]) if g[0] else 0, reg(g[1]))
    if m in R:  f7,f3=R[m];  return enc_r(f7,reg(o[2]),reg(o[1]),f3,reg(o[0]),0x33)
    if m in I:  return enc_i(num(o[2]),reg(o[1]),I[m],reg(o[0]),0x13)
    if m in SH: f7,f3=SH[m]; return enc_i((f7<<5)|(num(o[2])&31),reg(o[1]),f3,reg(o[0]),0x13)
    if m in LD: imm,rs1=memop(o[1]); return enc_i(imm,rs1,LD[m],reg(o[0]),0x03)
    if m in ST: imm,rs1=memop(o[1]); return enc_s(imm,reg(o[0]),rs1,ST[m],0x23)
    if m in BR: return enc_b(tgt(o[2]),reg(o[1]),reg(o[0]),BR[m],0x63)
    if m=='jal':  return enc_j(tgt(o[1]),reg(o[0]),0x6f)
    if m=='jalr':
        if len(o)==3: return enc_i(num(o[2]),reg(o[1]),0,reg(o[0]),0x67)
        imm,rs1=memop(o[1]); return enc_i(imm,rs1,0,reg(o[0]),0x67)
    if m=='lui':  return enc_u(num(o[1]),reg(o[0]),0x37)
    if m in FP:
        f5, f3, r2 = FP[m]
        rs2 = r2 if r2 is not None else reg(o[2])
        nops = 2 if r2 is not None else 3                 # so toan hang thanh ghi
        if f3 is None: f3 = RM[o[nops].lower()] if len(o) > nops else 7   # rm tuy chon, mac dinh dyn
        return enc_r(f5 << 2, rs2, reg(o[1]), f3, reg(o[0]), 0x53)
    raise ValueError(f"Lenh khong ho tro: {m}")

def assemble(src, pad=0, pad_load=0, pad_ctl=0):
    """Tra ve (words, listing). listing: danh sach (pc, word, text).
    pad      : chen N nop sau MOI lenh (pipeline chua xu ly hazard, Lab 8)
    pad_load : chen N nop sau moi lenh load (Lab 9: chua co stall load-use)
    pad_ctl  : chen N nop sau moi lenh nhay branch/jal/jalr (Lab 9-10: chua co flush)"""
    import os
    if not os.path.isfile(src):
        d = os.path.dirname(src) or '.'
        print(f"LOI: khong tim thay file '{src}'")
        print(f"Thu muc hien tai: {os.getcwd()}")
        if os.path.isdir(d):
            print(f"Cac file trong '{d}':", ', '.join(os.listdir(d)) or '(trong)')
        else:
            print(f"Thu muc '{d}' khong ton tai")
        sys.exit(1)
    labels, prog, pc = {}, [], 0
    for lineno, raw in enumerate(open(src, encoding='utf-8-sig'), 1):
        line = re.split(r'#|//', raw)[0].strip()
        while ':' in line:
            lab, line = line.split(':',1); labels[lab.strip()] = pc; line = line.strip()
        if not line: continue
        parts = line.replace(',',' ').split()
        for m,o in expand(parts[0].lower(), parts[1:]):
            prog.append((pc,m,o,lineno)); pc += 4
            n = pad + (pad_load if m in LD else 0) + (pad_ctl if (m in BR or m in ('jal', 'jalr')) else 0)
            for _ in range(n):
                prog.append((pc,'addi',['x0','x0','0'],lineno)); pc += 4
    words = []
    for p,m,o,ln in prog:
        try:
            words.append(encode(m,o,p,labels))
        except Exception as e:
            print(f"LOI dong {ln}: {m} {', '.join(o)}  ->  {e!r}"); sys.exit(1)
    listing = [(p, w, f"{m} {', '.join(o)}") for (p,m,o,_), w in zip(prog, words)]
    return words, listing

def write_hex(words, out):
    with open(out,'w', newline='\n') as f:
        f.write("v2.0 raw\n")
        for i in range(0,len(words),8):
            f.write(" ".join(f"{w:08x}" for w in words[i:i+8])+"\n")

def main(src, out, pad=0, pad_load=0, pad_ctl=0):
    words, listing = assemble(src, pad, pad_load, pad_ctl)
    write_hex(words, out)
    for p, w, t in listing:
        print(f"{p:04x}: {w:08x}   {t}")

if __name__ == "__main__":
    a = sys.argv
    if len(a) < 2:
        print("Dung: python tools/asm.py <file.s> [-o <file.hex>] [--pad N] [--pad-load N] [--pad-ctl N]"); sys.exit(1)
    opt = lambda k: int(a[a.index(k)+1]) if k in a else 0
    main(a[1], a[a.index('-o')+1] if '-o' in a else a[1].rsplit('.',1)[0]+'.hex',
         opt('--pad'), opt('--pad-load'), opt('--pad-ctl'))
