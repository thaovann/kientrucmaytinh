# Máy tính RISC-V 32-bit trên Logisim-evolution

Thiết kế, mô phỏng và kiểm thử một CPU 32-bit theo tập lệnh **RISC-V RV32I**, gồm hai phiên bản:

| Phiên bản | File | Đặc điểm |
|---|---|---|
| Đơn chu kỳ (single-cycle) | `single/riscv_single.circ` | Mỗi lệnh hoàn thành trong 1 chu kỳ |
| Pipeline 5 tầng | `pipeline/riscv_pipe.circ` | IF → ID → EX → MEM → WB, có **forwarding**, **stall** khi load-use, **flush** khi nhảy, **dự đoán nhánh** (BTB 16 mục + bộ đếm 2 bit), **I-cache và D-cache** (mục 1.2) |

Cả hai phiên bản đều có **ngắt (interrupt)** từ UART RX (mục 1.1) và **số thực** single precision theo phần mở rộng Zfinx (mục 1.3).

Hai phiên bản dùng chung thư viện module `modules/riscv_modules.circ`.

Những gì đã thay đổi so với bản gốc khi thêm UART RX, ngắt, cache và số thực: xem [THAY_DOI.md](THAY_DOI.md).

## 1. Tập lệnh hỗ trợ

| Nhóm | Lệnh |
|---|---|
| Số học / logic (R) | `add sub and or xor slt sltu sll srl sra` |
| Số học / logic (I) | `addi andi ori xori slti sltiu slli srli srai` |
| Bộ nhớ | `lw sw` và **`lb lh lbu lhu sb sh`** (mở rộng) |
| Nhảy có điều kiện | `beq bne` và **`blt bge bltu bgeu`** (mở rộng) |
| Nhảy không điều kiện | `jal jalr` |
| Nhân/chia (M-extension) | **`mul mulh mulhsu mulhu div divu rem remu`** (mở rộng) |
| Khác | `lui` |
| Số thực single precision (Zfinx, mục 1.3) | **`fadd.s fsub.s fmul.s fdiv.s fsqrt.s fmin.s fmax.s feq.s flt.s fle.s fsgnj.s fsgnjn.s fsgnjx.s fcvt.w.s fcvt.wu.s fcvt.s.w fcvt.s.wu`** (mở rộng) |

Tổng cộng 61 lệnh (25 lệnh bắt buộc + 36 lệnh mở rộng). Không hỗ trợ `auipc`, `fence`, `ecall`, CSR, `fclass.s`.

**Vào/ra ánh xạ bộ nhớ** (địa chỉ ≥ `0x80000000`, dùng `lw`/`sw`):

| Địa chỉ | Thiết bị | Ghi | Đọc |
|---|---|---|---|
| `0x80000000` | 8 LED | đặt LED | giá trị đã ghi |
| `0x80000004` | 8 LED 7 đoạn | 8 chữ số hex | giá trị đã ghi |
| `0x80000008` | UART TX → TTY | gửi 1 ký tự | `1` = sẵn sàng |
| `0x8000000C` | 8 công tắc DIP | – | trạng thái công tắc |
| `0x80000010` | UART RX ← bàn phím (Keyboard) | bỏ ký tự đầu hàng đợi (giá trị ghi tùy ý) | bit 8 = `1` khi có ký tự, bit 6..0 = mã ASCII của ký tự đầu hàng đợi; `0` khi hàng đợi rỗng |
| `0x80000014` | IE (cho phép ngắt) | bit 0 = `1`: bật ngắt UART RX | giá trị IE |

Khối IO chọn thiết bị bằng `Addr[4:2]`. Đọc các địa chỉ `0x80000018`, `0x8000001C` trả về 0, ghi vào đó không có tác dụng. Đọc UART RX không làm mất ký tự: chương trình đọc xong thì ghi vào `0x80000010` để lấy ký tự tiếp theo, ví dụ:
```
wait:   lw   t0, 16(s0)        # s0 = 0x80000000
        andi t1, t0, 0x100
        beqz t1, wait          # chưa có ký tự
        sw   x0, 16(s0)        # bỏ ký tự vừa đọc khỏi hàng đợi
        andi t0, t0, 0x7F      # t0 = ký tự
```

