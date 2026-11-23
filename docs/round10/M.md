# WP-M — Bộ não Motion (Vòng 10)

> Trạng thái: **HOÀN TẤT**.

## Đã xong
- **58 động từ chuyển động (`verb`)** + **7 mẫu `stagger`** trong `lib/motion/motion.js` và `lib/motion/verbs.py` (parity JS = Python 100%, tất định).
- **175 cơ chế hình ảnh** trong `config/metaphors.json` (`python -m vidlib.motionplan check` = 0 lỗi).
- **`vidlib/motionplan.py`**: chữ ký motion, lịch sử kênh chống lặp bố cục/kiểu bay/cơ chế, `lint_motion`, `brief_block` ưu tiên cơ chế trước số liệu.
- **`vidlib/spine.py`**: +6 kiểu bay camera mới (`orbit_tilt`, `push_through`, `rack`, `whip_rot`, `truck_parallax`, `spiral`) + tránh lặp giữa video.
- **Báo cáo phân tích**: `docs/MOTION_AUDIT.md`.
- **Kiểm thử**: `tests/test_motion_depth.py` và `tests/test_motion_lib.py` xanh 100%.
