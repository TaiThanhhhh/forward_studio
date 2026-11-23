# DECISIONS — các quyết định tự đưa ra trong lượt chạy không người (vòng 8 + 9 + UI)

Mỗi mục: bối cảnh → các lựa chọn → đã chọn → vì sao.

## D-001 · Branch gốc
- Bối cảnh: repo đang ở `feat/one-command-pipeline` (sạch, d7597eb), `main` là nhánh PR.
- Lựa chọn: tách từ `main` · tách từ `feat/one-command-pipeline`.
- Đã chọn: tách từ `feat/one-command-pipeline`.
- Vì sao: toàn bộ vòng 1–7 nằm ở nhánh này; `main` cũ hơn. Không merge, không push.

## D-002 · Tab Futurepedia
- Bối cảnh: tab anh mở sẵn không thấy được từ nhóm tab của phiên này (Claude in Chrome chỉ điều khiển tab trong nhóm MCP).
- Lựa chọn: dừng chờ · mở đúng URL đó trong một tab của nhóm MCP.
- Đã chọn: mở đúng URL trong tab nhóm MCP (không đi trang nào khác của site).
- Vì sao: giữ đúng tinh thần "chỉ trang Futurepedia đó"; không đăng nhập, không bấm gì.

## D-003 · Phần A khi trang bị Cloudflare chặn
- Bối cảnh: trang hiện ô "Verify you are human"; luật cấm vượt CAPTCHA và cấm bịa prompt.
- Lựa chọn: (a) bỏ hẳn phần A · (b) dựng hạ tầng nhập + công cụ chụp để anh chạy, dữ liệu thật vào sau · (c) tự viết 37 style "giống atlas".
- Đã chọn: (b). Thử tải lại trang một lần nữa sau Phần B.
- Vì sao: (c) là bịa nội dung — cấm. (b) để khi có dữ liệu thật chỉ cần một lệnh là ra 37 preset + dark-stage + tier,
  đúng nguyên tắc "làm tổng quát, không one-off". Phần C dùng 3 style 3D có sẵn (khác nhóm look) thay cho 3 style atlas.

## D-004 · Cách lấy prompt Atlas khi Chrome không cho ghi clipboard
- Bối cảnh: (1) tab Atlas qua được Cloudflare khi anh có mặt; (2) prompt mỗi style ~115 nghìn ký tự — không thể đi qua
  khung chat; (3) fetch từ trang về 127.0.0.1 bị Chrome Local Network Access chặn; (4) Clipboard API chỉ ghi khi tab đang
  focus — anh vắng, cửa sổ khác ở trước → chỉ lấy được prompt #01 (lúc anh còn ở máy); (5) tải file từ trang cần anh cho
  phép.
- Lựa chọn: vượt chặn LNA / tự bấm cấp quyền (không được) · tải file (cần phép) · gọi API riêng của site (khác cách anh
  giao, giống bot) · lấy metadata 37/37 qua DOM + prompt #01, còn lại `incomplete`, để sẵn script anh chạy.
- Đã chọn: cách cuối. `scripts/atlas_capture.js` chạy trong DevTools (anh tự chạy, ~2 phút) → `atlas-capture.json` →
  `scripts/atlas_import.py --from …`.
- Vì sao: đúng luật "không tự bịa prompt", không vượt rào trình duyệt; phân tích/tier/preset dựa trên metadata là đủ
  (style truyền ý tưởng qua mô tả + mã; tool đã có engine riêng nên không cần mã của atlas).

## D-005 · Bản gốc Atlas không vào git
- Bối cảnh: HubSpot Website Terms of Use (14/04/2026): chỉ dùng cá nhân, phi thương mại; cấm sao chép, tạo tác phẩm
  phái sinh, phân phối.
- Đã chọn: `vendor/3d-style-atlas/raw/` + `shots/` gitignore; preset là lời + mã của tool; `vidlib/atlas.check()` chặn
  mọi cụm 6 từ trùng nguyên văn (đã bắt và viết lại 18 cụm lỡ trùng trong bản nháp đầu).
- Vì sao: giảm rủi ro khi repo được push/chia sẻ; quyết định dùng thương mại để anh chốt (mục "Cần anh quyết định").

## D-006 · Tier 1 = 14 style
- Tiêu chí: hợp kênh ≥ 4/5, không trùng style đã có (hoặc nâng cấp rõ), phủ đủ 7 nhóm, không off-brand.
- Đã chọn: Neon Sign, Particle Swarm, Pin Wall, Split-Flap Board, Domino Chain, Glass and Light, Inflated, Studio Product,
  Exploded View, White Model, Data Skyline, Tiny Diorama, Circuit City, X-Ray.
- Bỏ ra tier 2 dù hợp kênh 4: Low-Poly, Soft Clay, Ink and Toon (đã có `lowpoly3d-black`, `clay3d-black`, `toon3d-lab`).

