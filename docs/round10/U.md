# WP-U — UI dễ dùng: không bao giờ phải mở source để copy/paste (Vòng 10)

> Trạng thái: **HOÀN TẤT**.

## Đã làm
1. **Nghiên cứu Best Practices**: `docs/research/UI_BEST_PRACTICES.md` (12 nguyên tắc từ Premiere/AE Essential Graphics, Figma UI3 Properties, Descript, Frame.io, Material 3 / Apple HIG / Fluent 2).
2. **CLI có kiểm + lịch sử hoàn tác**: `vidlib/sbedit.py` + `studio.py sb check|import|patch|history|restore|preview` + `studio.py ideas import`.
3. **Backend API (`ui/server/`)**:
   - `ui/server/services/jobs.py`: làn job nhanh `LIGHT` (`sb_import`, `sb_patch`, `sb_restore`, `sb_preview`, `ideas_import`), `run_sync`, nạp key `.env` cho tiến trình con.
   - `ui/server/app.py`: thêm `/api/v2/projects/<slug>/sb/{check,import,patch,history,restore,preview}`, `/api/v2/ideas/<batch>/import`, `/api/v2/env`, `/api/v2/catalog/schema`.
   - `ui/server/services/system.py`: `save_env()` chỉ cho phép 3 API key, không bao giờ lộ giá trị key.
   - `ui/server/services/catalog.py`: `schema()` xuất động beats/layouts/looks/creatures3d/rig2d/assets3d/verbs/metaphors/round10_styles.
4. **Frontend (`ui/web/app/`)**:
   - `pages/script.js` & `pages/projects.js`: thẻ "Việc tiếp theo" cho mọi trạng thái dừng, Copy brief 1 cú click, Copy `/video <slug>`, dán JSON + kéo-thả `.json`, kiểm lỗi theo trường/dòng, Lưu & chạy tiếp, lịch sử hoàn tác, nhập `ideas.json`.
   - `pages/board.js`: Properties panel sửa VO/thời lượng/hold/mode/scene/layout/params trực tiếp + nút **Xem trước 1 frame** + hoàn tác.
   - `pages/generate.js`: rõ trạng thái thiếu/đủ clip Flow, tải khung start/end.
   - `pages/library.js`: thêm tab **Kho Vòng 10** (style mới, 3D/2D characters, 3D models, 58 verbs, 175 cơ chế) và tab **API Keys** (ghi `.env` cục bộ).
5. **Kiểm thử**: thêm `Round10Usability` trong `tests/test_ui.py`.
