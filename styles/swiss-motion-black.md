# Swiss Motion Black (`swiss-motion-black`)

Kiểu chữ quốc tế (Swiss) bản đảo: nền đen, chữ và khối trắng ngà, MỘT màu tín hiệu đỏ; mọi thứ bám lưới, căn trái, tương phản cỡ cực lớn, chuyển động chính xác không nảy.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** numbers, rules, comparison, design, law, measurement, unit, record, percent, ratio
- **Nền đen tối thiểu:** 70% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải keynote (không gradient, glow, bóng)
- không phải kinetic typography (chữ không bay, xoay, nảy)
- không phải data-viz (khối là hình khối đồ hoạ, trừ khi lưới gán nghĩa)
- không phải Bauhaus (không trò chơi hình cơ bản 3 màu)
- không phải pictogram (ở đây chữ và lưới gánh hình)

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #F2F0EA
- `a` #E30613
- ĐẢO từ bản gốc giấy xám nhạt: nền đen, trắng ngà, một màu tín hiệu duy nhất — chỉ một thứ được mang màu đó

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 120 · chữ thường · vào bằng `type` (8 frame) · số `#E30613`

## Luật nhịp

- **fps:** ones, mượt — chính xác kiểu máy, không giật
- **easing:** chỉ hai đường cong: cubic-bezier(.7,0,.2,1) cho mọi cú 'snap'; tuyến tính cho nét đang vẽ và cho ngoại lệ
- **bounce:** không
- **enter:** wipe/clip-reveal, không bao giờ fade
- **delete:** nhát dao: một đường mảnh cắt qua rồi vật sập về đường giữa
- **beat:** snap bắt đầu sớm một nốt và ĐÁP đúng nhịp
- **cut_rule:** lia cứng đúng một cột/một trang

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** kẻ mảnh 1–2 px vẽ tuyến tính
- **circle:** không khoanh — đánh dấu bằng một đĩa đỏ nhỏ lệch lưới
- **label:** chữ đen in chồng trên khối đỏ

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→click, hit→thunk, whoosh→scrape, tick→tick, ding→snap
- nhạc: motorik/minimal techno, nhịp đều như lưới · 120 BPM
- persona giọng: giọng bảo tàng: chậm rãi, khẳng định, không cảm thán
- thumbnail: một chữ số khổng lồ căn trái + một đĩa đỏ + dòng chú thích mono nhỏ

## Cho Flow (khi style này dùng clip Flow)

- image_style: Swiss International Style graphic design — Strict modular grid, flush-left grotesque type with extreme scale contrast, flat off-white bars and blocks, exactly one red signal element, pure black background, no gradients or shadows
- video_motion: elements snap precisely onto the grid, wipes instead of fades, nothing bounces

## Nguồn

- lemo-opuscar — https://github.com/lemomo-ai/lemo-opuscar @ `3a7132b996be` · license: MIT cho mã; tài liệu chỉ đọc để hiểu, tự viết lại + ghi công
- lấy từ: styles/swiss-motion/STYLE.md (CC BY-NC 4.0) + demo (MIT)
- cách chuyển: đọc để hiểu ngữ pháp rồi tự viết lại bằng lời và mã của tool (không chép tài liệu/mã nguồn)
