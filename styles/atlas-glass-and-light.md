# Glass and Light · dark stage (`atlas-glass-and-light`)

Biến thể dark-stage của style #15 "Glass and Light" (Thế giới chất liệu) trong 3D Style Atlas: pha trộn, tỉ lệ, hoá học, mật độ chất lỏng. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #15 Glass and Light · nhóm Material worlds · tier 1 · brand_fit `ok` · hợp kênh 5/5 · gần `glass3d-black`
- **Block Flow (ảnh):** 3D lab glassware still life on a pure black stage (#000000): thin refractive glass with heavy foot, liquids pale where thin and deep where thick. Back-lit bottle photography, glow behind, darkness above, white edge highlights. One accent colour (deep red) only on the key element. Leave blank white measure marks on the glass empty (captions are added later).
- **Block Flow (chuyển động):** Tilt and pour thin streams, levels rising to marks, layering, a hard shake.
- **Hợp chủ đề (tags):** liquid, chemistry, acid, density, reaction, dissolve, oil, mix
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #ffffff
- `a` #b8242f
- `b` #dcc82e
- `c` #f2cb66
- sân khấu đen + accent deep red

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#f2cb66`

## Luật nhịp

- **fps:** full
- **easing:** mượt, chậm vào chậm ra
- **bounce:** không
- **camera:** slow dolly from wide on the bottles to close on the mixing jar
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
- thumbnail: một vật chủ đạo kiểu 3d lab glassware still life nổi giữa nền đen, accent deep red trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D lab glassware still life — Thin refractive glass with heavy foot, liquids pale where thin and deep where thick; back-lit bottle photography, glow behind, darkness above, white edge highlights
- video_motion: tilt and pour thin streams, levels rising to marks, layering, a hard shake

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#15` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #15 Glass and Light · Material worlds · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `glass` của engine three.js, block Flow ngắn tự viết
