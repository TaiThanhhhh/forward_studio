"""Kho tài sản THƯ VIỆN (vòng 10, WP-A): mô hình 3D glTF/GLB + icon SVG — chỉ giấy phép thoáng (CC0/MIT/ISC/BSD/Apache).

  config/assets3d.json        index 3D (commit): policy · vocab (tag/từ đồng nghĩa/cỡ thật) · packs (nguồn chính chủ, commit,
                              giấy phép đã kiểm, luật chọn file) · models (sinh bởi scripts/assets_fetch.py) · rejected (loại
                              sau khi xem sheet, có lý do) · aliases
  assets/lib/3d/<gói>/        file glTF/GLB/bin/png đã tải (gitignore — dựng lại: python studio.py assets fetch)
  assets/lib/svg/index.json   index icon SVG thư viện (commit) · assets/lib/svg/<gói>/<tên>.json = parts (gitignore)
  assets/lib/licenses/        văn bản giấy phép từng gói, lưu lúc tải (commit)

Storyboard: three.js `stage` prop {"type": "model:<tên>", "anim": "walk", "h": 0.6, …} · icon {"icon"|"type": "svg:<tên>"}
(SVG người dùng trước, thư viện sau). Engine không đọc đĩa: Python đổi tên → URL + meta lúc dựng job (userassets.resolve).
"""

import difflib
import fnmatch
import functools
import hashlib
import json
import math
import os
import re
import struct

from .common import ROOT, StudioError, load_json

INDEX = os.path.join(ROOT, "config", "assets3d.json")
LIB = os.path.join(ROOT, "assets", "lib")
LIB3D = os.path.join(LIB, "3d")
LIBSVG = os.path.join(LIB, "svg")
SVG_INDEX = os.path.join(LIBSVG, "index.json")
LICENSES = os.path.join(LIB, "licenses")


# --------------------------------------------------------------------------------------------------------------- index
@functools.lru_cache(maxsize=4)
def _load(path, mtime):
    return load_json(path, {})


def index():
    """config/assets3d.json (đọc lại khi file đổi)."""
    if not os.path.exists(INDEX):
        return {}
    return _load(INDEX, os.path.getmtime(INDEX))


def svg_index():
    if not os.path.exists(SVG_INDEX):
        return {}
    return _load(SVG_INDEX, os.path.getmtime(SVG_INDEX))


def allowed_licenses():
    return tuple((index().get("policy") or {}).get("allowed") or ("CC0-1.0", "MIT", "ISC", "BSD-2-Clause",
                                                                   "BSD-3-Clause", "Apache-2.0"))


def models():
    return index().get("models") or {}


def packs():
    return {k: v for k, v in (index().get("packs") or {}).items() if not k.startswith("_")}


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------------ từ khoá / tìm
def tokens(s):
    """'Food_Ingredient-TomatoSlice 2' → ['food', 'ingredient', 'tomato', 'slice'] (bỏ chữ cái đơn A/B/C và số)."""
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(s or ""))
    return [t for t in re.split(r"[^a-z0-9]+", s.lower()) if len(t) > 1 and not t.isdigit()]


def stem(t):
    """Dạng gốc đơn giản (khớp số nhiều): berries→berry, boxes→box, dogs→dog."""
    if len(t) > 4 and t.endswith("ies"):
        return t[:-3] + "y"
    if len(t) > 4 and t.endswith(("ches", "shes", "xes", "sses")):
        return t[:-2]
    if len(t) > 3 and t.endswith("s") and not t.endswith(("ss", "us", "is")):
        return t[:-1]
    return t


def _score(q, name, e):
    qs = [stem(t) for t in tokens(q)]
    if not qs:
        return 0.0
    nm = {stem(t) for t in tokens(name)}
    kw = {stem(t) for k in e.get("keywords") or [] for t in tokens(k)}
    tg = {stem(t) for k in e.get("tags") or [] for t in tokens(k)}
    sc = 0.0
    for t in qs:
        sc += 3 if t in nm else 2 if t in kw else 1 if t in tg else 0
    if name == q.strip().lower():
        sc += 10
    return sc / len(qs)


