# T18b: Ngat lien tiep - 4 ky tu co san truoc khi bat ngat; sau moi iret ngat xay ra ngay o lenh tiep theo
# RX = "abcd"
        j    main                 # 0x000
isr:    lui  t3, 0x80000          # 0x004: ISR chi dung t3, t4 (chuong trinh chinh khong dung)
        lw   t4, 16(t3)           # doc ky tu
        sw   x0, 16(t3)           # bo khoi hang doi
        addi t4, t4, -32          # chu thuong -> chu hoa (bit 8 "co ky tu" van con)
        sw   t4, 8(t3)            # TTY lay 7 bit thap
        addi s1, s1, 1            # dem so lan ngat
        iret
main:   li   s0, 0x80000000
        li   s1, 0
        li   a0, 0
        li   t0, 1
        sw   t0, 20(s0)           # IE = 1: ngat xay ra ngay (hang doi da co ky tu)
        addi a0, a0, 1            # moi lenh duoi day chi chay sau khi het ngat
        addi a0, a0, 2
        lw   a1, 20(s0)           # doc lai IE = 1
        sw   x0, 20(s0)           # IE = 0
        lw   a2, 20(s0)           # IE = 0
        li   tp, 0
        li   t4, 0
done:   j    done
# EXPECT TTY = "ABCD"
# EXPECT s1 = 4
# EXPECT a0 = 3
# EXPECT a1 = 1
# EXPECT a2 = 0
