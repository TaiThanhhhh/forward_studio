"""Ghép ảnh trước/sau của UI → qa/ui/before-after.png (cột trái: UI cũ qa/ui/before, cột phải: UI mới qa/ui/after)."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRS = [("1440x900_new.png", "1440x900_projects.png", "Tạo video / Projects"),
         ("1440x900_projects_P_tab-shots.png", "1440x900_p_P_board.png", "Shot → Board"),
         ("1440x900_projects_P.png", "1440x900_p_P_generate.png", "Dự án → Generate (bảng sản xuất Flow)"),
         ("1440x900_projects_P_tab-outputs.png", "1440x900_p_P_edit.png", "Kết quả → Edit (timeline)"),
         ("1440x900_projects_P_tab-qa.png", "1440x900_p_P_review.png", "QA → Review (comment timecode)"),
         ("1440x900_jobs.png", "1440x900_p_P_deliver.png", "Job → Deliver (cổng QA, gói nền tảng)"),
         ("1440x900_library_styles.png", "1440x900_library.png", "Thư viện style")]


def main():
    W, H, PAD, LAB = 960, 600, 16, 34
    font = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "RobotoMono-Variable.ttf"), 20)
    rows = [(b, a, t) for b, a, t in PAIRS if os.path.exists(os.path.join(ROOT, "qa", "ui", "before", b))
            and os.path.exists(os.path.join(ROOT, "qa", "ui", "after", a))]
    sheet = Image.new("RGB", (W * 2 + PAD * 3, len(rows) * (H + LAB + PAD) + PAD + 40), (17, 17, 17))
    d = ImageDraw.Draw(sheet)
    d.text((PAD, 10), "TRƯỚC (UI cũ)", font=font, fill=(168, 168, 168))
    d.text((W + PAD * 2, 10), "SAU (UI công đoạn)", font=font, fill=(127, 155, 255))
    y = 40 + PAD
    for b, a, t in rows:
        d.text((PAD, y), t, font=font, fill=(236, 236, 236))
        for i, p in enumerate((os.path.join(ROOT, "qa", "ui", "before", b), os.path.join(ROOT, "qa", "ui", "after", a))):
            sheet.paste(Image.open(p).convert("RGB").resize((W, H)), (PAD + i * (W + PAD), y + LAB))
        y += H + LAB + PAD
    out = os.path.join(ROOT, "qa", "ui", "before-after.png")
    sheet.save(out)
    print(out, len(rows), "cặp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