Lệnh giả mà assembler chấp nhận: `nop mv li j jr ret beqz bnez iret fmv.s fneg.s fabs.s fgt.s fge.s`, và `jal nhan` (tương đương `jal ra, nhan`). `li` nhận cả hằng số thực có hậu tố `f`, ví dụ `li a0, 3.25f` nạp mẫu bit `0x40500000`.

### 1.1. Ngắt (interrupt)

Khối IO đưa ra tín hiệu `IRQ = IE & (bàn phím có ký tự)`. CPU nhận ngắt mà không cần CSR hay lệnh mới:

- **Vào ngắt.** Khi `IRQ = 1` và CPU không ở trong trình phục vụ ngắt, tầng IF thay lệnh vừa nạp bằng lệnh `jalr tp, 4(x0)` (mã `0x00400267`). Lệnh này lưu `PC + 4` của lệnh bị ngắt vào `tp` (x4), rồi nhảy tới **vector ngắt `0x004`**. Lệnh bị thay chưa chạy và sẽ chạy lại khi quay về.
- **Thoát ngắt.** Lệnh giả `iret` = `jalr x0, -4(tp)` (mã `0xFFC20067`) quay lại lệnh bị ngắt.
- **Chặn ngắt lồng nhau.** Thanh ghi 1 bit `INH` trong CPU được đặt khi lệnh `jalr tp, 4(x0)` thực thi (ở tầng EX với bản pipeline), và xóa khi `iret` thực thi. Khi `INH = 1` thì không nhận ngắt.
- **Ngắt chính xác trên pipeline.** Lệnh chèn đi qua pipeline như lệnh `jalr` bình thường. Nếu nó bị flush (vì một lệnh nhảy trước đó đổi hướng), `IRQ` vẫn đang bằng 1 nên ngắt được chèn lại ở đường đúng. Bản pipeline không chèn khi đã có lệnh ngắt ở tầng ID hoặc EX.

Quy ước khi viết chương trình dùng ngắt:
- Đặt `j main` ở địa chỉ `0x000`, trình phục vụ ngắt (ISR) bắt đầu ở `0x004`.
- **`tp` dành riêng cho ngắt**: chương trình chính không dùng `tp` sau khi đã bật ngắt.
- ISR phải lưu và khôi phục mọi thanh ghi nó dùng (trên stack), và phải lấy ký tự ra khỏi hàng đợi (ghi `0x80000010`), nếu không ngắt sẽ xảy ra lại ngay sau `iret`.
- Bật ngắt bằng `sw` giá trị 1 vào `0x80000014`. Không hỗ trợ ngắt lồng nhau và chưa viết được ISR bằng C.

```
        j    main            # 0x000
isr:    addi sp, sp, -8      # 0x004: vector ngắt
        sw   t0, 0(sp)
        sw   t1, 4(sp)
        lui  t0, 0x80000
        lw   t1, 16(t0)      # đọc ký tự
        sw   x0, 16(t0)      # bỏ khỏi hàng đợi -> IRQ về 0
        sw   t1, 8(t0)       # in ra TTY
        lw   t1, 4(sp)
        lw   t0, 0(sp)
        addi sp, sp, 8
        iret
main:   li   sp, 0x700
        li   s0, 0x80000000
        li   t0, 1
        sw   t0, 20(s0)      # IE = 1
loop:   j    loop            # chương trình chính chạy tiếp, ký tự được xử lý trong ISR
```

### 1.2. Cache (bản pipeline)

Bản pipeline có hai cache riêng: **I-cache** (cho lệnh, nằm giữa PC và IMEM) và **D-cache** (cho dữ liệu, nằm giữa tầng MEM và DMEM). Cả hai dùng chung module `Cache` trong thư viện.

