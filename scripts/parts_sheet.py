"""Contact sheet vòng 21 — "bộ phận sống" + zoom xuyên bộ phận của engine html (render thật bằng Edge headless).

  python scripts/parts_sheet.py [style] [--out qa/round21] [--frames 90]

Dựng 3 cảnh mẫu: (1) nhân vật x-ray lộ não/tim/phổi + vầng sáng bộ phận + bong bóng suy nghĩ + cầm điện thoại;
(2) cú/vịt/nhà khoa học (rig mới) nói chuyện, mắt nhìn theo nhau, đi bộ không trượt chân;
(3) camera bám `hero.eye` rồi zoom 16× vào mắt (cuối shot = khung dẫn cho `zoom_through`).
Mỗi cảnh lấy 5 frame → <out>/parts_<style>.jpg. Để xem bằng mắt khi sửa rig2d.js / beat scene."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PIL import Image, ImageDraw  # noqa: E402

from engines import adapter  # noqa: E402
from vidlib.common import font  # noqa: E402

SCENES = {
    "xray": {
        "kicker": "INSIDE YOU", "title": "Stress, live",
        "actors": [
            {"id": "hero", "icon": "rig:adult:idle:sad", "x": 0.42, "y": 0.6, "size": 820, "xray": 0,
             "organs": ["brain", "heart", "lungs", "stomach"], "bpm": 110, "hold": "phone",
             "keys": [{"u": 0.25, "xray": 1, "ease": "smooth"}, {"u": 0.55, "focus": "heart"},
                      {"u": 0.8, "focus": "brain"}]},
            {"id": "clock", "icon": "clock", "x": 0.8, "y": 0.45, "size": 150, "role": "accent"},
        ],
        "labels": [{"text": "I can't be late!", "of": "hero.head", "bubble": "thought", "u": 0.1},
                   {"text": "110 BPM", "x": 0.78, "y": 0.6, "u": 0.55, "tag": True}],
    },
    "cast": {
        "kicker": "NEW CAST", "title": "Owl · Duck · Scientist",
        "actors": [
            {"id": "owl", "icon": "rig:owl:idle", "x": 0.22, "y": 0.62, "size": 300, "talk": [[0.1, 0.5]],
             "look_at": "sci.head"},
            {"id": "duck", "icon": "rig:duck:walk", "x": 0.15, "y": 0.86, "size": 220, "keys": [{"u": 1, "x": 0.55}]},
            {"id": "sci", "icon": "rig:scientist:point", "x": 0.7, "y": 0.6, "size": 480, "talk": [[0.5, 0.95]],
             "look_at": "owl.head",
             "hold": "flask"},
        ],
        "labels": [{"text": "Who?", "of": "owl.mouth", "bubble": "speech", "u": 0.12},
                   {"text": "You, owl.", "of": "sci.mouth", "bubble": "speech", "u": 0.55}],
    },
    "dive": {
        "kicker": "ZOOM THROUGH", "title": "Into the eye",
        "actors": [{"id": "hero", "icon": "rig:kid:idle:shock", "x": 0.5, "y": 0.62, "size": 560}],
        "camera": [{"u": 0.0, "x": 0.5, "y": 0.55}, {"u": 0.45, "at": "hero.head", "zoom": 1.6},
                   {"u": 1.0, "at": "hero.eye", "zoom": 16, "ease": "easeIn"}],
        "labels": [{"text": "pupil", "of": "hero.eye", "u": 0.3, "tag": True}],
    },
}


def main(argv):
    style = argv[0] if argv and not argv[0].startswith("--") else "cosmic-flat-black"
    out_dir = os.path.join(ROOT, argv[argv.index("--out") + 1]) if "--out" in argv else os.path.join(ROOT, "qa", "round21")
    n = int(argv[argv.index("--frames") + 1]) if "--frames" in argv else 90
    eng = adapter.get("html")
    rows = []
    for name, params in SCENES.items():
        work = os.path.join(ROOT, "qa", "round21", "_work", style, name)
        spec = adapter.ShotSpec(sid=name, engine="html", scene="scene", params=params, frames=n, style=style, work=work,
                                index=[1, 3])
        job = eng.job(spec)
        fr = [0, n // 4, n // 2, (3 * n) // 4, n - 1]
        eng.render(job, os.path.join(work, "frames"), fr, log=lambda m: None, workers=2)
        cells = []
        for f in fr:
            im = Image.open(os.path.join(work, "frames", f"f{f:04d}.jpg")).convert("RGB").resize((270, 480))
            ImageDraw.Draw(im).text((8, 6), f"{name} f{f}", font=font(20, "bold"), fill=(255, 255, 0))
            cells.append(im)
        rows.append(cells)
    sheet = Image.new("RGB", (270 * 5, 480 * len(rows)), (10, 10, 12))
    for r, cells in enumerate(rows):
        for c, im in enumerate(cells):
            sheet.paste(im, (c * 270, r * 480))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"parts_{style}.jpg")
    sheet.save(path, quality=88)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
