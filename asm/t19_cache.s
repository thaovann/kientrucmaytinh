# T19: Cache - doc mang 2 lan (lan 2 toan hit), xung dot chi so, ghi write-through khi hit/miss, sb/lh qua cache
        li   s0, 0x100            # mang a[0..31] tai 0x100 (8 dong cache)
        li   t1, 0
        li   t2, 32
        mv   t0, s0
init:   slli t3, t1, 1
        add  t3, t3, t1           # a[i] = 3*i  (ghi miss: khong cap phat dong)
        sw   t3, 0(t0)
        addi t0, t0, 4
        addi t1, t1, 1
        bne  t1, t2, init
        li   s1, 0                # lan 1: moi dong miss 1 lan (8 miss)
        mv   t0, s0
        li   t1, 0
pass1:  lw   t3, 0(t0)
        add  s1, s1, t3
        addi t0, t0, 4
        addi t1, t1, 1
        bne  t1, t2, pass1
        li   s2, 0                # lan 2: toan hit
        mv   t0, s0
        li   t1, 0
pass2:  lw   t3, 0(t0)
        add  s2, s2, t3
        addi t0, t0, 4
        addi t1, t1, 1
        bne  t1, t2, pass2
        li   t0, 0x200            # 0x100 va 0x200 cung chi so dong 0 -> xung dot
        li   t4, 0x1234
        sw   t4, 0(t0)            # 0x200 chua co trong cache: ghi thang RAM
        lw   a0, 0(t0)            # miss: nap dong 0x200 (thay dong 0x100)
        lw   a1, 0(s0)            # miss: nap lai dong 0x100
        lw   a2, 0(t0)            # miss
        li   t4, 999
        sw   t4, 4(t0)            # ghi hit (dong 0x200 dang o cache): cap nhat ca cache va RAM
        lw   a3, 4(t0)            # hit -> 999
        lw   a4, 0(s0)            # miss -> dong 0x100
        lw   a5, 4(t0)            # miss -> doc tu RAM: 999 (write-through)
        li   t4, 0xAB
        sb   t4, 9(s0)            # ghi 1 byte vao a[2] = 6 (dang o cache)
        lw   a6, 8(s0)            # 0x0000AB06
        lh   a7, 8(s0)            # 0xFFFFAB06
done:   j    done
# EXPECT s1 = 1488
# EXPECT s2 = 1488
# EXPECT a0 = 0x1234
# EXPECT a1 = 0
# EXPECT a2 = 0x1234
# EXPECT a3 = 999
# EXPECT a4 = 0
# EXPECT a5 = 999
# EXPECT a6 = 0xAB06
# EXPECT a7 = 0xFFFFAB06
# EXPECT MEM[0x10C] = 9
