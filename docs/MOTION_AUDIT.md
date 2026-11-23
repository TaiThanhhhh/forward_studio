# MOTION AUDIT — Đo lường & Giải phẫu Khuôn Lặp Motion (Vòng 10 · WP-M)

> Báo cáo đo lường 5 dự án video thật gần nhất trong `projects/` (trước Vòng 10), xác định nguyên nhân gốc làm motion bị lặp khuôn giữa các video, chỉ số mục tiêu và kết quả kiểm chứng bộ não motion mới (`vidlib/motionplan.py` + `lib/motion` + `config/metaphors.json`).

---

## 1. Đo lường 5 video thật trước Vòng 10

Chạy `python -m vidlib.motionplan audit --md`:

| Video | Style · Look | Narrative | Khung xương (chuỗi beat) | Bố cục (`layout`) | Kiểu bay `spine` | Kiểu vào (`enter`) | Số verb khác nhau | Tỉ lệ thẻ chung (`generic_share`) | Shot cơ chế (`mechanism_shots`) |
|---|---|---|---|---|---|---|---|---|---|
| `the-marathon-danger-hiding-in-your-water-bottle` | `flat-vector-black` · `flat` | — | `title → counter → scene → compare → scene → callout → fact → fact → title → title → fact` | `compare:bars`, `counter:bar`, `fact:left/center/stamp`, `title:center/left/hero` | `pan_d, pull, pan_l, pan_r…` | `pop` (chữ: `pop`) | **0** | **73%** | 3/11 |
| `what-a-marathon-does-to-your-brain` | `flat-vector-black` · `flat` | `rewind` | `stage → title → compare → scene → graph → vectors → equation → callout → counter → process → stage → stage → fact → graph → stage` | `compare:split`, `counter:ring`, `fact:stamp`, `process:list`, `title:center` | `pan_d, pull, pan_d, pull…` | `pop` (chữ: `pop`) | **0** | **27%** | 8/15 |
| `gta-6-is-slowing-down-the-internet` | `isometric-black` · `iso` | `chain_reaction` | `scene → title → scene → counter → scene → scene → counter → compare → scene → compare → scene → fact` | `compare:bars/balance`, `counter:giant/bar`, `fact:stamp`, `title:hero` | `pan_d, pan_r, pan_d, pan_r…` | `grow` (chữ: `mask`) | **0** | **50%** | 6/12 |
| `what-a-gta-6-all-nighter-does-to-your-legs` | `swiss-motion-black` · `swiss` | `timeline` | `scene → scene → title → callout → scene → counter → process → counter → compare → scene → fact` | `compare:bars`, `counter:giant/ring`, `fact:left`, `process:path`, `title:left` | `pan_r` × 11 (lặp 100%) | `wipe` (chữ: `mask`) | **0** | **46%** | 6/11 |
| `your-heart-rate-gaming-vs-a-marathon` | `clay3d-black` · `flat` | `versus` | `stage → scene → counter → compare → counter → compare → compare → compare → counter → stage → fact` | `compare:bars/balance/bars/split`, `counter:ring/giant/bar`, `fact:stamp` | `pan_r, pan_l, pan_r, pan_l…` | `pop` (chữ: `pop`) | **0** | **73%** | 3/11 |

### Ma trận độ giống khung xương (`skeleton_sim`, 0..1)

| | `the-marathon-dange` | `what-a-marathon-do` | `gta-6-is-slowing-d` | `what-a-gta-6-all-n` | `your-heart-rate-ga` |
|---|---|---|---|---|---|
| `the-marathon-dange` | **1.00** | 0.34 | 0.44 | 0.44 | 0.25 |
| `what-a-marathon-do` | 0.34 | **1.00** | 0.26 | 0.36 | 0.34 |
| `gta-6-is-slowing-d` | 0.44 | 0.26 | **1.00** | **0.63** | 0.39 |
| `what-a-gta-6-all-n` | 0.44 | 0.36 | **0.63** | **1.00** | 0.37 |
| `your-heart-rate-ga` | 0.25 | 0.34 | 0.39 | 0.37 | **1.00** |

---

## 2. Năm nguyên nhân gốc (Root Causes)

1. **Quá ít bố cục (`LAYOUTS`) và không nhớ lịch sử kênh**:
   - Trước Vòng 10, `title/counter/compare/fact` chỉ có 3 bố cục, `process` chỉ có 2.
   - `codeshot.assign_layouts` chỉ tránh lặp *trong cùng một video*, không đọc lịch sử các video trước → video nào cũng xoay quanh `counter:ring/giant/bar` và `compare:bars/split`.
