# Flat Vector Black (`flat-vector-black`)

Vector phẳng trên nền đen: khối màu đặc không viền, hình học hoá, vào cảnh bằng nảy đàn hồi so le, mỗi lúc chỉ một vật chính chuyển động.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** body, human, sleep, eat, drink, brain, heart, blood, health, habit, daily, life, water, banana, diet, coffee
- **Nền đen tối thiểu:** 60% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải cắt giấy (không bóng giấy, mép thẳng tuyệt đối)
- không phải sticker explainer (không viền trắng, không camera lia trên canvas lớn)
- không phải Swiss (được nảy, được tròn, chữ căn giữa)
- không gradient, không glow, không nét viền

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #FFF6E9
- `a` #FF5A4E
- `b` #4B5BFF
- `c` #FFC62B
- kem + san hô (nóng) + xanh ultramarine (lạnh) + vàng hướng dương (nhấn)

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 128 · IN HOA · vào bằng `pop` (7 frame) · số `#FFC62B`

## Luật nhịp

- **fps:** ones (30fps)
- **easing:** overshoot kiểu cubic-bezier(0.34,1.56,0.64,1): lấy đà → vọt → nảy về
- **bounce:** có
- **stagger_frames:** 3
- **squash_stretch:** ≈10%
- **cut_rule:** cắt theo vật: một vật bay ra kéo theo cảnh mới
- **rule:** một lúc chỉ một vật chính chuyển động

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên đặc bo tròn, vọt ra rồi nảy
- **circle:** vòng tròn nét đặc vẽ 1 vòng
- **label:** viên thuốc màu, chữ đen

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thud, whoosh→whoosh, tick→click, ding→ding
- nhạc: future-bass/pop tươi, 120 BPM, pluck + clap · 120 BPM
- persona giọng: bạn thân tò mò, nhanh, cười trong giọng
- thumbnail: một vật phẳng thật to giữa khung đen + 2–3 từ chữ tròn đậm; tối đa 3 màu

## Cho Flow (khi style này dùng clip Flow)

- image_style: Flat 2D vector — Solid flat colour shapes with no outlines and no gradients, geometric simplified forms, cream/coral/ultramarine palette on pure black
- video_motion: elastic overshoot entrances, one hero element moving at a time, slight squash and stretch

## Nguồn

- mg-styles-15 — https://github.com/Vincentwei1021/mg-styles-15 @ `269f6ed788cf` · license: MIT
- lấy từ: demos/01-flat-vector + prompts/01-flat-vector.md
- cách chuyển: port ý tưởng kỹ thuật từ mã MIT, viết lại thành module của engine html (không chạy repo gốc)