| Thông số | Giá trị |
|---|---|
| Tổ chức | Ánh xạ trực tiếp (direct-mapped), 16 dòng × 4 word = 256 byte mỗi cache |
| Chia địa chỉ | `Addr[3:2]` = word trong dòng, `Addr[7:4]` = chỉ số dòng, `Addr[31:8]` = tag |
| Bộ nhớ trong | RAM `TAG` 16 × 32 (bit 31 = valid), RAM `DATA` 64 × 32, bộ đếm `CNT` 3 bit |
| Khi miss | CPU **đóng băng 8 chu kỳ** để nạp cả dòng: chu kỳ 0–3 chép 4 word, chu kỳ 4–6 giả lập độ trễ của bộ nhớ chính, chu kỳ 7 ghi tag và valid. Chu kỳ tiếp theo là hit |
| Ghi (D-cache) | Write-through: luôn ghi vào RAM. Ghi trúng thì cập nhật word trong cache; ghi trượt thì không cấp dòng (no-allocate) và không đóng băng |
| Vùng I/O | Địa chỉ ≥ `0x80000000` không qua D-cache |

**Đóng băng CPU.** `stall = istall | dstall` được chốt vào latch `FRZ` (trong suốt khi clk = 0). Mọi phần tử nhớ của CPU chạy bằng `clk = clk_raw & ~FRZ`, còn hai cache chạy bằng `clk_raw`. Vì vậy khi miss, toàn bộ CPU (PC, thanh ghi pipeline, RegFile, BTB, `INH`…) giữ nguyên trạng thái trong lúc cache nạp dòng. Forwarding, stall, flush và ngắt không cần sửa gì. `IOWrite` ra khối IO bị chặn khi đang đóng băng để không ghi IO lặp lại. DMEM có thêm hai chân ra: `Word` (word thô của RAM, dùng khi nạp dòng) và `WWord` (word sau khi gộp byte của `sb`/`sh`, dùng cập nhật cache). Một khối LoadExt sau D-cache tạo kết quả cho `lb`/`lh`/`lbu`/`lhu`.

Kết quả số chu kỳ và tỉ lệ miss của từng chương trình nằm trong `report/so_sanh.md`. So với cùng một bộ nhớ chính chậm (5 chu kỳ mỗi lần đọc, ước tính trên mô hình), cache giúp chạy nhanh hơn 1,4–4,6 lần.

### 1.3. Số thực (Zfinx, cả hai bản)

CPU hỗ trợ số thực IEEE-754 single precision (32 bit) theo **Zfinx**, phần mở rộng chính thức của RISC-V trong đó số thực nằm ngay trong các thanh ghi `x0`–`x31`, không có tệp thanh ghi `f` riêng. Mã lệnh giống phần mở rộng F (opcode `OP-FP` = `0x53`). Vì vậy:
- Không có `flw`/`fsw`/`fmv.x.w`: số thực được nạp/lưu bằng `lw`/`sw` như số nguyên.
- Lệnh FP đi qua pipeline như một lệnh R-type: forwarding, stall và flush dùng lại nguyên vẹn. Các thanh ghi pipeline không phải sửa.

Phần cứng thay đổi:
- Thêm module **`FPU`** trong thư viện, dựng từ các khối `FPArithmetic` của Logisim: cộng, trừ, nhân, chia, căn, min/max, so sánh, FP↔Int. Đầu ra được chọn theo `funct5` qua một MUX 32→1.
- ROM của **Control** có thêm dòng cho opcode `0x53`, giống R-type.
- Tầng EX của cả hai CPU có thêm MUX `aluout = IsFP ? FPU : (ALU/MulDiv)`.

| Lệnh | Ghi chú |
|---|---|
| `fadd.s fsub.s fmul.s fdiv.s fsqrt.s` | Làm tròn về gần nhất, chẵn (RNE). Trường `rm` bị bỏ qua |
| `fmin.s fmax.s` | `-0 < +0`. **Khác chuẩn**: nếu có NaN thì trả về NaN |
| `feq.s flt.s fle.s` | Trả về 0 hoặc 1; có NaN thì trả về 0 |
| `fsgnj.s fsgnjn.s fsgnjx.s` | Gồm cả các lệnh giả `fmv.s`, `fneg.s`, `fabs.s` |
| `fcvt.w.s fcvt.wu.s rd, rs1[, rm]` | Theo `rm`: `rne` (0), `rtz` (1), `rdn` (2), `rup` (3); `rm` ≥ 4 (kể cả `dyn`) dùng RNE. **Khác chuẩn**: khi tràn hoặc NaN thì không bão hòa |
| `fcvt.s.w fcvt.s.wu` | Có dấu / không dấu |

