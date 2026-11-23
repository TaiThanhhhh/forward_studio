# forward_video — Giao diện Web Studio UI

Giao diện web cục bộ cho tool — làm mọi việc của `studio.py` bằng chuột: tạo video, xem kế hoạch (style + giọng + dạng
kịch bản), tải clip Flow theo shot, duyệt look, xem video/thumbnail/QA, theo dõi log trực tiếp.

```
python studio.py ui            # mở http://127.0.0.1:8765  (hoặc nháy đúp ui.bat)
python studio.py ui --port 9000 --no-open
```

Không cần cài thêm gì: backend là thư viện chuẩn Python, frontend là ES module thuần (không Node, không bước build).

## Kiến trúc (Phần D — UI công đoạn)

```
ui/
├── server/                    Backend (Python stdlib) — API cũ giữ nguyên + /api/v2/* cho các trang công đoạn
│   ├── app.py                 định tuyến, file tĩnh, /api/file (Range), /api/v2/thumb (ảnh nhỏ có cache), SSE, header bảo mật
│   └── services/              projects · catalog · jobs (hàng đợi, % + ETA từ log, danh sách trắng) · files · system
│                              · workspace.py (bundle workspace, review/comment, delivery, atlas gốc, assets, chi phí phiên)
└── web/
    ├── styles/tokens.css      design token (xám than nhiều tầng, 1 accent, trạng thái, Inter 13px + Roboto Mono, lưới 4px)
    ├── styles/base.css        khung: thanh trang 1–8 · thân trang · thanh trạng thái · drawer
    ├── styles/components.css  component (một khối = một component)
    └── app/
        ├── main.js            khung + điều hướng #/projects · #/p/<slug>/<trang> · #/library/<tab> · #/_design
        ├── core/              api.js (một lớp API + SSE + upload) · dom.js · icons.js · format.js (timecode…)
        │                      · store.js (localStorage an toàn, autosave, cache) · keys.js (phím tắt) · undo.js
        ├── ui/                kit.js (nút, bảng, split, toast, modal…) · overlays.js (palette, drawer, phím tắt) · media.js
        └── pages/             projects · script · board · generate · edit · review · deliver · library · design
```

Thiết kế + phím tắt: `docs/DESIGN_SYSTEM.md`. Audit UI cũ và số đo trước/sau: `docs/UI_AUDIT.md`.

## API

| Phương thức | Đường dẫn | Việc |
|---|---|---|
| GET | `/api/overview` | số liệu tổng quan, dự án gần đây, job, cân bằng Flow/code, kiểm tra môi trường |
| GET | `/api/projects[?demo=1]` | danh sách dự án (mặc định ẩn `_*`, `cmp-*`) |
| GET | `/api/projects/<slug>` | chi tiết: stage, shot (engine, cảnh, thời lượng, clip, prompt), đầu ra, QA, publish |
| POST | `/api/projects/<slug>/clips/<C01>` | tải clip Flow cho shot (body = file, header `X-Filename`) → `clips/C01.mp4` |
| POST | `/api/projects/<slug>/reveal` | mở thư mục dự án trong Explorer |
| GET | `/api/styles` · `/api/voices` · `/api/narratives?topic=` · `/api/stages` · `/api/models` | thư viện |
| GET | `/api/plan?topic=&style=&narrative=&flow=1/0` | kế hoạch style + giọng + dạng kịch bản (như `styles --plan`) |
| GET | `/api/ideas` | các lô ý tưởng trong `ideas/` |
| GET/POST | `/api/jobs` | danh sách / tạo job `{kind: video\|ideas\|tool, params}` |
| GET | `/api/jobs/<id>?from=N` · `/api/jobs/<id>/events` (SSE) | log job, luồng trực tiếp |
| POST | `/api/jobs/<id>/cancel` | huỷ (dừng cả worker render) |
| GET | `/api/file?root=projects\|qa\|styles\|docs\|ideas&path=` | đọc file (Range cho video) |
| GET | `/api/system` | môi trường + cấu hình |
| GET | `/api/v2/projects/<slug>/workspace` | mọi thứ một trang công đoạn cần: shot, timeline, chữ, VO + mốc từ, QA đỏ/vàng/xanh, gói nền tảng, quyền, manifest, version, chi phí, review |
| GET/POST | `/api/v2/projects/<slug>/review` | comment timecode + nét khoanh (op add/resolve/delete/restore) · trạng thái approved/changes |
| GET | `/api/v2/delivery` · `/api/v2/atlas/<n>` · `/api/v2/assets` · `/api/v2/session` | preset nền tảng · prompt gốc Atlas (chỉ máy này) · font/SFX/sổ quyền · chi phí 24h + job đang chạy |
| GET | `/api/v2/thumb?root=&path=&w=` | ảnh JPEG nhỏ có cache (lưới shot/style) |
| POST | `/api/jobs` kind mới | `deliver`, `rerender_shot`, `trim`, `reorder`, `redo_voice` (đều chạy `studio.py …`) |

## Bảo mật

- Chỉ nghe `127.0.0.1`; header `Host` phải là localhost (chặn DNS rebinding). Header: CSP, X-Frame-Options SAMEORIGIN, nosniff.
- POST cần `X-Studio-Client: web` + `Content-Type: application/json` (trang web khác không gửi được → chặn CSRF).
- Job chỉ là lệnh trong danh sách trắng, tham số được kiểm tra (style/stage/dạng kịch bản phải tồn tại, ý tưởng một dòng,
  không bắt đầu bằng `-`), chạy không qua shell.
- File chỉ đọc trong các gốc cho phép, chặn `..`/symlink ra ngoài. Không bao giờ trả giá trị API key.

Lịch sử job + log: `ui/.runtime/` (gitignore). Test: `python -m unittest tests.test_ui`.
