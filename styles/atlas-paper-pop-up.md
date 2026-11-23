# Paper Pop-Up · dark stage (`atlas-paper-pop-up`)

Biến thể dark-stage của style #02 "Paper Pop-Up" (Thế giới chất liệu) trong 3D Style Atlas: chuyện kể theo bước, mỗi trang mở một bước. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #02 Paper Pop-Up · nhóm Material worlds · tier 2 · brand_fit `adapted` · hợp kênh 3/5 · gần `papercraft3d-black` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** Stylized 3D pop-up paper book on a pure black stage (#000000): die-cut card layers, matt flat inks, cream fibre at cut edges, hinged folds. Single warm desk lamp top-left, layer-on-layer shadows, faint cool back rim. One accent colour (honey amber) only on the key element. Leave a blank paper ribbon across the bottom of the spread empty (captions are added later).
- **Block Flow (chuyển động):** Page turns only; old spread presses flat, next scene rises out of the fold.
- **Hợp chủ đề (tags):** story, fable, book, bee, honey, steps
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f5ecd9
- `a` #e8a33d
- `b` #22364e
- `c` #cbe0aa
- sân khấu đen + accent honey amber

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#cbe0aa`

## Luật nhịp

- **fps:** twos
- **easing:** gấp/mở như sách pop-up
- **bounce:** có
- **camera:** long lens down the book gutter (~25°), slow lateral drift, a breath per page turn
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
- thumbnail: một vật chủ đạo kiểu stylized 3d pop-up paper book nổi giữa nền đen, accent honey amber trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: Stylized 3D pop-up paper book — Die-cut card layers, matt flat inks, cream fibre at cut edges, hinged folds; single warm desk lamp top-left, layer-on-layer shadows, faint cool back rim
- video_motion: page turns only; old spread presses flat, next scene rises out of the fold

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#02` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #02 Paper Pop-Up · Material worlds · Story
- cách chuyển: dark-stage: nền #000, look 3D `paper` của engine three.js, block Flow ngắn tự viết
