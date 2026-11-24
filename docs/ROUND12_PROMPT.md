# Vòng 12 — Prompt cho Gemini 4 Neon (High)

> **Chuẩn Media Studio Toàn Cầu (Vox · Fern · Johnny Harris · Cleo Abram · Kurzgesagt · Neo):**
> Đồng bộ 2D ↔ 2.5D ↔ 3D · Thẩm mỹ trưởng thành (Adult Dark-Mode) · Less Is More · Không chồng chữ · Auto-Captions thông minh không che vật thể · Cơ chế đúng vật lý/ngữ cảnh · Nhịp thở điện ảnh kể chuyện bằng hình ảnh.
>
> Prompt này viết cho **Gemini 4 Neon (High)** làm việc trong repo `forward_studio` (dự án `forward_video` — kênh **"forward."**).
> Một agent điều phối (**Orchestrator**) đọc trọn file này và chia việc cho **6 Sub-Agent (WP-1 → WP-6)** chạy song song theo bảng phân quyền file ở mục 5.
> Người làm đọc **tiếng Việt**; khán giả xem/nghe **tiếng Anh tự nhiên**.

---

## 0. Đọc bắt buộc trước khi động vào code

1. `CLAUDE.md` và `docs/ARCHITECTURE.md` — nắm 4 tầng kiến trúc, luật phụ thuộc và lệnh test/lint.
2. `config/channel.json` — thông số nhịp (`pacing`), giọng (`vo`), vùng an toàn (`safe_zone`), phụ đề (`captions`), cổng QA (`qa`).
3. `vidlib/brief.py`, `vidlib/linter.py`, `vidlib/motionplan.py` — nơi sinh luật cho LLM và kiểm lỗi kịch bản.
4. `engines/html/core.js`, `engines/html/beats.js`, `engines/html/looks.js`, `engines/html/rig2d.js` — toàn bộ hệ 2D.
5. `engines/three/props.js`, `engines/three/creatures.js`, `engines/three/scenes/stage.js`, `engines/three/hybrid.js` — toàn bộ hệ 2.5D/3D.
6. `vidlib/autocaptions.py`, `vidlib/render.py`, `vidlib/qareport.py`, `vidlib/qagate.py` — phụ đề, ghép khung và cổng QC.

**Nguyên tắc cốt lõi của chủ kênh:**
- **Làm tổng quát cho toàn bộ tool**, tuyệt đối không vá riêng 1 video (mọi luật phải nằm ở engine, config, brief, linter và cổng QA để **mọi video sinh ra sau này tự động đạt chuẩn**).
- **Quy trình như một Studio Media lớn đang viral toàn cầu**: có Art Bible thống nhất, Grid 3 tầng cứng chống đè, ngân sách thị giác (Visual Budget), kiểm định khoa học/bối cảnh cho đạo cụ, và cổng QC tự động chặn mọi khung hình lỗi trước khi xuất bản.

---

## 1. Chẩn đoán 7 vấn đề gốc đã xác minh trong codebase

Mỗi vấn đề chủ kênh gặp khi generate video mới đều truy ra nguyên nhân trực tiếp trong mã nguồn hiện tại:

