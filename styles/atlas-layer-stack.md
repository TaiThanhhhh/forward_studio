# Layer Stack · dark stage (`atlas-layer-stack`)

Biến thể dark-stage của style #29 "Layer Stack" (Sơ đồ có chiều sâu) trong 3D Style Atlas: thứ cấu tạo theo lớp. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #29 Layer Stack · nhóm Diagrams with depth · tier 2 · brand_fit `ok` · hợp kênh 3/5 · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D stack of edge-lit glass sheets on a pure black stage (#000000): frosted glass sheets with aqua edges and white print over dark anodised metal. Small high back key, sheet-to-sheet shadows, cool rim, black surround. One accent colour (amber) only on the key element. Leave blank space beside each sheet for its name empty (captions are added later).
- **Block Flow (chuyển động):** Closed block opens sheet by sheet; a glowing bead then falls through the layers.
- **Hợp chủ đề (tags):** layers, stack, atmosphere, crust, tech-stack
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #ffffff
- `a` #ff9426
- `b` #8fded4
- `c` #8d8d8d
- sân khấu đen + accent amber

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#8d8d8d`

## Luật nhịp

- **fps:** full
- **easing:** mượt, chậm vào chậm ra
- **bounce:** không
- **camera:** long lens high three-quarter, rise with the first sheet, then a slow push
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
- thumbnail: một vật chủ đạo kiểu 3d stack of edge-lit glass sheets nổi giữa nền đen, accent amber trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D stack of edge-lit glass sheets — Frosted glass sheets with aqua edges and white print over dark anodised metal; small high back key, sheet-to-sheet shadows, cool rim, black surround
- video_motion: closed block opens sheet by sheet; a glowing bead then falls through the layers

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#29` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #29 Layer Stack · Diagrams with depth · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `glass` của engine three.js, block Flow ngắn tự viết