2. **Brief dạy LLM "thấy số là dùng `counter`/`compare`"**:
   - `vidlib/brief.py → mix_help()` trước đây ưu tiên hướng dẫn thẻ số liệu trước, khiến LLM biến mọi chi tiết vật lý/sinh học (nhịp tim 157 bpm, mất nước, tốc độ mạng) thành con số chạy lên (`counter`) hoặc hai cột (`compare`), đẩy `generic_share` lên tới **73%** ở `your-heart-rate-gaming-vs-a-marathon` và `the-marathon-danger-hiding-in-your-water-bottle`.
3. **Không có động từ chuyển động (`verb`) theo dữ liệu thực**:
   - Cả 5 video có `verbs_distinct = 0`. Diễn viên trong `scene` chỉ dùng một kiểu vào duy nhất của look (`pop`, `grow`, hoặc `wipe`) rồi đứng nhấp nhô nhẹ (`bob`). Tim 157 bpm không đập ở 157 nhịp/phút; người chạy không nhún theo guồng chân (`spm`).
4. **Hành lang bay `spine` hẹp và lặp**:
   - Giao giữa `look` và `narrative.moves` đôi khi chỉ còn 1–2 hướng (ví dụ `timeline` + `swiss` chỉ còn đúng `pan_r` lặp 11 lần liên tiếp), và `spine.sequence` không tránh kiểu bay của video liền trước.
5. **Thiếu chiều sâu 2D/3D và thiếu nhân vật có biểu cảm**:
   - `scene` 2D hoàn toàn phẳng (`z = 0`, không parallax, không DOF, không lớp tiền cảnh lướt qua ống kính).

---

## 3. Giải pháp đã triển khai & Chỉ số mục tiêu (Vòng 10)

| Hạng mục | Trước Vòng 10 | Sau Vòng 10 (Mục tiêu & Đã đạt) |
|---|---|---|
| Từ vựng động từ (`lib/motion`) | 0 verb (chỉ có 14 hàm easing) | **58 verb** (`in`: 17, `accent`: 18, `out`: 11, `idle`: 12) + **7 mẫu `stagger`**, parity JS = Python 100% |
| Kho cơ chế hình ảnh (`config/metaphors.json`) | 0 | **175 cơ chế** phủ 11 mảng kênh, tự kiểm từ vựng động với engine (`check_library()` = 0 lỗi) |
| Số bố cục mỗi beat (`engines/html`) | 2–3 bố cục/beat | **5–7 bố cục/beat** (`counter` 7, `compare` 7, `title` 5, `fact` 5, `process` 5) + **4 beat cơ chế mới** (`units`, `timeline`, `split`, `meter`) |
| Киểu bay camera một cú máy (`vidlib/spine.py`) | 8 kiểu | **14 kiểu bay** (thêm `orbit_tilt`, `push_through`, `rack`, `whip_rot`, `truck_parallax`, `spiral`) + tránh lặp video gần nhất |
| Tỉ lệ thẻ chung chung (`generic_max_share`) | Tới 73% | **≤ 45%** (cấu hình trong `config/channel.json → motion`, linter cảnh báo + gợi ý cơ chế thay thế) |
| Số shot cơ chế tối thiểu (`min_mechanism_shots`) | Có video chỉ 3/11 | **≥ 3 shot cơ chế/video**, brief ưu tiên **"mechanism first, number second"** |
| Độ giống khung xương tối đa (`skeleton_sim_max`) | 0.63 | **≤ 0.60** so với 3 video gần nhất (`DO NOT REPEAT` chèn thẳng vào brief) |

---

## 4. So sánh Brief giữa 2 chủ đề khác nhau

Brief sinh bởi `vidlib/brief.py` (mục `## 4c. Motion`) tự động rút top-6 cơ chế khớp từ khoá + gốc từ cho từng chủ đề:

- **Chủ đề A**: *"What happens to a dog's nose when it sniffs a flower?"*
  - Cơ chế khớp: `dog_sniff` (chó hít hoa trên đảo cỏ `meadow`, hạt mùi bay vào mũi), `olfactory_lock` (phân tử khớp thụ thể khứu giác), `breath_cycle_exchange`, `animal_ear_radar`, `neural_spark_chain`, `scale_zoom_nested`.
  - Gợi ý 3D `stage` (`creature` species `dachshund`/`dog`, gait `sniff`/`wag`) + 2D `rig:dog` + verb `heartbeat`, `breathe`, `wag`, `follow_through`.
- **Chủ đề B**: *"What happens to your phone battery in freezing cold?"*
  - Cơ chế khớp: `battery_drain` (beat `meter` kind `battery` tụt % và đổi màu), `thermal_mercury_drop` (nhiệt kế tụt xuống vùng đóng băng), `ion_traffic_jam` (hạt ion trong `scene` chậm dần rồi kẹt cứng với verb `shiver`), `screen_flicker_die` (`glitch` + `flicker`), `chemical_rate_split` (beat `split` so tốc độ phản ứng ở 25°C vs −10°C).
  - Hai chủ đề giao nhau **0 cơ chế chuyên biệt**, chỉ dùng chung bộ từ vựng verb.
