# Sticker Explainer Black (`sticker-explainer-black`)

Giải thích 'cứng' kiểu nhãn dán: mọi vật có viền trắng dày + bóng mềm như sticker, đặt trên canvas tối chấm lưới; camera lia dài nối các điểm thông tin; biểu đồ chính xác.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** facts, economy, materials, numbers, supply, comparison, phone, element, metal, price, cost, smartphone
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải flat vector (ở đây mọi mảnh có viền trắng 9 px + bóng)
- không phải evidence board (không ghim, không dây đỏ, không giấy)
- không vui nhộn: nghiêm, chữ đều nét, căn thẳng

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #EEF2F5
- `a` #FF5A36
- `b` #7FB7D9
- trắng xám lạnh + một màu nhấn cam đỏ + xanh xám phụ

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 112 · chữ thường · vào bằng `pop` (7 frame) · số `#FF5A36`

## Luật nhịp

- **fps:** ones
- **easing:** đường cong dài (smootherstep) cho camera; vật bật nhẹ
- **bounce:** không
- **rule:** mỗi câu thoại phải có một phần tử hình mới
- **charts:** cột mọc đúng tỉ lệ, số đếm lên
- **cut_rule:** ít cắt: một camera nối nhiều điểm

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** đường dẫn mảnh + chấm đầu
- **circle:** vòng nét đều
- **label:** nhãn trắng bo góc, chữ đen

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→click, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: nền tech-explainer sạch, click UI · 108 BPM
- persona giọng: biên tập viên khoa học điềm tĩnh, nhanh
- thumbnail: một sticker to viền trắng + con số khổng lồ + chú thích nhỏ

## Cho Flow (khi style này dùng clip Flow)

- image_style: Sticker-style explainer collage — Objects as die-cut stickers with a thick white outline and soft drop shadow, flat icons and precise charts on a dark dotted canvas, restrained two-colour palette
- video_motion: one long smooth camera move linking information points, elements pop in on each sentence

## Nguồn

- mg-styles-15 — https://github.com/Vincentwei1021/mg-styles-15 @ `269f6ed788cf` · license: MIT
- lấy từ: demos/19-paperclip + prompts/19-paperclip.md
- cách chuyển: port ý tưởng kỹ thuật từ mã MIT, viết lại thành module của engine html (không chạy repo gốc)
