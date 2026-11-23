# Vintage Comic Black (`vintage-comic-black`)

Truyện tranh cũ: một khung tranh giấy ngả vàng giữa sân khấu đen, mực viền dày, 4 màu phẳng + chấm Ben-Day cho tông giữa, bản màu lệch nhẹ; tiêu đề là hộp chú thích vàng, nhãn kết là bóng thoại; va chạm có tia tốc độ và trường năng lượng chấm đen.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** superhero, hero, villain, comic, cartoon, power, super, punch, fight, battle, rescue, strongest, fastest, vs, showdown, mutant
- **Nền đen tối thiểu:** 42% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải giấy toàn khung — giấy chỉ có trong khung tranh, quanh là đen
- không phải style `comic` cũ (chỉ kiểu chữ) — đây có khung, Ben-Day, bóng thoại
- không nhân vật siêu anh hùng có bản quyền
- không phải halftone CMYK (đây là màu phẳng + chấm một màu)

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #FFF6E0
- `a` #E62E2D
- `b` #1F6FD0
- `c` #FFD23A
- giấy kem + đỏ/xanh/vàng in 4 màu; ngoài khung tranh là đen

## Chữ (text_fx / thumbnail)

- font `Bangers-Regular.ttf` · cỡ 132 · IN HOA · vào bằng `pop` (7 frame) · số `#FFD23A`

## Luật nhịp

- **fps:** ones (30fps), va chạm giữ 2 frame
- **easing:** bounce — vào bằng nảy mạnh
- **bounce:** có
- **cut_rule:** cắt theo khung tranh: mỗi beat là một khung mới
- **rule:** nhãn kết luôn trong bóng thoại

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên khối mập viền mực
- **circle:** tia BAM răng cưa
- **label:** bóng thoại trắng / hộp chú thích vàng

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→impact, whoosh→whoosh, tick→click, ding→sting
- nhạc: surf-rock/brass anh hùng thập niên 60, 132 BPM · 132 BPM
- persona giọng: người dẫn truyện tranh kịch tính, nhấn từng câu như chữ BAM
- thumbnail: khung tranh giấy vàng trên nền đen, một nhân vật/vật với tia BAM + bóng thoại 2–3 từ

## Cho Flow (khi style này dùng clip Flow)

- image_style: Vintage comic book panel — A single aged-paper comic panel floating on pure black: thick black ink lines, four flat print colours with Ben-Day dot shading and slight colour-plate offset
- video_motion: punchy pops, speed lines on impact, held frames on hits

## Nguồn

- studio — engine html (looks.js + post2d.js, vòng 10) — engines/html/looks.js · engines/html/post2d.js (mã trong repo) @ `—` · license: mã của kênh; font OFL/Apache ghi ở docs/round10/H1.md
- lấy từ: bài tham khảo '10 Claude animation styles' (chỉ tên phong cách); kỹ thuật in tram/Bayer/rối bóng viết mới
- cách chuyển: look html mới (bút + hậu kỳ WebGL một pass) trên sân khấu đen; không chép mã/tài sản bên ngoài