Không có thanh ghi `fcsr`, cờ ngoại lệ (`fflags`) và `fclass.s`. Chương trình C dùng `float` cần biên dịch với `-march=rv32im_zfinx`; `cc.py` chưa hỗ trợ việc này.

Thông số: dữ liệu 32 bit, lệnh 32 bit, 32 thanh ghi × 32 bit (x0 luôn bằng 0), PC 32 bit. Bộ nhớ lệnh (ROM) và bộ nhớ dữ liệu (RAM) mỗi bộ 1024 word = 4 KB, địa chỉ theo byte.

## 2. Yêu cầu phần mềm

- **Logisim-evolution 4.1.0.** Để chạy test bằng dòng lệnh cần file `logisim-evolution-4.1.0-all.jar` và **Java 21** trở lên.
- **Python 3.8+**. Các công cụ chỉ dùng thư viện chuẩn.
- Chỉ khi biên dịch chương trình C: `pip install ziglang` (trình biên dịch clang + lld cho RISC-V, chạy được trên Windows/Linux/macOS).

## 3. Cấu trúc thư mục

```
riscv32/
├── README.md
├── modules/riscv_modules.circ   Thư viện 22 module: ALU, RegFile, ImmGen, BranchCmp, PCUnit, Control,
│                                IF_ID, ID_EX, EX_MEM, MEM_WB, ForwardUnit, WBBypass, HazardUnit,
│                                LoadExt, StoreMerge, MulDiv, IsMul, MemMap, BTB, PredRegs, Cache, FPU
├── single/riscv_single.circ     CPU đơn chu kỳ (circuit CPU, IMEM, DMEM, IO, main)
├── pipeline/riscv_pipe.circ     CPU pipeline 5 tầng (circuit CPU, IMEM, DMEM, IO, main)
├── asm/                         Chương trình test (assembly)
├── c/                           Thư viện cho chương trình C: start.S, link.ld, riscv_io.h, rt.c
├── demo/calc.c                  Chương trình C demo (công tắc → TTY, LED 7 đoạn, LED)
├── rom/                         File nạp ROM (.hex, định dạng "v2.0 raw"), file ROM điều khiển
├── tests/                       Test vector cho từng module
├── tools/                       Công cụ Python (xem mục 7)
└── report/                      Bảng kết quả kiểm thử (sinh tự động)
```

Hai file CPU nạp thư viện theo **đường dẫn tương đối** `../modules/riscv_modules.circ`. Khi chép project sang máy khác, phải giữ nguyên cấu trúc thư mục.

## 4. Mở project và chạy mô phỏng

1. Mở Logisim-evolution, chọn **File → Open**, chọn `single/riscv_single.circ` hoặc `pipeline/riscv_pipe.circ`.
2. Circuit `main` chứa khối `CPU`, một **Clock**, nút **RESET** và các Probe hiển thị `PC`, `Instr`, `WB`… Bản pipeline hiển thị thêm lệnh ở từng tầng: `Instr_D`, `Instr_E`, `Instr_M`, `Instr_W`.
3. Nhấn **Ctrl+R** để reset mô phỏng (PC về 0, xóa thanh ghi và RAM).
4. Chạy CPU:
   - **Ctrl+T**: tiến nửa chu kỳ. Hai lần Ctrl+T bằng một chu kỳ.
   - **Ctrl+K**: bật/tắt chạy tự động. Đổi tốc độ ở *Simulate → Auto-Tick Frequency*.
5. Quan sát trạng thái:
   - Nhấp đúp khối `CPU`, rồi nhấp đúp `RegFile` để xem 31 thanh ghi `x1…x31`.
   - Nhấp đúp `DMEM` để xem RAM (ô `n` ứng với địa chỉ byte `4n`).
6. Gõ phím cho UART RX: chọn công cụ **Poke** (bàn tay), nhấp vào khối **Keyboard** bên dưới khối `IO` rồi gõ. Ký tự được đưa vào hàng đợi của Keyboard và chương trình đọc ở địa chỉ `0x80000010`.

## 5. Nạp chương trình

