# Flowchart Black (`flowchart-black`)

Infographic quy trình phẳng bản tối: băng tiêu đề hổ phách chữ gần đen rất đậm, huy hiệu số có mũi nhọn, mũi tên vòng cung đuôi trong suốt, bóng lệch không nhoè, vành đồng hồ thị sai ở nền; đọc từng trạm.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** process, steps, cause, chain, recipe, manufacturing, time, cycle, make, made, produce, become
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải sơ đồ kỹ thuật (blueprint)
- không phải pictogram (có chiều đọc theo trạm, có mũi tên)
- không hợp ý kiến/cảm xúc/chuyện người — chỉ cho thứ có TRƯỚC–SAU

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #FCF9EC
- `a` #FBBF2F
- `b` #D41928
- ĐẢO từ nền kem: đen + kem + hổ phách; đỏ chỉ cho một điểm nhấn

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 116 · chữ thường · vào bằng `pop` (7 frame) · số `#FBBF2F`

## Luật nhịp

- **fps:** ones
- **easing:** ease-out; huy hiệu bật
- **bounce:** có
- **camera:** đi từng trạm một, nền thị sai 0.5
- **rule:** một màn hình chỉ một chủ thể + một hộp chú giải
- **cut_rule:** cắt khi sang trạm kế

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** vòng cung gradient: đuôi trong suốt → đầu hổ phách
- **circle:** huy hiệu số tròn có mũi nhọn
- **label:** hộp hổ phách bo góc + đường dẫn mảnh

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: ukulele/pluck ấm, đều · 106 BPM
- persona giọng: người hướng dẫn kiên nhẫn, từng bước
- thumbnail: băng hổ phách + 3 huy hiệu số nối mũi tên

## Cho Flow (khi style này dùng clip Flow)

- image_style: Flat process infographic — Amber title band with very heavy near-black type, numbered amber badges, arc arrows fading from transparent to amber, flat shapes with offset un-blurred shadows, black ground
- video_motion: the view travels station by station, badges pop in, arrows draw toward the next step

## Nguồn

- dashi-animationstyle — https://github.com/chuspeeism/dashi-animationstyle @ `aa620f3b859a` · license: MIT
- lấy từ: styles/扁平流程图/风格卡.md + 模板.html (MIT)
- cách chuyển: port ý tưởng kỹ thuật từ mã MIT, viết lại thành module của engine html (không chạy repo gốc); bỏ toàn bộ xử lý chữ Trung, bố cục lại 9:16
