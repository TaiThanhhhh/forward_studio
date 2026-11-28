"""Nhân vật hoạt hình 2D của engine html (rig2d.js) — bản Python chỉ ĐỌC từ vựng từ file JS (một nguồn sự thật):
loài (SPECIES + bộ xương), hành động (ACTIONS), biểu cảm (EXPRS), kiểu tóc (HAIRS), bí danh (RIG_ALIASES).
Dùng để kiểm tên icon "rig:<loài>[:<hành động>][:<biểu cảm>][:left|right]" trong storyboard trước khi render và để
brief/kho cơ chế liệt kê nhân vật có thật (tests/test_looks2d.py đối chiếu với JS bằng node)."""

import difflib
import functools
import os
import re

_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rig2d.js")
FACES = ("left", "right")
VIEWS = ("side", "front", "back")          # vòng 23: góc nhìn người tả thực


@functools.cache
def _src():
    with open(_JS, encoding="utf-8") as fh:
        return fh.read()


def _arr(name):
    m = re.search(rf"export const {name} = \[([^\]]*)\]", _src())
    return tuple(re.findall(r"'([^']+)'", m.group(1))) if m else ()


@functools.cache
def table():
    """{loài: bộ xương} theo thứ tự trong SPECIES."""
    body = _src().split("export const SPECIES = {", 1)[1].split("\n};", 1)[0]
    return dict(re.findall(r"^  (\w+): \{ plan: '(\w+)'", body, flags=re.M))


def species():
    return list(table())


def actions():
    return list(_arr("ACTIONS"))


def exprs():
    return list(_arr("EXPRS"))


def hairs():
    return list(_arr("HAIRS"))


@functools.cache
def aliases():
    body = re.search(r"export const RIG_ALIASES = \{([^}]*)\}", _src()).group(1)
    return dict(re.findall(r"(\w+): '(\w+)'", body))


def is_rig(name):
    return isinstance(name, str) and name.strip().lower().startswith("rig:")


def parse(name):
    """"rig:dog:walk:happy" → {species, action, expr, face, hair, bad} (giống parseRig của JS); None nếu không phải rig."""
    if not is_rig(name):
        return None
    parts = [p.strip() for p in name.strip().lower()[4:].split(":") if p.strip()]
    raw = parts[0] if parts else ""
    sp = raw if raw in table() else aliases().get(raw)
    out = {"species": sp, "raw": raw, "action": None, "expr": None, "face": None, "hair": None, "view": None, "bad": []}
    acts, exs, hs = actions(), exprs(), hairs()
    for tok in parts[1:]:
        key = ("action" if tok in acts else "expr" if tok in exs else "face" if tok in FACES
               else "hair" if tok in hs else "view" if tok in VIEWS else None)
        if key:
            out[key] = tok
        else:
            out["bad"].append(tok)
    return out


def _hint(tok, pool):
    near = difflib.get_close_matches(tok, pool, n=3, cutoff=0.5)
    return f" (gần nhất: {', '.join(near)})" if near else ""


def check(name):
    """Lỗi tiếng Việt cho một tên rig (None nếu hợp lệ). Gợi ý tên gần đúng."""
    r = parse(name)
    if r is None:
        return None
    if not r["species"]:
        pool = species() + list(aliases())
        return (f"icon '{name}': loài '{r['raw']}' không có{_hint(r['raw'], pool)}. Loài: {', '.join(species())} "
                f"(bí danh: {', '.join(sorted(aliases()))}).")
    if r["bad"]:
        pool = actions() + exprs() + list(FACES) + hairs()
        bad = ", ".join(f"'{b}'{_hint(b, pool)}" for b in r["bad"])
        return (f"icon '{name}': {bad} không phải hành động ({'|'.join(actions())}), biểu cảm ({'|'.join(exprs())}), "
                f"hướng (left|right), góc nhìn ({'|'.join(VIEWS)}) hay kiểu tóc ({'|'.join(hairs())}).")
    return None


def check_args(args):
    """Kiểm khối args {action, expr, face, hair} đi kèm icon rig (scene actor/keys có thể truyền)."""
    errs = []
    for key, pool in (("action", actions()), ("expr", exprs()), ("face", FACES), ("hair", hairs()), ("view", VIEWS),
                      ("outfit", outfits()), ("beard", ("stubble", "full"))):
        v = (args or {}).get(key)
        if v is not None and v not in pool:
            errs.append(f"rig: {key} '{v}' không có{_hint(str(v), list(pool))} (có: {'|'.join(pool)}).")
    return errs


def outfits():
    return list(_arr("OUTFITS"))


def parts():
    """Bộ phận có điểm neo (vòng 21) — `"actor.part"` trong labels/arrows/fx/camera và `through` của zoom_through."""
    return _arr("PARTS")


def organs():
    """Cơ quan vẽ được khi x-ray (`organs` của actor)."""
    return _arr("ORGANS")
