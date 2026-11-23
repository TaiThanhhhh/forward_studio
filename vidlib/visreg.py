"""Visual regression (AUD-903): golden frame cho từng engine/look, so SSIM + pHash.

  python scripts/visual_regression.py            # render → so với tests/golden/*.png → qa/visreg/report.md (exit 1 khi lệch)
  python scripts/visual_regression.py --update   # chấp nhận hình hiện tại làm golden mới (sau khi đã xem bằng mắt)

Mỗi ca dựng một frame cố định (dữ liệu demo, seed cố định) ở 1080×1920 rồi thu về 270×480 để so: SSIM ≥ ngưỡng và
khoảng cách Hamming pHash ≤ ngưỡng (GPU khác nhau cho lệch rất nhỏ → ngưỡng có biên).
"""
import os

import cv2
import numpy as np

from .common import ROOT

GOLDEN = os.path.join(ROOT, "tests", "golden")
OUT = os.path.join(ROOT, "qa", "visreg")
SIZE = (270, 480)
SSIM_MIN = 0.97
PHASH_MAX = 6

# ca: (id, engine, style, cách dựng)
CASES = [
    ("textcard-forward", "card", "forward"),
    ("html-flat", "html", "flat-vector-black"),
    ("html-hud", "html", "hud-black"),
    ("three-toon", "three", "toon3d-lab"),
    ("three-atlas-neon", "three", "atlas-neon-sign"),
    ("three-atlas-glass", "three", "atlas-glass-and-light"),
]


def load(path):
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None:
        raise FileNotFoundError(path)
    return cv2.resize(im, SIZE, interpolation=cv2.INTER_AREA)


def ssim(a, b):
    """SSIM trên kênh xám, cửa sổ Gauss 11×11 (σ 1.5) — công thức Wang et al. 2004."""
    a = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float64)
    b = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float64)
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    g = (11, 11)
    mu_a, mu_b = cv2.GaussianBlur(a, g, 1.5), cv2.GaussianBlur(b, g, 1.5)
    s_aa = cv2.GaussianBlur(a * a, g, 1.5) - mu_a ** 2
    s_bb = cv2.GaussianBlur(b * b, g, 1.5) - mu_b ** 2
    s_ab = cv2.GaussianBlur(a * b, g, 1.5) - mu_a * mu_b
    m = ((2 * mu_a * mu_b + c1) * (2 * s_ab + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (s_aa + s_bb + c2))
    return float(m.mean())


def phash(img):
    g = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    d = cv2.dct(g)[:8, :8]
    return (d > np.median(d)).flatten()


def hamming(a, b):
    return int(np.count_nonzero(phash(a) != phash(b)))


def compare(cur_path, gold_path):
    a, b = load(cur_path), load(gold_path)
    s, h = ssim(a, b), hamming(a, b)
    return {"ssim": round(s, 4), "phash": h, "ok": s >= SSIM_MIN and h <= PHASH_MAX}


def render(case, out):
    """Dựng frame của ca → out (.png, 1080×1920)."""
    from PIL import Image  # noqa: PLC0415

    from . import enginebench  # noqa: PLC0415
    cid, eng, style = case
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out[:-4] + ".jpg"
    if eng == "three":
        enginebench.style_frame_3d(style, tmp)
    elif eng == "card":
        os.environ["STUDIO_NO_BROWSER"] = "1"
        try:
            enginebench.style_frame(style, tmp)
        finally:
            os.environ.pop("STUDIO_NO_BROWSER", None)
    else:
        enginebench.style_frame(style, tmp)
    Image.open(tmp).convert("RGB").save(out)
    os.remove(tmp)
    return out


def run(update=False, cases=None, log=print):
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for case in [c for c in CASES if not cases or c[0] in cases]:
        cur = render(case, os.path.join(OUT, f"{case[0]}.png"))
        gold = os.path.join(GOLDEN, f"{case[0]}.png")
        if update or not os.path.exists(gold):
            os.makedirs(GOLDEN, exist_ok=True)
            cv2.imwrite(gold, load(cur))
            rows.append({"case": case[0], "ssim": 1.0, "phash": 0, "ok": True, "note": "golden mới"})
        else:
            rows.append({"case": case[0], **compare(cur, gold), "note": ""})
        r = rows[-1]
        log(f"  {'OK  ' if r['ok'] else 'LỆCH'} {r['case']:<22} SSIM {r['ssim']:.4f} · pHash {r['phash']} {r['note']}")
    L = ["# Visual regression", "", f"Ngưỡng: SSIM ≥ {SSIM_MIN} · pHash ≤ {PHASH_MAX} bit (so ở {SIZE[0]}×{SIZE[1]}).", "",
         "| Ca | SSIM | pHash | Đạt | Ghi chú |", "|---|---|---|---|---|"]
    L += [f"| {r['case']} | {r['ssim']:.4f} | {r['phash']} | {'✓' if r['ok'] else '✗'} | {r['note']} |" for r in rows]
    with open(os.path.join(OUT, "report.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    return rows
