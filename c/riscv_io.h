/* Thu vien I/O toi gian cho CPU RISC-V tren Logisim (Lab 15).
   Thiet bi anh xa bo nho: dung con tro volatile de trinh bien dich khong bo qua lenh doc/ghi. */
#ifndef RISCV_IO_H
#define RISCV_IO_H

#define IO_LED   (*(volatile unsigned *)0x80000000u)   /* ghi: 8 LED            doc: gia tri da ghi */
#define IO_HEX   (*(volatile unsigned *)0x80000004u)   /* ghi: 8 LED 7 doan     doc: gia tri da ghi */
#define IO_UART  (*(volatile unsigned *)0x80000008u)   /* ghi: gui 1 ky tu ra TTY; doc: 1 = san sang */
#define IO_SW    (*(volatile unsigned *)0x8000000Cu)   /* doc: 8 cong tac DIP */
#define IO_RX    (*(volatile unsigned *)0x80000010u)   /* UART RX (ban phim). doc: bit 8 = co ky tu, bit 6..0 = ky tu;
                                                           ghi (gia tri bat ky): bo ky tu dau hang doi */

#define IO_IE    (*(volatile unsigned *)0x80000014u)   /* bit 0 = cho phep ngat UART RX (doc/ghi).
                                                           Trinh phuc vu ngat phai viet bang assembly tai 0x004, xem README */

static inline int kbhit_(void) { return (IO_RX >> 8) & 1u; }   /* 1 neu co ky tu dang cho */
static inline char getc_(void) {                               /* cho va lay 1 ky tu tu ban phim */
    unsigned v;
    while (!((v = IO_RX) & 0x100u)) { }
    IO_RX = 0;
    return (char)(v & 0x7Fu);
}

static inline void putc_(char c) {
    while (IO_UART == 0) { }        /* cho UART san sang */
    IO_UART = (unsigned char)c;
}
static inline void puts_(const char *s) { while (*s) putc_(*s++); }

/* In so nguyen khong dau o he 10 (dung DIVU/REMU cua M-extension) */
static inline void putu(unsigned v) {
    char buf[11]; int i = 0;
    do { buf[i++] = (char)('0' + v % 10u); v /= 10u; } while (v);
    while (i) putc_(buf[--i]);
}
static inline void puti(int v) { if (v < 0) { putc_('-'); putu(0u - (unsigned)v); } else putu((unsigned)v); }

/* Doi so sang BCD de LED 7 doan hien thi so he 10 (toi da 8 chu so) */
static inline unsigned to_bcd(unsigned v) {
    unsigned r = 0; int sh = 0;
    do { r |= (v % 10u) << sh; v /= 10u; sh += 4; } while (v && sh < 32);
    return r;
}
#endif