| # | Vấn đề thực tế | Nguyên nhân gốc trong code | Mục tiêu sửa triệt để |
|---|---|---|---|
| **1** | **Object 2D, 2.5D, 3D không đồng bộ** | `rig2d.js` (2D phẳng, mắt to, bảng màu vai `hot/cold/accent`) và `creatures.js` (3D trụ tròn, màu cố định trong `TONES` như áo đỏ `#E8483C` / quần xanh `#2F3E66`) dùng 2 hệ màu & 2 tỉ lệ hoàn toàn tách biệt. Khi cắt 2D ↔ 3D khán giả không nhận ra cùng một nhân vật/vật thể. | Tạo **Shared Visual Identity Contract** (`design_system` trong style + bảng token màu/tỉ lệ chung): nhân vật 2D (`rig2d`), 2.5D (`card2d`/`multiplane`) và 3D (`creatures`/`mannequin`) dùng **cùng palette, cùng tỉ lệ đầu/thân, cùng ngôn ngữ viền & ánh sáng**. |
| **2** | **Background nền hơi trẻ con** | `props.js` (`SET_COL`: cỏ xanh neon `#4FA83A`, hoa vàng kẹo `#FFD23F`, cây hình cầu kẹo mút), `creatures.js` (mắt to hoạt hình có chấm sáng, tỉ lệ đầu tròn kiểu app thiếu nhi), `looks.js` (`flat` rải hình học confetti, `story` vẽ mây tròn). | Chuyển toàn bộ thẩm mỹ mặc định sang **Adult Editorial / Documentary Dark-Mode** (kiểu Vox · Fern · Johnny Harris · Neo): bảng màu trầm tinh tế (đá phiến, rêu đêm, đất nung trầm, kem ấm `#ECEAE2`), ánh sáng studio rim/spotlight mềm, nhân vật tỉ lệ người lớn/giải phẫu thanh lịch, loại bỏ mắt googly và màu kẹo ở các style người lớn. |
| **3** | **Nhiều object gây rối — thiếu "Less Is More"** | `brief.py` khuyến khích nhồi `actors[]` + `arrows[]` + `fx[]` + `labels[]` + `kicker` + `title` + `sub` + `overlay2d[]` + `captions` cùng lúc vào 1 khung 9:16; `linter.py` chưa giới hạn số vật thể/số cụm chữ mỗi shot. | Áp **Visual Budget cứng** ở cả `brief.py` lẫn `linter.py`: tối đa **1 chủ thể chính + 1 yếu tố tương tác/cơ chế** (≤ 3 actor tổng) và tối đa **1 cụm chữ nhấn ≤ 4 từ** mỗi shot; tắt kicker/subtitle dư thừa trên các shot kể chuyện bằng hình. |
| **4** | **Auto-captions che vật thể & làm rối khung** | `autocaptions.py` đóng cứng `cy = 1420` bất chấp vật thể hay nhãn đáy nằm ở đâu; trong khi `core.js` đặt `A.bottom = 1516` khiến mọi beat HTML (nhãn `22 MILES`, `HORSE CORE`, `2X FASTER`) và đạo cụ 3D tràn thẳng vào vùng phụ đề. | Thiết lập **Kiến trúc Grid 3 Tầng Cứng (9:16 Sacred 3-Zone Grid)** tách biệt tuyệt đối Sân khấu hình ảnh (`y: 400–1240`) và Kênh phụ đề (`y: 1340–1450`); thêm preset **`studio_clean`** tinh tế và **Smart Suppression** (tự ẩn/dịch phụ đề khi shot là thẻ toàn chữ `title`/`fact`, đo vùng chiếm chỗ để không đè chủ thể). |
| **5** | **Object overheat phức tạp & sai thực tế/bối cảnh** | Các cơ chế kiểu `core_temperature`/`sweat_cooling` hoặc cảnh `stage` hay ghép nhiệt kế khổng lồ bay lơ lửng giữa đường chạy, kèm khói đỏ, kèm badge `OVERHEATED`, kèm phổi bay trước mặt ngựa — vừa rối vừa phi vật lý/lệch bối cảnh. | Thiết kế lại hệ **Grounded Visual Metaphors**: hiệu ứng nhiệt (`thermal_glow` / core heat gradient trực tiếp ngay trên cơ thể nhân vật 2D & 3D + 1 thanh telemetry mảnh cạnh mép) thay vì dán nhiệt kế khổng lồ lơ lửng; cập nhật `metaphors.json` & `brief.py` bắt buộc kiểm tra **Context Coherence** (vật thể phải thuộc về không gian thật của frame). |
| **6** | **Bug chữ chồng chữ** | `beats.js:645-646` (`factFlip`) đặt `P.text` tại `cy - 150` (tràn 5–6 dòng xuống `cy + 450`) rồi đặt `P.em` cứng tại `cy + 250` → **đè trực tiếp lên nhau**. Ngoài ra `core.js` chưa có bộ kiểm tra/tách va chạm giữa các `boxes[]` và QA chưa có cổng chặn lỗi chồng chữ. | Sửa toàn bộ tọa độ tĩnh thành **Flow Layout động** (tính theo `b.y1 + margin`, tự co `size` vừa khung); thêm **Collision Resolver** trong `core.js` + cổng **QA ĐỎ `không chồng chữ (text overlap)`** trong `qareport.py`/`qagate.py` chặn xuất bản ngay lập tức nếu 2 khối chữ giao nhau > 5%. |
| **7** | **Nhịp hơi nhanh & quá nhiều chữ thay vì visual/câu chuyện** | `channel.json` ép `target_wps: 3.7`, `vo.speed: 1.12`, `shot_avg: 1.5–2.5s`, `change_every_sec: 1.2s`, cắt lặng `150ms` → video nói vội như đọc tin nhanh, cắt cảnh liên tục khiến khán giả không kịp thưởng thức hình ảnh và câu chuyện. | Chuyển chuẩn nhịp sang **Cinematic Adult Explainer**: `target_wps: 3.0` (khoảng `2.6–3.4`), `vo.speed_max: 1.06`, giữ nhịp thở tự nhiên `240–320ms` trước điểm nhấn; mỗi shot dài **`2.5–4.2s`** với chuyển động nội tại mượt (slow dolly, biến đổi trạng thái vật lý liên tục); viết lại `brief.py` theo nguyên tắc **"Show, Don't Type"**. |

---

## 2. Chuẩn thiết kế & Quy trình sản xuất của Studio Media Lớn (Luật bất biến)

Mọi thay đổi trong Vòng 12 phải tuân thủ **6 chuẩn bất biến** sau:

### 2.1 Kiến trúc Khung dọc 9:16 — 3 Tầng Tuyệt Đối (Sacred 3-Zone Grid)
Mọi engine (`html`, `three`, `manim`) và lớp hậu kỳ (`textfx`, `autocaptions`) phải đọc chung một nguồn tọa độ từ `config/channel.json → layout_grid`:
- **Zone A — Header tinh giản (`y: 250 – 370`)**: chỉ dành cho kicker/source nhỏ (≤ 26px mono, opacity 0.65) khi thật sự cần ngữ cảnh; **mặc định tắt** trên shot hành động (`scene`, `stage`).
- **Zone B — Sân khấu Thị giác (`y: 390 – 1240`, tâm `y = 815`)**: vùng thiêng cho **nhân vật, cơ chế vật lý, mô hình 3D, biểu đồ**.
  - Mọi beat HTML đặt `A.bottom = 1240` khi captions bật (không bao giờ đẩy tag/nhãn xuống quá `y = 1230`!).
  - Auto-frame của `stage.js` nâng `footroom` / `bottom_margin` tương ứng (`~0.24` từ đáy khung 1920px) để đáy diorama/nhân vật nằm trọn phía trên `y = 1280` — **tuyệt đối không để phụ đề cắt ngang chân nhân vật hay đáy diorama**.
