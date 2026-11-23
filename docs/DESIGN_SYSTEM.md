# Design system — forward. studio (UI Phần D)

Nguồn: `ui/web/styles/tokens.css` (token) → `components.css` (component) → `ui/web/app/ui/kit.js` (component JS).
Trang xem trực tiếp: `#/_design`. Quy tắc: **không mã màu/khoảng cách rời trong component** — chỉ dùng biến token.

## Nguyên tắc

- **Công cụ, không phải trang marketing.** Gọn, dày thông tin, thao tác nhanh bằng bàn phím; tổ chức theo công đoạn sản
  xuất (1 Projects · 2 Script · 3 Board · 4 Generate · 5 Edit · 6 Review · 7 Deliver · 8 Library), kiểu "trang" của
  Resolve; panel + inspector kiểu NLE; review theo timecode kiểu Frame.io; command palette kiểu Linear.
- **Một hành động chính mỗi màn hình** (nút accent duy nhất); phần nâng cao ẩn sau "Nâng cao".
- **Tối nhưng không đen**: giao diện xám than nhiều tầng; đen tuyệt đối (`--canvas`) chỉ dành cho vùng video/khung hình
  của kênh — nhờ vậy khung đen của video luôn nổi khỏi giao diện.
- **Viền mảnh thay bóng đổ**, bo góc nhỏ, chuyển động 120–180 ms chỉ để báo phản hồi.
- **Trạng thái một bảng màu cho cả app**: xanh = ok, vàng = cảnh báo, đỏ = lỗi/chặn, cyan = đang xử lý. Accent xanh điện
  KHÔNG dùng làm màu trạng thái.

## Token

| Nhóm | Token | Giá trị | Dùng cho |
|---|---|---|---|
| Bề mặt | `--s0 … --s4` | #111 · #161616 · #1c1c1c · #232323 · #2c2c2c | nền app → panel → ô nhập/hover → chọn → nhấn |
| Khung hình | `--canvas` | #000 | chỉ player, thumbnail, style frame |
| Viền | `--line`, `--line-2` | #2a2a2a, #3a3a3a | viền 1 px |
| Chữ | `--t1`, `--t2`, `--t3` | #ececec (15.3:1), #a8a8a8 (7.6:1), #8a8a8a (5.0:1) trên `--s1` | chính, phụ, mờ — đều đạt WCAG AA cho 13 px |
| Accent | `--accent`, `--accent-text`, `--accent-soft` | #3a64ff (chữ trắng 4.7:1), #7f9bff (6.2:1), 16% alpha | nút chính, vùng đang chọn, focus |
| Trạng thái | `--ok`, `--warn`, `--err`, `--proc` (+ `-soft`) | #3fb950, #d6a01e, #f2554b, #35b6c9 | badge, cổng QA, job |
| Engine | `--eng-flow/three/html/manim/board` | tím, cyan, xanh lá, vàng, đỏ | chỉ chấm/viền 2 px (không nền lớn) |
| Chữ | `--font-sans` / `--font-mono` | Inter (UI) / Roboto Mono (timecode, frame, mã shot, thông số) | |
| Cỡ chữ | `--fs-11 … --fs-20` | 11 · 12 · **13 (cơ bản)** · 14 · 16 · 20 | thang chặt như phần mềm dựng phim |
| Lưới | `--u1 … --u8` | 4 · 8 · 12 · 16 · 20 · 24 · 32 px | mọi khoảng cách |
| Mật độ | `--row`, `--ctl` | gọn 28/26 px · thoáng 36/32 px (`data-density`) | hàng bảng, chiều cao nút/ô |
| Bo góc | `--r1 … --r3` | 2 · 4 · 6 px | chip · nút/panel · modal |
| Chuyển động | `--t-fast/mid/slow` | 120 · 160 · 180 ms (0 khi `prefers-reduced-motion`) | hover · panel · drawer |

