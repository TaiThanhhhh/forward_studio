"""Bảng soát kho tài sản thư viện (vòng 10, WP-A) — xem từng mô hình/icon ở các look, loại cái hỏng/xấu (index → rejected).

  python scripts/assets_sheet.py [gói…] [--looks toon3d-lab,retro90-lowpoly-black] [--svg] [--svg-looks a,b]
→ qa/assets3d/<gói>__<style>.jpg  (mỗi trang 15 mô hình 3×5, có nhãn tên; nhân vật chạy anim mặc định)
→ qa/assetlib/<style>_pNN.jpg      (icon SVG thư viện, 48/trang, nhãn tên đè bằng PIL)
3D: MỘT trang trình duyệt cho cả gói — mỗi frame hiện một trang lưới (visible theo frame, cùng ô lưới → cùng khung máy),
render 2 worker. Mô hình chuẩn hoá theo cạnh lớn nhất (size) để cùng cỡ ô.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from engines import adapter  # noqa: E402
from vidlib import assets3d as A  # noqa: E402
from vidlib import coderender  # noqa: E402

COLS, ROWS, CELL = 3, 5, 1.15
LOOKS = ["toon3d-lab", "retro90-lowpoly-black"]
SVG_LOOKS = ["flat-vector-black", "line-boil-black", "sketchnote-black"]
OUT3D = os.path.join(ROOT, "qa", "assets3d")
OUT2D = os.path.join(ROOT, "qa", "assetlib")


def pages_of(names, per=COLS * ROWS):
    return [names[i:i + per] for i in range(0, len(names), per)]


def grid_params(pages, fps=30):
    """Mọi trang chồng lên cùng lưới; prop chỉ hiện ở frame = số trang của nó (đổi ở nửa frame → không lệch số thực)."""
    props = []
    for k, page in enumerate(pages):
        vis = [{"t": (k - 0.5) / fps, "visible": True}] if k else []
        vis.append({"t": (k + 0.5) / fps, "visible": False})
        for i, n in enumerate(page):
            c, r = i % COLS, i // COLS
            x, y = (c - (COLS - 1) / 2) * CELL, (ROWS - 1 - r) * CELL * 1.18
            e = A.models()[n]
            p = {"id": f"m{k}_{i}", "type": f"model:{n}", "at": [x, y, 0], "rot": [0, -25, 0], "size": 0.82,
                 "visible": k == 0, "keys": list(vis), "blob": False}
            if e.get("anims"):
                p["anim_offset"] = 0.6
            props.append(p)
            props.append({"id": f"t{k}_{i}", "type": "text", "text": n[:22], "w": 1.05, "h": 0.12, "px": 120,
                          "at": [x, y - 0.13, 0.45], "visible": k == 0, "keys": list(vis), "blob": False})
    return {"props": props, "blob": False, "frame": {"orbit": 0, "push": 0, "headroom": 0.0, "margin": 1.04, "elev": 8}}


def sheet3d(pack, style, workers=2, log=print):
    names = [n for n, e in A.models().items() if e["pack"] == pack]
    if not names:
        return None
    pages = pages_of(names)
    work = os.path.join(OUT3D, "_work", f"{pack}__{style}")
    spec = adapter.ShotSpec(sid="LIB", engine="three", scene="stage", params=grid_params(pages), frames=max(2, len(pages)),
                            fps=30, width=1080, height=1920, style=style, work=work)
    job = adapter.get("three").job(spec)
    fdir = os.path.join(work, "frames")
    st = coderender.render(job, fdir, frames=list(range(len(pages))), workers=min(workers, len(pages)), log=lambda *_: None)
    ims = [Image.open(os.path.join(fdir, f"f{k:04d}.jpg")).convert("RGB").resize((540, 960)) for k in range(len(pages))]
    per_row = 4
    rows = (len(ims) + per_row - 1) // per_row
    out = Image.new("RGB", (540 * min(per_row, len(ims)), 960 * rows))
    for i, im in enumerate(ims):
        out.paste(im, ((i % per_row) * 540, (i // per_row) * 960))
    os.makedirs(OUT3D, exist_ok=True)
    path = os.path.join(OUT3D, f"{pack}__{style}.jpg")
    out.save(path, quality=84)
    log(f"  ✓ {os.path.relpath(path, ROOT)} · {len(names)} mô hình · {len(pages)} trang · {st.get('sec_per_frame')} s/trang")
    return path


def sheet_svg(style, per=48, cols=6, log=print):
    icons = sorted((A.svg_index().get("icons") or {}).keys())
    eng = adapter.get("html")
    try:
        font = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "RobotoMono-Variable.ttf"), 19)
    except OSError:
        font = ImageFont.load_default()
    os.makedirs(OUT2D, exist_ok=True)
    paths = []
    for k, chunk in enumerate(pages_of(icons, per)):
        work = os.path.join(OUT2D, "_work", style, f"p{k}")
        objs = [{"parts": A.svg_parts(n) or []} for n in chunk]
        spec = adapter.ShotSpec(sid=f"LIB{k}", engine="html", scene="catalog", frames=24, style=style, work=work,
                                params={"names": objs, "cols": cols, "no_bg": True,
                                        "title": f"svg lib · {style} · {k + 1}/{(len(icons) + per - 1) // per}"})
        job = eng.job(spec)
        eng.render(job, os.path.join(work, "frames"), [20], log=lambda m: None, workers=1)
        im = Image.open(os.path.join(work, "frames", "f0020.jpg")).convert("RGB")
        d = ImageDraw.Draw(im)
        W = im.size[0]
        cw = (W - 80) / cols
        for i, n in enumerate(chunk):
            x, y = 40 + (i % cols + 0.5) * cw, 140 + (i // cols) * 214 + 80 + 108
            d.rectangle([x - cw / 2 + 4, y - 16, x + cw / 2 - 4, y + 16], fill=(0, 0, 0))
            d.text((x, y), n[:15], fill=(200, 200, 200), font=font, anchor="mm")
        p = os.path.join(OUT2D, f"{style}_p{k:02d}.jpg")
        im.save(p, quality=82)
        paths.append(p)
    log(f"  ✓ qa/assetlib/{style}_p*.jpg · {len(icons)} icon · {len(paths)} trang")
    return paths


def main(argv):
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    looks = LOOKS
    if "--looks" in argv:
        looks = argv[argv.index("--looks") + 1].split(",")
    if "--svg" in argv:
        sl = argv[argv.index("--svg-looks") + 1].split(",") if "--svg-looks" in argv else SVG_LOOKS
        for st in sl:
            sheet_svg(st)
        return 0
    skip = {argv[i + 1] for i, a in enumerate(argv) if a == "--looks"}
    packs = [a for a in argv if not a.startswith("--") and a not in skip] or list(A.packs())
    for st in looks:
        for pk in packs:
            sheet3d(pk, st)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
