# WP-X — Hybrid 2D ↔ 3D + nối verb vào engine 3D (Vòng 10)

> Trạng thái: **HOÀN TẤT**.

## Đã làm
1. **`engines/three/hybrid.js` (mới)**:
   - `makeCard2D`: prop `card2d` vẽ icon / `rig:<loài>` / chữ bằng bút 2D vào `CanvasTexture` cập nhật mỗi frame trong không gian 3D (hỗ trợ `look`: `pixel16`, `sprite8`, `cutout`, `halftone`, `comic`, `silhouette`, `flat`; `billboard`, `two_sided`, `thickness`, `cut_edge`).
   - `makeMultiplane`: prop `multiplane` nhiều lớp cắt giấy 2D ở các `z` khác nhau trong 3D (parallax & bóng thật).
   - `makeOverlay2D`: lớp Canvas 2D trong suốt (`overlay2d: [{text, icon, of, offset, z: "front"|"back"}]`) bám toạ độ chiếu màn hình của prop 3D theo từng frame + xuất `textBoxes()` cho QA OCR.
   - `make3DPost2D`: tái dùng `engines/html/post2d.js` cho `world.look3d.post` (`pixel`, `halftone`, `misregister`, `paper`) để shot 3D cùng chất với shot 2D.
2. **Nối vào `engines/three/scenes/stage.js` & `main.js`**:
   - Thêm prop `card2d`, `multiplane`, `overlay2d` và móc `do: [{u|t|f, verb, dur, args}]` gọi `MO.play` + `MO.threeDelta` của `lib/motion`.
   - Cập nhật khối chú thích đầu `stage.js` (brief đọc động).
3. **Validate**: thêm `stage_hybrid_errors` trong `engines/adapter.py`.
4. **Kiểm thử**: `tests/test_hybrid2d3d.py` (validate, `motionplan.verb_support()["three"] == True`, Node test `card2d` + `multiplane` + `do` verb `hop` + `overlay2d` texts).