- **Zone C — Kênh Phụ đề (`y: 1340 – 1460`, tâm `y = 1395`)**: dành riêng cho Auto-Captions kiểu studio gọn gàng, sạch mắt, nằm an toàn phía trên UI của YouTube Shorts / TikTok.

### 2.2 Art Direction trưởng thành (Adult Editorial Standard)
- **Đối tượng khán giả**: người lớn 22–40 tuổi (thích khoa học, chạy bộ, thể hình, công nghệ — gu thẩm mỹ kiểu **Vox · Fern · Johnny Harris · ColdFusion · Neo · Cleo Abram**).
- **Hệ màu (Cinematic Desaturated Dark-Mode)**:
  - Nền tối sâu có sắc thái (`#0B0D11` / `#0E1117` / `#101318`) — không đen phẳng chết cứng và không nền hoạt hình sáng rực.
  - Mực chính kem ấm (`#ECEAE2`) — dễ chịu hơn trắng `#FFFFFF` gắt mắt.
  - Môi trường trầm tự nhiên: cỏ rêu đêm `#2C4A3B`, đất đá phiến `#3C352E`, đường chạy đất nung trầm `#8F3E30`, bê tông/khán đài `#1C212B`.
  - **Chỉ 1 màu nhấn có ý nghĩa** mỗi khung (amber `#E8B84B`, cobalt `#3B82F6`, hoặc vermilion `#DF4B3C` cho nhiệt/cảnh báo).
- **Nhân vật & Hình khối**:
  - Hỗ trợ `character_style: "editorial" | "cartoon"` trong style JSON (mặc định **`"editorial"`** cho tất cả style người lớn; chỉ giữ `"cartoon"` cho `retro90-lowpoly-black`, `comic`, `cartoon-story-black`, `paper-cutout-black`).
  - Ở chế độ `"editorial"`: `rig2d` và `creatures`/`mannequin` dùng **tỉ lệ người lớn cân đối** (đầu nhỏ hơn, thân mảnh rõ dáng chạy/chuyển động, **không mắt tròn trắng googly**, dùng hình khối phẳng/tối giản thanh lịch hoặc đường nét giải phẫu sạch, đồng bộ màu áo/da/thân 100% giữa 2D và 3D).

### 2.3 Luật "Less Is More" (Ngân sách Thị giác & Chữ)
- **Visual Budget mỗi shot**:
  - Tối đa **1 chủ thể chính (Hero)** + **1 vật/cơ chế tương tác** (tổng `actors` nổi bật ≤ 3, không tính lớp nền mờ `z ≥ 1.8`).
  - Tối đa **1 cụm chữ on-screen ≤ 4 từ** (hoặc 1 con số + đơn vị) khi Auto-Captions đang bật.
  - **Không bao giờ nhân đôi nội dung**: chữ trên màn hình chỉ hiển thị **con số / tên cơ chế / mốc dữ liệu**, KHÔNG viết lại nguyên câu VO!
- **Grounded Physics & Context Coherence**:
  - Mọi hiện tượng sinh lý/vật lý (nhiệt độ tăng, mệt mỏi, nhịp tim, mất nước, áp suất) phải thể hiện **trực tiếp trên chính vật thể/môi trường đang diễn ra câu chuyện**:
    - *Overheat*: thân nhân vật/động vật chuyển dần sang sắc **thermal core glow** (hồng ngoại/cam ấm tập trung ở vùng ngực/thân + làn sóng nhiệt mờ tinh tế) + **1 vạch đo nhiệt tối giản cố định ở mép phải**, KHÔNG dựng nhiệt kế 3D khổng lồ cắm xuống đường chạy!
    - *Nhịp thở / Phổi*: chỉ hiển thị khi camera **zoom vào mặt cắt giải phẫu (cutaway/X-ray)**, không dán icon phổi bay lơ lửng giữa trời bên cạnh con ngựa đang chạy!

### 2.4 Nhịp điệu điện ảnh (Visual-First Pacing)
- Giọng đọc tự nhiên, đĩnh đạc: mục tiêu **`3.0 từ/giây`** (`2.5–3.5 wps`), `vo.speed_max = 1.08`, giữ khoảng lặng thở `220–320 ms` trước beat `payoff` và `twist`.
- Thời lượng shot trung bình **`2.4 – 3.8 giây`** (hook `1.8 – 2.5s`, các shot cơ chế `3.0 – 4.5s`). Ít cắt cảnh vụn hơn (video 40s chỉ cần **10–13 shot chất lượng cao** thay vì 16–20 shot nhảy giật!), đổi lại **bên trong mỗi shot có chuyển biến rõ ràng** (camera glide, trạng thái vật thể thay đổi từ A → B).