def search(q, limit=20, tag=None, kind="3d"):
    """[(điểm, tên, mục)] — khớp tên (3) > từ khoá (2) > tag (1), có dạng gốc; kind '3d' | 'svg'."""
    pool = models() if kind == "3d" else (svg_index().get("icons") or {})
    out = []
    for n, e in pool.items():
        if tag and tag not in (e.get("tags") or []):
            continue
        s = _score(q, n, e)
        if s > 0:
            out.append((round(s, 3), n, e))
    out.sort(key=lambda x: (-x[0], len(x[1]), x[1]))
    return out[:limit]


def aliases():
    return {k: v for k, v in (index().get("aliases") or {}).items() if not k.startswith("_")}


def lookup(name):
    """Tên chính xác → bí danh → khớp từ khoá tốt nhất (điểm trung bình ≥ 1: mỗi từ trúng tên/từ khoá/tag).
    (tên, mục) hoặc (None, gợi ý)."""
    m = models()
    n = str(name or "").strip().lower()
    if n in m:
        return n, m[n]
    a = aliases().get(n)
    if a in m:
        return a, m[a]
    hits = search(n, limit=8)
    if hits and hits[0][0] >= 1.0:
        return hits[0][1], hits[0][2]
    sugg = [h[1] for h in hits[:6]] or difflib.get_close_matches(n, list(m), n=6, cutoff=0.5)
    return None, sugg


# ---------------------------------------------------------------------------------------------------- animation names
def anim_norm(s):
    """Chuẩn hoá tên clip — GIỐNG animNorm() của engines/three/models.js (test đối chiếu)."""
    s = str(s or "").lower()
    s = s.split("|")[-1]
    return re.sub(r"[^a-z0-9]", "", s)


def anim_match(names, q):
    """Chọn clip theo tên — GIỐNG pickClip() của models.js: đúng tên → chuẩn hoá bằng → bắt đầu bằng → chứa."""
    if q in (None, "", True):
        return names[0] if names else None
    q0, qn = str(q), anim_norm(q)
    for test in (lambda n: n == q0, lambda n: anim_norm(n) == qn, lambda n: anim_norm(n).startswith(qn),
                 lambda n: qn in anim_norm(n)):
        for n in names:
            if qn and test(n):
                return n
    return None


# --------------------------------------------------------------------------------------------------- dữ liệu cho job
def model_path(e):
    return os.path.join(ROOT, e["file"])


def url_of(e):
    return "/" + e["file"]


def render_defaults():
    return dict(index().get("render") or {})


def job_data(name):
    """Mục index → dữ liệu engine cần (không đường dẫn đĩa, chỉ URL phục vụ qua server cục bộ của coderender)."""
    n, e = lookup(name)
    if not n:
        return None
    pk = packs().get(e.get("pack")) or {}
    return {"model_url": url_of(e), "model": {
        "name": n, "h": e.get("h"), "dims": e.get("dims"), "anims": [a["name"] for a in e.get("anims") or []],
        "hide": e.get("hide") or [], "skinned": bool(e.get("skinned")), "textured": bool(e.get("textured")),
        "sha": (e.get("files") or {}).get(os.path.basename(e["file"]), {}).get("sha256", ""),
        "license": pk.get("license") or e.get("license"), **render_defaults(), **(e.get("render") or {})}}


def prop_errors(prop):
    """Lỗi của một prop "model:<tên>" (tên sai có gợi ý, anim không có, chưa tải file)."""
    t = prop.get("type")
    name = t[6:]
    n, e = lookup(name)
    if not n:
        sugg = e
        return [f"mô hình '{name}' không có trong kho 3D (gần nhất: {', '.join(sugg) or '—'}) — tìm: "
                f"`python studio.py assets search {name}`."]
    errs = []
    if not os.path.isfile(model_path(e)):
        errs.append(f"mô hình '{n}' chưa tải về máy ({e['file']}) — chạy `python studio.py assets fetch`.")
    names = [a["name"] for a in e.get("anims") or []]
    want = [prop.get("anim")] + [k.get("anim") for k in prop.get("keys") or [] if isinstance(k, dict)]
    for a in want:
        if a in (None, "", False):
            continue
        if not names:
            errs.append(f"mô hình '{n}' không có animation (bỏ 'anim').")
            break
        if anim_match(names, a) is None:
            common = ("idle", "walk", "run", "jump", "sit", "cheer", "wave", "dance", "lie", "pickup", "throw",
                      "death", "punch")
            show = sorted(names, key=lambda x: (not any(c in anim_norm(x) for c in common), names.index(x)))[:24]
            errs.append(f"mô hình '{n}': anim '{a}' không có (có: {', '.join(show)}{'…' if len(names) > 24 else ''}).")
    for k in ("h", "size", "anim_speed", "anim_offset", "anim_blend"):
        v = prop.get(k)
        if v is not None and not (isinstance(v, (int, float)) and not isinstance(v, bool)):
            errs.append(f"mô hình '{n}': {k} phải là số.")
    return errs


