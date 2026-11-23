# Pixel 16-bit Black (`pixel16-black`)

Pixel art 16-bit: cả khung hạ về lưới 1/5, lượng tử về bảng ≤ 48 màu sinh từ palette + Bayer dither, viền tối cùng tông; nền là trời sao + dải núi thị sai trôi liên tục; chữ font pixel có bóng đổ 1 khối.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** game, gaming, video-game, rpg, quest, level, boss, pixel, console, 16-bit, player, speedrun, dungeon, retro, nostalgia, controller
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không nhân vật game có bản quyền (Mario, Sonic…) — chỉ phong cách
- không phải 8-bit (đây nhiều màu hơn, có dither, viền cùng tông)
- không blur/glow — mọi cạnh là khối pixel

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #F7F1E3
- `a` #F2544B
- `b` #3D8BEF
- `c` #F9C846
- trắng kem + đỏ san hô + xanh SNES + vàng; mỗi màu thành dải 6 nấc sáng

## Chữ (text_fx / thumbnail)

- font `PixelifySans-Variable.ttf` · cỡ 120 · IN HOA · vào bằng `pop` (7 frame) · số `#F9C846`

## Luật nhịp

- **fps:** nội dung on 2s, nền thị sai on ones
- **easing:** out, chuyển động bám lưới pixel
- **bounce:** không
- **cut_rule:** cắt như qua màn chơi: khung mới trượt vào
- **rule:** không vật nào lệch khỏi lưới pixel

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên pixel
- **circle:** khung chọn pixel
- **label:** hộp thoại RPG viền đôi

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, glitch
- gói SFX (cue chung → âm): pop→pop, hit→hit, whoosh→whoosh_soft, tick→tick, ding→ting
- nhạc: chiptune 16-bit giai điệu RPG, 128 BPM · 128 BPM
- persona giọng: người kể chuyện game thủ, tươi, hơi tinh nghịch
- thumbnail: một sprite 16-bit thật to trên trời sao pixel, chữ pixel 2–3 từ có bóng

## Cho Flow (khi style này dùng clip Flow)

- image_style: 16-bit pixel art — Low-resolution 16-bit era pixel art with a limited palette, ordered dithering and dark same-hue outlines, on a pure black starfield
- video_motion: movement snaps to the pixel grid, parallax background layers

## Nguồn

- studio — engine html (looks.js + post2d.js, vòng 10) — engines/html/looks.js · engines/html/post2d.js (mã trong repo) @ `—` · license: mã của kênh; font OFL/Apache ghi ở docs/round10/H1.md
- lấy từ: bài tham khảo '10 Claude animation styles' (chỉ tên phong cách); kỹ thuật in tram/Bayer/rối bóng viết mới
- cách chuyển: look html mới (bút + hậu kỳ WebGL một pass) trên sân khấu đen; không chép mã/tài sản bên ngoài
