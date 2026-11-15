#!/usr/bin/env python3
"""Mo hinh khoi Cache (giong circuit "Cache" trong modules/riscv_modules.circ), chinh xac tung chu ky.

Cache anh xa truc tiep (direct-mapped), 16 dong x 4 word = 256 byte:
    Addr[3:2] = word trong dong, Addr[7:4] = chi so dong, Addr[31:8] = tag
    TAG RAM  (16 x 32): {valid = bit 31, tag = Addr >> 8}       (sau reset = 0 -> khong hop le)
    DATA RAM (64 x 32): chi so = {dong, word}
Miss (Req = 1 va tag khong khop) -> Stall = 1. Bo dem CNT (3 bit) dem 0..7 o moi canh len khi Stall:
    CNT = 0..3: ghi MemData (word tai FillAddr) vao DATA      (nap 4 word cua dong)
    CNT = 7   : ghi tag + valid vao TAG -> chu ky sau la hit  (CNT 4..6: gia lap do tre bo nho chinh)
=> moi lan miss ton dung FILL = 8 chu ky. Khong Stall: CNT = 0.
Ghi (WE = 1): write-through, khong cap phat dong khi miss; neu hit thi cap nhat word trong DATA.
FillAddr = {Addr[31:4], CNT[1:0], 00}: dia chi gui toi bo nho chinh khi dang nap.
RData = DATA[Stall ? FillAddr[7:2] : Addr[7:2]]   (doc bat dong bo)
"""
M = 0xFFFFFFFF
LINES, WORDS, FILL = 16, 4, 8

def tagw(a): return ((a >> 8) | 0x80000000) & M

class Cache:
    def __init__(self):
        self.tag = [0] * LINES
        self.data = [0] * (LINES * WORDS)
        self.cnt = 0
        self.misses = self.accesses = 0
    def hit(self, a): return self.tag[(a >> 4) & 15] == tagw(a)
    def stall(self, a, req): return int(bool(req) and not self.hit(a))
    def fill_addr(self, a): return (a & 0xFFFFFFF0) | ((self.cnt & 3) << 2)
    def rdata(self, a, req=1):
        return self.data[((self.fill_addr(a) if self.stall(a, req) else a) >> 2) & 63]
    def edge(self, a, req, memdata=0, we=0, wdata=0):
        """Canh len cua clock: memdata = word cua bo nho chinh tai fill_addr(a)."""
        if self.stall(a, req):
            if self.cnt == 0: self.misses += 1
            if self.cnt < 4: self.data[(self.fill_addr(a) >> 2) & 63] = memdata & M
            if self.cnt == 7: self.tag[(a >> 4) & 15] = tagw(a)
            self.cnt = (self.cnt + 1) & 7
        else:
            if req: self.accesses += 1
            if we and self.hit(a): self.data[(a >> 2) & 63] = wdata & M
            self.cnt = 0

class NoCache(Cache):
    """CHI DUNG DE UOC TINH (khong co mach): khong cache, moi lan doc bo nho chinh ton LAT + 1 chu ky
       (cung do tre voi luc nap dong cua Cache: 4 chu ky cho + truyen du lieu)."""
    LAT = 4
    def __init__(self, mem_fn):
        super().__init__(); self.mem_fn = mem_fn
    def stall(self, a, req): return int(bool(req) and self.cnt < self.LAT)
    def rdata(self, a, req=1): return self.mem_fn(a)
    def edge(self, a, req, memdata=0, we=0, wdata=0):
        if self.stall(a, req):
            if self.cnt == 0: self.misses += 1
            self.cnt += 1
        else:
            self.cnt = 0
