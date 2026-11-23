"""Bảng xem MỌI đạo cụ (icon) của engine html theo từng style — để soát chất lượng khi thêm/sửa icon.

  python scripts/icon_sheet.py [style1,style2,…]        (mặc định: một style đại diện cho mỗi look)
→ qa/icons/<style>.jpg (mỗi trang 40 icon, ghép dọc) + qa/icons/_all.jpg (các style cạnh nhau, thu nhỏ).
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PIL import Image  # noqa: E402

from engines import adapter, html  # noqa: E402

DEFAULT = [
    "flat-vector-black",
    "line-boil-black",
    "isometric-black",
    "hud-black",
    "sticker-explainer-black",
    "swiss-motion-black",
    "spy-titles-black",
    "sketchnote-black",
    "synthwave-black",
    "chalk",
]
PER_PAGE = 40


def sheet(style, out_dir):
    names = sorted(html.icon_table()[0])
    pages = [names[i : i + PER_PAGE] for i in range(0, len(names), PER_PAGE)]
    eng = adapter.get("html")
    imgs = []
    for k, chunk in enumerate(pages):
        work = os.path.join(ROOT, "qa", "icons", "_work", style, f"p{k}")
        spec = adapter.ShotSpec(
            sid=f"ICONS{k}",
            engine="html",
            scene="catalog",
            frames=24,
            style=style,
            work=work,
            params={"names": chunk, "cols": 5, "no_bg": True, "title": f"{style} · {k + 1}/{len(pages)}"},
        )
        job = eng.job(spec)
        eng.render(job, os.path.join(work, "frames"), [20], log=lambda m: None, workers=1)
        imgs.append(Image.open(os.path.join(work, "frames", "f0020.jpg")).convert("RGB"))
    w, h = imgs[0].size
    out = Image.new("RGB", (w * len(imgs), h))
    for i, im in enumerate(imgs):
        out.paste(im, (i * w, 0))
    p = os.path.join(out_dir, f"{style}.jpg")
    out.save(p, quality=88)
    return p


def main(argv):
    styles = argv[0].split(",") if argv else DEFAULT
    out_dir = os.path.join(ROOT, "qa", "icons")
    os.makedirs(out_dir, exist_ok=True)
    paths = [sheet(s, out_dir) for s in styles]
    ims = [Image.open(p) for p in paths]
    sw = 900
    ims = [im.resize((sw, int(im.height * sw / im.width))) for im in ims]
    allim = Image.new("RGB", (sw, sum(i.height for i in ims)))
    y = 0
    for im in ims:
        allim.paste(im, (0, y))
        y += im.height
    allim.save(os.path.join(out_dir, "_all.jpg"), quality=85)
    print("\n".join(paths))


if __name__ == "__main__":
    main(sys.argv[1:])