# ------------------------------------------------------------------------------------------------------- SVG thư viện
def svg_entry(name):
    icons = svg_index().get("icons") or {}
    n = str(name or "").strip().lower()
    if n in icons:
        return n, icons[n]
    a = (svg_index().get("aliases") or {}).get(n)
    return (a, icons[a]) if a in icons else (None, None)


def svg_path(name):
    n, e = svg_entry(name)
    if not n:
        return None
    p = os.path.join(ROOT, e["file"])
    return p if os.path.isfile(p) else None


def svg_parts(name):
    p = svg_path(name)
    if not p:
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh).get("parts") or []


def svg_license(name):
    n, e = svg_entry(name)
    if not n:
        return None
    pk = (svg_index().get("packs") or {}).get(e.get("pack")) or {}
    return f"{pk.get('title', e.get('pack'))} — {pk.get('license', '?')} ({pk.get('source', {}).get('url', '')})"


def model_license(name):
    n, e = lookup(name)
    if not n:
        return None
    pk = packs().get(e.get("pack")) or {}
    url = pk.get("page") or pk.get("source", {}).get("url", "")
    return f"{pk.get('title', e.get('pack'))} — {pk.get('license', '?')} ({url})"


# ------------------------------------------------------------------------------------------------------- đọc glTF/GLB
def read_gltf(path):
    """(json, bin chunk | None) của .gltf hoặc .glb."""
    with open(path, "rb") as fh:
        b = fh.read()
    if b[:4] == b"glTF":
        ln = struct.unpack_from("<I", b, 12)[0]
        j = json.loads(b[20:20 + ln].decode("utf-8"))
        off, binc = 20 + ln, None
        if off + 8 <= len(b):
            bl, bt = struct.unpack_from("<II", b, off)
            if bt == 0x004E4942:
                binc = b[off + 8:off + 8 + bl]
        return j, binc
    return json.loads(b.decode("utf-8")), None


def external_uris(j):
    """URI tương đối (buffer, ảnh) mà file glTF cần cạnh nó."""
    out = []
    for k in ("buffers", "images"):
        for x in j.get(k) or []:
            u = x.get("uri")
            if u and not u.startswith("data:"):
                out.append(u.replace("%20", " "))
    return out


def _mat_trs(n):
    if "matrix" in n:
        m = n["matrix"]
        return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
    tx, ty, tz = n.get("translation", [0, 0, 0])
    x, y, z, w = n.get("rotation", [0, 0, 0, 1])
    sx, sy, sz = n.get("scale", [1, 1, 1])
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[r[0][0] * sx, r[0][1] * sy, r[0][2] * sz, tx], [r[1][0] * sx, r[1][1] * sy, r[1][2] * sz, ty],
            [r[2][0] * sx, r[2][1] * sy, r[2][2] * sz, tz], [0, 0, 0, 1]]


def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _lin2srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def role_of(r, g, b):
    """Màu 0..1 → vai (cùng luật svgimport.js / media.js): ink dim hot cold accent."""
    mx, mn = max(r, g, b), min(r, g, b)
    lum, d = (mx + mn) / 2, mx - mn
    s = 0 if d == 0 else d / (1 - abs(2 * lum - 1) + 1e-9)
    if s < 0.25 or d < 0.08:
        return "ink" if lum > 0.45 else "dim"
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    h = (h * 60 + 360) % 360
    return "hot" if h < 60 or h >= 330 else "cold" if 150 <= h < 260 else "accent"


