# Glass 3D Black (`glass3d-black`)

Kính mờ / pha lê 3D trên nền đen: vật thể trong suốt khúc xạ, cạnh sáng fresnel, dải rim màu cyan-hồng, bloom nhẹ. Toàn bộ bằng code (three.js MeshPhysicalMaterial transmission).

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** water, ice, glass, crystal, light, prism, lens, liquid, transparent, drink, bottle, diamond, bubble
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải kính thật chụp ảnh
- không nền gradient (nền đen #000000)
- không vật đục mờ không trong suốt

## Bảng màu (nền đen + tối đa 2–3 màu)

- `ink` #EAF6FF
- `a` #7FD8FF
- `b` #FF7AC8
- `c` #C9B8FF
- `bg` #000000

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#C9B8FF`

## Luật nhịp

- **fps:** full
- **easing:** mượt, chậm vào chậm ra
- **bounce:** không
- **camera:** quay chậm quanh vật
- **cut_rule:** cắt lúc ánh sáng loé qua cạnh kính

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** tia sáng mảnh
- **circle:** vòng sáng mảnh
- **label:** nhãn chữ mảnh sáng

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, fade
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: glassy pads, soft bells, airy pulse · 96 BPM
- persona giọng: giọng trầm, rõ, chậm rãi như phim tài liệu khoa học
- thumbnail: một vật pha lê khúc xạ ánh sáng cyan-hồng giữa nền đen, cạnh sáng rực

## Cho Flow (khi style này dùng clip Flow)

- image_style: Stylized 3D glass render — Frosted and clear glass objects with refraction, bright fresnel edges, cyan and pink rim light strips, soft bloom, floating in pure black space
- video_motion: slow elegant rotations, smooth push-ins, liquid easing

## Nguồn

- studio — engine three.js (look3d) — https://github.com/mrdoob/three.js @ `None` · license: MIT
- lấy từ: engines/three/main.js → LOOK3D (chất liệu + env map studio + hậu kỳ ACES/bloom/grain)
- cách chuyển: preset chất liệu 3D của engine three.js trên sân khấu đen; prompt Flow 3D cùng look cho ngày có Flow