### 2.5 Nguyên tắc kỹ thuật kế thừa (không được phá vỡ)
- **Tất định 100%**: không `Math.random()`, không clock thời gian thực; mọi frame là hàm thuần của `f`.
- **Không thêm engine thứ 6**: mọi nâng cấp nằm gọn trong 5 đường dựng hiện có (`three`, `html`, `manim`, `board`, `Flow`).
- **Tương thích ngược**: dự án cũ sinh trước `apply_since` không bị hỏng; mọi test cũ + mới phải pass 100%, `ruff check .` 0 lỗi.
- **Không `git commit` / `git push`** — hoàn thành xong báo cáo rõ để chủ kênh kiểm duyệt và commit.

---

## 3. Phân chia 6 Gói Việc (Work Packages) cho Sub-Agents

Orchestrator điều phối **đợt 1 song song** (`WP-1`, `WP-2`, `WP-3`, `WP-5`), sau đó chạy **đợt 2** (`WP-4`, `WP-6`) để tích hợp, kiểm định chéo và render đối chiếu.

---

### WP-1 — Hệ thống Mỹ thuật Người lớn & Đồng bộ 2D ↔ 2.5D ↔ 3D
**File sở hữu:**
- `engines/three/props.js`
- `engines/three/creatures.js`
- `engines/three/paint.js`
- `engines/html/rig2d.js`
- `engines/html/looks.js`
- `vidlib/codeshot.py` (chỉ hàm `world()` và truyền `design_system` vào job)

**Yêu cầu chi tiết:**
1. **Shared Visual Identity (`design_system`)**:
   - Đọc token `character_style` (`"editorial"` mặc định cho style người lớn, `"cartoon"` cho style hoạt hình/retro90) và bảng màu nhân vật thống nhất (`actor_a`, `actor_b`, `actor_neutral`, `heat_glow`, `env_ground`, `env_foliage`, `env_track`) từ `styles/<id>.json` → truyền xuống CẢ `job.html` lẫn `job.world` của `three.js`.
   - Khi vẽ cùng một cặp nhân vật (ví dụ `adult` + `horse`), màu thân chính, màu nhấn và tỉ lệ hình khối giữa `rig:adult` (2D), `card2d` (2.5D) và `creature:adult` / `mannequin` (3D) phải **khớp nhau 100%**.
2. **Nâng cấp `rig2d.js` & `creatures.js` chế độ `"editorial"`**:
   - Thêm nhánh `style: 'editorial'` trong `rig2d.js`: tỉ lệ giải phẫu/tối giản thanh lịch (đầu cân đối hơn, không vẽ 2 mắt tròn to trắng đen kiểu hoạt hình thiếu nhi; sử dụng mặt phẳng sạch/bóng đổ nhẹ kiểu Kurzgesagt/Vox/Fern).
   - Trong `creatures.js`: khi `ctx.job.world.character_style === 'editorial'` (hoặc mặc định cho các style không phải `retro90`/`cartoon`), tắt mắt googly to, dùng bảng màu tinh tế lấy từ `world.colors` thay vì áo đỏ tươi `#E8483C` + quần xanh đồ chơi `#2F3E66`, giảm độ cứng viền đen (`ink.px ≤ 1.0` hoặc tắt viền dùng rim light mềm).
3. **Khử nền "trẻ con" trong `props.js`, `paint.js`, `looks.js`**:
   - Nâng cấp `SET_COL` mặc định sang bảng màu **Adult Dark-Mode** (cỏ rêu đêm `#2C4D3B`, đất đá phiến `#3D362F`, đường chạy đất nung trầm `#8F3F31`, tán cây trầm `#244236` thay vì xanh lá neon `#4FA83A` và cây kẹo mút bóng loáng).
   - Nâng cấp `tree()` và `diorama` / `meadow` / `stadium`: cây có dáng tán nhiều tầng tinh tế (pine/cypress tối giản kiến trúc) thay vì 1 hình cầu tròn trên que gỗ; giảm độ bão hòa cỏ/hoa; thêm viền tối mềm (edge vignette) để bối cảnh 3D hòa mượt vào không gian dark-mode của kênh.
   - Trong `looks.js`: ở `flat`, thay `shapesDrift` (confetti tròn/tam giác bay) bằng lưới điểm/đường dẫn tinh tế độ mờ thấp (`alpha 0.14`) để hết cảm giác thiếu nhi.
4. **Hiệu ứng Nhiệt gắn thân (Grounded Thermal Glow)**:
   - Thêm thuộc tính `heat: 0..1` (hỗ trợ keyframe `{u, heat}`) cho `creature` / `mannequin` trong `engines/three/creatures.js` & `stage.js` và cho `actor` trong `engines/html/core.js`: khi `heat` tăng từ `0 → 1`, vùng thân/lõi nhân vật tự chuyển sắc ấm/đỏ nhiệt + tỏa quầng nhiệt mềm tinh tế — **thay thế hoàn toàn việc phải nhồi nhiệt kế khổng lồ bay lơ lửng**.

**Tiêu chí nghiệm thu WP-1:**
- Dựng ảnh đối chiếu 2D (`rig:adult`, `rig:horse`) cạnh 3D (`adult`, `horse`) trên cùng 1 style (`vox-editorial-black`, `flat-vector-black`) lưu vào `qa/round12/sync_2d_3d.jpg`: cùng tông màu, cùng tỉ lệ trưởng thành, không còn nét trẻ con.
- Ảnh bối cảnh `diorama` và `stadium` mới lưu tại `qa/round12/adult_sets.jpg`.

---