**Chọn font.** Inter: thiết kế cho màn hình, chữ số đều (`tnum`), đọc tốt ở 13 px, đã có sẵn trong `assets/fonts/`
(OFL) — không tải thêm. Roboto Mono cho mọi con số cần thẳng cột (timecode `00:00:12:17`, frame, LUFS, kích thước).

## Component

| Component | File | Ghi chú |
|---|---|---|
| Nút (`primary`, mặc định, `ghost`, `danger`, `sm`, chỉ icon) | `kit.Btn` | tự bắt lỗi async → toast lỗi; chặn bấm đúp |
| Trạng thái `St` / chip / kbd / chấm engine | `kit.St` | |
| Tiến độ `Progress` (role progressbar, % thật) | `kit.Progress` | không spinner vô tận |
| Bảng `Table` | `kit.Table` | sắp xếp theo cột, lọc, chọn nhiều (click / Ctrl / Shift), Enter/double-click mở, ảo hoá > 200 hàng |
| Panel chia `Split` | `kit.Split` | kéo hoặc ←/→ trên thanh chia; nhớ kích thước (localStorage) |
| Empty state | `kit.Empty` | luôn kèm hành động kế tiếp cụ thể |
| Callout | `kit.Callout` | đỏ/vàng/xanh/cyan, có nút sửa tại chỗ |
| Toast có Hoàn tác | `kit.toast` | `action` + `actionLabel`; lỗi giữ lâu gấp đôi |
| Modal / xác nhận | `kit.Modal`, `kit.confirm` | Esc đóng, trả focus; mọi thao tác tốn thời gian/phá huỷ đều xác nhận |
| Command palette | `overlays.palette` | Ctrl+K: trang, dự án, lệnh |
| Jobs drawer | `overlays.JobsDrawer` | %, frame n/m, ETA, huỷ, chạy lại, log trực tiếp (SSE) |
| Player | `media.Player` | J/K/L, Space, ←/→ (Shift ×10), I/O, marker comment, lớp vẽ khoanh |
| Waveform | `media.Waveform` | decode WebAudio, mốc từng từ bấm để nghe |
| Timeline | `media.Timeline` | lane video (màu engine) / chữ / VO / nhạc / SFX, playhead |
| Filmstrip shot | `.shotgrid/.shot` (Board) | khung đầu/cuối (ảnh nhỏ qua `/api/v2/thumb`), kéo-thả đổi thứ tự |

## Phím tắt (bảng đầy đủ: phím `?` trong app)

| Phím | Việc |
|---|---|
| `1`–`8` | chuyển trang công đoạn |
| `Ctrl+K` · `Ctrl+P` · `Ctrl+J` | command palette · chọn dự án · hàng đợi job |
| `Ctrl+Z` · `Ctrl+Shift+Z` | hoàn tác · làm lại (thứ tự shot, checklist, xoá comment) |
| `Space` · `J` `K` `L` | phát/dừng · lùi / dừng / tiến (bấm lặp = nhanh ×2) |
| `←` `→` · `Shift+←/→` | 1 frame · 10 frame |
| `I` · `O` · `Alt+X` | điểm vào · điểm ra · xoá vùng |
| `C` · `X` · `↑/↓` · `Tab` (Generate) | chép prompt · đánh dấu đã tạo · đổi thẻ · đổi prompt |
| `N` · `D` · `M` · `Ctrl+Enter` (Review) | comment mới · vẽ khoanh · tới comment kế · gửi |
| `R` (Board/Edit) · `Alt+←/→` (Board) | render lại shot đang chọn · dời shot |
| `N` · `/` (Projects) | gõ ý tưởng mới · lọc |
| `?` · `Esc` | bảng phím tắt · đóng |

## Kiểm tra

- `python scripts/ui_check.py --axe <axe.min.js>` — axe-core WCAG 2 A/AA mọi trang + đo chuyển trang + mở video.
- `python scripts/ui_shots.py qa/ui/after` — chụp mọi trang (1440×900, 1920×1080).
- `python scripts/ui_e2e.py` — Playwright làm trọn video qua UI (Projects → … → Deliver).
