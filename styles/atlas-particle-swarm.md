# Particle Swarm · dark stage (`atlas-particle-swarm`)

Biến thể dark-stage của style #23 "Particle Swarm" (Nội dung phẳng thành vật thật) trong 3D Style Atlas: phân tử, nhiệt, nổ, thứ làm từ nhiều đơn vị. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #23 Particle Swarm · nhóm Flat content made physical · tier 1 · brand_fit `adapted` · hợp kênh 5/5
- **Block Flow (ảnh):** 3D swarm of tiny glass beads on a pure black stage (#000000): polished glass seed beads, uneven sizes, bright glints, translucent far-side glow. Soft warm window-style key top-left, bead-on-bead shadows. One accent colour (golden corn) only on the key element. Leave a blank caption plate below the swarm empty (captions are added later).
- **Block Flow (chuyển động):** Bead streams that overshoot and settle; breathing forms, colour fronts, bursts.
- **Hợp chủ đề (tags):** molecule, atom, popcorn, particles, explode, boil, gas, melt
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f2f8ff
- `a` #ffb030
- `b` #1d7fe6
- `c` #7cc4ff
- sân khấu đen + accent golden corn

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#7cc4ff`

## Luật nhịp

- **fps:** full
- **easing:** mượt, chậm vào chậm ra
- **bounce:** không
- **camera:** long lens, shallow focus, slow dolly drifting to square-on
- **cut_rule:** cắt lúc ánh sáng loé qua cạnh kính

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** tia sáng mảnh
- **circle:** vòng sáng mảnh
- **label:** nhãn chữ mảnh sáng

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, fade
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: glassy pads, soft bells, airy pulse · 96 BPM
- persona giọng: giọng trầm, rõ, chậm rãi như phim tài liệu khoa học
- thumbnail: một vật chủ đạo kiểu 3d swarm of tiny glass beads nổi giữa nền đen, accent golden corn trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D swarm of tiny glass beads — Polished glass seed beads, uneven sizes, bright glints, translucent far-side glow; soft warm window-style key top-left, bead-on-bead shadows
- video_motion: bead streams that overshoot and settle; breathing forms, colour fronts, bursts

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#23` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #23 Particle Swarm · Flat content made physical · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `glass` của engine three.js, block Flow ngắn tự viết