### WP-2 — Sửa triệt để Bug Chữ Chồng Chữ & Hệ thống Layout Grid 3 Tầng (2D HTML)
**File sở hữu:**
- `engines/html/core.js`
- `engines/html/beats.js`

**Yêu cầu chi tiết:**
1. **Áp dụng Grid 3 Tầng (`A.top`, `A.bottom`, `A.stageBottom`) trong `core.js`**:
   - Đọc `JOB.layout_grid` (hoặc mặc định `stage_bottom = 1240` khi `JOB.captions_on !== false`, ngược lại `1500`).
   - Đặt `A.bottom = stage_bottom` để **100% các beat HTML** (`title`, `compare`, `counter`, `meter`, `timeline`, `callout`, `process`, `units`, `fact`, `scene`) tự động co bố cục nằm gọn phía trên vùng Auto-Captions — **không bao giờ còn cảnh chữ đáy đè lên phụ đề**.
2. **Sửa triệt để bug chữ chồng chữ trong `beats.js`**:
   - **`factFlip` (`beats.js:644-647`)**: tính tọa độ `P.em` ĐỘNG theo `const tb = c.text(P.text, ...)` → đặt `P.em` tại `tb.y1 + 70`, và tự động thu nhỏ cỡ chữ `P.text` (`96 → 76 → 64`) nếu tổng chiều cao `P.text + P.em` vượt quá chiều cao thẻ `chh - 140`. **Cấm tuyệt đối hardcode `cy + 250`!**
   - **`fact`, `factStamp`, `factLeft`, `factQuote`, `titleReveal`, `compareRace`, `counterUnits`, `processDomino`, `callout`, `sceneBeat`**: rà soát từng hàm, đảm bảo mọi khối chữ thứ cấp (`sub`, `em`, `result`, `tag`, `labels`) đều tính vị trí từ bounding box thực tế của khối trước đó và kẹp trong `[A.top, A.bottom]`.
   - **Tối giản chữ mặc định (Less Is More)**: trên các beat trực quan (`scene`, `split`, `meter`, `timeline`, `compare:race`), giảm kích thước kicker (`24px`, opacity `0.55`), nếu không truyền `title` thì không chừa khoảng trống thừa để hình ảnh chiếm trọn tâm khung hình.
3. **Runtime Text Collision Resolver & Overlap Telemetry trong `core.js`**:
   - Trong `textImpl`, kiểm tra `box` mới với danh sách `boxes` đã vẽ ở frame hiện tại: nếu có va chạm dọc (`overlapArea / minArea > 0.05` và không phải chữ `quiet`), tự động dịch nhẹ xuống/lên trong vùng an toàn (hoặc ghi nhận vào `overlapList` nếu không thể né).
   - Xuất thêm hàm **`window.overlapPairs()`** trả về danh sách mọi cặp chữ bị đè nhau trong frame hiện tại (`[{a, b, ratio}]`) để QA tự động đọc và **chặn xuất bản (ĐỎ)**!

**Tiêu chí nghiệm thu WP-2:**
- `factFlip` với đoạn chữ dài 15–20 từ + `em` dài 6 từ: **0% chồng chữ**.
- Chạy `scripts/html_sheet.py` qua 15 beat: `window.overlapPairs()` trả về `[]` ở 100% các frame.

---

### WP-3 — Auto-Captions Tinh Tế Kiểu Studio & Không Che Vật Thể
**File sở hữu:**
- `vidlib/autocaptions.py`
- `vidlib/render.py`
- `vidlib/pipeline.py` (chỉ phần truyền cờ `captions_on` vào job & `render`)

**Yêu cầu chi tiết:**
1. **Thêm preset mặc định mới cho kênh người lớn: `studio_clean`**:
   - Phong cách phụ đề tinh gọn của các kênh viral người lớn (Cleo Abram · Johnny Harris · Fern · Vox):
     - Cụm ngắn **2–4 từ** đặt cố định trong **Zone C (`y = 1390`, an toàn tuyệt đối phía dưới Zone B `1240`)**.
     - Nền thanh kính mờ cực gọn (`rgba(10, 12, 16, 0.68)`, bo góc mềm `12px`, không viền chói).
     - Chữ **Inter / BeVietnamPro SemiBold-Bold** cỡ vừa (`48–52px`, không viết hoa gào thét, không bóng đen dày kiểu meme), từ đang đọc chuyển màu sáng tinh tế (`#FFFFFF` / `#F5D547` nhẹ nhàng, scale tối đa `1.04×` thay vì phồng to `1.15×` gây rối mắt).
   - Giữ lại đầy đủ các preset cũ (`capcut_pop`, `capcut_pill`, `capcut_box`, `vox_highlight`, `off`) để người dùng tự chọn khi muốn.
2. **Smart Suppression & Object-Aware Clearance (Không che vật thể & Không nhân đôi chữ)**:
   - Truyền metadata của shot hiện tại vào `autocaptions.Layer.draw(img, t_abs, shot=shot)`:
     - **Tự ẩn thông minh (auto-suppress)** trên các shot mà chính khung hình ĐÃ là thẻ câu chữ lớn (`beat == "twist"` với `fact`, hoặc `title` layout `kinetic`/`reveal` khi toàn khung đang nhấn mạnh chữ), tránh tình trạng **cùng 1 câu xuất hiện 2 lần chồng lên nhau**.
     - **Kiểm tra mật độ điểm ảnh vùng Zone C**: đo độ sáng/độ phức tạp (edge energy) của vùng nền dưới caption; nếu phát hiện vật thể nổi bật (3D/Flow) nằm sát `y = 1390`, tự động dịch nhẹ lên/xuống trong biên `[1330, 1460]` về phía vùng tối thoáng hơn và tăng nhẹ độ mờ nền để chữ luôn đọc rõ mà không cắt ngang chủ thể.
