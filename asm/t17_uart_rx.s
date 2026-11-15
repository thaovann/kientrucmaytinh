# T17: UART RX (ban phim) - doc tung ky tu, doi chu thuong -> chu hoa, in lai ra TTY (echo) toi khi gap '\n'
# RX = "hello, RISC-V!\n"
        li   s0, 0x80000000       # dia chi co so vung I/O
        li   s1, 0                # dem so ky tu
        li   s2, 10               # '\n'
loop:   lw   t0, 16(s0)           # doc UART RX: bit 8 = co ky tu, bit 6..0 = ky tu
        andi t1, t0, 0x100
        beqz t1, loop             # chua co ky tu: cho
        sw   x0, 16(s0)           # bo ky tu da doc khoi hang doi
        andi t0, t0, 0x7F
        addi t2, t0, -97          # t2 = c - 'a'
        sltiu t2, t2, 26          # t2 = 1 neu 'a' <= c <= 'z'
        beqz t2, tx
        addi t0, t0, -32          # chu thuong -> chu hoa
tx:     lw   t3, 8(s0)            # cho UART TX san sang
        beqz t3, tx
        sw   t0, 8(s0)
        addi s1, s1, 1
        bne  t0, s2, loop
        sw   s1, 0(s0)            # LED = so ky tu da nhan
        lw   a0, 16(s0)           # hang doi da rong: doc = 0
done:   j    done
# EXPECT TTY = "HELLO, RISC-V!\n"
# EXPECT s1 = 15
# EXPECT LED = 15
# EXPECT a0 = 0
