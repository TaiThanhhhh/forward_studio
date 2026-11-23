# WP-T — 3D thời 90 + nhân vật con vật 3D + bối cảnh (engine three)

> Trạng thái: **HOÀN TẤT**.

## Đã làm
1. **Look 3D `retro90` (N64) và `psx` (PS1)** trong `engines/three/main.js` (`LOOK3D`, ghi đè được qua `world.look3d`):
   - Vật liệu `gouraud` (ShaderMaterial tự viết): chiếu sáng theo ĐỈNH (hemi ambient + key + rim + spec Blinn nhẹ), nội suy màu qua mặt đa giác ít đỉnh (`facet: 10` cho N64, `8` cho PS1) với pháp tuyến mượt; `ink_px: 0` (không nét viền), `blob` bóng tròn dưới chân, fog theo đỉnh tan vào `#000`.
   - Rung đỉnh `SNAP` (`wobble` theo lưới độ phân giải thấp) và nội suy UV `affine` kiểu PS1.
   - Texture thủ tục độ phân giải thấp (`tex_px: 128` lọc `bilinear` cho `retro90`; `tex_px: 64` lọc `nearest` cho `psx`).
   - Pass hậu kỳ retro: render nội bộ `1/res_div` (`res_div: 3` N64, `4` PS1) → lượng tử màu `color_bits: 5` (15-bit) + Bayer 4×4 dither (vùng đen tuyền `#000` không bị dither) → upscale `bilinear` + `vi_blur` (N64) hoặc `nearest` (PS1).
   - `text_hd`: chữ diegetic trong cảnh vẽ lại ở độ phân giải gốc (vật khác chỉ ghi depth để che khuất đúng) giúp OCR đọc rõ.
   - Bỏ pass normal/depth khi look không dùng nét ink/rim/DOF; đã gỡ biến debug tạm `window.__dbg`.
2. **Kho nhân vật/con vật 3D thủ tục** `engines/three/creatures.js`:
   - 22 loài (`SPECIES`: `dog`, `dachshund`, `cat`, `fox`, `wolf`, `bear`, `rabbit`, `mouse`, `pig`, `cow`, `horse`, `sheep`, `chicken`, `penguin`, `fish`, `frog`, `turtle`, `dino`, `bird`, `deer`, `kid`, `adult`) + bí danh (`ALIASES`), 13 dáng đi/hành động (`GAITS`: `idle`, `walk`, `trot`, `run`, `sniff`, `sit`, `jump`, `wag`, `eat`, `sleep`, `fall`, `cheer`, `wave`), 9 biểu cảm (`EXPRS`: `neutral`, `happy`, `shock`, `sad`, `angry`, `sleepy`, `sniff`, `blink`, `wink`), 6 kiểu tóc người (`HAIRS`).
   - Mặt vẽ trên texture canvas (mắt có chấm sáng, lông mày, miệng), chớp mắt tất định, chuyển động phụ tai/đuôi trễ pha (follow-through), quay đầu nhìn theo mục tiêu hoặc `"camera"`.
3. **Bối cảnh (`set`) & đạo cụ thiên nhiên** (`engines/three/props.js`, `paint.js`, `scenes/stage.js`, `physics.js`):
   - 3 bối cảnh mới dạng đảo nổi / diorama mép tan vào đen: `meadow` (đảo cỏ nổi, hoa, cụm cỏ, đá, đồi xa mờ dần), `tabletop` (mặt bàn/góc phòng, va chạm mặt bàn tổng quát `0.76 m`), `street` (đoạn phố low-poly).
   - Prop thiên nhiên: `flower`, `tuft`, `rock`, `tree`, `bush`.
4. **Style & kiểm lỗi Python**:
   - `styles/retro90-lowpoly-black.json` (`world.look3d = "retro90"`, `black_min = 0.45`, palette thời 90 trên nền đen).
   - `engines/adapter.py`: `creature_vocab()` đọc từ vựng trực tiếp từ `creatures.js` & `props.js`, `stage_creature_errors()` kiểm tra set/loài/gait/expr/hair/look sai kèm gợi ý gần nhất.

## Số đo & Ảnh kiểm (`qa/retro90/`, `qa/creatures/`)
- **So sánh 3 look** (`python scripts/props3d_sheet.py --retro` → `qa/retro90/compare.jpg`, `look_lowpoly.jpg`, `look_retro90.jpg`, `look_psx.jpg`):
  - `lowpoly`: nền đen `49.6%` (`0.496`)
  - `retro90`: nền đen `52.2%` (`0.522`), `2.901 s/frame` (1 frame lẻ kể cả khởi tạo)
  - `psx`: nền đen `54.2%` (`0.542`), `2.671 s/frame`
- **Cảnh mẫu "dachshund hít hoa trên meadow"** (`python scripts/props3d_sheet.py --meadow` → `qa/retro90/meadow_f00.jpg`, `meadow_f30.jpg`, `meadow_f50.jpg`, `meadow_f75.jpg`, `meadow.mp4`, `report.json`):
  - Tỉ lệ nền đen: `f00 = 0.534`, `f30 = 0.514`, `f50 = 0.484`, `f75 = 0.453`; trung bình cả clip `black_clip_mean = 0.494 >= black_min (0.45)` → **`black_ok: true`**.
  - Tất định 2 worker (đảo thứ tự frame `[12, 61]` vs `[61, 12]`): MD5 khớp tuyệt đối (`{"12": true, "61": true}`).
  - Tốc độ render 90 frame (2 worker, RTX 4070 Laptop GPU): **`0.059 s/frame`** (`0.118 s/frame/worker`, tổng `5.33 s`).
  - Đối chiếu mục 1.1: hình học ít đa giác + đổ bóng Gouraud theo đỉnh (**Đạt**), màu bão hoà thập niên 90 trên sân khấu đen (**Đạt**), mặt vẽ trên texture lọc bilinear (**Đạt**), cụm cỏ/bông hoa vàng/đồi xa sương mờ vào đen (**Đạt**), không nét viền (`ink_px: 0`) + hành động hít hoa rồi quay sang camera vẫy đuôi (**Đạt**).
- **Bảng mặt & biểu cảm** (`qa/creatures/faces_dachshund.jpg`, `faces_kid.jpg`): 9 biểu cảm × 1080×1920.
- Đã dọn sạch thư mục tạm `qa/retro90/_work/` và `qa/creatures/_work/`.

## Kiểm thử
- `python -m unittest tests.test_retro3d` → **9/9 test XANH**.
- `python -m ruff check scripts/props3d_sheet.py engines/adapter.py tests/test_retro3d.py` → **0 lỗi**.