3. **Đồng bộ với Engine**:
   - Khi `cap_preset != "off"`, `pipeline.py` / `codeshot.py` gắn `"captions_on": True` và `"layout_grid": channel()["layout_grid"]` vào `job.json` để cả `html` và `three` tự chừa trống Zone C!

**Tiêu chí nghiệm thu WP-3:**
- Video render với `studio_clean`: phụ đề nằm sạch sẽ ở Zone C, **0% đè lên nhãn beat 2D**, **0% cắt ngang đáy diorama/nhân vật 3D**, không nhân đôi chữ ở `title`/`fact`.

---

### WP-4 — Cơ Chế Đúng Vật Lý/Ngữ Cảnh, Luật "Less Is More" & 3D Framing
**File sở hữu:**
- `config/metaphors.json`
- `vidlib/brief.py`
- `vidlib/linter.py`
- `vidlib/motionplan.py`
- `engines/three/scenes/stage.js`
- `engines/three/hybrid.js`

**Yêu cầu chi tiết:**
1. **3D Framing tôn trọng Zone C (`stage.js`)**:
   - Đọc `JOB.layout_grid` (hoặc `captions_on`): khi phụ đề bật, tự động tăng `footroom` (đẩy tâm nhìn `look.y` xuống nhẹ để toàn bộ mô hình 3D + bệ diorama nổi cao hơn vùng `y > 1280` — không bao giờ bị phụ đề cắt ngang chân nhân vật hay mép sân chạy!).
   - Hỗ trợ prop `heat` keyframe trong `stage.js` (truyền vào `creature.set.heat` / `mannequin.set.heat`) để diễn tả quá nhiệt/căng cơ ngay trên cơ thể nhân vật.
   - Tinh chỉnh `overlay2d` trong `hybrid.js`: gọn hơn (`px: 34–38`), thanh lịch kiểu editorial (nền tối mỏng `rgba(12,15,20,0.82)`, đường dẫn mảnh `2px`, không hộp to cồng kềnh).
2. **Thiết kế lại các cơ chế phức tạp/phi thực tế trong `config/metaphors.json`**:
   - Rà soát và tinh gọn các metaphor về nhiệt/sinh lý/chạy bộ (`core_temperature`, `sweat_cooling`, `lactic_burn`, `oxygen_delivery`, `breaths_per_minute`, `heart_rate_ecg`, `heart_rate_duel`, `glycogen_tank`):
     - Mỗi recipe chỉ tối đa **2–3 actor thật sự cần thiết** (xóa các vật thể trang trí thừa).
     - Thay "nhiệt kế khổng lồ cạnh người chạy" bằng **cơ thể đổi sắc nhiệt `heat` + 1 đường telemetry tối giản** hoặc **cận cảnh giọt mồ hôi bốc hơi mang nhiệt đi**.
3. **Nâng cấp `vidlib/brief.py` & `vidlib/linter.py` theo chuẩn Studio Visual-First**:
   - Thêm mục **VISUAL BUDGET & STORYTELLING RULES (LESS IS MORE)** vào brief gửi LLM:
     - Tối đa 1 chủ thể chính + 1 cơ chế tương tác mỗi shot; cấm nhồi > 3 vật thể nổi bật.
     - **Context Coherence Check**: mọi vật thể trong shot 3D/2D phải thuộc về bối cảnh thực tế của cảnh đó (không thả nhiệt kế/icon y tế bay lơ lửng giữa sân vận động; muốn giải thích cơ quan bên trong thì cắt sang shot cận cảnh giải phẫu/cutaway riêng!).
     - **Visual-First, Text-Minimal**: ưu tiên kể chuyện bằng hành động & thay đổi trạng thái vật lý; hạn chế tối đa `kicker`/`title`/`labels` thừa khi Auto-Captions đã truyền đạt lời thoại.
   - Thêm **Clutter Linter** trong `vidlib/linter.py`:
     - Cảnh báo khi `scene` có `> 4` actors (không tính `z >= 1.8`), hoặc `stage` có `> 5` props (không tính `frame: false`), hoặc tổng số cụm chữ on-screen trong 1 shot `> 3` (hoặc > 12 từ on-screen ngoài `fact`/`quote`).

**Tiêu chí nghiệm thu WP-4:**
- `python -m vidlib.motionplan check` pass 0 lỗi.
- Storyboard nhồi 6 actor + 4 label + title + kicker bị `linter.py` bắt chính xác và gợi ý tinh gọn.

---

### WP-5 — Nhịp Điệu Điện Ảnh (Adult Pacing) & Cấu Hình Kênh
**File sở hữu:**
- `config/channel.json`
- `vidlib/timeline.py`
- `vidlib/vo.py`
- `prompts/storyboard_schema.json`

