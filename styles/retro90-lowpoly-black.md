# Retro 90s Low-poly 3D Black (`retro90-lowpoly-black`)

3D đa giác thời cuối thập niên 90 (kiểu console N64/PS1, tự dựng — không nhân vật có bản quyền) trên sân khấu đen: khối ít đỉnh nhưng đổ bóng Gouraud mượt theo đỉnh, texture vẽ bằng code độ phân giải thấp lọc mờ, màu bão hoà cam/xanh lá/xanh trời, không viền, render nội bộ thấp + dither 15-bit, bóng tròn dưới vật. Nhân vật con vật 3D có mặt vẽ trên texture + bối cảnh đảo cỏ nổi (meadow) tan vào đen.

- **Engine:** `three`
- **Hợp chủ đề (tags):** animal, animals, pet, pets, dog, puppy, cat, kitten, nostalgia, nostalgic, retro, 90s, gaming, game, videogame, console, childhood, nature, farm, zoo, cartoon, wildlife, meadow, garden, bird, fish, frog, rabbit, fox, dinosaur, horse, cow, pig, sheep
- **Nền đen tối thiểu:** 25% khung hình (QA đo)

## Nó KHÔNG phải là

- không low-poly hiện đại mặt phẳng gắt + nét viền (đó là lowpoly3d-black)
- không nền ban ngày chói sáng — giữ chất darkmode (nền tối sâu / bầu trời đêm chuyển sắc)
- không nhân vật game có bản quyền (Mario, Crash, Pikachu…) — chỉ phong cách thời 90, nhân vật tự dựng
- không ảnh thật, không người thật

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #080D16
- `ink` #FFF4DC
- `a` #FF8A2A
- `b` #3FA9F5
- `c` #FFD23F
- nền darkmode xanh đêm sâu #080D16 + kem sáng + cam console + xanh trời + vàng hoa — giữ chất darkmode của kênh nhưng có không gian/bầu trời đêm thời 90

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 122 · IN HOA · vào bằng `pop` (7 frame) · số `#FFD23F`

## Luật nhịp

- **fps:** full (30fps)
- **easing:** nảy tròn, hơi bậc kiểu game thời 90 (hop, squash nhẹ)
- **bounce:** có
- **camera:** camera bám nhân vật kiểu game 3D thời 90: orbit chậm + đẩy vào nhẹ
- **cut_rule:** cắt khi nhân vật xong một hành động nhỏ (hít, nhảy, vẫy đuôi)

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên khối đa giác màu vàng
- **circle:** vòng nhẫn xoay kiểu vật phẩm game
- **label:** biển gỗ/nhãn bo tròn chữ dày

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip, iris
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: chiptune-ish marimba + synth bass vui, giai điệu game phiêu lưu thời 90 (tự tổng hợp) · 118 BPM
- persona giọng: người kể chuyện ấm áp, tinh nghịch, hoài niệm tuổi thơ
- thumbnail: một chú chó low-poly cam đang hít bông hoa vàng trên đảo cỏ nổi giữa nền đen, ánh sáng mềm, mép đảo tan vào bóng tối

## Cho Flow (khi style này dùng clip Flow)

- image_style: Late-1990s console-era low-polygon 3D render — Chunky low-polygon models with smooth per-vertex (Gouraud) shading, small blurry hand-painted textures, saturated orange, grass-green and sky-blue colours, no outlines, slightly soft low-resolution image with subtle colour banding, a small floating grass island on a pure black void
- video_motion: bouncy game-like character animation, simple looping walk and hop cycles, gentle camera orbit

## Nguồn

- studio — engine three.js (look3d retro90) — https://github.com/mrdoob/three.js @ `r160` · license: MIT
- lấy từ: engines/three/main.js → LOOK3D.retro90 (Gouraud theo đỉnh + hậu kỳ retro) · engines/three/creatures.js · props.js setScene
- cách chuyển: tự viết shader Gouraud + pass lượng tử/Bayer dither/phóng ảnh cho three.js r160 (không chép mã ngoài); nhân vật sinh thủ tục từ bảng loài
