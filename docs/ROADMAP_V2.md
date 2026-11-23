# ROADMAP V2 (sau vòng 9)

Thứ tự theo giá trị / công sức. Mã AUD trỏ tới `docs/archive/AUDIT_V2.md` + `docs/archive/audit/area-*.md`.

## Ngay khi anh quyết định (mỗi việc < 1 giờ)
1. Điền `rights/ledger.json → decisions` (gói ElevenLabs, gói Flow, Atlas, avatar) + đơn giá `config/costs.json` → cổng QA
   hết vàng ở mục quyền, chi phí/video ra số USD.
2. Nâng Pillow (AUD-709) → chạy `python -m unittest discover -s tests -t .` + `python scripts/visual_regression.py`.
3. Safe zone Reels (D-009): nếu chọn dời dải chữ → sửa `config/channel.json → safe_zone.caption_band`, render lại 1 video,
   xem `qa/report.html` (mục safe zone Reels phải xanh).
4. C2PA (AUD-604): `pip install c2pa-python` + chứng chỉ (tự ký để thử) → thêm bước ký trong `vidlib/deliver.py` sau remux.

## Vòng 10 — chất lượng tiếng + nguồn
- AUD-406/407/408: fade 5–10 ms mọi SFX/nối VO, crossfade vòng lặp nhạc (`vidlib/sfx.py`, `vidlib/mix.py`).
- AUD-403/404: mix trung gian float32; xin ElevenLabs `pcm_48000`/mp3 192k thay mp3 128k.
- AUD-409: khoá mức theo LUFS (K-weighting) + duck có look-ahead; nhạc thấp hơn giọng 16–18 LU.
- AUD-303: ingest chặn (đỏ) nguồn < 720p khi không dry-run; hướng dẫn tải 1080p trong scripts.html.
- AUD-506 / AUD-1204: `.srt` thời lượng tối thiểu 0.8 s, gộp cue mồ côi, số viết bằng chữ số.

## Vòng 11 — độ bền + kiến trúc
- AUD-212: khoá theo dự án (file lock) cho CLI + UI.
- AUD-209: engine board RESUME theo đoạn (giữ `_parts` đã xong).
- AUD-103/111: gộp `job_hash`, tách `vidlib/pipeline.py` (937 dòng) thành stage modules.
- AUD-802/804: cache TTS nhiều phiên bản theo câu; hash job gồm harness + font.
- AUD-1103: `studio.py archive <slug>` (nén nguồn sự thật nhẹ: storyboard, plan, audio, manifest).

## 3D Style Atlas — look riêng còn thiếu (D-008)
- Shader dither 1-bit (Dithered), hatching bút chì (Pencil Sketch), lọc sơn dầu Kuwahara (Painted), instancing hạt
  (Particle Swarm, Pin Wall, LED Wall), split-flap cơ khí. Mỗi look = một mục trong `LOOK3D` + cảnh/đạo cụ trong `stage`.
- Khi có look mới: đổi `look3d` trong `config/atlas.json` → `python scripts/atlas_import.py` → `scripts/atlas_frames.py`
  → `scripts/visual_regression.py --update` (sau khi xem bằng mắt).

## Xuất bản + số liệu
- AUD-1206: nhập CSV retention/CTR từ YouTube Studio (`studio.py metrics import <csv>`) → điểm tham khảo cho bộ chọn
  style/hook (chỉ cộng điểm nhẹ, không thay chống lặp).
- AUD-1205/1208: ghi lại thumbnail/tiêu đề đã đăng vào manifest (`version` đã đăng).