**Yêu cầu chi tiết:**
1. **Cập nhật `config/channel.json`**:
   - Thêm khối **`layout_grid`**:
     ```json
     "layout_grid": {
       "header": [250, 370],
       "stage": [390, 1240],
       "captions": [1340, 1460]
     }
     ```
   - Điều chỉnh **`pacing`** sang nhịp trưởng thành có khoảng thở (không cắt vụn vội vã):
     - `hook_max_sec: 2.2`, `shot_avg_min: 2.2`, `shot_avg_max: 3.8`, `shot_max_sec: 4.8`, `code_shot_max_sec: 5.5`, `change_every_sec: 1.8`.
   - Điều chỉnh **`vo`** sang nhịp kể chuyện điềm tĩnh, uy tín:
     - `target_wps: 3.0`, `speed: 1.04`, `speed_min: 0.96`, `speed_max: 1.08`, `max_silence_ms: 260`, `keep_silence_ms: 140`, `pre_payoff_pause_ms: 420`.
   - Điều chỉnh **`script`**:
     - `words_per_sec: 3.0`, `words_per_sec_min: 2.4`, `words_per_sec_max: 3.6`, `sentence_words: [7, 14]`.
   - Điều chỉnh **`captions`**:
     - `preset: "studio_clean"`, `y: 1395`, `max_words: 4`, `max_chars: 26`, `suppress_on_text_beats: true`.
2. **Tinh chỉnh `vidlib/timeline.py` & `vidlib/vo.py`**:
   - Không cắt gọt khoảng lặng quá gắt làm câu nói dính liền nghẹt thở; giữ khoảng nghỉ tự nhiên giữa các câu chuyển ý (setup → escalate → payoff → twist) để hình ảnh kịp "lắng" trong đầu người xem.
   - Đảm bảo video cũ (sinh trước `2026-11-23`) hoặc test cũ vẫn tương thích (cập nhật các assertion nếu test đọc thẳng hằng số từ `channel.json`).

**Tiêu chí nghiệm thu WP-5:**
- Video 40s có ~10–13 shot (trung bình 3.0–3.5s/shot), giọng đọc ~3.0 wps tự nhiên, có khoảng thở rõ trước twist/payoff.

---

### WP-6 — Cổng QC Studio Tự Động, Kiểm Thử & Dựng Đối Chiếu Thực Tế
**File sở hữu:**
- `vidlib/qareport.py`
- `vidlib/qagate.py`
- `vidlib/coderender.py` (chỉ thu thập thêm `overlapPairs()` trong `text_crops` / QA)
- `tests/test_round12.py` (mới)
- `docs/ROUND12_REPORT.md` (mới)

**Yêu cầu chi tiết:**
1. **Thêm 3 cổng QC Studio mới vào `qareport.py` & `qagate.py`**:
   - **`không chồng chữ (text overlap)` (ĐỎ — chặn xuất bản)**: đọc `window.overlapPairs()` từ mọi shot code; nếu bất kỳ cặp chữ nào giao nhau `> 5%` diện tích → **ĐỎ**, in rõ tên shot, frame và 2 chuỗi chữ bị chồng!
   - **`phụ đề tách vùng hình (caption clearance)` (VÀNG/ĐỎ)**: kiểm tra không có `textBoxes()` nào của shot code nằm lấn vào vùng Zone C (`y > 1280`) khi Auto-Captions đang bật!
   - **`mật độ thị giác (less is more)` (VÀNG)**: báo cáo tỉ lệ shot vượt quá ngân sách vật thể/chữ.
2. **Bộ kiểm thử tự động `tests/test_round12.py`**:
   - Test `factFlip` và mọi beat 2D không có `overlapPairs()`.
   - Test `autocaptions` preset `studio_clean` + cơ chế tự ẩn trên `fact`/`title`.
   - Test đồng bộ màu & chế độ `editorial` giữa `rig2d` (2D) và `creatures` (3D).
   - Test Clutter Linter bắt lỗi shot quá rối và cho qua shot tinh gọn.
   - Test cổng QA ĐỎ chặn video khi cố tình tạo 2 khung chữ đè nhau.
3. **Kiểm chứng thực tế End-to-End (trên 2 chủ đề KHÁC NHAU)**:
   - **Thử nghiệm A (Running — từ `ideas/run/ideas.json`)**: chọn 1 ý tưởng như *"Your Heart Can Drift Without Speed"* hoặc *"A Tiny Water Loss Changes Everything"*, dựng bằng **`vox-editorial-black`** (dry-run hoặc VO có sẵn) với **10–12 shot tinh gọn** (Visual-First, không rối, hiệu ứng `heat` gắn thân, phụ đề `studio_clean`).
   - **Thử nghiệm B (Tái dựng đối chiếu)**: chạy lại `why-a-human-can-outrun-a-horse-in-a-marathon` để so sánh trước/sau Vòng 12 (0 chồng chữ, nền trưởng thành, 2D↔3D đồng bộ, phụ đề không che vật thể).
   - Lưu ảnh kiểm định vào `qa/round12/` và viết báo cáo nghiệm thu chi tiết bằng tiếng Việt vào `docs/ROUND12_REPORT.md`.

---

## 4. Quy chuẩn Studio Quốc Tế cho AI Viết Storyboard (nhúng vào `vidlib/brief.py`)

Prompt sinh storyboard của tool phải đào tạo LLM suy nghĩ như **Giám đốc Sáng tạo (Creative Director)** của Vox / Fern / Johnny Harris:

