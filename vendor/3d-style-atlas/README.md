# vendor/3d-style-atlas — bản chụp 3D Style Atlas (chỉ dùng nội bộ)

- `raw/NN-<slug>.json` — metadata nguyên văn của từng style (+ `prompt_full` nếu lấy được). **Gitignore.**
- `shots/NN.png` — ảnh chụp nhỏ modal của từng style (tham khảo, không dùng làm thumbnail). **Gitignore.**
- `INDEX.md` — bảng 37 dòng + nguồn + tóm tắt điều khoản (commit được: chỉ là dữ kiện).

Điều khoản trang (HubSpot Website Terms of Use): cá nhân, phi thương mại; không sao chép/phân phối nội dung. Vì vậy
bản gốc không vào git, không vào prompt Flow, không vào video. Preset `styles/atlas-*.json` sinh từ `config/atlas.json`
(lời của tool).

## Lấy nốt prompt toàn văn (anh tự chạy, ~2 phút)

1. Mở https://www.futurepedia.io/resources/3d-style-atlas/view (tự qua xác minh nếu có).
2. F12 → Console → dán `scripts/atlas_capture.js` → Enter, không bấm gì cho tới khi tải về `atlas-capture.json`.
3. `python scripts/atlas_import.py --from "%USERPROFILE%\Downloads\atlas-capture.json"`

Lệnh 3 ghi `raw/`, sinh lại preset, `INDEX.md`, bảng trong `docs/3D_ATLAS_ANALYSIS.md`, và chạy kiểm "không chép
nguyên văn" trên cả prompt mới.
