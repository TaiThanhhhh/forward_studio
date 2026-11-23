# X-ray 3D Black (`xray3d-black`)

Quét X-quang 3D trên nền đen: vật thể bán trong suốt chỉ sáng ở viền (fresnel), cộng sáng, bloom, hạt phim — nhìn xuyên vào cơ thể/vật. Toàn bộ bằng code.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** body, heart, lungs, brain, bone, skeleton, blood, organ, disease, medicine, hospital, doctor, inside, x-ray
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không ảnh X-quang y tế thật
- không máu me (chỉ ánh sáng viền)
- không nền (đen #000000)

## Bảng màu (nền đen + tối đa 2–3 màu)

- `ink` #E6F7FF
- `a` #49C6FF
- `b` #FF4D5E
- `c` #FFE08A
- `bg` #000000

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#FFE08A`

## Luật nhịp

- **fps:** full
- **easing:** mượt, nhịp tim
- **bounce:** không
- **camera:** quét xuyên lớp
- **cut_rule:** cắt theo nhịp tim

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên sáng mảnh
- **circle:** vòng quét đỏ
- **label:** nhãn y khoa mảnh

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, fade
- gói SFX (cue chung → âm): pop→pop, hit→heartbeat, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: heartbeat pulse, soft drones, clinical blips · 88 BPM
- persona giọng: giọng bác sĩ điềm tĩnh, rõ ràng
- thumbnail: một cơ quan/vật thể trong suốt sáng viền cyan giữa nền đen, một điểm đỏ phát sáng

## Cho Flow (khi style này dùng clip Flow)

- image_style: Stylized 3D x-ray scan render — Translucent objects glowing only at their silhouettes (fresnel rim), additive cyan light, red highlight on the key organ or part, film grain, pure black background
- video_motion: slow scanning sweeps, gentle pulsing, push-ins through layers

## Nguồn

- studio — engine three.js (look3d) — https://github.com/mrdoob/three.js @ `None` · license: MIT
- lấy từ: engines/three/main.js → LOOK3D (chất liệu + env map studio + hậu kỳ ACES/bloom/grain)
- cách chuyển: preset chất liệu 3D của engine three.js trên sân khấu đen; prompt Flow 3D cùng look cho ngày có Flow
