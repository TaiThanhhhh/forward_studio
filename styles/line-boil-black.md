# Line Boil Black (`line-boil-black`)

Hoạt hình vẽ tay từng khung trên nền đen: nét kem 'sôi' (vẽ lại lệch nhẹ mỗi 2 frame), tô lệch khuôn, chạy on twos, cel FX (khói, tia) bằng nét.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** fire, heat, burn, flame, cook, kitchen, chemistry, reaction, boil, hot, lava, match, candle, vinegar, soda, baking, mix, fizz, foam, bottle
- **Nền đen tối thiểu:** 70% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải sổ tay vẽ tay (nét ở đây luôn rung; sketchnote nét đứng yên, có hatching)
- không phải chalk/board (không bảng, không phấn)
- không mượt kiểu vector: cố ý giật on twos

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #F3EAD7
- `a` #FF4B33
- `b` #FFD23F
- mực kem + đỏ cà chua + vàng nắng

## Chữ (text_fx / thumbnail)

- font `PatrickHand-Regular.ttf` · cỡ 132 · IN HOA · vào bằng `write_on` (10 frame) · số `#FFD23F`

## Luật nhịp

- **fps:** on twos (15 hình/giây trên 30fps); hành động nhanh on ones; giữ hình on threes
- **easing:** ease-out tay, có smear 1 frame khi lao nhanh
- **bounce:** không
- **boil:** 2.2 px đổi mỗi 2 frame
- **cut_rule:** cắt cứng ngay trên smear

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên nét tay rung
- **circle:** vòng tay vẽ 1.1 vòng, hở
- **label:** chữ tay + gạch chân rung

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, flash
- gói SFX (cue chung → âm): pop→pop, hit→thud, whoosh→whoosh_soft, tick→scratch, ding→ting
- nhạc: jazz pizzicato/xylophone tinh nghịch · 104 BPM
- persona giọng: người kể chuyện ấm, hơi tinh quái
- thumbnail: vật vẽ nét kem rung trên đen, một mảng đỏ lệch khuôn, chữ tay 2–3 từ

## Cho Flow (khi style này dùng clip Flow)

- image_style: Hand-drawn frame-by-frame cel animation — Boiling cream ink linework redrawn every two frames, slightly off-register red and yellow fills, cel FX smoke and sparks, pure black background
- video_motion: animated on twos, smear frames on fast moves, lines never perfectly still

## Nguồn

- mg-styles-15 — https://github.com/Vincentwei1021/mg-styles-15 @ `269f6ed788cf` · license: MIT
- lấy từ: demos/05-cel-boil + prompts/05-cel-boil.md
- cách chuyển: port ý tưởng kỹ thuật từ mã MIT, viết lại thành module của engine html (không chạy repo gốc); chi tiết boil bổ sung cho cơ chế boil đã có từ vòng 4–6
