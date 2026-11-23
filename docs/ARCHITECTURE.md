# Kiến trúc & bản đồ thư mục

Đọc file này trước khi sửa code. Chi tiết từng module: bảng "Bản đồ code" trong `CLAUDE.md`.

## Bốn tầng

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 1. Giao diện       ui/ (web, python studio.py ui)  ·  studio.py (CLI)  ·  /video (Claude Code) │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ 2. Pipeline        vidlib/  — stage idea → … → qa, idempotent theo dấu vân tay (work/state.json) │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ 3. Engine dựng     engines/adapter.py → three · html · manim · board   (+ clip Google Flow)     │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ 4. Dữ liệu/cấu hình config/ · styles/ · prompts/ · brand/ · assets/   (một nguồn sự thật)         │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

Quy tắc phụ thuộc: tầng trên gọi tầng dưới, không ngược lại. UI không tự làm việc của pipeline — nó chạy
`studio.py` như job và đọc file pipeline đã ghi. Engine không đọc storyboard — chỉ nhận `job.json` (ShotSpec).

## Bản đồ thư mục

```
studio/
├── studio.py              CLI một lệnh (video, ideas, ui, styles, voices, narratives, status…)
├── video.bat · ui.bat     nháy đúp trên Windows: pipeline / giao diện web
│
├── ui/                    GIAO DIỆN WEB — xem ui/README.md
│   ├── server/            backend Python thuần (API, job, SSE, file an toàn)
│   └── web/               frontend ES module thuần (tokens → components → features)
│
├── vidlib/                PIPELINE (Python) — storyboard, compiler prompt Flow, timeline, giọng, âm thanh, render, QA
├── engines/               ENGINE DỰNG SHOT CODE — chung một giao diện engines/adapter.py
│   ├── adapter.py         ShotSpec → Clip; chọn engine; hash mã engine cho RESUME
│   ├── three/             three.js trong Edge headless: main.js (look 3D: toon/clay/plastic/glass/chrome/lowpoly/
│   │                      paper/holo/xray), props.js (đạo cụ 3D), cast.js, scenes/*.js (stage = cảnh dữ liệu)
│   ├── html/              motion graphics 2D Canvas: 13 look × 11 beat × 190 đạo cụ
│   ├── manim/             sơ đồ Manim CE (đồ thị, vector, phương trình)
│   └── board/             evidence board + phim câm (Python/OpenCV)
├── lib/motion/            thư viện chuyển động dùng chung JS + Python (cùng API, test đối chiếu)
│
├── config/                channel.json (kênh, nhịp, QA…), voice.json, mix.json, narratives.json, flow-models.json
├── styles/                <id>.json = một style (chữ, palette, world/look3d cho three.js, html look, flow prompt…)
│                          <id>.md = thẻ sinh tự động (studio.py styles --cards)
├── prompts/               brief cho LLM (storyboard, ý tưởng) + schema
├── brand/                 style bible kênh + font fallback
├── assets/                fonts/ (mọi font), sfx/, brand/, tessdata/ (OCR), user/ (ảnh người dùng tự đưa)
│
├── projects/<slug>/       MỖI VIDEO MỘT THƯ MỤC (gitignore): storyboard.json (nguồn sự thật), clips/, work/, out/,
│                          thumbnails/, qa/, publish.md
├── ideas/<lô>/            lô 10 ý tưởng (brief.md + ideas.json)
├── qa/                    ảnh soát chung: props3d/, html/, icons/, styles/, smoke.md
│
├── tests/                 unittest (python -m unittest discover -s tests -t .)
├── scripts/               công cụ: smoke.py, props3d_sheet.py, icon_sheet.py, html_sheet.py, style_compare.py,
│                          vendor_fetch.py
├── docs/                  ARCHITECTURE (file này), CHANGELOG, PERF, STYLE_AUDIT, CREDITS, BLENDER_MCP, CLEANUP_PLAN
│                          · archive/ = tài liệu lịch sử không còn bảo trì (chỉ mục: docs/archive/README.md)
└── vendor/                mã bên thứ ba: three/ (r160), cartoon-short-kit, claude-animated-shorts (+ repo tham khảo
                           chỉ-đọc, dựng lại bằng scripts/vendor_fetch.py)
```

## Trộn nhiều loại chuyển động trong một video

Mỗi shot tự chọn engine (`codeshot.engine_of`): `code.engine` ghi rõ → engine đó; không thì theo tên cảnh (cảnh của
three.js → 3D; beat html → 2D; trùng tên như `scale`/`outro` → theo params); style chỉ quyết định engine mặc định.
Mọi engine lấy màu/font của style video (three.js: `world` + `look3d`; manim: palette html, tự nâng độ sáng màu tối),
nên một video có thể: hook bằng 3D → số liệu bằng chart 2D → cơ chế bằng `scene`/`process` hoặc vector Manim →
payoff bằng 3D. Shot 2D liền nhau bay liền một cú máy (`vidlib/spine.py`); ranh giới engine dùng chuyển cảnh.

## Thêm một thứ mới

| Muốn thêm | Làm ở | Kiểm tra |
|---|---|---|
| Style | `styles/<id>.json` (+ `PREFERENCE` trong `vidlib/styles.py`) → `studio.py styles --cards` | `tests/test_hybrid.py`, `scripts/props3d_sheet.py <id>` |
| Look 3D | một mục trong `LOOK3D` (`engines/three/main.js`) → `world.look3d` của style | `scripts/props3d_sheet.py` |
| Đạo cụ 3D | hàm trong `engines/three/props.js` + mục `mk` trong `scenes/stage.js` | `scripts/props3d_sheet.py` |
| Beat 2D | hàm trong `engines/html/beats.js` + `PARAMS` trong `engines/html/__init__.py` | `scripts/html_sheet.py` |
| Màn hình UI | `ui/web/app/features/<tên>/view.js` + `define()` trong `main.js` | `tests/test_ui.py` |
| API UI | hàm `@route` trong `ui/server/app.py`, logic ở `ui/server/services/` | `tests/test_ui.py` |
