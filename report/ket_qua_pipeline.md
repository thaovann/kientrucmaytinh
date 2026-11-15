## Ket qua kiem thu CPU pipeline 5 tang

| Chuong trinh | Muc dich | So lenh | Chu ky | CPI | Stall | Flush | Dong test dat | Ket qua |
|---|---|---|---|---|---|---|---|---|
| `t10_loaduse.s` | T10: Load-use - lw roi dung ngay ket qua (chay dung tu Lab 10, khong can nop; khong co lenh nhay) | 22 | 92 | 4.18 | 5 | 1 | 183/183 | **PASS** |
| `t11_control.s` | T11: Hazard dieu khien - nhay ngay sau lenh tinh dieu kien, sau load, jal/jalr lien tiep (chay dung tu Lab 11) | 36 | 146 | 4.06 | 1 | 11 | 291/291 | **PASS** |
| `t13_bytes.s` | T13: LB LH LBU LHU SB SH - doc/ghi byte va half-word, mo rong dau va khong dau | 33 | 131 | 3.97 | 1 | 1 | 261/261 | **PASS** |
| `t14_muldiv.s` | T14: M-extension - MUL MULH MULHSU MULHU DIV DIVU REM REMU, ca bien va phu thuoc lien tiep | 97 | 251 | 2.59 | 1 | 5 | 501/501 | **PASS** |
| `t14b_mulhw.s` | T14b: cung bai toan nhu t6_mul.s nhung dung lenh MUL phan cung (de so sanh so chu ky) | 17 | 66 | 3.88 | 0 | 1 | 131/131 | **PASS** |
| `t15_io.s` | T15: I/O anh xa bo nho - LED, HEX (7 doan), UART TX (TTY), cong tac SW | 124 | 269 | 2.17 | 24 | 5 | 537/537 | **PASS** |
| `t16_predict.s` | T16: Du doan nhanh - vong lap long nhau, mau xen ke, hai nhanh trung chi so BTB, goi ham bang jal | 356 | 567 | 1.59 | 0 | 50 | 1133/1133 | **PASS** |
| `t17_uart_rx.s` | T17: UART RX (ban phim) - doc tung ky tu, doi chu thuong -> chu hoa, in lai ra TTY (echo) toi khi gap '\n' | 207 | 300 | 1.45 | 30 | 4 | 599/599 | **PASS** |
| `t18_irq.s` | T18: Ngat UART RX - chuong trinh chinh tinh toan, trinh phuc vu ngat (ISR) nhan ky tu va in ra TTY | 1045 | 1509 | 1.44 | 107 | 119 | 3017/3017 | **PASS** |
| `t18b_irq_burst.s` | T18b: Ngat lien tiep - 4 ky tu co san truoc khi bat ngat; sau moi iret ngat xay ra ngay o lenh tiep theo | 47 | 122 | 2.60 | 0 | 10 | 243/243 | **PASS** |
| `t19_cache.s` | T19: Cache - doc mang 2 lan (lan 2 toan hit), xung dot chi so, ghi write-through khi hit/miss, sb/lh qua cache | 539 | 824 | 1.53 | 64 | 7 | 1647/1647 | **PASS** |
| `t1_arith.s` | T1: So hoc / logic va cac ca bien (tran so, dich 0/31, so am, x0) | 32 | 113 | 3.53 | 0 | 1 | 225/225 | **PASS** |
| `t2_sum.s` | T2: Vong lap tinh tong 1..10, luu vao bo nho | 35 | 80 | 2.29 | 0 | 3 | 159/159 | **PASS** |
| `t3_fib.s` | T3: 12 so Fibonacci dau tien, luu mang tai 0x100 | 90 | 143 | 1.59 | 0 | 3 | 285/285 | **PASS** |
| `t4_recursion.s` | T4: De quy fib(8) dung stack (JAL/JALR/SW/LW voi sp) | 637 | 1018 | 1.60 | 66 | 102 | 2035/2035 | **PASS** |
| `t5_sort.s` | T5: Sap xep noi bot (bubble sort) 8 so co dau tai 0x200 | 283 | 452 | 1.60 | 28 | 23 | 903/903 | **PASS** |
| `t6_mul.s` | T6: Nhan bang phan mem (dich va cong), goi ham nhieu lan | 446 | 581 | 1.30 | 0 | 28 | 1161/1161 | **PASS** |
| `t7_hazard.s` | T7: Chuoi lenh phu thuoc sat nhau (de kiem tra pipeline o Lab 9-11) | 36 | 148 | 4.11 | 5 | 6 | 295/295 | **PASS** |
| `t9_forward.s` | T9: Forwarding - phu thuoc sat nhau, khong load-use, khong nhay (chay dung tu Lab 9, khong can nop) | 20 | 77 | 3.85 | 0 | 1 | 153/153 | **PASS** |
| `test6a_alu.s` | Lab 6A: lenh ALU R-type, I-type, LUI (chua co nhay, chua co bo nho) | - | 156 | - | 0 | 0 | 311/311 | **PASS** |
| `test6b_mem.s` | Lab 6B: LW / SW | - | 108 | - | 0 | 0 | 215/215 | **PASS** |
| `test6c_branch.s` | Lab 6C: BEQ BNE BLT BGE BLTU BGEU, JAL. x10 dem so nhanh dung = 8, x31 phai = 0 | 28 | 119 | 4.25 | 0 | 10 | 237/237 | **PASS** |
| `test6d_jalr.s` | Lab 6D: JALR, goi ham / tra ve. Ket qua: a0 = 28, t3 = 42, t4 = 1, x31 = 0 | 15 | 82 | 5.47 | 0 | 10 | 163/163 | **PASS** |

*So lenh*: so lenh thuc thi (mo hinh tap lenh) toi vong lap dung. *Chu ky*: so chu ky da so sanh (gom ca chu ky nap/xa pipeline). *Dong test dat*: so dong test vector khop (2 dong/chu ky).
