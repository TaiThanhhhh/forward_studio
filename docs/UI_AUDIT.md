# UI AUDIT — giao diện cũ (trước Phần D, 15/11/2026) + đo lại sau Phần D (mục 5)

Ảnh: `qa/ui/before/` (13 màn hình, 1440×900, Playwright + Edge). Skill `frontend-design` không có trong phiên này →
dùng 10 heuristic của Nielsen + checklist anti-slop của brief.

## 1. 10 heuristic của Nielsen (1 = kém, 5 = tốt)

| # | Heuristic | Điểm | Bằng chứng |
|---|---|---|---|
| 1 | Hiển thị trạng thái hệ thống | 2 | Tổng quan đứng ở skeleton xám (không biết đang tải gì, bao lâu); job chỉ có log, không %, không ETA; trạng thái QA chỉ ĐẠT/CẦN XEM |
| 2 | Khớp thế giới thật | 3 | Có stepper stage, nhưng tổ chức theo "dashboard/dự án/job" kiểu SaaS, không theo công đoạn sản xuất (kịch bản → board → tạo → dựng → duyệt → giao) |
| 3 | Quyền kiểm soát, tự do | 2 | Không undo; "Làm lại từ stage…" là select phá huỷ không xác nhận; không huỷ thao tác kéo-thả clip |
| 4 | Nhất quán, chuẩn | 3 | Nút chính lặp ở topbar ("Tạo video") và từng trang; cùng một trạng thái (đỏ/vàng/xanh) có 3 kiểu hiển thị |
| 5 | Phòng lỗi | 2 | Form Tạo video mất hết khi F5 (AUD-1003); không chặn chạy khi job khác đang chạy cùng dự án ở tầng UI |
| 6 | Nhận ra hơn nhớ lại | 3 | Prompt Flow nằm ở scripts.html riêng, phải nhớ shot nào đã tạo; không checklist |
| 7 | Linh hoạt, hiệu quả | 1 | Không phím tắt, không command palette, mọi việc bằng chuột; 15 shot = 15 lần kéo-thả riêng |
| 8 | Thẩm mỹ, tối giản | 2 | Thẻ bo 12–16 px, bóng đổ 3 tầng, khoảng trắng lớn; chữ "null" lộ trên trang dự án; nhiều nút cùng nổi bật |
| 9 | Giúp nhận biết/sửa lỗi | 1 | Lỗi API bị nuốt im lặng (AUD-1001); lỗi job chỉ có trong log thô |
| 10 | Trợ giúp, tài liệu | 3 | Có mô tả dưới tiêu đề trang; không bảng phím tắt, không gợi ý bước kế tiếp cụ thể |
| | **Tổng** | **22/50** | |

## 2. Năm tác vụ chính — số thao tác + số màn hình

| Tác vụ | Cũ: thao tác | Cũ: màn hình | Ghi chú |
|---|---|---|---|
| 1. Tạo video từ ý tưởng | 4 (nav → gõ → Xem kế hoạch → Tạo) | 3 (Tạo video → Job → Dự án) | phải tự mở dự án sau khi job xong |
| 2. Tạo asset Flow theo bảng sản xuất rồi nạp clip (15 shot) | ~65 (≈2–3 copy/shot ở scripts.html + 15 kéo-thả + Chạy tiếp) | 3 (Dự án → scripts.html ở tab khác → tab Shot) | không checklist, không thứ tự theo cây keyframe, không tự map clip |
| 3. Sửa một shot hỏng rồi render lại riêng shot đó | không làm được trong UI (sửa storyboard.json bằng editor + "Làm lại từ stage" = render lại cả video) | 2 + editor ngoài | |
| 4. Review và comment một bản render | không làm được (chỉ xem video) | 1 | không timecode, không vẽ, không so 2 version |
| 5. Xuất bản Shorts / Reels / TikTok | không có preset; tự lấy final.mp4 + publish.md | 1 | không cổng QA chặn, không ledger, không gói theo nền tảng |

## 3. Dấu hiệu "AI slop"