1. Viết chương trình assembly trong `asm/`, ví dụ `asm/vidu.s`.
2. Dịch ra file nạp ROM:
   ```
   python tools/asm.py asm/vidu.s -o rom/vidu.hex
   ```
   Lệnh in ra listing (địa chỉ, mã máy, lệnh). Nếu có lỗi, nó báo kèm số dòng.
3. Trong Logisim, nhấp đúp `IMEM` ở cây Design, chuột phải vào ROM, chọn **Load Image…** rồi chọn `rom/vidu.hex`.
4. Quay về `main`, nhấn **Ctrl+R**, rồi chạy.

Để xem trước kết quả đúng của chương trình (trạng thái thanh ghi và bộ nhớ cuối cùng), dùng mô phỏng tập lệnh bằng Python:
```
python tools/rvsim.py asm/vidu.s          # thêm -t để in từng lệnh
python tools/pipesim.py asm/vidu.s -t     # sơ đồ pipeline từng chu kỳ (IF/ID/EX/MEM/WB, stall, flush)
```

Chương trình nên kết thúc bằng vòng lặp dừng `done: j done`.

### Chương trình C
```
python tools/cc.py demo/calc.c                     # -> rom/calc.hex, nạp vào ROM như trên
python tools/cc.py demo/calc.c --run --sw 10       # chạy thử bằng mô phỏng Python, in TTY/LED/HEX
python tools/cc.py vidu.c --run --rx "abc\n"       # --rx: chuỗi giả lập gõ từ bàn phím (UART RX)
```
`cc.py` biên dịch (rv32im, không thư viện chuẩn), kiểm mọi lệnh nằm trong tập lệnh CPU, và sinh thêm đoạn mã đầu ROM để chép dữ liệu (`.rodata`, `.data`) vào RAM. Bộ nhớ cho C: mã từ `0x0`, dữ liệu từ `0x1000`, ngăn xếp từ `0x2000` đi xuống. Thiết bị I/O dùng qua `c/riscv_io.h`.

## 6. Chạy kiểm thử

Mọi lệnh chạy từ thư mục `riscv32`. Có thể đặt biến môi trường `LOGISIM_JAR` thay cho tham số `--jar`.

### 6.1. Toàn bộ, bằng một lệnh
```
python tools/check_all.py --jar <đường dẫn>/logisim-evolution-4.1.0-all.jar
python tools/check_all.py --jar <jar> --java "C:\jdk-21\bin\java.exe"   # khi lệnh java mặc định cũ hơn Java 21
```
Lệnh chạy lần lượt các phần ở mục 6.2–6.4, ghi bảng kết quả vào `report/`, rồi in tổng kết. Mất khoảng 1–2 phút.

### 6.2. Test từng module
```
python tools/run_tests.py --jar <jar>              # tất cả
python tools/run_tests.py --jar <jar> ALU Control  # chỉ một số module
```
Mỗi module được kiểm bằng test vector trong `tests/`:
- module tổ hợp: vét cạn các ca biên và thêm các ca ngẫu nhiên;
- module tuần tự: kiểm theo từng chu kỳ clock, dùng cột `<set>`/`<seq>`.

### 6.3. Test CPU theo từng chu kỳ
```
python tools/cpu_test.py "asm/t*_*.s" --jar <jar>              # CPU đơn chu kỳ
python tools/cpu_test.py "asm/t*_*.s" --pipe 17 --jar <jar>    # CPU pipeline (dự đoán nhánh + cache)
python tools/cpu_test.py rom/calc_test.hex --sw 13 --jar <jar>  # chương trình C (file .hex), công tắc = 13
```
Với mỗi chương trình, công cụ làm các việc sau:
1. Dịch chương trình.
2. Nạp chương trình vào ROM của một **bản sao** file `.circ` (file gốc không bị sửa).
3. Chạy Logisim ở chế độ dòng lệnh.
4. So sánh **ở mọi chu kỳ** các tín hiệu `PC`, `Instr`, `RegWrite`, `rd`, `WB`, `MemWrite`, `MemAddr`, `MemWData` (và `IOWrite`, khi CPU có pin I/O) với mô hình tham chiếu (`rvsim.py` cho đơn chu kỳ, `pipesim.py` cho pipeline). Giá trị công tắc lấy từ dòng `# SW = ...` trong file `.s` hoặc tùy chọn `--sw`. Chuỗi gõ từ bàn phím (UART RX) lấy từ dòng `# RX = "..."` hoặc tùy chọn `--rx`.

