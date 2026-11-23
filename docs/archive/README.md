# docs/archive — tài liệu lịch sử (không còn bảo trì)

Các file ở đây **mô tả trạng thái tại thời điểm viết**, không phải hiện trạng tool. Đọc hiện trạng ở `CLAUDE.md`,
`docs/ARCHITECTURE.md`, `HUONG_DAN.md`, `docs/CHANGELOG.md`. Chuyển vào đây bằng `git mv` (giữ lịch sử:
`git log --follow docs/archive/<file>`). Nội dung giữ nguyên văn — đường dẫn bên trong còn trỏ chỗ cũ: file nào đã
chuyển thì đọc `docs/<file>` thành `docs/archive/<file>`.

| File | Viết lúc | Nội dung | Vì sao lưu trữ | Thay bằng |
|---|---|---|---|---|
| `AUDIT.md` | 13/11/2026 (vòng 1) | hiện trạng tool trước khi nâng cấp thành pipeline một lệnh | mô tả trạng thái đã hết đúng (chính AUDIT_V2 ghi ở AUD-1312) | `docs/ARCHITECTURE.md`, `CLAUDE.md` |
| `PLAN.md` | 13/11/2026 (vòng 1) | kế hoạch + quyết định kiến trúc vòng 1, kết quả kiểm chứng Flow, quy tắc nhịp lấy từ research | kế hoạch đã làm xong; quy tắc đã vào `config/channel.json` + `config/flow-models.json` | `docs/CHANGELOG.md` (vòng 1), `config/*.json` |
| `AUDIT_V2.md` | 15–16/11/2026 (vòng 9) | audit 13 mảng, 142 phát hiện, trạng thái sửa | bản chụp một lần, sinh bởi `scripts/build_audit_doc.py` (đã gỡ, xem commit `3937877`) | việc còn mở: `docs/ROADMAP_V2.md` |
| `audit/area-*.md` (7) | 15/11/2026 (vòng 9) | báo cáo con từng mảng, nguồn web có ngày | bằng chứng gốc của AUDIT_V2; vẫn được trích ở `_doc` của `config/delivery.json`, `rights/ledger.json` | — |
| `RUN_LOG.md` | 15–16/11/2026 | nhật ký lượt chạy vòng 8 + 9 + UI | nhật ký phiên đã đóng | `docs/RUN_REPORT.md` |
| `BLOCKERS.md` | 15/11/2026 | B-01, B-02 (Atlas bị Cloudflare/clipboard chặn) | cả hai đã gỡ ngày 15/11 | `docs/DECISIONS.md` D-002…D-004b |

Quy ước: một tài liệu hết hiệu lực thì chuyển vào đây + thêm một dòng vào bảng (không xoá — xem
`docs/research/REPO_BEST_PRACTICES.md`, mục docs-as-code).
