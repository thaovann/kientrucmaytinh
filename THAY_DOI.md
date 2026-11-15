# Các thay đổi so với bản ban đầu

Tài liệu này liệt kê những gì đã thay đổi khi thêm bốn chức năng mở rộng vào máy tính RISC-V 32-bit, so với bản gốc ở [shukuchicoding/simple_computer_architecture](https://github.com/shukuchicoding/simple_computer_architecture). Bản gốc chỉ có một commit, `ccc2d1f init commit`; mọi thay đổi dưới đây nằm trong các commit sau commit đó. Có thể xem toàn bộ khác biệt bằng `git diff --stat ccc2d1f`: 36 file thay đổi, thêm khoảng 7.000 dòng, xóa khoảng 500 dòng (phần lớn là file mạch và test vector).

Thứ tự các chức năng theo thứ tự đã làm:

1. [Nhập từ bàn phím (UART RX)](#1-nhập-từ-bàn-phím-uart-rx) – cả hai CPU
2. [Ngắt (interrupt)](#2-ngắt-interrupt) – cả hai CPU
3. [Cache (I-cache và D-cache)](#3-cache-i-cache-và-d-cache) – CPU pipeline
4. [Số thực (floating point, Zfinx)](#4-số-thực-floating-point-zfinx) – cả hai CPU

**Phần không thay đổi.** Cấu trúc pipeline 5 tầng IF → ID → EX → MEM → WB, forwarding, stall khi load-use, flush khi nhảy và dự đoán nhánh giữ nguyên. Trong thư viện `modules/riscv_modules.circ`, 19 module cũ không bị sửa; riêng `Control` chỉ có thêm một dòng trong ROM (mục 4). Mọi chương trình test cũ cho kết quả giống hệt trước khi mở rộng. Chỉ số chu kỳ của bản pipeline thay đổi, do cache.

Cách mở project, nạp chương trình và chạy test được mô tả trong [README.md](README.md).

---

## 1. Nhập từ bàn phím (UART RX)

**Chức năng.** CPU đọc ký tự gõ từ khối **Keyboard** của Logisim qua địa chỉ `0x80000010`, dùng `lw`/`sw` như các thiết bị khác.

| Thao tác | Kết quả |
|---|---|
| Đọc `0x80000010` | bit 8 = `1` nếu có ký tự; bit 6..0 = mã ASCII của ký tự đầu hàng đợi; `0` nếu hàng đợi rỗng. Đọc không làm mất ký tự |
| Ghi `0x80000010` (giá trị tùy ý) | Bỏ ký tự đầu hàng đợi, chuyển sang ký tự tiếp theo |

```
wait:   lw   t0, 16(s0)        # s0 = 0x80000000
        andi t1, t0, 0x100
        beqz t1, wait          # chưa có ký tự
        sw   x0, 16(s0)        # bỏ ký tự vừa đọc
        andi t0, t0, 0x7F      # t0 = ký tự
```

Khi chạy bằng giao diện: chọn công cụ **Poke** (bàn tay), nhấp vào khối Keyboard nằm dưới khối IO trong circuit `main`, rồi gõ phím.

**Thay đổi phần cứng** (giống nhau ở `single/riscv_single.circ` và `pipeline/riscv_pipe.circ`):

| Circuit | Thay đổi |
|---|---|
| `IO` | Giải mã địa chỉ bằng `Addr[4:2]` thay cho `Addr[3:2]`: Decoder và MUX đọc tăng từ 4 lên 8 địa chỉ |
| `IO` | Thêm chân vào `RXData[7]`, `RXAvail`; chân ra `RXRead = IOWrite & (Addr[4:2] = 4)` |
| `IO` | Giá trị đọc RX = `RXAvail << 8 \| RXData` |
| `main` | Thêm khối Keyboard, nối Data/Available vào IO và `RXRead` vào chân Read Enable |
| `CPU` | **Không đổi**: lệnh ghi dùng tín hiệu `IOWrite` có sẵn |

**Phần mềm và tài liệu**
- `tools/rvsim.py`, `tools/pipesim.py`: mô hình hàng đợi bàn phím. Chuỗi gõ vào khai báo trong file `.s` bằng dòng `# RX = "abc\n"`.
- `tools/cpu_test.py`, `tools/cc.py`: thêm tùy chọn `--rx`.
- `c/riscv_io.h`: thêm `IO_RX`, `getc_()`, `kbhit_()`.
- `tools/check_all.py`: thêm tùy chọn `--java` để chỉ định lệnh Java 21.

**Kiểm thử**
- Test vector của khối IO và MemMap được sinh lại, có thêm các ca kiểm tra RX.
- Chương trình mới `asm/t17_uart_rx.s` đọc bàn phím, đổi chữ thường thành chữ hoa rồi in ra TTY.
- Chạy circuit `main` thật ở chế độ `-tty`: gõ `hello, RISC-V!` thì TTY in ra `HELLO, RISC-V!` trên cả hai CPU.

---

## 2. Ngắt (interrupt)

**Chức năng.** Khi bàn phím có ký tự và ngắt đang được bật, CPU tạm dừng chương trình chính, nhảy tới trình phục vụ ngắt (ISR) ở địa chỉ `0x004`, rồi quay lại bằng lệnh `iret`.

| Địa chỉ | Ghi | Đọc |
|---|---|---|
| `0x80000014` (IE) | bit 0 = `1`: bật ngắt UART RX | giá trị IE |

**Cơ chế.** Không cần thanh ghi CSR hay lệnh mới trong phần cứng:
- **Vào ngắt:** khi `IRQ = IE & (có ký tự)` bằng 1, tầng IF thay lệnh vừa nạp bằng `jalr tp, 4(x0)` (mã `0x00400267`). Lệnh này lưu `PC + 4` của lệnh bị ngắt vào `tp` và nhảy tới `0x004`.
- **Thoát ngắt:** lệnh giả `iret` = `jalr x0, -4(tp)` quay lại đúng lệnh bị ngắt.
- **Chặn ngắt lồng nhau:** thanh ghi 1 bit `INH` được đặt khi lệnh ngắt thực thi và được xóa khi `iret` thực thi.
- **Ngắt chính xác trên pipeline:** nếu lệnh chèn bị flush vì một lệnh nhảy phía trước đổi hướng, `IRQ` vẫn bằng 1 nên ngắt được chèn lại ở đường đúng.

**Quy ước khi viết chương trình dùng ngắt**
- Địa chỉ `0x000` chứa `j main`; ISR bắt đầu ở `0x004`.
- `tp` (x4) dành riêng cho ngắt.
- ISR lưu và khôi phục các thanh ghi nó dùng, và phải lấy ký tự ra khỏi hàng đợi.

**Thay đổi phần cứng**

| Circuit | Thay đổi |
|---|---|
| `IO` (cả hai bản) | Thêm thanh ghi `IE` ở `0x80000014`; chân ra `IRQ = IE & RXAvail` |
| `main` (cả hai bản) | Nối `IO.IRQ` sang `CPU.IRQ`; đi lại dây `IORData` để nhường chỗ cho cổng mới |
| `CPU` đơn chu kỳ | Thêm chân `IRQ`, MUX thay lệnh khi có ngắt, bộ so sánh nhận ra `iret`, thanh ghi `INH` |
| `CPU` pipeline | Như trên. Bộ so sánh xét lệnh ở tầng EX; thêm 2 bộ so sánh để không chèn ngắt khi đã có lệnh ngắt ở tầng ID hoặc EX |

**Phần mềm**
- `tools/asm.py`: thêm lệnh giả `iret`.
- `tools/rvsim.py`, `tools/pipesim.py`: mô hình thanh ghi IE, IRQ và INH, cùng việc chèn lệnh ngắt. Dòng `# RX_GAP = N` trong file `.s` cho ký tự đến cách nhau N chu kỳ.
- `tools/cpu_test.py`: tự thêm cột `IRQ` vào test vector khi CPU có chân này.

**Kiểm thử**
- `asm/t18_irq.s`: 7 ký tự đến rải rác trong lúc chương trình chính tính toán, nên ngắt rơi vào lúc stall load-use, ngay sau rẽ nhánh và quanh `jal`/`ret`.
- `asm/t18b_irq_burst.s`: ngắt xảy ra liên tiếp ngay sau mỗi `iret`.
- `asm/demo18_irq.s`: demo chạy liên tục. Vòng lặp chính đếm trên LED 7 đoạn, gõ phím thì ISR in chữ hoa ra TTY.

---

## 3. Cache (I-cache và D-cache)

**Chức năng.** Bản pipeline có hai cache: **I-cache** cho lệnh (giữa PC và IMEM) và **D-cache** cho dữ liệu (giữa tầng MEM và DMEM). Cache mô phỏng bộ nhớ chính chậm: mỗi lần miss tốn 8 chu kỳ, còn hit chỉ tốn 1 chu kỳ.

| Thông số | Giá trị |
|---|---|
| Tổ chức | Ánh xạ trực tiếp (direct-mapped), 16 dòng × 4 word = 256 byte mỗi cache |
| Chia địa chỉ | `Addr[3:2]` = word trong dòng, `Addr[7:4]` = chỉ số dòng, `Addr[31:8]` = tag |
| Khi miss | CPU đóng băng 8 chu kỳ: 4 chu kỳ chép 4 word, 3 chu kỳ giả lập độ trễ, 1 chu kỳ ghi tag và valid |
| Ghi (D-cache) | Write-through; ghi trúng thì cập nhật cache, ghi trượt thì không cấp dòng |
| Vùng I/O | Địa chỉ ≥ `0x80000000` không qua D-cache |

**Đóng băng CPU khi miss.** Tín hiệu `stall` được chốt vào latch `FRZ`. Mọi phần tử nhớ của CPU chạy bằng `clk = clk_raw & ~FRZ`, còn hai cache chạy bằng clock gốc `clk_raw`. Khi miss, toàn bộ CPU giữ nguyên trạng thái trong lúc cache nạp dòng, nên forwarding, stall, flush, dự đoán nhánh và ngắt không phải sửa.

**Thay đổi phần cứng**

| Nơi | Thay đổi |
|---|---|
| Thư viện module | **Thêm module `Cache`**: RAM `TAG` 16 × 32, RAM `DATA` 64 × 32, bộ đếm `CNT` 3 bit |
| `CPU` pipeline, tầng IF | I-cache; MUX địa chỉ IMEM = PC hoặc địa chỉ nạp dòng |
| `CPU` pipeline, tầng MEM | D-cache; MUX địa chỉ DMEM; một khối LoadExt sau D-cache cho `lb`/`lh`/`lbu`/`lhu` |
| `CPU` pipeline, clock | Latch `FRZ` và cổng chặn clock; chặn `IOWrite` trong lúc đóng băng |
| `DMEM` pipeline | Thêm 2 chân ra: `Word` (word thô của RAM) và `WWord` (word sau khi gộp byte của `sb`/`sh`) |
| CPU đơn chu kỳ | **Không có cache** |

**Phần mềm**
- `tools/cache.py`: mô hình module Cache.
- `tools/pipesim.py`: mức mới `--lab 17` (= lab 16 + cache); lab 16 vẫn giữ để so sánh.
- `tools/cpu_test.py`, `tools/check_all.py`: kiểm thử bản pipeline ở `--pipe 17`.
- `tools/compare.py`: thêm bảng tỉ lệ miss và cột ước tính "không cache, bộ nhớ 5 chu kỳ mỗi lần đọc".
- `tools/gen_cache_tests.py`: sinh `tests/cache.txt`.

**Kiểm thử và kết quả**
- Module Cache đạt 1.964/1.964 ca.
- `asm/t19_cache.s` kiểm tra hit/miss, xung đột chỉ số, ghi trúng và ghi trượt, `sb`/`lh` qua cache.
- So với cùng bộ nhớ chính chậm nhưng không có cache, CPU chạy nhanh hơn 1,4–4,6 lần (bảng chi tiết trong `report/so_sanh.md`).
- Bản pipeline trước khi có cache (lab 16) giả định bộ nhớ trả kết quả trong 1 chu kỳ, điều không thực tế, nên so với bản đó thì bản có cache tốn nhiều chu kỳ hơn.

---

## 4. Số thực (floating point, Zfinx)

**Chức năng.** Cả hai CPU tính số thực IEEE-754 single precision (32 bit) theo **Zfinx**. Đây là phần mở rộng chính thức của RISC-V trong đó số thực nằm ngay trong các thanh ghi `x0`–`x31`, không có 32 thanh ghi `f` riêng. Số thực được nạp và lưu bằng `lw`/`sw`.

Zfinx được chọn thay cho F vì lệnh FP khi đó có định dạng giống lệnh R-type, nên đi qua pipeline như lệnh `add`. Forwarding, stall và flush hoạt động sẵn; các thanh ghi pipeline không phải sửa.

| Lệnh | Ghi chú |
|---|---|
| `fadd.s fsub.s fmul.s fdiv.s fsqrt.s` | Làm tròn về gần nhất, chẵn (RNE) |
| `fmin.s fmax.s` | Nếu có NaN thì trả về NaN (khác chuẩn) |
| `feq.s flt.s fle.s` | Trả về 0 hoặc 1 |
| `fsgnj.s fsgnjn.s fsgnjx.s` | Kèm lệnh giả `fmv.s`, `fneg.s`, `fabs.s` |
| `fcvt.w.s fcvt.wu.s rd, rs1[, rm]` | `rm` = `rne`, `rtz`, `rdn` hoặc `rup`; khi tràn số thì không bão hòa (khác chuẩn) |
| `fcvt.s.w fcvt.s.wu` | Có dấu / không dấu |

```
        li     a0, 1.5f        # hằng số thực
        li     a1, 2.25f
        fadd.s a2, a0, a1      # a2 = 3.75 (0x40700000)
        fcvt.w.s a3, a2, rtz   # a3 = 3
```

**Thay đổi phần cứng**

| Nơi | Thay đổi |
|---|---|
| Thư viện module | **Thêm module `FPU`**, dựng từ các khối `FPArithmetic` của Logisim. Kết quả được chọn theo `funct5` qua một MUX 32→1 |
| Thư viện module, `Control` | Thêm một dòng trong ROM cho opcode `0x53`, cùng tín hiệu điều khiển với R-type |
| `CPU` (cả hai bản), tầng EX | MUX `aluout = IsFP ? FPU : (ALU/MulDiv)`. Bản pipeline đưa vào FPU các toán hạng đã qua forwarding |

**Phần mềm**
- `tools/asm.py`: 17 lệnh FP với toán hạng `rm` tùy chọn; lệnh giả `fmv.s`, `fneg.s`, `fabs.s`, `fgt.s`, `fge.s`; `li` nhận hằng số thực có hậu tố `f`.
- `tools/fpu.py`: mô hình module FPU, dùng chung cho `rvsim.py`, `pipesim.py` và `gen_fpu_tests.py`.
- `tools/gen_roms.py`: thêm opcode `0x53`, sinh lại `rom/control.rom` và `tests/control.txt`.

**Kiểm thử**
- Module FPU đạt 749/749 ca, gồm số vô cực, số rất nhỏ (subnormal), −0 và NaN.
- `asm/t20_fp.s` đạt 21 giá trị mong đợi, lấy từ hằng số IEEE đã biết (ví dụ √2 = `0x3FB504F3`), chạy đúng trên cả hai CPU.

**Giới hạn:** không có thanh ghi `fcsr`, cờ ngoại lệ và `fclass.s`; chưa biên dịch được chương trình C dùng `float`.

---

## Tổng kết kiểm thử

| Hạng mục | Ban đầu | Hiện tại |
|---|---|---|
| Tập lệnh | 44 lệnh | 61 lệnh (25 bắt buộc + 36 mở rộng) |
| Thư viện module | 20 module | 22 module (thêm `Cache`, `FPU`) |
| Test vector module | 25/25 lượt, 12.255 ca | 27/27 lượt, 15.202 ca |
| CPU đơn chu kỳ | 19/19 chương trình | 24/24 chương trình |
| CPU pipeline | 19/19 chương trình | 24/24 chương trình |

Chạy lại toàn bộ kiểm thử bằng một lệnh:

```
python tools/check_all.py --jar <đường dẫn>/logisim-evolution-4.1.0-all.jar
```

Các kết quả trên được kiểm thử trên Logisim-evolution 5.0.0.
