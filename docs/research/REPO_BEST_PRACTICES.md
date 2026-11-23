# Giữ repo + pipeline gọn — các công ty lớn làm gì (tra 22/11/2026)

Ngắn gọn: mỗi nguyên tắc → nguồn → việc cụ thể ở repo này (mã việc trỏ tới bảng trong `docs/CLEANUP_PLAN.md`).

## 1. Mã/tài liệu là khoản nợ, không phải tài sản — xoá có chủ đích, có hạn
- **Nguồn**: *Software Engineering at Google*, chương 15 "Deprecation" — "code is a liability, not an asset"; cảnh báo
  khuyến nghị (advisory) hiếm khi tự dọn xong, cần **hạn chót + người phụ trách**, chặn dùng mới ("prevent
  backsliding") ([abseil.io/ch15](https://abseil.io/resources/swe-book/html/ch15.html)). Google SRE, chương
  "Simplicity": xoá mã chết thường xuyên, "negative lines of code", API tối thiểu ([sre.google](https://sre.google/sre-book/simplicity/)).
- **Ở đây**: lệnh cũ `new/prompts/preview/build/cover` + lệnh chết `setup/looks` trong `studio.py` có từ vòng 1, chưa
  ai đặt hạn → đề xuất **in cảnh báo "sẽ bỏ ở vòng 12"** rồi xoá (P-02). Launcher macOS `scripts/*.command` (máy chủ
  kênh là Windows, venv macOS không chạy) → đã xoá (A-07). Nhánh `ui` lặp hai lần trong `studio.py main` → xoá (P-01).

## 2. Một nguồn sự thật cho tài liệu; tài liệu chết thì xoá/lưu trữ; sửa tài liệu cùng lần sửa mã
- **Nguồn**: Google documentation guide — "Minimum viable documentation", "Change your documentation in the same CL
  as the code change", "Dead docs are bad… delete what you're certain is wrong", liên kết thay vì chép lại
  ([google.github.io/styleguide/docguide](https://google.github.io/styleguide/docguide/best_practices.html)).
- **Ở đây**: 6 tài liệu lịch sử (AUDIT 13/11, PLAN vòng 1, AUDIT_V2 + 7 báo cáo con, RUN_LOG, BLOCKERS đã gỡ hết) →
  `docs/archive/` có chỉ mục (A-01…A-06). CLAUDE.md lệch thực tế (ghi `ui/web/app/features/*`, thực tế `pages/`;
  thiếu `vidlib/pipeline.py`…) → sửa khi WP-I gom tài liệu (D-01). Bảng lệnh có ở 4 nơi (CLAUDE.md, README,
  HUONG_DAN, docstring `studio.py`) → một bảng sinh từ parser (P-04).

## 3. Ghi quyết định thành ADR ngắn, bất biến, thay bằng bản mới
- **Nguồn**: Michael Nygard (2011) qua [Martin Fowler — ADR](https://www.martinfowler.com/bliki/ArchitectureDecisionRecord.html);
  Microsoft Engineering Playbook — decision log, ADR đầu tiên "record architecture decisions"
  ([playbook.microsoft.com](https://playbook.microsoft.com/code-with-engineering/design/design-reviews/decision-log/)).
- **Ở đây**: `docs/DECISIONS.md` (D-001…D-011) đã đúng tinh thần ADR → **giữ**, thêm trạng thái (`chờ chủ kênh` /
  `đã chốt` / `thay bởi D-…`). Các mục "Cần anh quyết định" đang chép ở 3 nơi (RUN_REPORT, AUDIT_V2, ROADMAP_V2) →
  gộp về một bảng trong DECISIONS.md (G-01).

## 4. Pipeline kiểu DAG, cache theo NỘI DUNG (không theo thời gian sửa)
- **Nguồn**: Bazel — mỗi action khai đủ đầu vào/đầu ra; action cache = hash action → kết quả, CAS theo nội dung;
  build tái lập được thì dùng lại kết quả ở máy khác ([bazel.build/remote/caching](https://bazel.build/remote/caching)).
- **Ở đây**: `pipeline.STAGES` đã là chuỗi stage có dấu vân tay (`work/state.json`) — đúng hướng. Lệch: `_fp` băm
  **đường dẫn + mtime** (AUD-213: đổi máy/checkout = dựng lại); stage `script` trong `STAGES` không có hàm riêng (ghi
  trong `s_storyboard`); stage `clips` là cổng chờ, không phải việc → đề xuất tách "stage" khỏi "cổng chờ" (Q-01, Q-02).

## 5. Đồ sinh ra không vào kho mã; artifact trung gian có hạn giữ + GC
- **Nguồn**: GitHub — repo nên < 1 GB, file nhị phân lớn phân phối bằng release/LFS
  ([docs.github.com — large files](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github));
  GitHub Actions — artifact có `retention-days` (mặc định 90 ngày), dọn theo lịch
  ([docs.github.com — retention](https://docs.github.com/en/organizations/managing-organization-settings/configuring-the-retention-period-for-github-actions-artifacts-and-logs-in-your-organization));
  `bazel-remote` có GC giới hạn dung lượng (cùng trang Bazel ở mục 4); git: `git gc` gói object rời
  ([git-scm.com/docs/git-gc](https://git-scm.com/docs/git-gc)).
- **Ở đây**: `qa/` chiếm **75%** dung lượng file track (39 MB / 134 file, ảnh UI cũ, mp4, ảnh diff visreg đổi mỗi lần
  chạy) → chỉ track ảnh kiểm "đã duyệt" nhỏ + golden ở `tests/golden/`, còn lại gitignore (R-01, cần chủ kênh đồng ý
  vì đổi cách xem ảnh kiểm). `docs/charsheet_*.jpg`, `docs/perf*.json` là đầu ra tool → chuyển sang `qa/` (R-02).
  `projects/*/work/` ~200 MB/video (frame shot code) → GC tự động sau khi qua cổng QA + version, giữ N dự án gần nhất
  (R-03). `out/deliver/` 3 bản remux giống hệt nhau → hardlink (R-04). `.git` 62 MB toàn object rời → `git gc` (R-05).

## 6. CLI nhất quán: một kiểu lệnh, không lệnh "bắt tất cả", mặc định đúng cho số đông, cảnh báo trước khi bỏ
- **Nguồn**: Command Line Interface Guidelines — "Be consistent across subcommands", "Don't have a catch-all
  subcommand", "Make the default the right thing for most users", "Warn before you make a non-additive change"
  ([clig.dev](https://clig.dev/)).
- **Ở đây**: `python studio.py "<ý tưởng>"` là lệnh bắt tất cả (đã vá AUD-112 bằng luật "có dấu cách"); `--yes` vừa xác
  nhận map clip vừa bỏ qua look-check (hai nghĩa); 27 từ khoá lệnh, nhóm `styles --plan/--cards/--gallery/--rank` là cờ
  thay vì lệnh con; danh sách gợi ý khi gõ sai thiếu `rerender/shots/trim/svg` → đề xuất nhóm lệnh danh từ–động từ
  (`project …`, `style …`, `asset …`) với bí danh cũ có cảnh báo (P-03…P-05).

## 7. Thay đổi nhỏ, tách dọn dẹp khỏi tính năng
- **Nguồn**: Google eng-practices — "Small CLs", tách refactor khỏi thay đổi chức năng
  ([google.github.io/eng-practices](https://google.github.io/eng-practices/review/developer/small-cls.html)); Google
  Testing Blog — Code Health ([testing.googleblog.com](https://testing.googleblog.com/2017/04/code-health-googles-internal-code.html)).
- **Ở đây**: dọn dẹp vòng 10 đi thành các lô riêng, mỗi lô có test xanh trước/sau (đợt 1 = docs + script; đợt sau =
  `studio.py`/CLAUDE.md khi WP sở hữu xong). Gợi ý commit tách: "chore(docs): archive…", "chore(scripts): remove macOS
  launchers" — chủ kênh tự commit.
