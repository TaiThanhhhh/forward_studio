# assets/user — ảnh, icon SVG, animation Lottie/Rive do BẠN đưa vào

Engine board không bao giờ tự tải ảnh người thật từ web. Video nhắc tới nhà khoa học thật (vd Leidenfrost):
- hoặc để tool **vẽ** chân dung tối giản (đoạn chèn `SILENT_FILM`, actor `figure`),
- hoặc tự tải ảnh **public domain** (Wikimedia Commons, Library of Congress) vào thư mục này, ghi nguồn + giấy phép vào
  `sources` của storyboard, rồi dùng trong shot:

```json
{"id": "C04", "beat": "setup", "vo": "…", "beat_recipe": "REVEAL_PHOTO",
 "board": {"image": "assets/user/leidenfrost_1756.jpg", "gray": true, "caption": "J. G. LEIDENFROST"}}
```

Shot chỉ có `board.image` (không có `start_frame`/`action`) không cần clip Flow. Không đưa logo/masthead báo đài vào đây.

## Icon SVG, Lottie, Rive (từ 18/11/2026)

Chỉ đưa file anh có quyền dùng thương mại (tự vẽ, mua, hoặc giấy phép cho phép như MIT/CC0) và ghi nguồn. Linter sẽ nhắc
nếu thiếu ghi chú.

| Loại | Đặt ở đâu | Gọi trong storyboard |
|---|---|---|
| Icon SVG | `python studio.py svg <file.svg> --name rocket --license "Lucide, ISC"` → `svg/rocket.json` | `"icon": "svg:rocket"` (mọi beat html) · `stage` prop `"type": "svg:rocket"` (khối 3D) |
| Lottie | `lottie/<tên>.json` (đổi màu theo style được) hoặc `.lottie`, kèm `lottie/<tên>.license.txt` | actor `scene`: `{"id": "a", "lottie": "<tên>", "x": 0.5, "y": 0.5, "size": 500, "colors": "palette", "speed": 1, "loop": true}` |
| Rive | `rive/<tên>.riv`, kèm `rive/<tên>.license.txt` | actor `scene`: `{"id": "a", "rive": "<tên>", "animation": "idle"}` hoặc `"state_machine": "<tên>"` |

`colors` của Lottie JSON: `palette` (mặc định: mỗi màu đổi sang vai gần nhất của style) · `hot`/`cold`/`accent`/`ink`
(tô một màu, giữ sáng tối) · `keep` (giữ màu gốc). File `.lottie` và Rive giữ màu gốc.
