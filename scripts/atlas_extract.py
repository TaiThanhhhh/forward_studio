"""Rút dữ kiện từ prompt toàn văn của 3D Style Atlas → vendor/3d-style-atlas/cards/NN.json (cục bộ, gitignore).

  python scripts/atlas_extract.py [--print]

Mỗi prompt gồm: hướng dẫn → STYLE CARD (Look, Motion, Light, Materials, Camera, Finish, Good for) → STAGE KIT →
SOUND KIT → STROKEFONT → REFERENCE STYLE SOURCE. Lấy: các trường STYLE CARD, bảng màu hex của mã style (tần suất +
khoá màu nền/sương), thông số hoàn thiện (bloom/grain/vignette/DOF…) xuất hiện trong mã. Dùng để viết lại preset bằng
lời của tool (config/atlas.json) — không chép câu chữ.
"""
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "vendor", "3d-style-atlas", "raw")
OUT = os.path.join(ROOT, "vendor", "3d-style-atlas", "cards")
FIELDS = ("Name", "Family", "Use", "Look", "Motion", "Light", "Materials", "Camera", "Finish", "Good for")
FINISH_KEYS = ("bloom", "grain", "vignette", "vig", "dof", "aperture", "focus", "exposure", "toneMapping", "fog",
               "chromatic", "ca", "samples", "fov", "shadow")


def card(text):
    m = re.search(r"\nSTYLE CARD\n(.*?)\n\n", text, re.S)
    out = {}
    if not m:
        return out
    for line in m.group(1).split("\n"):
        k, _, v = line.partition(":")
        if k.strip() in FIELDS:
            out[k.strip()] = v.strip()
    return out


def source(text):
    i = text.rfind("REFERENCE STYLE SOURCE")
    return text[i:] if i >= 0 else ""


def colors(src):
    hexes = [h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}\b", src)]
    hexes += ["#" + h.lower()[2:] for h in re.findall(r"0x[0-9a-fA-F]{6}\b", src)]
    bg = {}
    for key in ("background", "bg", "fog", "clear", "backdrop", "sky", "floor", "wall"):
        mm = re.search(rf"\b{key}\w*\s*[:=]\s*['\"]?(#[0-9a-fA-F]{{6}}|0x[0-9a-fA-F]{{6}})", src)
        if mm:
            v = mm.group(1).lower()
            bg[key] = v if v.startswith("#") else "#" + v[2:]
    return collections.Counter(hexes).most_common(10), bg


def finish(src):
    out = {}
    for k in FINISH_KEYS:
        for mm in re.finditer(rf"\b{k}\w*\s*:\s*(-?\d+(?:\.\d+)?)", src):
            out.setdefault(k, []).append(float(mm.group(1)))
    return {k: v[:4] for k, v in out.items()}


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for p in sorted(glob.glob(os.path.join(RAW, "*.json"))):
        with open(p, encoding="utf-8") as fh:
            r = json.load(fh)
        t = r.get("prompt_full") or ""
        src = source(t)
        cols, bg = colors(src)
        rec = {"number": r["number"], "name": r["name"], "card": card(t), "colors": cols, "bg": bg,
               "finish": finish(src), "source_chars": len(src)}
        with open(os.path.join(OUT, f"{r['number']:02d}.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
        rows.append(rec)
    print(f"[atlas] {len(rows)} thẻ → {OUT} · có STYLE CARD: {sum(1 for r in rows if r['card'])}")
    if "--print" in (argv or sys.argv):
        for r in rows:
            c = r["card"]
            print(f"\n#{r['number']:02d} {r['name']} · nền {r['bg']} · màu {[h for h, _ in r['colors'][:6]]}")
            for k in ("Materials", "Light", "Camera", "Motion", "Finish"):
                print(f"  {k}: {c.get(k, '')[:210]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
