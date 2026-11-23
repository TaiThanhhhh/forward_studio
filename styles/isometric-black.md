# Isometric Black (`isometric-black`)

Thế giới thu nhỏ 2.5D trên sân khấu tối: sàn lưới đẳng trục không điểm tụ, bục và cột là lăng trụ 'mọc' lên, camera chỉ trượt song song.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** city, machine, system, energy, data, engineering, building, factory, power, grid, traffic, network
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải 3D phối cảnh (toon3d-lab): không điểm tụ, camera không xoay
- không phải flat vector: mọi khối có mặt trên + 2 mặt bên
- không phải sơ đồ kỹ thuật blueprint

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #E9EDF5
- `a` #FF8A65
- `b` #5DE6B1
- `c` #9B8CFF
- trắng lạnh + cam đào (nóng) + bạc hà (lạnh) + oải hương (nhấn)

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 120 · IN HOA · vào bằng `pop` (7 frame) · số `#5DE6B1`

## Luật nhịp

- **fps:** ones
- **easing:** khối mọc: đáy đáp trước, thân kéo scaleY từ 0 có vượt, nắp đậy trễ 2–3 frame
- **bounce:** có
- **stagger_frames:** 3
- **camera:** trượt song song, thị sai 1 : 0.8 : 0.6, không xoay
- **cut_rule:** cắt khi sóng ô sàn lật qua

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên nằm trên mặt sàn đẳng trục
- **circle:** vòng nhấn nét đặc
- **label:** chữ đậm phía trên khối

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→click, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: pluck FM/marimba sáng, công nghệ · 110 BPM
- persona giọng: kỹ sư trẻ hào hứng, rõ ràng
- thumbnail: một khối đẳng trục phát sáng trên sàn lưới tối, số to phía trên

## Cho Flow (khi style này dùng clip Flow)

- image_style: Isometric 2.5D illustration — True isometric projection with no vanishing point, miniature objects as extruded prisms with a lighter top face and two darker side faces, dark stage with a faint isometric grid floor
- video_motion: objects grow upward from the floor with a small overshoot, camera only slides in parallel, never rotates

## Nguồn

- mg-styles-15 — https://github.com/Vincentwei1021/mg-styles-15 @ `269f6ed788cf` · license: MIT
- lấy từ: demos/03-isometric + prompts/03-isometric.md
- cách chuyển: port ý tưởng kỹ thuật từ mã MIT, viết lại thành module của engine html (không chạy repo gốc)
