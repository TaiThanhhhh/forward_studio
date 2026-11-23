# 3D Style Atlas — phân tích và chuyển thành preset dark-stage

Nguồn: **3D Style Atlas** (Futurepedia / HubSpot Media, https://www.futurepedia.io/resources/3d-style-atlas/view), chụp
ngày 15/11/2026. 37 style, 7 nhóm. Bản gốc chỉ lưu cục bộ ở `vendor/3d-style-atlas/` (gitignore) vì điều khoản HubSpot
chỉ cho dùng cá nhân, phi thương mại (xem `vendor/3d-style-atlas/INDEX.md`). Mọi chữ trong preset là lời của tool;
`vidlib/atlas.py → check()` chặn mọi cụm 6 từ trùng nguyên văn với bản gốc.

Trạng thái chụp: metadata **37/37** + prompt toàn văn **37/37** (4,27 triệu ký tự, mỗi prompt khớp đúng tên style).
Từ mỗi prompt, `scripts/atlas_extract.py` rút STYLE CARD (Look, Motion, Light, Materials, Camera, Finish) + bảng màu hex
trong mã nguồn tham chiếu → `vendor/3d-style-atlas/cards/` (cục bộ). Mỗi preset (`config/atlas.json`) được viết lại theo
đúng thẻ + màu của chính style đó, dạng ghi chú sản xuất của tool; bộ kiểm chặn mọi cụm 6 từ trùng với prompt gốc.

## 1. Phần chung của 37 style

**Cấu trúc prompt (#01).** Mỗi prompt "Copy prompt" ~115 nghìn ký tự gồm: lời dặn ("làm motion graphic three.js theo
style này, xây lại quanh nội dung của tôi") → chỗ điền nội dung → **toàn bộ mã nguồn của cảnh mẫu** → **bộ kit render**
(dựng từng frame để xuất MP4) → **bộ kit âm thanh**. Tức là style được truyền bằng *mã*, không bằng mô tả. Tool này đã có
đủ ba phần đó (engine three.js + coderender + SFX tổng hợp), nên thứ cần lấy là *ngôn ngữ thị giác*, không phải mã.

**Vật liệu.** Gần như mọi style là "một chất liệu thật, nhất quán toàn cảnh": giấy bồi/giấy cắt (Paper Pop-Up, Shadow
Box, Embossed), đất nặn (Soft Clay), gỗ + đồng (Marble Run, Domino Chain, Toy Blocks), thuỷ tinh + chất lỏng (Glass and
Light, Layer Stack, Particle Swarm), kim loại (Pin Wall, Circuit City, Device Hero), nhựa/vinyl bóng (Inflated, Factory
Line), đá/thạch cao trắng (White Model, Data Skyline), ánh sáng tự phát (Neon Sign, LED Wall), hoặc **bộ lọc** biến cảnh 3D
thành chất liệu 2D (Painted, Ink and Toon, Pencil Sketch, Dithered, Voxel, Low-Poly, X-Ray).

**Ánh sáng.** Hai họ: (a) *studio sản phẩm* — softbox dải, rim lạnh, sàn gương/seamless (Exploded View, Studio Product,
Device Hero, Hero Icon); (b) *nguồn sáng nằm trong cảnh* — đèn sân khấu, neon, LED, đèn gallery, xung tín hiệu (Spotlight
Stage, Neon Sign, LED Wall, Museum Gallery, Circuit City). Họ (b) vốn đã tối → chuyển sang sân khấu đen gần như không mất
gì. Họ (a) chỉ cần đổi seamless trắng thành khoảng đen.

**Camera.** Một "cú máy" chủ đạo mỗi style: orbit chậm quanh mô hình (Diorama, White Model, Voxel), dolly dọc một tuyến
(Low-Poly, Circuit City, Museum, Domino), push qua các lớp (Shadow Box, Layer Stack), macro trượt (Glass, Embossed,
Studio Product). Không cắt cảnh giữa các beat — thay đổi xảy ra *trong* cảnh. Khớp với "một cú máy liền" của tool.

**Bảng màu.** Ít màu, **một accent dành cho điều quan trọng** (tháp đỏ son trong Data Skyline, domino cuối màu đỏ, amber
cho câu trả lời trong Layer Stack, accent duy nhất của White Model). Trùng đúng luật một accent của kênh.

**Chữ.** Luôn là *vật thể trong cảnh*: cờ giấy, ruy băng, biển, bảng đồng, thẻ easel, vạch đo trên thuỷ tinh, mặt domino,
lá split-flap. Không có phụ đề nổi. → Tool giữ nguyên tinh thần nhưng **AI không vẽ chữ**: prompt ảnh chỉ chừa mặt trống
(`flow.plate`), chữ do `text_fx` (neo vào vật) hoặc chữ 3D của engine.

**Nhịp.** Mỗi beat = một thay đổi vật lý gây ra beat sau (thứ gì đó sáng lên / đầy lên / đổ xuống / bật lên), có một dòng
chú thích ngắn. Đây chính là cấu trúc nhân quả của "What happens if…".

## 2. Cách chuyển sang preset của tool

- **Engine** (`config/atlas.json → engine`): `three` = dựng toàn bộ bằng engine three.js (chất liệu cần chính xác, có số/
  chữ, cơ chế lặp lại: Neon, Exploded View, Domino, Data Skyline, Split-Flap…); `hybrid` = clip Flow cho khoảnh khắc chất
  liệu thật (chất lỏng, vinyl, diorama) + three.js cho sơ đồ/số; `flow` = chỉ Flow (Painted, Monument Type — đều off-brand).
- **Look 3D**: map vào 9 preset `LOOK3D` có sẵn (`toon/clay/plastic/glass/chrome/lowpoly/paper/holo/xray`), ghi đè tham số
  khi cần (vd White Model = clay rough 0.95, Neon = holo bloom 0.85). Không thêm look mới ở vòng này.
- **Dark-stage**: nền `#000`, ánh key/rim tối, một accent (`palette.a`). `brand_fit`: `ok` (vốn tối) · `adapted` (đổi nền
  sáng → đen, vẫn nhận ra) · `off-brand` (bản sắc nằm ở nền sáng/hoàng hôn → bộ chọn tự động bỏ qua, chọn tay vẫn được).
- **Block Flow ngắn** (≤ 80 từ/block, tự viết): `image_style_block` (chất liệu + ánh sáng + accent + chỗ chừa chữ),
  `video_motion_block` (chuyển động + camera), `avoid_block`. Compiler ghép vào khung có sẵn: giữ `Audio: complete
  silence`, AVOID, ràng buộc khung đầu/cuối và reference. Không bao giờ dán prompt atlas vào Flow.
- **Phần còn lại** (kiểu chữ, world three.js, html, SFX, nhạc, giọng, thumbnail) kế thừa từ style 3D nền gần nhất
  (`base`), đổi palette.

## 3. Bảng 37 style

Hợp kênh 1–5 = hợp kênh "What happens if…" nền đen (thí nghiệm vật lý/hoá/sinh, số liệu, nhân quả).

<!-- atlas-table:begin -->
| # | Style | Nhóm | Engine | Look 3D | Hợp kênh | Tier | brand_fit | Trùng | Lý do |
|---|---|---|---|---|---|---|---|---|---|
| 01 | Low-Poly | Bộ lọc trên 3D | three | lowpoly | 4/5 | 2 | ok | lowpoly3d-black | Trùng lowpoly3d-black (đã có) → tier 2; nền đen giữ được vì mô hình nổi trong khoảng tối. |
| 02 | Paper Pop-Up | Thế giới chất liệu | hybrid | paper | 3/5 | 2 | adapted | papercraft3d-black | Gần papercraft3d-black; bàn gỗ ánh đèn mất khi đổi sang nền đen nhưng trang sách vẫn nhận ra. |
| 03 | Soft Clay | Thế giới chất liệu | hybrid | clay | 4/5 | 2 | ok | clay3d-black | Trùng clay3d-black → tier 2. |
| 04 | Tiny Diorama | Không gian và hành trình | hybrid | clay | 4/5 | 1 | adapted | — | Ô đất nổi trong khoảng đen hợp sân khấu đen tự nhiên; chưa có style nào kiểu diorama hành trình. |
| 05 | Blueprint Build | Sơ đồ có chiều sâu | three | holo | 3/5 | 2 | adapted | blueprint | Màu xanh bản vẽ là bản sắc; trên nền đen thành nét trắng → 'adapted'. Đã có style 2D blueprint. |
| 06 | Spotlight Stage | Không gian và hành trình | hybrid | paper | 3/5 | 2 | ok | — | Vốn là phòng tối → giữ bản sắc; kênh ít dùng dạng sân khấu kể chuyện → tier 2. |
| 07 | Neon Sign | Nội dung phẳng thành vật thật | three | holo | 5/5 | 1 | ok | neon | Tự nhiên là ánh sáng trên nền tối, hợp điện/nhiệt/ánh sáng của kênh; bản 3D mạnh hơn style 2D 'neon'. |
| 08 | Exploded View | Sơ đồ có chiều sâu | three | plastic | 5/5 | 1 | adapted | — | Sàn sáng gốc đổi sang khoảng đen vẫn đọc rõ; 'bên trong X' là dạng ý tưởng hay của kênh. |
| 09 | Marble Run | Cỗ máy giải thích | three | plastic | 3/5 | 2 | ok | — | Hợp nền tối; chủ đề phân loại ít gặp ở kênh thí nghiệm → tier 2. |
| 10 | X-Ray | Bộ lọc trên 3D | three | xray | 5/5 | 1 | ok | xray3d-black | Vốn nền tối, accent ấm duy nhất = luật một màu của kênh. Gộp thông số vào xray3d-black (bản tier 1 thêm accent ấm). |
| 11 | LED Wall | Nội dung phẳng thành vật thật | three | holo | 3/5 | 2 | ok | — | Nền đêm giữ được; ít hợp thí nghiệm vật lý → tier 2. |
| 12 | Inflated | Thế giới chất liệu | hybrid | plastic | 4/5 | 1 | adapted | plastic-toy3d-black | Phòng chụp sáng một màu mất khi đổi nền đen ('adapted') nhưng độ căng phồng mang nghĩa — rất hợp thí nghiệm áp suất. |
| 13 | Painted | Bộ lọc trên 3D | flow | toon | 2/5 | 2 | off-brand | gallery-pointillist-black | Bản sắc là ánh hoàng hôn trên vải toan sáng → mất khi về nền đen: off-brand (chỉ chọn tay). |
| 14 | Circuit City | Không gian và hành trình | hybrid | chrome | 4/5 | 1 | ok | — | Vốn là cảnh đêm; mảng công nghệ của kênh chưa có cảnh 3D thành phố mạch. |
| 15 | Glass and Light | Thế giới chất liệu | hybrid | glass | 5/5 | 1 | ok | glass3d-black | Thí nghiệm hoá học là lõi của kênh; ánh sáng xuyên chất lỏng trên nền tối rất mạnh. Nâng cấp glass3d-black. |
| 16 | Factory Line | Cỗ máy giải thích | three | plastic | 3/5 | 2 | adapted | — | Sàn sáng gốc → nền đen; hợp quy trình nhưng ít hợp thí nghiệm → tier 2. |
| 17 | White Model | Sơ đồ có chiều sâu | three | clay | 4/5 | 1 | adapted | — | Mô hình trắng trên sân khấu đen rất nổi; luật một accent trùng luật kênh. |
| 18 | Voxel | Bộ lọc trên 3D | three | lowpoly | 3/5 | 2 | ok | lowpoly3d-black | Gần lowpoly3d-black → tier 2. |
| 19 | Data Skyline | Sơ đồ có chiều sâu | three | clay | 4/5 | 1 | adapted | scale-zoom-black | Số liệu là nửa còn lại của mỗi video kênh; dạng tháp đếm được hợp shot payoff. |
| 20 | Ink and Toon | Bộ lọc trên 3D | three | toon | 4/5 | 2 | adapted | toon3d-lab | Trùng toon3d-lab (đã là style 3D gốc của kênh) → tier 2; giấy ấm gốc mất khi về nền đen. |
| 21 | Pin Wall | Nội dung phẳng thành vật thật | three | chrome | 4/5 | 1 | ok | — | Khung tối + ghim kim loại hợp nền đen; núi lửa/sóng/động đất là chủ đề 'what happens if' quen. |
| 22 | Toy Blocks | Thế giới chất liệu | hybrid | clay | 2/5 | 2 | off-brand | — | Bản sắc là phòng chơi nắng ấm → off-brand trên nền đen (chỉ chọn tay). |
| 23 | Particle Swarm | Nội dung phẳng thành vật thật | three | glass | 5/5 | 1 | adapted | — | Vách giấy sáng gốc → nền đen ('adapted'); hạt nóng lên/bung ra = đúng ngôn ngữ thí nghiệm nhiệt của kênh. |
| 24 | Museum Gallery | Không gian và hành trình | hybrid | plastic | 3/5 | 2 | ok | — | Phòng tối giữ bản sắc; dòng thời gian ít gặp ở kênh → tier 2. |
| 25 | Pencil Sketch | Bộ lọc trên 3D | three | toon | 2/5 | 2 | off-brand | sketchnote-black | Giấy vẽ trắng là bản sắc → off-brand; nền đen đã có chalk/sketchnote. |
| 26 | Domino Chain | Cỗ máy giải thích | three | plastic | 4/5 | 1 | ok | — | Nhân quả + 'cứ thế nhân lên' là cốt của 'what happens if'; nền gỗ tối hợp sân khấu đen. |
| 27 | Node Network | Sơ đồ có chiều sâu | three | plastic | 3/5 | 2 | ok | flowchart-black | Gần flowchart-black (2D) → tier 2. |
| 28 | Shadow Box | Nội dung phẳng thành vật thật | three | paper | 3/5 | 2 | ok | papercraft3d-black | Ánh sáng ấm sau lưng trên nền tối giữ bản sắc; gần papercraft3d-black → tier 2. |
| 29 | Layer Stack | Sơ đồ có chiều sâu | three | glass | 3/5 | 2 | ok | — | Vốn gần đen; hợp lớp khí quyển/vỏ Trái Đất nhưng chủ đề hẹp → tier 2. |
| 30 | Dithered | Bộ lọc trên 3D | three | toon | 3/5 | 2 | ok | — | 1-bit = đen + một màu, hợp luật kênh; cần shader dither riêng (chưa có) → tier 2. |
| 31 | Floating Screens | Sản phẩm và màn hình | three | glass | 1/5 | 2 | off-brand | — | Phòng sáng ấm là bản sắc + chủ đề app không phải mảng kênh → off-brand. |
| 32 | Device Hero | Sản phẩm và màn hình | hybrid | chrome | 3/5 | 2 | ok | chrome3d-black | Studio tối giữ bản sắc; hợp ý tưởng 'thả điện thoại vào X' nhưng hẹp → tier 2. |
| 33 | Studio Product | Sản phẩm và màn hình | hybrid | chrome | 4/5 | 1 | ok | chrome3d-black | Studio gần đen sẵn; 'thử độ bền một vật' là dạng thí nghiệm hay của kênh. |
| 34 | Split-Flap Board | Nội dung phẳng thành vật thật | three | plastic | 4/5 | 1 | ok | — | Hợp dạng kịch bản đếm ngược; chữ do engine/text_fx vẽ, không để AI vẽ. |
| 35 | Hero Icon | Sản phẩm và màn hình | three | plastic | 1/5 | 2 | off-brand | plastic-toy3d-black | Phòng chụp sáng một màu + chủ đề thương hiệu app → off-brand. |
| 36 | Embossed | Nội dung phẳng thành vật thật | three | paper | 2/5 | 2 | adapted | — | Giấy sáng trên bàn ép tối → 'adapted'; chỉ hợp thẻ tiêu đề → tier 2. |
| 37 | Monument Type | Không gian và hành trình | flow | clay | 2/5 | 2 | off-brand | — | Hoàng hôn trên mặt muối là bản sắc → off-brand. |
<!-- atlas-table:end -->

## 4. Tier 1 (14 style) — vì sao

Chọn theo: hợp kênh ≥ 4, **mang thứ mới** (không trùng style đã có, hoặc nâng cấp rõ), phủ đủ 7 nhóm. Ghi ở
`docs/DECISIONS.md` D-004.

| Nhóm | Tier 1 |
|---|---|
| Nội dung phẳng thành vật thật | Neon Sign · Particle Swarm · Pin Wall · Split-Flap Board |
| Cỗ máy giải thích | Domino Chain |
| Thế giới chất liệu | Glass and Light · Inflated |
| Sản phẩm và màn hình | Studio Product |
| Sơ đồ có chiều sâu | Exploded View · White Model · Data Skyline |
| Không gian và hành trình | Tiny Diorama · Circuit City |
| Bộ lọc trên 3D | X-Ray |

Không vào tier 1 dù hợp kênh 4: Low-Poly, Soft Clay, Ink and Toon — đã có `lowpoly3d-black`, `clay3d-black`,
`toon3d-lab` gần như y hệt.

**Off-brand (6):** Painted, Toy Blocks, Pencil Sketch, Floating Screens, Hero Icon, Monument Type.
