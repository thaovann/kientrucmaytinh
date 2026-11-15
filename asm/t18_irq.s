# T18: Ngat UART RX - chuong trinh chinh tinh toan, trinh phuc vu ngat (ISR) nhan ky tu va in ra TTY
# RX = "IRQ ok\n"
# RX_GAP = 61
# Ky tu thu i toi o chu ky 61*(i+1): ngat roi vao nhieu cho khac nhau (load-use, nhanh, jal/ret).
        j    main                 # 0x000
# ---------------- 0x004: vector ngat. Vao day thi tp = PC bi ngat + 4, ngat bi chan toi khi iret
isr:    addi sp, sp, -12
        sw   t0, 0(sp)            # luu thanh ghi ISR dung
        sw   t1, 4(sp)
        sw   t2, 8(sp)
        lui  t0, 0x80000          # t0 = 0x80000000 (vung I/O)
        lw   t1, 16(t0)           # doc UART RX (bit 8 = co ky tu)
        sw   x0, 16(t0)           # bo ky tu khoi hang doi -> IRQ ve 0
        andi t1, t1, 0x7F
        sw   t1, 8(t0)            # in ra TTY (UART TX luon san sang)
        lw   t2, 0x100(x0)        # dem so ky tu da nhan
        addi t2, t2, 1
        sw   t2, 0x100(x0)
        lw   t2, 8(sp)
        lw   t1, 4(sp)
        lw   t0, 0(sp)
        addi sp, sp, 12
        iret                      # jalr x0, -4(tp): quay lai lenh bi ngat, bat lai ngat
# ---------------- chuong trinh chinh
main:   li   sp, 0x400
        li   s0, 0x80000000
        li   t0, 1
        sw   t0, 20(s0)           # IE = 1: cho phep ngat UART RX
        li   a0, 0                # a0 = 1 + 2 + ... + 100
        li   a1, 1
        li   a2, 101
sum:    sw   a1, 0x104(x0)
        lw   t5, 0x104(x0)
        add  a0, a0, t5           # load-use: stall
        jal  sq                   # goi ham: a3 += a1*a1
        addi a1, a1, 1
        bne  a1, a2, sum
        li   t1, 7
wait:   lw   t0, 0x100(x0)        # cho ISR nhan du 7 ky tu
        bne  t0, t1, wait
        sw   x0, 20(s0)           # IE = 0
        sw   a0, 0(s0)            # LED = tong
        li   tp, 0                # xoa tp va vung stack cua ISR: trang thai cuoi khong phu thuoc
        sw   x0, -4(sp)           #   thoi diem ngat (de so sanh mo hinh single-cycle va pipeline)
        sw   x0, -8(sp)
        sw   x0, -12(sp)
done:   j    done
sq:     mul  t6, a1, a1
        add  a3, a3, t6
        ret
# EXPECT TTY = "IRQ ok\n"
# EXPECT MEM[0x100] = 7
# EXPECT a0 = 5050
# EXPECT a3 = 338350
# EXPECT sp = 0x400