1. **1 Shot = 1 Ý tưởng Hình ảnh duy nhất (Single Visual Beat)**: Nếu phải giải thích 2 thứ (ví dụ *vừa nhịp tim vừa nhiệt độ*), tách thành **2 shot nối tiếp**, tuyệt đối không nhồi cả hai vào 1 màn hình.
2. **Show the Physics, Not the Label**: Khán giả đã NGHE giọng đọc và THẤY phụ đề tinh gọn ở đáy → **không viết lại lời thoại lên giữa màn hình**. Trên màn hình chỉ để: hành động chuyển động + tối đa 1 con số/đơn vị neo thực tế (`41.2°C`, `157 BPM`, `22 MI`).
3. **Context-Locked Objects**:
   - Đang ở bối cảnh sân chạy / đường núi → chỉ xuất hiện vận động viên, đường chạy, ánh sáng, mồ hôi, sắc nhiệt cơ thể.
   - Muốn giải thích cơ quan bên trong (tim, phổi, mạch máu, cơ bắp) → **chuyển sang shot Cutaway/Anatomical tối giản trên nền đen**, không ghép nội tạng bay lơ lửng giữa bãi cỏ!
4. **Cinematic Breathing Room**: Mỗi câu VO dài 8–13 từ, tốc độ ~3.0 từ/giây, mỗi shot giữ **2.5–4.0 giây** để chuyển động camera và hiệu ứng vật lý diễn ra trọn vẹn.

---

## 5. Phân quyền file & Giao thức tránh xung đột

| Gói việc | File sở hữu độc quyền | Không được chạm |
|---|---|---|
| **WP-1** | `engines/three/props.js`, `creatures.js`, `paint.js`, `engines/html/rig2d.js`, `looks.js`, `vidlib/codeshot.py` | `beats.js`, `core.js`, `autocaptions.py`, `channel.json` |
| **WP-2** | `engines/html/core.js`, `engines/html/beats.js` | `looks.js`, `rig2d.js`, `autocaptions.py`, `props.js` |
| **WP-3** | `vidlib/autocaptions.py`, `vidlib/render.py`, `vidlib/pipeline.py` (khối render/captions) | `beats.js`, `core.js`, `props.js`, `metaphors.json` |
| **WP-4** | `config/metaphors.json`, `vidlib/brief.py`, `vidlib/linter.py`, `vidlib/motionplan.py`, `engines/three/scenes/stage.js`, `engines/three/hybrid.js` | `props.js`, `creatures.js`, `core.js`, `beats.js` |
| **WP-5** | `config/channel.json`, `vidlib/timeline.py`, `vidlib/vo.py`, `prompts/storyboard_schema.json` | `engines/*`, `autocaptions.py`, `qareport.py` |
| **WP-6** | `vidlib/qareport.py`, `vidlib/qagate.py`, `vidlib/coderender.py`, `tests/test_round12.py`, `docs/ROUND12_REPORT.md` | Các file thuộc WP-1..WP-5 (chỉ đọc/tích hợp cuối) |

**Giao thức phối hợp:**
- **Đợt 1 (song song):** Chạy `WP-5` (cố định `channel.json` & `layout_grid` trước tiên), cùng lúc chạy `WP-1`, `WP-2`, `WP-3`.
- **Đợt 2 (song song sau Đợt 1):** Chạy `WP-4` (đọc `heat` từ WP-1 & `layout_grid` từ WP-5) và `WP-6` (đọc `overlapPairs()` từ WP-2 & `studio_clean` từ WP-3).
- **Bước cuối (Orchestrator):** Chạy toàn bộ test + lint + dựng thử 2 video thực tế + mở ảnh `qa/round12/*.jpg` để **tự soi bằng mắt (visual inspection)** từng khung hình trước khi báo cáo xong.

---

## 6. Định nghĩa "Hoàn thành" (Definition of Done)

Nhiệm vụ chỉ được tính là **XONG** khi đạt đủ **100%** các tiêu chí sau:
1. `python -m ruff check .` → **0 lỗi**.
2. `python -m unittest discover -s tests -t .` → **100% pass** (toàn bộ test cũ + `tests/test_round12.py`).
3. `python -m vidlib.motionplan check` → **0 lỗi**.
4. **0 lỗi chồng chữ (`overlapPairs == []`)** trên toàn bộ 15 beat HTML (đã kiểm chứng trên `factFlip` và contact sheet).
5. **Auto-Captions `studio_clean`** nằm gọn trong Zone C, không che vật thể 3D/2D, tự ẩn trên shot chữ lớn.
6. **Đồng bộ 2D ↔ 2.5D ↔ 3D & Thẩm mỹ trưởng thành**: ảnh đối chiếu tại `qa/round12/sync_2d_3d.jpg` và `qa/round12/adult_sets.jpg` chứng minh 2D và 3D cùng 1 ngôn ngữ tạo hình người lớn, không màu kẹo/trẻ con.
7. **Đã render và soi trực quan ít nhất 2 video thực tế** (1 chủ đề mới từ `ideas/run/ideas.json` + 1 bản đối chiếu `why-a-human-can-outrun-a-horse-in-a-marathon`), QA đạt **0 lỗi ĐỎ**, báo cáo đầy đủ bằng tiếng Việt tại `docs/ROUND12_REPORT.md`.
8. **Không `git commit` / `git push`** — chỉ để sạch sẽ (hoặc `git add -A` nếu chủ kênh yêu cầu) để chủ kênh tự duyệt.
