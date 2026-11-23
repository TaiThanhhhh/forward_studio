# Style bible — kênh "forward."

Nguồn: đo trực tiếp `assets/brand/avatar.png` (1024×1024) và xem `assets/brand/refs/*`.
Token máy đọc được nằm trong `brand/style.json`. Mọi prompt, text_fx, outro và thumbnail đều đọc màu từ file đó (chất liệu/chữ theo `styles/*.json`), không có màu viết tay ở chỗ khác.

## 1. Bảng màu

| Token | Hex | Dùng ở đâu |
|---|---|---|
| `bg` | `#000000` | Nền video và nền ảnh frame cho Flow. Avatar là `#110F10`, nhưng prompt đòi đen tuyệt đối để Flow không vẽ gradient. Khi ghép, mọi điểm ảnh tối hơn `#141414` coi như nền. |
| `ink` | `#FFFFFF` | Nét chính, chữ chính |
| `fill` | `#8A8A8A` | Mảng phụ, vật ở hậu cảnh |
| `accent` | `#1849F7` | **Xanh điện của avatar.** Một điểm nhấn duy nhất mỗi khung: vật quan trọng, viên pill của từ đang nói, chấm "điểm bắt đầu", thumbnail |
| `accent_glow` | `#3F6BFF` | Quầng sáng quanh accent và chữ xanh **cỡ lớn** (≥ 120 px) trên nền đen. Xanh gốc chỉ đạt 3,3:1 trên nền đen. |
| `danger` | `#FF2D2D` | **Chỉ** dùng cho bùng nổ, cảnh báo, vòng khoanh đỏ trên thumbnail |

Quy tắc: mỗi khung có tối đa **đen + trắng + xám + 1 màu** (xanh, hoặc đỏ khi nguy hiểm). Không gradient, không pastel, không texture.

## 2. Nét & hình khối

- Nét trắng dày đều, khoảng 4% cạnh ngắn của vật (avatar: 40 px trên 1024). Trong frame 9:16, nét của chủ thể chính dày khoảng 10–14 px trên 1080 px.
- Đầu nét **vuông**, góc vuông hoặc bo rất nhẹ. Hình học kiểu bậc thang/mạch điện, gọn và có chủ đích.
- Motif kênh là **chấm tròn xanh** đứng trước một đường trắng: "điểm bắt đầu tiến về phía trước". Dùng làm logo outro, dấu trang trí cho tag "THÍ NGHIỆM #n", và điểm nhấn trên thumbnail.
- Nhân vật 2D đơn giản, không bắt buộc stickman: đầu tròn, **mắt to** (hai chấm trắng có tròng) để đọc được cảm xúc, thân và tay chân là nét trắng, biểu cảm phóng đại. Vật thể và sơ đồ cũng theo cùng ngôn ngữ nét.
- Phong cách tham chiếu từ refs: Manim/3Blue1Brown (nét trắng trên nền đen tuyệt đối, một khối màu), choreography có easing rõ ràng.

## 3. Chuyển động

- Snappy: anticipation ngắn (2–3 frame), hành động nhanh, overshoot nhẹ, squash-and-stretch, smear frame ở cú chuyển động nhanh.
- Không trôi lờ đờ, không "settle" kéo dài ở cuối clip.
- Nền đứng yên tuyệt đối. Năng lượng nằm ở chủ thể.

## 4. Chữ

- Font: **Be Vietnam Pro** Black/ExtraBold (đủ dấu tiếng Việt), dự phòng Montserrat Black, cuối cùng là Inter. Font được nhúng sẵn trong `assets/fonts/`.
- Caption: chữ trắng, viền đen dày, bóng mềm. **Từ đang nói** nằm trong viên pill `accent` với chữ trắng (độ tương phản 6,3:1).
- Label minh hoạ: bộ đếm số, mũi tên, vòng khoanh, tag, so sánh `x1000`. Preset nằm ở `styles/*.json`.
- Chữ **không bao giờ** được để Flow vẽ. Mọi chữ đều thêm ở hậu kỳ.

## 5. Bố cục 9:16 (1080×1920)

- Chủ thể ở vùng giữa, hơi lệch lên trên, chiếm khoảng 55% khung.
- Ảnh frame cho Flow phải chừa trống **12% trên** và **30% dưới**. Trong 30% dưới thì 20% đáy là vùng UI của nền tảng, 10% còn lại là dải caption.
- Không đặt chữ ở 20% đáy và cột icon bên phải (x > 900 ở nửa dưới).
- Overlay safe-zone có trong chế độ preview. Số liệu nằm ở `config/channel.json → safe_zone`.