def gltf_meta(path, hide=()):
    """Đo mô hình: bbox (đơn vị gốc, bỏ node ẩn), số tam giác, animation (tên + giây), skin/morph, vật liệu → vai màu."""
    j, _ = read_gltf(path)
    acc = j.get("accessors") or []
    nodes = j.get("nodes") or []
    hide_l = [h.lower() for h in hide]
    hidden = lambda nm: any(h in str(nm or "").lower() for h in hide_l)  # noqa: E731
    lo, hi = [math.inf] * 3, [-math.inf] * 3
    tris = 0
    mesh_nodes = []
    ident = [[1 if i == k else 0 for k in range(4)] for i in range(4)]

    def visit(i, parent, skip):
        n = nodes[i]
        m = _mul(parent, _mat_trs(n))
        sk = skip or hidden(n.get("name"))
        if "mesh" in n:
            mesh_nodes.append(n.get("name") or f"node{i}")
            if not sk:
                for prim in (j["meshes"][n["mesh"]].get("primitives") or []):
                    pa = acc[prim["attributes"]["POSITION"]]
                    if "min" not in pa:
                        continue
                    for cx in (pa["min"][0], pa["max"][0]):
                        for cy in (pa["min"][1], pa["max"][1]):
                            for cz in (pa["min"][2], pa["max"][2]):
                                v = [m[r][0] * cx + m[r][1] * cy + m[r][2] * cz + m[r][3] for r in range(3)]
                                for a in range(3):
                                    lo[a], hi[a] = min(lo[a], v[a]), max(hi[a], v[a])
        for c in n.get("children") or []:
            visit(c, m, sk)

    sc = (j.get("scenes") or [{}])[j.get("scene", 0)]
    for r in sc.get("nodes") or []:
        visit(r, ident, False)
    for me in j.get("meshes") or []:
        for prim in me.get("primitives") or []:
            if prim.get("mode", 4) != 4:
                continue
            ia = prim.get("indices")
            tris += (acc[ia]["count"] if ia is not None else acc[prim["attributes"]["POSITION"]]["count"]) // 3
    anims = []
    for a in j.get("animations") or []:
        dur = 0.0
        for s in a.get("samplers") or []:
            ia = acc[s["input"]]
            if ia.get("max"):
                dur = max(dur, float(ia["max"][0]))
        anims.append({"name": a.get("name") or f"anim{len(anims)}", "dur": round(dur, 3)})
    mats = []
    for m in j.get("materials") or []:
        pbr = m.get("pbrMetallicRoughness") or {}
        f = pbr.get("baseColorFactor") or [1, 1, 1, 1]
        rgb = [_lin2srgb(max(0.0, min(1.0, c))) for c in f[:3]]
        tex = "baseColorTexture" in pbr
        mats.append({"name": m.get("name") or "", "hex": "#" + "".join(f"{round(c * 255):02x}" for c in rgb),
                     "role": "texture" if tex else role_of(*rgb), "tex": tex})
    morph = any(p.get("targets") for me in j.get("meshes") or [] for p in me.get("primitives") or [])
    bbox = [lo, hi] if lo[0] != math.inf else [[0, 0, 0], [0, 0, 0]]
    return {"bbox": [[round(v, 4) for v in bbox[0]], [round(v, 4) for v in bbox[1]]], "tris": tris, "anims": anims,
            "skinned": bool(j.get("skins")), "morph": morph, "materials": mats, "mesh_nodes": mesh_nodes,
            "textured": any(m["tex"] for m in mats)}


