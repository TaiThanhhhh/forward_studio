# WP-A — Kho tài sản: mô hình 3D CC0 (glTF) + icon SVG có giấy phép

> Trạng thái: **HOÀN TẤT**.

## Đã làm
1. **Vendor three.js addons r160** (commit `d04539a7673693dbefdc1efd3eb2ffd1cfd1fb89`):
   - `vendor/three/addons/loaders/GLTFLoader.js` (sha256 `d073b438…`)
   - `vendor/three/addons/utils/SkeletonUtils.js` (sha256 `83748c50…`)
   - `vendor/three/addons/utils/BufferGeometryUtils.js` (sha256 `9be041e9…`)
   - Khai báo import map `three/addons/` trong `engines/three/index.html`; ghi nhận vào `vendor/SOURCES.json` (khối `files.three-addons`) và hỗ trợ kiểm/tải lại trong `scripts/vendor_fetch.py`.
2. **Engine nạp mô hình glTF/GLB** (`engines/three/models.js` + móc trong `engines/three/scenes/stage.js`):
   - Nạp tuần tự trước `window.ready`, clone bằng `SkeletonUtils.clone` cho mesh có xương, chuẩn hoá chiều cao thật (`h` hoặc `size`, đặt đáy ở `y = 0`), tháo phụ kiện ẩn (`hide`).
   - Đổi chất liệu sang `ctx.toon(...)` theo `look3d` hiện tại (`toon`, `clay`, `retro90`, `psx`…), ánh xạ màu sang bảng màu style trong không gian OKLab, thu nhỏ & lọc texture theo `tex_px` của look, vá shader skinning (`skinPatchVS`) cho vật liệu `gouraud` và `ndMat`.
   - Animation tất định: đặt `action.time` là hàm thuần của frame `f` rồi gọi `mixer.update(0)`, hỗ trợ chuyển đổi/trộn chéo clip qua `keys: [{u, anim}]`.
3. **Kho 3D & SVG + Công cụ quản lý** (`config/assets3d.json`, `assets/lib/svg/index.json`, `vidlib/assets3d.py`, `vidlib/userassets.py`, `scripts/assets_fetch.py`, `scripts/assets_sheet.py`, `studio.py assets`):
   - **Kho 3D (`config/assets3d.json`)**: **479 mô hình** glTF/GLB (**10 mô hình có animation**, tổng **68.4 MB** trong `assets/lib/3d/`, gitignore) từ 16 gói CC0-1.0 chính chủ:
     - 10 gói KayKit (Kay Lousberg, CC0-1.0): `kaykit-restaurant` (99), `kaykit-hexagon` (84), `kaykit-furniture` (53), `kaykit-halloween` (37), `kaykit-city` (32), `kaykit-dungeon` (26), `kaykit-space` (25), `kaykit-prototype` (21), `kaykit-adventurers` (13), `kaykit-skeletons` (2).
     - 4 gói Kenney Starter Kits (Kenney, CC0-1.0): `kenney-city` (15), `kenney-platformer` (13), `kenney-racing` (13), `kenney-arena` (8).
     - `threejs-robot` (`RobotExpressive`, Tomás Laulhé / Quaternius & Don McCurdy, CC0-1.0): 1 mô hình với 14 clip hành động.
     - `polyhaven` (Poly Haven, CC0-1.0): 37 mô hình đạo cụ/đồ ăn/công nghệ/thiên nhiên chọn lọc (chỉ giữ `baseColorTexture`).
   - **Kho SVG (`assets/lib/svg/index.json`)**: **926 icon** từ gói `phosphor` (Phosphor Icons fill, MIT, commit `2b75f3ad12b4`), đã chạy SVGO + đo hình học thành `parts` (38 MB trong `assets/lib/svg/phosphor/`, gitignore), loại bỏ toàn bộ nhóm `BRAND`/logo.
   - **Resolver & CLI**: `vidlib/userassets.py` giải tên `model:<tên>` và `svg:<tên>` (ưu tiên icon kênh → SVG người dùng → SVG thư viện) + trả `license_notes`; `studio.py assets [search | fetch | sheet | check]`.
4. **Sổ quyền & Credits**:
   - Lưu toàn bộ văn bản giấy phép gốc kèm SHA-256 trong `assets/lib/licenses/`.
   - Cập nhật `docs/CREDITS.md` và `rights/ledger.json` (thêm `code:three-addons`, `lib3d:kenney`, `lib3d:kaykit`, `lib3d:threejs-robot`, `lib3d:polyhaven`, `libsvg:phosphor`, và 2 font OFL-1.1 `font:PressStart2P`, `font:PixelifySans`).

## Ảnh kiểm & Kiểm thử
- **Contact sheets 3D (`qa/assets3d/`)**: 32 bảng ảnh (16 gói × 2 style `toon3d-lab` và `retro90-lowpoly-black`, đã dọn `qa/assets3d/_work/`).
- **Kiểm tra kho (`assets3d.check()`)**: 479 mô hình 3D + 926 icon SVG thư viện đạt **0 lỗi** (mọi gói có giấy phép trong danh sách cho phép, văn bản giấy phép & file nhị phân khớp SHA-256).
- **Unit tests**:
  - `python -m unittest tests.test_assets3d tests.test_userassets` → **14 test XANH** (kiểm tra nạp index, `search`, `lookup`, `check()`, `prop_errors` gợi ý khi sai tên model/anim, `userassets.resolve`, và parity `animNorm`/`pickName` giữa Python và JS).
- **Ruff**:
  - `python -m ruff check scripts/assets_fetch.py scripts/assets_sheet.py scripts/vendor_fetch.py vidlib/assets3d.py vidlib/userassets.py tests/test_assets3d.py` → **0 lỗi**.