- Nền tối ám xanh navy (#0a0b0e + bề mặt xanh) thay vì xám than trung tính; accent xanh dùng cho nút, tab, chip, link,
  nhãn engine — mọi thứ đều "nổi".
- Card bo 12–16 px + bóng đổ 3 tầng ở mọi khối (KPI, bảng, panel) — kiểu template SaaS.
- Trang Tổng quan: các khối KPI to, khoảng trắng phung phí, nội dung thật ít; skeleton không báo tiến độ.
- Nhiều nút chính trên một màn hình (topbar "Tạo video" + "Chạy tiếp" + "Chạy thử" cùng cấp).
- Chữ "null" lộ ra (dữ liệu thiếu không có trạng thái rỗng).
- Không có font mono cho timecode/frame/mã shot nhất quán (có Roboto Mono nhưng dùng lẻ tẻ).
- Spinner/skeleton vô tận ở chỗ có thể báo % thật (job render in "N/M frame").
- Không có nội dung giả/lorem ipsum (điểm tốt), icon là SVG (không emoji) (điểm tốt).

## 4. Hướng sửa (Phần D)

Tổ chức lại theo công đoạn: **1 Projects · 2 Script · 3 Board · 4 Generate · 5 Edit · 6 Review · 7 Deliver · 8 Library**,
phím số chuyển trang; Jobs drawer + command palette (Ctrl+K) + thanh trạng thái dùng chung; design token xám than nhiều
tầng, một accent, chữ 13 px Inter + Roboto Mono cho số; mỗi màn hình một hành động chính; tự lưu; lỗi có nút sửa tại chỗ.
Kết quả đo lại: mục 5 bên dưới.

## 5. Sau Phần D — đo lại (16/11/2026)

Ảnh: `qa/ui/after/` (1440×900 + 1920×1080) · ghép trước/sau: `qa/ui/before-after.png`. Số thao tác đo bằng
`scripts/ui_e2e.py` (Playwright bấm thật trên UI mới, 4 dự án thử ở Phần C → `qa/ui/e2e.json`).

### 5.1 Năm tác vụ — trước → sau

| Tác vụ | Trước: thao tác / màn hình | Sau: thao tác / màn hình | Cách làm mới |
|---|---|---|---|
| 1. Tạo video từ ý tưởng | 4 / 3 | **2** (style tự chọn) · 3 (chọn style ở "Nâng cao") / **2** | gõ ý tưởng ở Projects → Tạo video (Ctrl+Enter); dự án mới tự mở ở trang Script, tiến độ ở Jobs drawer |
| 2. Bảng sản xuất Flow + nạp clip | ~65 / 3 (15 shot) | nạp clip **3–4 bất kể số shot** · chép prompt 1 phím `C` mỗi prompt (15 shot ≈ 30 phím) / **1** | Generate: thẻ theo thứ tự cây keyframe, checklist tự lưu, thả cả loạt clip → tự map theo tên |
| 3. Sửa một shot rồi render lại riêng shot đó | không làm được trong UI | **3–4 / 1** | Edit (hoặc Board): chọn shot trên timeline → Render lại shot (`R`) → xác nhận; chỉ shot đó + hậu kỳ chạy lại |
| 4. Review + comment một bản render | không làm được | **4 / 1** | Review: `D` vẽ khoanh trên khung → gõ → Thêm comment (gắn timecode) → Duyệt; so A/B 2 version |
| 5. Xuất Shorts / Reels / TikTok | không có preset | **1 / 1** | Deliver: cổng QA (đỏ thì nút bị khoá) → Xuất gói → bảng spec từng nền tảng đo bằng ffprobe |

### 5.2 Nielsen — chấm lại (tự đánh giá, cùng thang)

| # | Heuristic | Trước | Sau | Thay đổi chính |
|---|---|---|---|---|
| 1 | Trạng thái hệ thống | 2 | 4 | Jobs drawer: %, frame n/m, ETA, log trực tiếp; thanh trạng thái; cổng QA đỏ/vàng/xanh một bảng màu |
| 2 | Khớp thế giới thật | 3 | 4 | 8 trang theo công đoạn sản xuất (phím 1–8) |
| 3 | Kiểm soát, tự do | 2 | 4 | Hoàn tác/làm lại (thứ tự shot, checklist, xoá comment); huỷ job; xác nhận mọi thao tác phá huỷ |
| 4 | Nhất quán | 3 | 4 | Một nút chính mỗi màn hình; token dùng chung; một kiểu badge trạng thái |
| 5 | Phòng lỗi | 2 | 4 | Tự lưu nháp; chặn job trùng dự án + chặn tải clip khi đang chạy (409); cổng QA khoá Xuất gói; job trên dự án chạy thử giữ chế độ chạy thử |
| 6 | Nhận ra hơn nhớ | 3 | 4 | Checklist Flow theo cây keyframe; ảnh đầu/cuối mỗi shot; gợi ý bước kế tiếp ở empty state |
| 7 | Linh hoạt, hiệu quả | 1 | 5 | Ctrl+K, phím số, J/K/L/I/O, `C` chép prompt, `R` render lại, kéo-thả đổi thứ tự |
| 8 | Thẩm mỹ, tối giản | 2 | 4 | Xám than nhiều tầng, viền 1 px, bo 2–6 px, 13 px; phần nâng cao ẩn |
| 9 | Nhận biết/sửa lỗi | 1 | 4 | Lỗi API thành toast/callout có nút sửa; lỗi tiếng Việt rõ (vd. file đang mở ở trình phát) |
| 10 | Trợ giúp | 3 | 4 | Bảng phím `?`; mô tả + bước kế tiếp mỗi trang; `docs/DESIGN_SYSTEM.md`, trang `#/_design` |
| | **Tổng** | **22/50** | **41/50** | |

### 5.3 Khả năng truy cập + hiệu năng

- axe-core 4.10.2 (WCAG 2 A/AA) trên 11 route (Projects, 7 trang dự án, Library ×3, `_design`): **0 vi phạm**
  (0 serious/critical) — `python scripts/ui_check.py --axe <axe.min.js> --slug <dự án>` → `qa/ui/check.json`.
- Chuyển trang (đã có workspace trong bộ nhớ): **1.8–10 ms** (lần đo trước 2–25 ms; mục tiêu < 100 ms).
- Mở video ở Review: **41–100 ms** tới khi phát được, qua 3 lần đo (mục tiêu < 1 s).
- Còn lại: mật độ "thoáng" chưa chụp ảnh riêng; chưa thử bằng trình đọc màn hình thật (chỉ axe).