# --------------------------------------------------------------------------------------------------------------- kiểm
def check(files=True):
    """[(mức, thông điệp)] — mức 'err' | 'warn'. Mọi mục: giấy phép trong danh sách cho phép, gói có văn bản giấy phép
    khớp SHA, file có trên đĩa khớp SHA-256 (thiếu file = warn: chưa tải), tên duy nhất, có từ khoá."""
    out = []
    ok = set(allowed_licenses())
    pk = packs()
    for pid, p in pk.items():
        if p.get("license") not in ok:
            out.append(("err", f"gói {pid}: giấy phép '{p.get('license')}' không nằm trong danh sách cho phép "
                        f"({', '.join(sorted(ok))})."))
        for lf in p.get("license_files") or []:
            fp = os.path.join(ROOT, lf["path"])
            if not os.path.isfile(fp):
                out.append(("err", f"gói {pid}: thiếu văn bản giấy phép {lf['path']}."))
            elif lf.get("sha256") and sha256_file(fp) != lf["sha256"]:
                out.append(("err", f"gói {pid}: {lf['path']} khác SHA đã ghi lúc kiểm."))
        if not p.get("checked") or not (p.get("page") or (p.get("source") or {}).get("url")):
            out.append(("err", f"gói {pid}: thiếu ngày kiểm giấy phép / URL nguồn."))
    missing = 0
    for n, e in models().items():
        if e.get("pack") not in pk:
            out.append(("err", f"mô hình {n}: gói '{e.get('pack')}' không có trong packs."))
            continue
        if not e.get("keywords"):
            out.append(("warn", f"mô hình {n}: chưa có từ khoá."))
        if not files:
            continue
        base = os.path.dirname(model_path(e))
        for fn, meta in (e.get("files") or {}).items():
            fp = os.path.join(base, fn)
            if not os.path.isfile(fp):
                missing += 1
            elif sha256_file(fp) != meta.get("sha256"):
                out.append(("err", f"mô hình {n}: {fn} khác SHA-256 trong index."))
    if missing:
        out.append(("warn", f"{missing} file mô hình chưa có trên máy — chạy `python studio.py assets fetch`."))
    si = svg_index()
    for pid, p in (si.get("packs") or {}).items():
        if p.get("license") not in ok:
            out.append(("err", f"gói SVG {pid}: giấy phép '{p.get('license')}' không được phép."))
        lf = p.get("license_file") or {}
        if lf and not os.path.isfile(os.path.join(ROOT, lf.get("path", ""))):
            out.append(("err", f"gói SVG {pid}: thiếu văn bản giấy phép {lf.get('path')}."))
    smiss = 0
    for n, e in (si.get("icons") or {}).items():
        if e.get("pack") not in (si.get("packs") or {}):
            out.append(("err", f"icon {n}: gói '{e.get('pack')}' không có."))
        if files:
            fp = os.path.join(ROOT, e["file"])
            if not os.path.isfile(fp):
                smiss += 1
            elif e.get("parts_sha256") and sha256_file(fp) != e["parts_sha256"]:
                out.append(("err", f"icon {n}: {e['file']} khác SHA-256 trong index."))
    if smiss:
        out.append(("warn", f"{smiss} icon SVG thư viện chưa có trên máy — chạy `python studio.py assets fetch svg`."))
    names3d, names2d = set(models()), set(si.get("icons") or {})
    for a, t in aliases().items():
        if t not in names3d:
            out.append(("err", f"bí danh 3D '{a}' → '{t}' không có."))
    del names2d
    return out


def summary():
    """Số mô hình theo tag chính + có animation + dung lượng — cho `studio.py assets` và tài liệu."""
    from collections import Counter  # noqa: PLC0415
    ms = models()
    tags = Counter(e.get("group") or (e.get("tags") or ["?"])[0] for e in ms.values())
    anim = [n for n, e in ms.items() if e.get("anims")]
    return {"models": len(ms), "animated": len(anim), "groups": dict(tags.most_common()),
            "bytes": sum((p.get("bytes") or 0) for p in packs().values()),
            "svg": len(svg_index().get("icons") or {})}


def require():
    if not index():
        raise StudioError("Chưa có config/assets3d.json — chạy `python scripts/assets_fetch.py --discover`.")
    return index()


def pack_select(p, names):
    """Luật chọn file của gói (include/exclude theo glob trên tên file, không phân biệt hoa thường)."""
    inc = [x.lower() for x in p.get("include") or ["*"]]
    exc = [x.lower() for x in p.get("exclude") or []]
    out = []
    for n in names:
        b = os.path.basename(n).lower()
        if any(fnmatch.fnmatch(b, x) for x in inc) and not any(fnmatch.fnmatch(b, x) for x in exc):
            out.append(n)
    return out
