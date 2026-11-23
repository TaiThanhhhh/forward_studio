# Dithered · dark stage (`atlas-dithered`)

Biến thể dark-stage của style #30 "Dithered" (Bộ lọc trên 3D) trong 3D Style Atlas: chu kỳ, đồng hồ, trạng thái. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #30 Dithered · nhóm Filters over 3D · tier 2 · brand_fit `ok` · hợp kênh 3/5 · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D scene in 1-bit dithering on a pure black stage (#000000): tonal greys mapped to paper, ink or ordered dot patterns. Hard low window sun top-left, long crisp shadows, almost no fill. One accent colour (paper cream) only on the key element. Leave blank retro window readouts empty (captions are added later).
- **Block Flow (chuyển động):** Stepped motion without blur: ticks, snaps, overshoots, instant readout changes.
- **Hợp chủ đề (tags):** timer, routine, cycle, retro, minutes
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f4e8cc
- `a` #f4e8cc
- `b` #3a1510
- `c` #ffffff
- sân khấu đen + accent paper cream

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 124 · IN HOA · vào bằng `pop` (7 frame) · số `#ffffff`

## Luật nhịp

- **fps:** twos
- **easing:** stop-motion / claymation bật nảy có squash-and-stretch và overshoot nhẹ
- **bounce:** có
- **camera:** long lens slightly down, slow truck and pull-back, pixel grid locked to the subject
- **cut_rule:** cắt đúng pha va chạm hoặc khoảnh khắc mô hình biến dạng

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên khối 3D nổi hoặc nét trắng dày
- **circle:** vòng sáng 3D bao quanh vật thể
- **label:** biển 3D trong cảnh hoặc chữ nổi viền đậm

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: nhịp plucky tactile, marimba + bass ấm kiểu mô hình sống động · 112 BPM
- persona giọng: người kể chuyện tò mò, giàu năng lượng, nhấn nhá rõ
- thumbnail: một vật chủ đạo kiểu 3d scene in 1-bit dithering nổi giữa nền đen, accent paper cream trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D scene in 1-bit dithering — Tonal greys mapped to paper, ink or ordered dot patterns; hard low window sun top-left, long crisp shadows, almost no fill
- video_motion: stepped motion without blur: ticks, snaps, overshoots, instant readout changes

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#30` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #30 Dithered · Filters over 3D · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `toon` của engine three.js, block Flow ngắn tự viết