Khi có sai lệch, công cụ in ra chu kỳ bị sai, lệnh đang nằm ở từng tầng, và giá trị thực tế so với giá trị mong đợi.

Các tùy chọn khác:
- `--md report/x.md`: ghi bảng kết quả dạng Markdown.
- `--gen tests/x.txt`: chỉ sinh test vector, để chạy bằng menu *Simulate → Test Vector*.

### 6.4. So sánh hiệu năng
```
python tools/compare.py "asm/t*_*.s" --md report/so_sanh.md
```

## 7. Công cụ

| File | Chức năng |
|---|---|
| `tools/asm.py` | Assembler RV32I: từ `.s` sinh `.hex` (Logisim "v2.0 raw") |
| `tools/rvsim.py` | Mô phỏng tập lệnh (mô hình tham chiếu đơn chu kỳ); kiểm các dòng `# EXPECT` trong file `.s` |
| `tools/pipesim.py` | Mô hình pipeline 5 tầng chính xác từng chu kỳ (`--lab 8/9/10/11/16/17`; 17 = có cache) |
| `tools/cache.py` | Mô hình khối Cache (dùng chung cho `pipesim.py` và `gen_cache_tests.py`) |
| `tools/fpu.py` | Mô hình khối FPU (dùng chung cho `rvsim.py`, `pipesim.py`, `gen_fpu_tests.py`) |
| `tools/cc.py` | Biên dịch chương trình C thành file nạp ROM (cần `pip install ziglang`) |
| `tools/cpu_test.py` | So sánh CPU Logisim với mô hình, từng chu kỳ |
| `tools/run_tests.py` | Chạy test vector của các module |
| `tools/check_all.py` | Chạy toàn bộ kiểm thử, sinh báo cáo |
| `tools/compare.py` | Bảng so sánh số chu kỳ và CPI |
| `tools/gen_*.py` | Sinh test vector và nội dung ROM điều khiển (`rom/control.rom`, `rom/aluctl.rom`) |
| `tools/package.py` | Đóng gói bài nộp thành file `.zip` |

## 8. Chương trình test

| File | Nội dung | Kết quả chính |
|---|---|---|
| `t1_arith.s` | Số học/logic, tràn số, dịch 0/31/33, so sánh có/không dấu, ghi x0 | 26 giá trị EXPECT |
| `t2_sum.s` | Vòng lặp tổng 1..10 | `x2 = 55`, `MEM[0] = 55` |
| `t3_fib.s` | 12 số Fibonacci ghi vào mảng | `MEM[0x12C] = 89` |
| `t4_recursion.s` | Đệ quy `fib(8)` dùng stack | `s0 = 21` |
| `t5_sort.s` | Sắp xếp nổi bọt 8 số có dấu | mảng tại `0x200` tăng dần |
| `t6_mul.s` | Phép nhân bằng dịch và cộng | `123 × 456 = 56088`, `−7 × 9 = −63` |
| `t7_hazard.s` | Chuỗi lệnh phụ thuộc sát nhau | 17 giá trị EXPECT |
| `t9_forward.s` | Forwarding, bypass WB→ID | 13 giá trị EXPECT |
| `t10_loaduse.s` | Load-use (5 lần stall) | 7 giá trị EXPECT |
| `t11_control.s` | Hazard điều khiển: branch sau `lw`, `jal`/`jalr` liên tiếp | `x31 = 0` (không chạy nhầm lệnh nào) |
| `t13_bytes.s` | LB/LH/LBU/LHU, SB/SH ở mọi vị trí byte | 21 giá trị EXPECT |
| `t14_muldiv.s` | 8 lệnh M, tràn, chia cho 0, giai thừa, UCLN | 22 giá trị EXPECT |
| `t14b_mulhw.s` | Bài toán của `t6_mul` bằng lệnh `mul` | 26 chu kỳ pipeline (so với 653) |
| `t15_io.s` | LED, HEX, UART TX, công tắc; ghi I/O không đè RAM | TTY = `Hi RISC-V!` |
| `t16_predict.s` | Vòng lồng nhau, mẫu xen kẽ, `jal`, hai nhánh trùng chỉ số BTB | 463 chu kỳ (555 khi chưa dự đoán) |
| `t17_uart_rx.s` | UART RX: đọc bàn phím, đổi chữ thường thành chữ hoa, in lại ra TTY tới khi gặp `\n` | TTY = `HELLO, RISC-V!\n` |
| `t18_irq.s` | Ngắt: chương trình chính tính tổng và gọi hàm, 7 ký tự đến cách nhau 61 chu kỳ, ISR in ra TTY | TTY = `IRQ ok\n`, `a0 = 5050` |
| `t18b_irq_burst.s` | Ngắt liên tiếp: 4 ký tự có sẵn trước khi bật ngắt | TTY = `ABCD`, 4 lần ngắt |
| `t19_cache.s` | Cache: đọc mảng 2 lần (lần 2 toàn hit), xung đột chỉ số, ghi write-through khi hit/miss, `sb`/`lh` qua cache | `s1 = s2 = 1488`, 11 giá trị EXPECT |
| `t20_fp.s` | Số thực: 5 phép toán, các chế độ làm tròn của `fcvt`, so sánh, min/max, số thực trong bộ nhớ, hazard (forwarding, load-use) | 21 giá trị EXPECT, `Σ1/k² (k=1..20) = 0x3FCC4F14` |
| `test6a…6d_*.s` | Từng nhóm lệnh: ALU, bộ nhớ, branch, JALR | |
| `demo15_io.s` | Demo I/O chạy liên tục (không có vòng dừng) | |
| `demo18_irq.s` | Demo ngắt: vòng lặp chính đếm trên LED 7 đoạn, gõ phím thì ISR in chữ hoa ra TTY | |

