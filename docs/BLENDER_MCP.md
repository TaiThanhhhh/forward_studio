# Hướng dẫn dựng Video 3D (Three.js 3D · Google Flow 3D · Blender MCP)

Hệ thống hiện hỗ trợ đầy đủ **3 đường dựng 3D** tuỳ mục đích:

1. **Toàn bộ bằng code Three.js (`--style toon3d-lab`):**
   - Không cần Google Flow (`code_only: true`).
   - Dựng bằng WebGL Three.js (`engines/three/main.js`, `engines/three/props.js`, `engines/three/scenes/stage.js`) với toon/clay shading 3 bậc, viền mực theo normal+depth, rim light, bóng đổ thật, DOF.
   - Hỗ trợ **nhân vật 3D khớp nối** (`mannequin` / `human3d` / `runner3d` / `lifter3d` với các pose động `idle`, `run`, `sprint`, `walk`, `squat`, `lift`, `curl`, `press`, `point`, `cheer`, `fall`), **35+ đạo cụ 3D chuyên biệt** phủ đủ 4 vũ trụ chủ đề A–D + khoa học/vũ trụ, **tự động đùn khối 3D (`icon3d`) cho toàn bộ 189 icon của kênh**, đạo cụ tổ hợp `parts`, và **hệ hạt 3D (`fx`)** (`steam`, `smoke`, `sparks`, `burst`, `splash`, `bubbles`, `shockwave`, `fire`).
2. **Kết hợp AI Video 3D trên Google Flow + Code 3D (`--style clay3d-black`):**
   - `vidlib/compiler.py` nhận diện `flow.is_3d = true` trong style card để sinh prompt 3D (*Stylized 3D clay diorama*) trên nền đen `#000000` và tự động gỡ bỏ `"3D render"` / `"3D shading"` khỏi khối `Avoid:`.
   - Các shot `mode: code` trong cùng video dùng chung bảng màu `world` 3D của `clay3d-black` để nối mượt với clip Flow.
3. **Blender MCP — tuỳ chọn cho shot 3D "hero" phức tạp (KHÔNG nằm trong pipeline tự động):**

Blender nặng (cài ~1 GB, render vài giây đến vài phút mỗi frame) nên **không** phải một engine của `mode: code`. Chỉ dùng
khi một video cần đúng MỘT shot 3D mô phỏng vật lý nặng (kim loại nóng chảy phản xạ thật, chất lỏng Flip Fluids, khói thể tích).

## Cách đưa một shot Blender vào video
Pipeline coi clip Blender như một **clip nguồn bình thường**, giống clip Flow:

1. Trong storyboard, để shot đó ở `mode: frames_start` (hoặc `auto`) như một shot Flow, **không** phải `mode: code`.
2. Render trong Blender ra `projects/<slug>/clips/<ID>.mp4`: 1080×1920, 30 fps, nền đen tuyệt đối (World colour #000000,
   Film → Transparent tắt), không chữ/số trong cảnh (chữ do `text_fx` thêm ở hậu kỳ), không tiếng.
3. Chạy `python studio.py video <slug> --from ingest` — ingest, auto-trim, camera ảo, mix và QA xử lý như clip Flow.

Nối mạch với shot code bên cạnh: `start_frame.seed_from` vẫn xuất frame cuối của shot code làm ảnh tham chiếu
(`frames/<ID>_start.png`) — mở ảnh đó trong Blender làm background để khớp vị trí vật.

## Nếu muốn điều khiển Blender bằng Claude (MCP)
- Cài Blender ≥ 4.2 và một add-on MCP cho Blender (tự chọn, tự kiểm tra license/bảo mật như `docs/STYLE_AUDIT.md` đã làm
  với các nguồn khác: đọc script cài đặt, không chạy `curl | sh`).
- Khai báo MCP server ở **cấp người dùng**, không khai trong repo này, để phiên làm video bình thường không tải nó.
- Trong phiên có MCP: yêu cầu dựng cảnh theo mô tả shot trong `storyboard.json`, camera dọc 9:16, nền đen, rồi render ra
  đường dẫn ở bước 2. Sau đó quay lại pipeline `/video`.

## Giới hạn có chủ đích
- Không có stage nào của pipeline gọi Blender; QA freeze/black/loudness vẫn áp dụng cho clip Blender như mọi clip khác.
- Bảng màu, độ dày nét của style không tự áp vào Blender — người dựng phải tự khớp (xem `styles/<id>.md`).
