# PERF — tốc độ render các engine của `mode: code`

## 1. Engine three.js toon (engines/three/, Edge headless + WebGL)

Đo ngày 14/11/2026 bằng `python studio.py perf 150` · cảnh `scale` · style `forward` · 1080×1920 · JPEG q0.95.

- Máy: 13th Gen Intel(R) Core(TM) i7-13620H · 16 luồng CPU · Windows-11-10.0.26300-SP0
- WebGL GPU: ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Laptop GPU (0x00002820) Direct3D11 vs_5_0 ps_5_0, D3D11)
- WebGL CPU (swiftshader): ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero) (0x0000C0DE)), SwiftShader driver)

| Chế độ | Worker | Frame | Tổng (s) | s/frame (wall) | s/frame/worker |
|---|---|---|---|---|---|
| GPU mặc định · ANGLE (Intel, Intel(R) UHD Graphics (0 | 1 | 150 | 8.0 | 0.053 | 0.053 |
| GPU mặc định · ANGLE (Intel, Intel(R) UHD Graphics (0 | 2 | 150 | 7.98 | 0.053 | 0.106 |
| GPU mặc định · ANGLE (Intel, Intel(R) UHD Graphics (0 | 4 | 150 | 9.93 | 0.066 | 0.265 |
| GPU mặc định · ANGLE (Intel, Intel(R) UHD Graphics (0 | 8 | 150 | 21.16 | 0.141 | 1.129 |
| GPU ép card rời · ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 | 1 | 150 | 6.58 | 0.044 | 0.044 |
| GPU ép card rời · ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 | 2 | 150 | 4.65 | 0.031 | 0.062 |
| GPU ép card rời · ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 | 8 | 150 | 14.24 | 0.095 | 0.759 |
| CPU swiftshader · ANGLE (Google, Vulkan 1.3.0 (SwiftShad | 1 | 6 | 4.17 | 0.695 | 0.695 |
| CPU swiftshader · ANGLE (Google, Vulkan 1.3.0 (SwiftShad | 8 | 16 | 15.11 | 0.944 | 7.554 |

- Nhanh nhất: GPU, 2 worker → **0.031 s/frame** (wall). Nhiều worker hơn chỉ tranh GPU. Mặc định `code_render`: `gpu = high`, `workers = 0` (= 2), `resume = true`.
- Kit gốc (một tiến trình, swiftshader): 3–10 s/frame. Swiftshader trên máy này: 0.695 s/frame.

## 2. Engine board (engines/board/, Python + OpenCV, CPU)

Đo ngày 14/11/2026 bằng `python studio.py perf board` · `projects/steel-ball-1000c-board/work/board/board.json` (style `board-black`, 1237 frame 1080×1920, 12 thẻ, 7 dấu/nhãn, 1 đoạn phim câm, có cả clip Flow toàn màn hình) · x264 CRF 17 · chia đoạn theo tiến trình rồi nối `concat -c copy`.

- Máy: 13th Gen Intel(R) Core(TM) i7-13620H · 16 luồng CPU

| Tiến trình | Frame | Tổng (s) | s/frame (wall) | s/frame/tiến trình |
|---|---|---|---|---|
| 1 | 1237 | 171.0 | 0.1382 | 0.1382 |
| 4 | 1237 | 69.63 | 0.0563 | 0.2252 |
| 8 | 1237 | 58.38 | 0.0472 | 0.3775 |
| 12 | 1237 | 55.21 | 0.0446 | 0.5356 |

- Nhanh nhất: 12 tiến trình → **0.0446 s/frame** (wall) → video 40 s (1.200 frame) ≈ **0.9 phút**. Một tiến trình: 0.1382 s/frame (plugin gốc ghi 0.15–0.3 s/frame ở 1920×1080).
- Mặc định (`config/channel.json → board`): `workers = 0` (= số luồng − 2, tối đa 12), mỗi tiến trình 1 luồng OpenCV (tránh tranh CPU), `crf = 17`.

## So sánh

- three.js (GPU): 0.031 s/frame — chỉ render shot có `code.scene`.
- board (CPU): 0.0446 s/frame — CẢ video board_spine (bảng, clip Flow, dấu đỏ, phim câm, grain), không cần GPU hay trình duyệt.
- Video board_spine có cảnh three.js (thẻ 'màn hình nhỏ') thì cảnh đó render bằng three.js trước, engine board dùng frame của nó làm texture.

## 3. Engine html (engines/html/, Canvas 2D trong Edge headless) và engine manim

Đo ngày 14/11/2026 bằng `python studio.py perf engines` · 90 frame 1080×1920 · beat `drop` · style `hud-black` · 13th Gen Intel(R) Core(TM) i7-13620H (16 luồng).

| Engine | Worker | Tổng (s) | s/frame (wall) |
|---|---|---|---|
| html (harness của tool: Playwright + Edge) | 1 | 5.86 | 0.065 |
| html (harness của tool: Playwright + Edge) | 2 | 4.99 | 0.055 |
| html (harness của tool: Playwright + Edge) | 4 | 6.88 | 0.076 |
| html (harness của tool: Playwright + Edge) | 6 | 9.64 | 0.107 |
| html (harness của tool: Playwright + Edge) | 8 | 13.92 | 0.155 |
| manim CE (Cairo, 1 tiến trình; beat `graph`) | 1 | 54.32 | 0.604 |

- html nhanh nhất: 2 worker → **0.055 s/frame**. Canvas 2D chạy trên CPU của tiến trình trình duyệt, nhưng shot ngắn (60–150 frame) thì thời gian mở trình duyệt chiếm phần lớn → ít worker nhanh hơn. Mặc định `code_render.html_workers = 0` (= 2, theo số đo).
- manim chậm hơn hẳn (dựng lại chữ mỗi frame) → chỉ dùng cho shot sơ đồ (đồ thị, vector, phương trình).

## 4. Có thay harness render bằng HyperFrames không?

Cùng nội dung (90 frame của engine html), HyperFrames 0.9.45 chụp + mã hoá:

| Harness | Worker | Tổng (s) | s/frame (tổng) | s/frame (riêng bước chụp) |
|---|---|---|---|---|
| Harness của tool (Playwright, JPEG từ canvas) | 2 | 4.99 | 0.055 | 0.055 |
| HyperFrames (Node + Chrome, screenshot) | 3 | 15.66 | 0.174 | 0.074 |

- **Quyết định: GIỮ harness của tool** — HyperFrames chậm hơn trên cùng nội dung; ngoài ra nó cần Node ≥ 22 lúc chạy (tool hiện không cần Node), ~120 MB node_modules, mặc định bật telemetry và tải GSAP/font từ CDN lúc render, và không có RESUME theo frame.
- Giá trị giữ lại từ HyperFrames: hợp đồng 'trang tua được theo thời gian' (engine html dùng cùng ý tưởng) và catalog component để tham khảo khi viết beat mới (`vendor/hyperframes/registry`).
