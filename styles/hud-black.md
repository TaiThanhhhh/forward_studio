# HUD Black (`hud-black`)

Giao diện khoa học viễn tưởng: nét xanh cyan mảnh phát sáng, lưới lục giác, vòng xoay có vạch, radar quét, số nhảy rồi chốt; trạng thái báo động đổi sang cam.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** space, tech, military, robot, ai, radiation, extreme, pressure, speed, rocket, satellite, astronaut, orbit, missile, moon, mars, asteroid, alien
- **Nền đen tối thiểu:** 60% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải neon tubes (ống neon dày, chớp tắt) — đây là nét mảnh 3–4 px, dày đặc dữ liệu
- không phải synthwave (không mặt trời, không lưới phối cảnh, không hồng)
- không phải blueprint (không giấy xanh, không chú thích kỹ thuật tĩnh)

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #00E5FF
- `a` #FF6A00
- `b` #B8FBFF
- cyan (nét + lạnh) + cam báo động (nóng/khoá mục tiêu) + cyan nhạt cho chữ phụ

## Chữ (text_fx / thumbnail)

- font `RobotoMono-Variable.ttf` · cỡ 96 · IN HOA · vào bằng `type` (14 frame) · số `#FF6A00`

## Luật nhịp

- **fps:** ones
- **easing:** nét mọc theo thứ bậc, so le; ngoặc khoá co 1.4 → 1.0 (ra nhanh, vào chậm)
- **bounce:** không
- **numbers:** nhảy ngẫu nhiên 3–5 frame rồi chốt giá trị thật
- **type:** gõ máy chữ + con trỏ nháy
- **cut_rule:** cắt trên tiếng beep khoá mục tiêu

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** đường dẫn mảnh gấp khúc 90°
- **circle:** 4 ngoặc góc khoá mục tiêu
- **label:** [ CHỮ MONO TRONG NGOẶC ]

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, glitch
- gói SFX (cue chung → âm): pop→click, hit→impact, whoosh→whoosh_soft, tick→tick, ding→ting
- nhạc: darksynth nhịp đều, beep HUD · 100 BPM
- persona giọng: điều phối viên bình tĩnh, khô, chính xác
- thumbnail: vật giữa 4 ngoặc khoá cam trên lưới cyan, một con số mono thật to

## Cho Flow (khi style này dùng clip Flow)

- image_style: Sci-fi HUD interface graphics — Thin glowing cyan linework, hexagonal grid, rotating tick rings, target lock brackets, orange alert accents, scanlines, pure black background
- video_motion: lines draw on in staggered order, brackets snap onto the target, subtle micro-glitches

## Nguồn

- mg-styles-15 — https://github.com/Vincentwei1021/mg-styles-15 @ `269f6ed788cf` · license: MIT
- lấy từ: demos/22-hud + prompts/22-hud.md
- cách chuyển: port ý tưởng kỹ thuật từ mã MIT, viết lại thành module của engine html (không chạy repo gốc)