Các giá trị mong đợi được ghi ngay trong file bằng các dòng `# EXPECT x10 = 55`, `# EXPECT MEM[0x100] = 50`, `# EXPECT LED = 0x5A`, `# EXPECT TTY = "Hi\n"`. Dữ liệu vào cho mô phỏng: `# SW = 0x5A` (công tắc), `# RX = "abc\n"` (bàn phím), `# RX_GAP = 61` (ký tự thứ i đến ở chu kỳ 61·(i+1); không có dòng này thì mọi ký tự có sẵn từ đầu).

Kiểm tra toàn hệ thống (circuit `main`, gồm cả Keyboard và TTY) mà không mở giao diện: nạp ROM rồi chạy Logisim ở chế độ `-tty`. Chuỗi đưa vào stdin được chuyển tới Keyboard, còn nội dung TTY được in ra stdout:
```
printf 'hello, RISC-V!\n' | java -jar <jar> single/riscv_single.circ -tty tty    # in: HELLO, RISC-V!  (Ctrl+C để dừng)
```

## 9. Kết quả kiểm thử

- Test vector module: **27/27 lượt đạt** (22 module thư viện + IMEM, DMEM, IO; 15.202 ca).
- CPU đơn chu kỳ: **24/24 chương trình đạt**.
- CPU pipeline có dự đoán nhánh và cache: **24/24 chương trình đạt mà không chèn `nop`**, khớp mô hình từng chu kỳ.
- UART RX chạy đúng trên circuit `main` của cả hai CPU (chế độ `-tty`: gõ `hello, RISC-V!` thì in ra `HELLO, RISC-V!`).
- Ngắt chạy đúng trên circuit `main` của cả hai CPU (`demo18_irq.s`, chế độ `-tty`: gõ `hello, irq!` thì ISR in ra `HELLO, IRQ!` trong khi vòng lặp chính vẫn chạy).
- Bảng `report/so_sanh.md` ghi `sai` cho `t18*` ở cột Lab 9/10. Đây là điều mong đợi: các mức đó chèn `nop` sau lệnh nhảy thay vì flush, còn lệnh nhảy do ngắt chèn vào thì không có `nop`. Ngắt cần pipeline có flush đầy đủ (Lab 11, 16).
- Chương trình C `demo/calc.c` chạy khớp mô hình từng chu kỳ trên cả hai CPU.

Chi tiết xem `report/ket_qua_single.md`, `report/ket_qua_pipeline.md`, `report/so_sanh.md`.