## D-007 · Tier 2 không vào vòng chọn tự động
- Bối cảnh: anh yêu cầu bộ chọn bỏ off-brand; tier 2 chưa nói. Thêm 31 style một lúc làm loãng vòng xoay và chưa soát
  hình từng style.
- Đã chọn: `config/atlas.json → auto_tiers: [1]` — tier 1 vào vòng tự động (chống lặp 3 video vẫn tính), tier 2 + off-brand
  chỉ chọn tay (`--style atlas-…`). Đổi bằng một dòng config.

## D-008 · Look 3D: dùng 9 preset có sẵn, không thêm look mới vòng này
- Mỗi style atlas map vào `toon/clay/plastic/glass/chrome/lowpoly/paper/holo/xray` + ghi đè tham số (vd White Model = clay
  rough 0.95). Look riêng còn thiếu (dither 1-bit, hatching bút chì, sơn dầu, LED/pin instancing) ghi ở ROADMAP_V2.

## D-004b · Lấy đủ 37 prompt khi anh có mặt
- Bối cảnh: anh hỏi vì sao chỉ có 1/37 prompt. Nguyên nhân thật: extension Claude in Chrome của phiên này đang nối với một
  Chrome trên **macOS** ("Browser 1"), không phải Chrome trên máy Windows → tab, clipboard và tải file đều nằm bên máy đó.
- Đã làm: anh chọn kết nối lại (switch_browser) → Chrome "DESKTOP-08UA6S3" trên máy này; chụp lại 37/37 (hook Clipboard.write
  trong trang, mở từng thẻ, nghỉ ~1,5 s), rồi một cú bấm thật chép cả danh sách vào clipboard → `scripts/atlas_clip_save.py`.
  Hook đã tự gỡ, hàm gốc kiểm `[native code]`, tab đã đóng.
- Kết quả: 37 file raw, mỗi prompt khớp đúng tên style; preset viết lại theo STYLE CARD + màu của từng style.

## D-009 · Safe zone: đỉnh/cạnh theo union, đáy giữ kiểu Shorts (chờ anh quyết)
- Bối cảnh: Meta (Reels) khuyên tránh 35% đáy (y > 1248); dải chữ chính của kênh là 1150–1450.
- Đã làm: top 220 → 270, lề 60 → 65 (đạt Shorts/TikTok, đỉnh/cạnh Reels). Đáy giữ nguyên → preset Reels báo VÀNG.
- Lựa chọn cho anh: (a) giữ (ưu tiên bố cục Shorts) · (b) dời `caption_band` lên ~[960, 1240] cho mọi video (an toàn cả
  Reels, chữ gần chủ thể hơn) · (c) render riêng bản Reels với dải chữ cao hơn (tốn ×2 thời gian render chữ).

## D-010 · Màu "nóng" của preset Atlas
- Bối cảnh: soát contact sheet tier 1 thấy bi thép 1.000°C phát sáng xanh/xám ở vài style vì `danger` lấy màu phụ (b) của bảng màu.
- Đã chọn: `danger` (world) + vai `hot` (chart html) = màu ấm nhất trong a/b/c (`atlas.warm_key`, đỏ→cam→vàng, đủ bão hoà);
  bảng màu không có màu ấm (vd Studio Product, Floating Screens) → giữ đỏ-cam của style nền. Có test.
- Bổ sung 16/11 (soát lại contact sheet): style nền `chrome3d-black` có `danger` xanh (#8FB8FF) và nước màu cam → Studio
  Product vẫn ra bi xanh, Circuit City/Pin Wall ra nước cam. Đã chọn: base cũng lạnh → `defaults.hot_fallback` #FF5A3C
  (html thêm ô `hot` riêng vào palette); nước mang màu ấm → màu lạnh nhất của bảng màu (`atlas.cold_key`), không có thì
  `defaults.cold_fallback`. 13 preset đổi, golden + 3 video thử không đổi (không dùng base chrome). Test: mọi preset có bi
  ấm + nước không ấm.

## D-011 · Slug trùng trong bài kiểm đầu-cuối
- Bối cảnh: `slugify` cắt ngắn ý tưởng → 4 ý tưởng "What happens if … (nhãn)" ra cùng một slug; lượt Atlas đầu tiên ghi đè
  storyboard của dự án style cũ vừa xong.
- Đã làm: dừng ngay; đổi tên dự án đó thành `e2e-classic-flat-vector` (out/ đã kiểm giữ nguyên, storyboard khôi phục);
  dự án Atlas dở → `_e2e-partial-glass-run1` (ẩn, không xoá); nhãn phân biệt chuyển lên ĐẦU ý tưởng.
- Ghi chú cho tool: tạo hai video cùng câu hỏi sẽ dùng chung dự án — đúng ý đồ "một ý tưởng một dự án", nhưng UI nên báo
  "dự án đã có" trước khi chạy (ROADMAP).
