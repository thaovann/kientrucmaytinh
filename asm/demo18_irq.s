# Demo ngat: vong lap chinh dem lien tuc tren LED 7 doan; moi phim go tren Keyboard gay ngat,
# trinh phuc vu ngat doi chu thuong -> chu hoa, in ra TTY va hien so phim da go tren LED.
# Chay lien tuc (khong co vong dung). Go phim: cong cu Poke, nhap vao khoi Keyboard roi go.
# RX = "hello, irq!\n"
        j    main                 # 0x000
isr:    addi sp, sp, -12          # 0x004: vector ngat
        sw   t0, 0(sp)
        sw   t1, 4(sp)
        sw   t2, 8(sp)
        lui  t0, 0x80000          # vung I/O
        lw   t1, 16(t0)           # doc ky tu
        sw   x0, 16(t0)           # bo khoi hang doi
        andi t1, t1, 0x7F
        addi t2, t1, -97          # t2 = c - 'a'
        sltiu t2, t2, 26
        beqz t2, tx
        addi t1, t1, -32          # chu thuong -> chu hoa
tx:     sw   t1, 8(t0)            # in ra TTY
        addi s3, s3, 1            # s3 danh rieng cho ISR: so phim da go
        sw   s3, 0(t0)            # LED = so phim
        lw   t2, 8(sp)
        lw   t1, 4(sp)
        lw   t0, 0(sp)
        addi sp, sp, 12
        iret
main:   li   sp, 0x700
        li   s0, 0x80000000
        li   s3, 0
        li   t0, 1
        sw   t0, 20(s0)           # IE = 1
        li   a0, 0
loop:   addi a0, a0, 1
        sw   a0, 4(s0)            # HEX = bo dem
        j    loop
