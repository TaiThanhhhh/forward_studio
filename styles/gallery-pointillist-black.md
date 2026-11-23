# Gallery Pointillist Black (`gallery-pointillist-black`)

Tranh lồng khung: cảnh thí nghiệm được chấm lại bằng nét cọ điểm màu (pointillism, tông đêm) bên trong MỘT khung tranh treo trên tường đen; chữ là nhãn bảo tàng sắc nét bên ngoài lớp sơn. Phong cách hội hoạ không bao giờ phủ kín khung hình.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** art, color, light, painting, optics, perception, rainbow, prism, sunset, vision, aurora, firework, bioluminescence, night-sky, glow
- **Nền đen tối thiểu:** 40% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải nền hội hoạ toàn khung — tranh luôn nằm trong khung treo trên tường đen
- không sao chép một bức tranh có thật
- không phải line-boil/sketchnote: hình là CHẤM MÀU, không có nét viền

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #F3EDE0
- `a` #FF8A3C
- `b` #4FA3E0
- `c` #F2D15C
- trong tranh: cam/xanh/vàng chấm cạnh nhau trên nền đêm; ngoài tranh: chỉ đen + kem

## Chữ (text_fx / thumbnail)

- font `Caladea-Bold.ttf` · cỡ 108 · chữ thường · vào bằng `write_on` (12 frame) · số `#F2D15C`

## Luật nhịp

- **fps:** lớp sơn on twos (chấm đổi mỗi 2 frame); chữ on ones
- **easing:** smootherstep, chậm
- **bounce:** không
- **cut_rule:** cắt chậm, như bước sang bức kế trong phòng tranh

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** không mũi tên trong tranh — chỉ nhãn bảo tàng
- **circle:** không khoanh
- **label:** nhãn bảo tàng: chữ kem viền đen

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, fade
- gói SFX (cue chung → âm): pop→ting, hit→thud, whoosh→whoosh_soft, tick→tick, ding→sparkle
- nhạc: piano ấn tượng chậm, vang phòng tranh · 84 BPM
- persona giọng: giám tuyển thì thầm trong phòng tranh
- thumbnail: bức tranh chấm màu trong khung gỗ trên tường đen + nhãn bảo tàng 2–3 từ

## Cho Flow (khi style này dùng clip Flow)

- image_style: Framed pointillist painting on a black gallery wall — A single framed painting made of small dabs of pure colour in a night palette, hung on a pure black wall with a small museum label, the painting never fills the frame
- video_motion: the dabs shimmer slightly, slow push toward the frame

## Nguồn

- huashu-art-motion — https://github.com/alchaincyf/huashu-art-motion @ `1468196505a5` · license: MIT cho mã/ngữ pháp; không dùng tài sản nhân vật
- lấy từ: references/风格配方 (cách 'một era = một hàm vẽ'), 29_seurat (MIT)
- cách chuyển: chỉ lấy ý tưởng 'cảnh → lớp chất liệu hội hoạ'; bộ chấm màu viết mới; KHÔNG dùng ảnh nhân vật Huashu, frame library hay clip Clawd
