# T20: So thuc single precision (Zfinx: so thuc nam trong thanh ghi x) - phep toan, lam tron, chuyen doi, so sanh, hazard
        li   s0, 1.5f
        li   s1, 2.25f
        fadd.s a0, s0, s1         # 3.75
        fmul.s a1, a0, a0         # dung ngay ket qua (forwarding): 14.0625
        li   t0, 2.0f
        fsqrt.s a2, t0            # sqrt(2) = 0x3FB504F3
        li   t0, 10.0f
        li   t1, 4.0f
        fdiv.s a3, t0, t1         # 2.5
        li   t0, 3.0f
        li   t1, -0.5f
        fmul.s a4, t0, t1         # -1.5
        fsub.s a5, a4, a0         # -1.5 - 3.75 = -5.25
        fneg.s a6, a5             # 5.25
        fabs.s a7, a4             # 1.5
        # chuyen doi va lam tron
        li   t0, -2.7f
        fcvt.w.s s2, t0, rtz      # -2
        li   t0, 2.5f
        fcvt.w.s s3, t0, rne      # 2 (lam tron ve so chan)
        li   t0, -2.5f
        fcvt.w.s s4, t0, rdn      # -3
        li   t0, 2.1f
        fcvt.w.s s5, t0, rup      # 3
        li   t0, -7
        fcvt.s.w s6, t0           # -7.0
        li   t0, -1
        fcvt.s.wu s7, t0          # 4294967296.0
        # so sanh, min/max
        li   t0, 1.0f
        li   t1, 2.0f
        flt.s s8, t0, t1          # 1
        fle.s s9, t1, t0          # 0
        li   t2, -0.0f
        feq.s s10, t2, x0         # -0 == +0 -> 1
        fmax.s s11, t0, t1        # 2.0
        fmin.s t3, a4, t0         # -1.5
        # so thuc trong bo nho + load-use: tong 1/k^2, k = 1..20
        li   t4, 0x200
        li   t5, 1.0f
        sw   t5, 0(t4)            # MEM[0x200] = 1.0
        li   t6, 0                # tong (bit 0 = +0.0)
        li   t1, 1                # k
        li   t2, 21
sum:    fcvt.s.w t0, t1           # (float) k
        fmul.s t0, t0, t0         # k*k
        lw   t5, 0(t4)            # 1.0 tu bo nho
        fdiv.s t0, t5, t0         # load-use: 1 / (k*k)
        fadd.s t6, t6, t0
        addi t1, t1, 1
        bne  t1, t2, sum
        sw   t6, 4(t4)            # MEM[0x204] = tong
        li   t0, 1000.0f
        fmul.s t0, t6, t0
        fcvt.w.s t5, t0, rtz      # (int)(1000 * tong) = 1596
done:   j    done
# EXPECT a0 = 0x40700000
# EXPECT a1 = 0x41610000
# EXPECT a2 = 0x3FB504F3
# EXPECT a3 = 0x40200000
# EXPECT a4 = 0xBFC00000
# EXPECT a5 = 0xC0A80000
# EXPECT a6 = 0x40A80000
# EXPECT a7 = 0x3FC00000
# EXPECT s2 = -2
# EXPECT s3 = 2
# EXPECT s4 = -3
# EXPECT s5 = 3
# EXPECT s6 = 0xC0E00000
# EXPECT s7 = 0x4F800000
# EXPECT s8 = 1
# EXPECT s9 = 0
# EXPECT s10 = 1
# EXPECT s11 = 0x40000000
# EXPECT t3 = 0xBFC00000
# EXPECT t5 = 1596
# EXPECT MEM[0x204] = 0x3FCC4F14
