# Embossed · dark stage (`atlas-embossed`)

Biến thể dark-stage của style #36 "Embossed" (Nội dung phẳng thành vật thật) trong 3D Style Atlas: câu trích, tiêu đề cuối. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #36 Embossed · nhóm Flat content made physical · tier 2 · brand_fit `adapted` · hợp kênh 2/5 · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D macro letterpress on cotton paper on a pure black stage (#000000): cream cotton paper with inked impressions, mirror copper foil, etched brass type. Low hard raking lamp, lit far walls and shadowed floors in every impression. One accent colour (copper foil) only on the key element. Leave the pressed area left blank — the line is set in post empty (captions are added later).
- **Block Flow (chuyển động):** Press cycle: plate swings down, lifts to reveal the impression, foil stamp follows.
- **Hợp chủ đề (tags):** quote, saying, motto, title-card, press
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #efe5d0
- `a` #f2a56b
- `b` #3e5173
- `c` #ffe9cf
- sân khấu đen + accent copper foil

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#ffe9cf`

## Luật nhịp

- **fps:** twos
- **easing:** gấp/mở như sách pop-up
- **bounce:** có
- **camera:** shallow-focus long lens from the plate down to the paper, slow pass to the foil
- **cut_rule:** cắt khi trang mở xong

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên giấy cắt
- **circle:** vòng giấy
- **label:** nhãn giấy dán

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: pizzicato strings, paper rustle, light percussion · 104 BPM
- persona giọng: người kể chuyện ấm, như đọc sách pop-up
- thumbnail: một vật chủ đạo kiểu 3d macro letterpress on cotton paper nổi giữa nền đen, accent copper foil trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D macro letterpress on cotton paper — Cream cotton paper with inked impressions, mirror copper foil, etched brass type; low hard raking lamp, lit far walls and shadowed floors in every impression
- video_motion: press cycle: plate swings down, lifts to reveal the impression, foil stamp follows

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#36` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #36 Embossed · Flat content made physical · Title
- cách chuyển: dark-stage: nền #000, look 3D `paper` của engine three.js, block Flow ngắn tự viết
