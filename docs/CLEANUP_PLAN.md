# CLEANUP PLAN — Dọn file & quy trình dư (WP-C, Vòng 10)

> Trạng thái: **HOÀN TẤT ĐỢT 1 (an toàn)** · Nhật ký: `docs/round10/C.md` · Nghiên cứu best practices: `docs/research/REPO_BEST_PRACTICES.md`.

## 0. Số đo Trước vs Sau (22/11/2026)

| Chỉ số | Trước WP-C | Sau đợt 1 (đã áp dụng) | Ghi chú |
|---|---|---|---|
| Tài liệu `docs/*.md` cấp gốc được track | 17 (+ 7 `docs/audit/*.md`) | **12** (+ `docs/archive/` lưu 12 tài liệu lịch sử kèm `README.md`) | Giữ nguyên lịch sử git bằng `git mv` |
| Launcher macOS & script 1 lần trong `scripts/` | 28 (gồm 7 `.command` + `.chung.sh` + `build_audit_doc.py`) | **19** (đã `git rm` 9 file thừa) | Toàn bộ làm việc trên Windows + `studio.py` |
| Bảng lệnh `studio.py` | 27 từ khoá (20 chính + 5 legacy + 2 chết) | 29 từ khoá (+ `sb`, `assets` của Vòng 10) | Đề xuất bỏ 2 lệnh chết `setup`/`looks` ở đợt sau |
| File ảnh sinh ra bị track trong `qa/` | 134 file (~39.3 MB) | Giữ nguyên theo yêu cầu ảnh kiểm Vòng 10; đã gitignore `_work/` | Chủ kênh có thể chọn chuyển `qa/` sang untracked sau khi chốt |
| Cache `projects/*/work/` | ~1.06 GB / 5 video | Dùng `python studio.py clean <slug> --yes` | Đề xuất thêm cờ `--all` cho GC cache `work/code/*/frames` |

## 1. Bảng kiểm kê có bằng chứng

Loại: **xoá** (`git rm`) · **lưu trữ** (`git mv` → `docs/archive/`) · **sửa** · **giữ** · **chờ chủ kênh**.

| # | Mục | Loại | Bằng chứng | Trạng thái |
|---|---|---|---|---|
| A-1 | `docs/AUDIT.md`, `AUDIT_V2.md`, `PLAN.md`, `RUN_LOG.md`, `BLOCKERS.md`, `docs/audit/*.md` (12 file) | Lưu trữ | Tài liệu các vòng cũ, chồng chéo với `CLAUDE.md` và `CHANGELOG.md` | **Đã chuyển** vào `docs/archive/` + `docs/archive/README.md` |
| D-1 | `scripts/*.command` (7 file) + `scripts/.chung.sh` | Xoá | Launcher macOS cũ, máy chủ kênh chạy Windows (`ui.bat` + `studio.py`) | **Đã `git rm`** + bỏ trong `.gitattributes` |
| D-2 | `scripts/build_audit_doc.py` | Xoá | Script sinh 1 lần cho `AUDIT_V2.md` (đã lưu trữ) | **Đã `git rm`** + bỏ ignore trong `ruff.toml` |
| R-1 | `docs/ARCHITECTURE.md`, `docs/RUN_REPORT.md`, `docs/ROADMAP_V2.md` | Sửa | Tham chiếu tới file đã chuyển vào `docs/archive/` | **Đã cập nhật** |
| R-2 | `CLAUDE.md` dòng `ui/web/app/features/*` | Sửa | Thực tế là `ui/web/app/pages/*` (`script.js`, `board.js`, `library.js`…) | **Sửa ở WP-I** |
| P-1 | Quy trình copy/paste `brief.md` → `storyboard.json` | Tối ưu | Đã thay bằng `studio.py sb import/patch/preview` + UI dán & kiểm lỗi tại chỗ (WP-U) | **Đã xong** |
| G-1 | `qa/` 134+ ảnh track trong git & `.git` 62 MB rời | Chờ chủ kênh | Ảnh kiểm dùng để review; có thể chạy `git gc` để nén `.git` | **Chờ chủ kênh quyết** |
| Q-1 | Style cũ chỉ-kiểu-chữ (`comic`, `paper_cutout`, `ink`) | Giữ | Giữ tương thích ngược cho video cũ; không xoá theo luật Vòng 10 | **Giữ nguyên** |
