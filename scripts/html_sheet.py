"""Contact sheet của engine html: mọi beat × một style (frame 1/4, giữa, cuối) → qa/html/<style>.jpg.
  python scripts/html_sheet.py <style>[,style…] [beat,beat…] [--frames 60] [--out tên] [--dir qa/looks2d] [--data demo.json]
  python scripts/html_sheet.py --rigs <style>[,style…] [--dir qa/looks2d] [--frame 40]
      → bảng nhân vật 2D rig2d: mọi loài × mọi hành động (một ô mỗi cặp) → <dir>/rigs_<style>.jpg
Dùng dữ liệu mẫu engines/html/demo.json. Để xem nhanh khi sửa look/beat. Render ≤ 2 worker (chừa GPU cho việc khác)."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PIL import Image, ImageDraw  # noqa: E402

from engines import adapter, html  # noqa: E402
from vidlib.common import load_json  # noqa: E402

WORKERS = 2


def _arg(argv, key, default=None):
    return argv[argv.index(key) + 1] if key in argv else default


def beat_sheet(style, beats, n, data, out_dir, out_name=None):
    demo = load_json(data)   # khoá "beat__layout" → beat đó với biến thể bố cục trong params
    eng = adapter.get("html")
    cells, secs = [], []
    for i, b in enumerate(beats):
        work = os.path.join(ROOT, "qa", "html", "_work", style, b)
        spec = adapter.ShotSpec(
            sid=b, engine="html", scene=b.split("__")[0], params=demo[b], frames=n, style=style, work=work,
            index=[i + 1, len(beats)]
        )
        job = eng.job(spec)
        fr = [n // 4, n // 2, n - 1]
        st = eng.render(job, os.path.join(work, "frames"), fr, log=lambda m: None, workers=WORKERS)
        if st.get("sec_per_frame"):
            secs.append(st["sec_per_frame"])
        cells += [Image.open(os.path.join(work, "frames", f"f{f:04d}.jpg")).convert("RGB").resize((270, 480)) for f in fr]
    cols = 6 if len(cells) > 6 else len(cells)
    rows = -(-len(cells) // cols)
    sheet = Image.new("RGB", (cols * 270, rows * 480))
    for i, im in enumerate(cells):
        sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{out_name or style}.jpg")
    sheet.save(out, quality=88)
    return out, secs


def rig_sheet(style, out_dir, frame=40):
    """Mỗi loài một khung 1080×1920 (12 hành động, lưới 3×4, nhãn tên) → ghép thành một bảng."""
    from engines.html import rig2d  # noqa: PLC0415

    eng = adapter.get("html")
    species, actions = rig2d.species(), rig2d.actions()
    tiles = []
    for sp in species:
        actors, labels = [], []
        for j, a in enumerate(actions):
            x, y = 0.2 + (j % 3) * 0.3, 0.3 + (j // 3) * 0.16
            actors.append({"id": f"{sp}{j}", "icon": f"rig:{sp}:{a}", "x": x, "y": y, "size": 250})
            labels.append({"text": a, "x": x, "y": y + 0.075, "u": 0, "size": 40})
        work = os.path.join(ROOT, "qa", "html", "_work", style, f"rig_{sp}")
        spec = adapter.ShotSpec(sid=f"RIG_{sp}", engine="html", scene="scene", frames=frame + 1, style=style, work=work,
                                params={"title": sp, "actors": actors, "labels": labels})
        job = eng.job(spec)
        eng.render(job, os.path.join(work, "frames"), [frame], log=lambda m: None, workers=1)
        tiles.append(Image.open(os.path.join(work, "frames", f"f{frame:04d}.jpg")).convert("RGB").resize((360, 640)))
    cols = 6
    rows = -(-len(tiles) // cols)
    sheet = Image.new("RGB", (cols * 360, rows * 640 + 60))
    ImageDraw.Draw(sheet).text((12, 18), f"rig2d · {style} · frame {frame}", fill=(200, 200, 200))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 360, 60 + (i // cols) * 640))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"rigs_{style}.jpg")
    sheet.save(out, quality=86)
    return out


def main(argv):
    out_dir = os.path.join(ROOT, _arg(argv, "--dir", os.path.join("qa", "html")))
    if "--rigs" in argv:
        for style in _arg(argv, "--rigs").split(","):
            print(rig_sheet(style, out_dir, int(_arg(argv, "--frame", 40))))
        return
    styles = argv[0].split(",")
    beats = argv[1].split(",") if len(argv) > 1 and not argv[1].startswith("--") else list(html.BEATS)
    n = int(_arg(argv, "--frames", 60))
    data = _arg(argv, "--data", os.path.join(ROOT, "engines", "html", "demo.json"))
    for style in styles:
        out, secs = beat_sheet(style, beats, n, data, out_dir, _arg(argv, "--out") if len(styles) == 1 else None)
        print(out, f"(≈{sum(secs) / len(secs):.3f} s/frame gồm mở trình duyệt)" if secs else "")


if __name__ == "__main__":
    main(sys.argv[1:])
