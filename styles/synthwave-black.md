# Synthwave Black (`synthwave-black`)

Thập niên 80: lưới phối cảnh hồng lao về phía camera, mặt trời sọc lặn sau chân trời, chữ crôm, glow hai lớp, sọc quét VHS.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** retro, music, sound, speed, car, night, electric, game, 80s, neon, arcade
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải HUD (không dữ liệu, không ngoặc khoá)
- không phải neon tubes (có chân trời, mặt trời, chữ crôm đặc)
- không dùng cho chủ đề nghiêm túc/lịch sử

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #F6F0FF
- `a` #FF2BD6
- `b` #2BE8FF
- `c` #FFC43D
- magenta (nóng) + cyan (lạnh) + vàng mặt trời

## Chữ (text_fx / thumbnail)

- font `Anton-Regular.ttf` · cỡ 132 · IN HOA · vào bằng `flicker` (10 frame) · số `#FFC43D`

## Luật nhịp

- **fps:** ones, cố ý khựng 2 frame kiểu băng từ ở khoảnh khắc chính
- **easing:** chữ ĐẬP vào (scale 1.7 → 1) + chớp
- **bounce:** không
- **glow:** hai lớp: sát 6 px + toả 30 px
- **cut_rule:** cắt trên snare gated-reverb

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên neon hai lớp glow
- **circle:** vòng neon chớp 3 lần rồi sáng
- **label:** chữ crôm nhiều nấc

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, glitch, flash
- gói SFX (cue chung → âm): pop→snap, hit→boom, whoosh→riser, tick→tick, ding→sparkle
- nhạc: synthwave: bass saw arpeggio, snare gated-reverb, pad dày · 118 BPM
- persona giọng: DJ đêm khuya, trầm, tự tin
- thumbnail: chữ crôm 2 từ trên mặt trời sọc + lưới hồng; chỉ dùng cho tập hợp chủ đề

## Cho Flow (khi style này dùng clip Flow)

- image_style: 80s synthwave illustration — Neon magenta perspective grid, striped retro sun on the horizon, chrome lettering, double glow, VHS scanlines, black night sky
- video_motion: grid rushes toward the camera, titles slam in with a flash, occasional tape stutter

## Nguồn

- mg-styles-15 — https://github.com/Vincentwei1021/mg-styles-15 @ `269f6ed788cf` · license: MIT
- lấy từ: demos/10-synthwave + prompts/10-synthwave.md
- cách chuyển: port ý tưởng kỹ thuật từ mã MIT, viết lại thành module của engine html (không chạy repo gốc)
