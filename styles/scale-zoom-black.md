# Scale Zoom Black (`scale-zoom-black`)

Giải thích bằng thang kích thước: vật phẳng đặc trên nền đêm, đúng tỉ lệ trong từng khung; camera lao qua các bậc theo thang log; vòng 'điểm dừng kế tiếp' vàng + đường ngắm chấm; quầng sáng là hai vành đặc.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** size, scale, big, small, huge, tiny, giant, space, atom, distance, how-big, how-small, planet, micro, galaxy, black-hole, universe, cell, moon, sun, earth, star, mars, jupiter
- **Nền đen tối thiểu:** 60% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải isometric (không phép chiếu, không diorama)
- không phải data storytelling (không biểu đồ trên giấy)
- không phải HUD (không wireframe phát sáng)
- không phải 3D mềm (không rim light, bloom, DOF)
- không blur, không gradient, không trong suốt

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #F4F1E8
- `a` #FFD23F
- `b` #5AC8FA
- `c` #FF6B4A
- kem + vàng mặt trời (vòng điểm dừng) + xanh (lạnh) + đỏ cam (nóng)

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 120 · chữ thường · vào bằng `pop` (7 frame) · số `#FFD23F`

## Luật nhịp

- **fps:** ones — camera chuyển động mọi frame
- **easing:** vòng khoá bằng lò xo (một lần vượt); chấm đường ngắm bật 0 → 1.3 → 1 từng cái
- **bounce:** có
- **rule:** trong một khung mọi vật cùng một tỉ lệ; dải thang log ở góc đọc từ cùng camera
- **never_moves:** phụ đề đã đáp và vị trí dải thang
- **cut_rule:** không cắt giữa các bậc: zoom liên tục

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** đường ngắm chấm
- **circle:** vòng vàng + vòng ngoài nét đứt xoay chậm
- **label:** nhãn hai dòng: tên + kích thước mono

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut
- gói SFX (cue chung → âm): pop→pop, hit→thud, whoosh→whoosh, tick→tick, ding→ding
- nhạc: ambient rộng + pluck khi tới mỗi bậc · 96 BPM
- persona giọng: hướng dẫn viên thiên văn ngạc nhiên vừa đủ
- thumbnail: hai vật cùng tỉ lệ cạnh nhau (to/nhỏ) + vòng vàng + '×1,000'

## Cho Flow (khi style này dùng clip Flow)

- image_style: Flat scale-comparison illustration — Flat opaque shapes with at most one shade step, glow drawn as two hard concentric rings, a yellow dashed target ring, objects drawn to true scale on a black night ground
- video_motion: continuous logarithmic zoom from one scale to the next, a dotted sight line pops out toward the next stop

## Nguồn

- lemo-opuscar — https://github.com/lemomo-ai/lemo-opuscar @ `3a7132b996be` · license: MIT cho mã; tài liệu chỉ đọc để hiểu, tự viết lại + ghi công
- lấy từ: styles/flat-space-explainer/STYLE.md — 'Scale Zoom Explainer' (CC BY-NC 4.0)
- cách chuyển: đọc để hiểu ngữ pháp rồi tự viết lại bằng lời và mã của tool (không chép tài liệu/mã nguồn); luật camera 'đi giữa các thang' đối chiếu thêm với grammar y1 của huashu-art-motion
