## So sanh hieu nang

| Chuong trinh | So lenh | Single-cycle (chu ky) | Lab 8 (+3 nop/lenh) | Lab 9 forwarding (+nop sau lw, nhay) | Lab 10 +stall (+nop sau nhay) | Lab 11 day du (khong nop) | Lab 16 du doan nhanh | Khong cache, bo nho 5 chu ky/lan (uoc tinh) | Lab 17 + cache (miss = 8 chu ky) | CPI Lab 17 |
|---|---|---|---|---|---|---|---|---|---|---|
| t10_loaduse.s | 22 | 22 | 94 | 40 | 36 | 36 | 36 | 154 | 92 | 4.18 |
| t11_control.s | 36 | 36 | sai | sai | sai | 68 | 66 | 304 | 146 | 4.06 |
| t13_bytes.s | 33 | 33 | 138 | 57 | 43 | 43 | 43 | 189 | 131 | 3.97 |
| t14_muldiv.s | 97 | 97 | 381 | 141 | 141 | 133 | 115 | 549 | 251 | 2.59 |
| t14b_mulhw.s | 17 | 17 | 74 | 26 | 26 | 26 | 26 | 104 | 66 | 3.88 |
| t15_io.s | 124 | 124 | 486 | 239 | 235 | 189 | 165 | 799 | 269 | 2.17 |
| t16_predict.s | 356 | 356 | 1353 | 611 | 611 | 555 | 463 | 2289 | 567 | 1.59 |
| t17_uart_rx.s | 207 | 207 | 810 | 367 | 366 | 294 | 252 | 1234 | 300 | 1.45 |
| t18_irq.s | 1045 | 1045 | 4193 | sai | sai | 1789 | 1397 | 6964 | 1509 | 1.44 |
| t18b_irq_burst.s | 47 | 47 | 197 | sai | sai | 74 | 74 | 344 | 122 | 2.60 |
| t19_cache.s | 539 | 539 | 2069 | 812 | 804 | 798 | 624 | 3094 | 824 | 1.53 |
| t1_arith.s | 32 | 32 | 134 | 41 | 41 | 41 | 41 | 179 | 113 | 3.53 |
| t2_sum.s | 35 | 35 | 137 | 65 | 64 | 62 | 48 | 214 | 80 | 2.29 |
| t3_fib.s | 90 | 90 | 355 | 124 | 123 | 121 | 103 | 489 | 143 | 1.59 |
| t4_recursion.s | 637 | 637 | 2587 | 1281 | 1248 | 1048 | 914 | 4544 | 1018 | 1.60 |
| t5_sort.s | 283 | 283 | 1089 | 548 | 518 | 418 | 364 | 1794 | 452 | 1.60 |
| t6_mul.s | 446 | 446 | 1703 | 859 | 859 | 653 | 509 | 2519 | 581 | 1.30 |
| t7_hazard.s | 36 | 36 | sai | 67 | 66 | 60 | 60 | 274 | 148 | 4.11 |
| t9_forward.s | 20 | 20 | 86 | 29 | 29 | 29 | 29 | 119 | 77 | 3.85 |
| test6c_branch.s | 28 | 28 | 109 | 61 | 61 | 55 | 55 | 249 | 119 | 4.25 |
| test6d_jalr.s | 15 | 15 | sai | 52 | 52 | 42 | 42 | 184 | 82 | 5.47 |

Ghi chu: CPU single-cycle co 1 chu ky/lenh nhung chu ky rat dai (bang tong tre ca 5 tang); pipeline co chu ky ngan hon ~5 lan (bang tre tang cham nhat). CPI Lab 17 (co cache) gom ca chu ky dong bang khi cache miss va vai chu ky nap/xa pipeline ban dau.

## Cache

| Chuong trinh | I-cache miss / doc lenh | Ti le miss I | D-cache miss / doc du lieu | Ti le miss D | Chu ky dong bang | Khong cache -> co cache (chu ky) | Tang toc |
|---|---|---|---|---|---|---|---|
| t10_loaduse.s | 6 / 50 | 12.0% | 1 / 18 | 5.6% | 56 | 154 -> 92 | 1.67x |
| t11_control.s | 9 / 83 | 10.8% | 1 / 2 | 50.0% | 80 | 304 -> 146 | 2.08x |
| t13_bytes.s | 9 / 68 | 13.2% | 2 / 49 | 4.1% | 88 | 189 -> 131 | 1.44x |
| t14_muldiv.s | 16 / 139 | 11.5% | 1 / 2 | 50.0% | 136 | 549 -> 251 | 2.19x |
| t14b_mulhw.s | 5 / 31 | 16.1% | 0 / 0 | - | 40 | 104 -> 66 | 1.58x |
| t15_io.s | 11 / 192 | 5.7% | 2 / 15 | 13.3% | 104 | 799 -> 269 | 2.97x |
| t16_predict.s | 13 / 476 | 2.7% | 0 / 0 | - | 104 | 2289 -> 567 | 4.04x |
| t17_uart_rx.s | 6 / 258 | 2.3% | 0 / 0 | - | 48 | 1234 -> 300 | 4.11x |
| t18_irq.s | 12 / 1425 | 0.8% | 2 / 131 | 1.5% | 112 | 6964 -> 1509 | 4.61x |
| t18b_irq_burst.s | 6 / 80 | 7.5% | 0 / 0 | - | 48 | 344 -> 122 | 2.82x |
| t19_cache.s | 12 / 740 | 1.6% | 14 / 94 | 14.9% | 200 | 3094 -> 824 | 3.75x |
| t1_arith.s | 9 / 50 | 18.0% | 0 / 0 | - | 72 | 179 -> 113 | 1.58x |
| t2_sum.s | 3 / 59 | 5.1% | 1 / 2 | 50.0% | 32 | 214 -> 80 | 2.67x |
| t3_fib.s | 4 / 115 | 3.5% | 1 / 2 | 50.0% | 40 | 489 -> 143 | 3.42x |
| t4_recursion.s | 7 / 969 | 0.7% | 6 / 105 | 5.7% | 104 | 4544 -> 1018 | 4.46x |
| t5_sort.s | 9 / 389 | 2.3% | 2 / 60 | 3.3% | 88 | 1794 -> 452 | 3.97x |
| t6_mul.s | 9 / 518 | 1.7% | 0 / 0 | - | 72 | 2519 -> 581 | 4.34x |
| t7_hazard.s | 10 / 78 | 12.8% | 1 / 7 | 14.3% | 88 | 274 -> 148 | 1.85x |
| t9_forward.s | 6 / 35 | 17.1% | 0 / 0 | - | 48 | 119 -> 77 | 1.55x |
| test6c_branch.s | 8 / 63 | 12.7% | 0 / 0 | - | 64 | 249 -> 119 | 2.09x |
| test6d_jalr.s | 5 / 47 | 10.6% | 0 / 0 | - | 40 | 184 -> 82 | 2.24x |

Cache (Lab 17): I-cache va D-cache rieng, moi cache direct-mapped 16 dong x 4 word (256 byte), D-cache write-through, khong cap phat dong khi ghi miss. Moi lan miss CPU dong bang 8 chu ky de nap 1 dong (gia lap bo nho chinh cham: cho 4 chu ky + 4 word). Lab 16 gia dinh bo nho chinh tra ket qua trong 1 chu ky (khong thuc te). Cot 'Khong cache' la uoc tinh tren mo hinh: cung bo nho chinh do (4 chu ky cho + 1 chu ky truyen = 5 chu ky moi lan doc lenh/doc du lieu), khong co mach tuong ung.
