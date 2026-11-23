"""3D Style Atlas → preset style của tool (biến thể dark-stage).

Nguồn sự thật:
- `config/atlas.json` — phân tích + bản chuyển của tool cho từng style (engine, look 3D, tier, brand_fit, block prompt
  viết bằng lời của tool). Đây là thứ được commit.
- `vendor/3d-style-atlas/raw/NN-<slug>.json` — bản gốc chụp từ trang (mô tả, "Shown here", "Good for", prompt toàn văn
  nếu lấy được). Chỉ nằm cục bộ (gitignore, điều khoản HubSpot: cá nhân, phi thương mại). Dùng để đối chiếu và hiển thị
  "prompt gốc" trong UI; KHÔNG bao giờ được ghép vào prompt Flow.

`build()` sinh `styles/atlas-<id>.json` (+ thẻ .md) từ bảng phân tích + style nền (`base`: world/html/kiểu chữ), không
chép chữ của atlas. `python scripts/atlas_import.py` chạy toàn bộ: preset, INDEX.md, bảng trong docs/3D_ATLAS_ANALYSIS.md.
"""
import copy
import glob
import json
import os
import re

from .common import CONFIG_DIR, ROOT, load_json, save_json

RAW_DIR = os.path.join(ROOT, "vendor", "3d-style-atlas", "raw")
SHOTS_DIR = os.path.join(ROOT, "vendor", "3d-style-atlas", "shots")
STYLES_DIR = os.path.join(ROOT, "styles")
PREFIX = "atlas-"
MAX_BLOCK_WORDS = 80          # block ngắn: không bao giờ dán prompt dài của atlas vào Flow
ENGINES = ("flow", "three", "hybrid")
BRAND_FIT = ("ok", "adapted", "off-brand")
KIND_BASE = {"toon": "toon3d-lab", "clay": "clay3d-black", "plastic": "plastic-toy3d-black", "glass": "glass3d-black",
             "chrome": "chrome3d-black", "lowpoly": "lowpoly3d-black", "paper": "papercraft3d-black",
             "holo": "hologram3d-black", "xray": "xray3d-black"}


def config():
    return load_json(os.path.join(CONFIG_DIR, "atlas.json"), {})


def entries():
    return list(config().get("styles") or [])


def style_id(e):
    return PREFIX + e["id"]


def category(cid):
    return next((c for c in config().get("categories") or [] if c["id"] == cid), {"id": cid, "name": cid, "vi": cid})


def raw(n):
    """Bản gốc của style số n (dict) hoặc None khi chưa chụp. Không bao giờ ném lỗi."""
    for p in glob.glob(os.path.join(RAW_DIR, f"{int(n):02d}-*.json")):
        try:
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None
    return None


def kind_of(look3d):
    return look3d if isinstance(look3d, str) else (look3d or {}).get("kind", "toon")


def words(text):
    return re.findall(r"[a-z0-9']+", (text or "").lower())


def shingles(text, n=6):
    w = words(text)
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def copied_phrases(ours, theirs, n=6):
    """Các cụm n từ liên tiếp trùng nguyên văn giữa chữ của tool và chữ gốc của atlas (kiểm "không chép")."""
    return sorted(shingles(ours, n) & shingles(theirs, n))


# ------------------------------------------------------------------ block prompt (lời của tool)
def image_block(e):
    return (f"{e['medium']} on a pure black stage (#000000): {e['materials']}. {_cap(e['lighting'])}. "
            f"One accent colour ({e['accent_name']}) only on the key element. "
            f"Leave {e['plate']} empty (captions are added later).")


def motion_block(e):
    return f"{_cap(e['motion'])}."


def avoid_items(e):
    d = config().get("defaults", {})
    items = ["any text, letters or numbers", "logos", *d.get("avoid", []), *(e.get("avoid") or [])]
    return list(dict.fromkeys(items))


def avoid_block(e):
    return "Avoid: " + ", ".join(avoid_items(e)) + "."


def _cap(x):
    x = " ".join(str(x or "").split()).rstrip(".")
    return x[:1].upper() + x[1:]


# ------------------------------------------------------------------ preset
def _base(e):
    name = e.get("base") or KIND_BASE.get(kind_of(e.get("look3d")), "toon3d-lab")
    with open(os.path.join(STYLES_DIR, f"{name}.json"), encoding="utf-8") as fh:
        st = json.load(fh)
    # trường thẻ style còn thiếu ở base cũ (vd toon3d-lab) lấy từ clay3d-black
    with open(os.path.join(STYLES_DIR, "clay3d-black.json"), encoding="utf-8") as fh:
        filler = json.load(fh)
    for k in ("transitions", "sfx_pack", "music", "voice_persona", "marks", "pacing", "voice_tags"):
        st.setdefault(k, copy.deepcopy(filler[k]))
    if "world" not in st:                     # base 2D (vd gallery) → world của look 3D tương ứng
        with open(os.path.join(STYLES_DIR, KIND_BASE.get(kind_of(e.get("look3d")), "toon3d-lab") + ".json"),
                  encoding="utf-8") as fh:
            w = json.load(fh)
        for k in ("world", "cast_palette"):
            if k in w:
                st[k] = w[k]
    return name, st


def preset(e):
    """Một preset hoàn chỉnh (dict) cho entry `e` của config/atlas.json."""
    d = config().get("defaults", {})
    cat = category(e["cat"])
    base_name, st = _base(e)
    st = copy.deepcopy(st)
    pal = {"bg": d.get("bg", "#000000"), **e["palette"], "_doc": f"sân khấu đen + accent {e['accent_name']}"}
    three = e["engine"] in ("three", "hybrid")
    st.update({
        "name": f"{e['name']} · dark stage",
        "description": (f"Biến thể dark-stage của style #{e['n']:02d} \"{e['name']}\" ({cat['vi']}) trong 3D Style Atlas: "
                        f"{e['good_for']}. Viết lại bằng lời của tool trên sân khấu đen, một accent."),
        "source": {"repo": f"{config()['source']['name']} ({config()['source']['publisher']})",
                   "url": config()["source"]["url"], "sha": f"#{e['n']:02d}", "license": "HubSpot Website Terms of Use "
                   "(cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md",
                   "from": f"#{e['n']:02d} {e['name']} · {cat['name']} · {e.get('tag', '')}",
                   "how": f"dark-stage: nền #000, look 3D `{kind_of(e['look3d'])}` của engine three.js, "
                          "block Flow ngắn tự viết"},
        "atlas": {"number": e["n"], "id": e["id"], "name": e["name"], "tag": e.get("tag", ""), "fit": e["fit"],
                  "duplicate_of": e.get("dup") or "", "why": e.get("why", ""),
                  "frame_props": e.get("frame_props") or d.get("frame_props")},
        "category": e["cat"], "category_name": cat["name"], "tier": int(e["tier"]), "brand_fit": e["brand_fit"],
        "variant": "dark-stage",
        "code_only": e["engine"] == "three",
        "image_style_block": image_block(e), "video_motion_block": motion_block(e), "avoid_block": avoid_block(e),
        "palette": pal, "materials": e["materials"], "lighting": e["lighting"], "camera": e["camera"],
        "text_style": {"plate": e["plate"], "font": st.get("font"), "uppercase": bool(st.get("uppercase")),
                       "rule": "chữ do text_fx / chữ 3D của engine; prompt ảnh chỉ chừa chỗ trống"},
        "good_for": e["good_for"],
        "what_it_is_not": list(d.get("not") or []), "not": list(d.get("not") or []),
        "tags": list(e["tags"]), "black_min": max(float(st.get("black_min") or 0.5), 0.5),
        "thumbnail": f"một vật chủ đạo kiểu {e['medium'].lower()} nổi giữa nền đen, accent {e['accent_name']} trên chi "
                     f"tiết sắp xảy ra chuyện",
    })
    if e["engine"] == "three":
        st["code_engine"] = "three"
    else:
        st.pop("code_engine", None)
    st["pacing"] = {**(st.get("pacing") or {}), "camera": e["camera"]}
    st["flow"] = {"is_3d": True, "medium": e["medium"], "look": f"{_cap(e['materials'])}; {e['lighting']}",
                  "motion": e["motion"], "motion_block": motion_block(e), "plate": e["plate"],
                  "accent": e["palette"]["a"], "accent_name": e["accent_name"], "camera": _cap(e["camera"]),
                  "avoid_add": [a for a in avoid_items(e) if a not in ("any text, letters or numbers", "logos")]}
    if three or "world" in st:
        w = st.setdefault("world", {})
        w["look3d"] = copy.deepcopy(e["look3d"])
        w["bg"] = w["fog"] = pal["bg"]
        cols = w.setdefault("colors", {})
        hot = warm_key(e["palette"])
        cols.update({"accent": e["palette"]["a"], "accent_glow": e["palette"]["a"], "white": e["palette"]["ink"],
                     "label": e["palette"]["ink"]})
        if hot:                     # bi thép nóng / cảnh báo = màu ấm nhất của style
            cols["danger"] = e["palette"][hot]
        elif not warm_key({"x": cols.get("danger", "")}, ("x",)):  # bảng màu + base đều lạnh (vd chrome) → đỏ-cam chung
            cols["danger"] = d.get("hot_fallback", "#FF5A3C")
        if warm_key({"x": cols.get("water", "")}, ("x",)):          # base chrome để nước màu cam → "nước đá" phải lạnh
            ck = cold_key(e["palette"])
            cols["water"] = e["palette"][ck] if ck else d.get("cold_fallback", "#4FB3FF")
        if isinstance(w.get("ink"), dict):
            w["ink"]["rim"] = e["palette"]["a"]
    h = st.setdefault("html", {})
    h["palette"] = {k: pal[k] for k in ("bg", "ink", "a", "b", "c")}
    hot = warm_key(e["palette"])
    roles = dict(h.get("roles") or {})
    if hot:
        roles["hot"] = hot
        roles["cold"] = next((k for k in ("b", "c", "a") if k != hot), "b")
    else:                           # không có màu ấm: thêm ô "hot" riêng vào palette html (chart nhiệt độ vẫn nóng)
        h["palette"]["hot"] = d.get("hot_fallback", "#FF5A3C")
        roles["hot"] = "hot"
        roles.setdefault("cold", "a")
    roles["accent"] = "a" if hot != "a" else roles.get("accent", "c")
    h["roles"] = roles
    st["number_fill"] = e["palette"]["c"]
    if isinstance(st.get("shadow"), dict):
        st["shadow"]["color"] = e["palette"]["a"]
    st["fill"] = e["palette"]["ink"]
    st["_generated"] = "vidlib/atlas.py từ config/atlas.json — sửa ở đó rồi chạy python scripts/atlas_import.py"
    st["_base"] = base_name
    return st


def warm_key(pal, keys=("a", "b", "c")):
    """Khoá màu ấm nhất (đỏ → cam → vàng, đủ bão hoà) trong a/b/c, hoặc None nếu bảng màu không có màu ấm."""
    import colorsys  # noqa: PLC0415
    best, score = None, 0.0
    for k in keys:
        v = str(pal.get(k) or "").lstrip("#")
        if len(v) != 6:
            continue
        r, g, b = (int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))
        hue, light, sat = colorsys.rgb_to_hls(r, g, b)
        hue *= 360
        warm = 1.0 if hue <= 30 or hue >= 340 else (0.8 if hue <= 45 else (0.5 if hue <= 60 else 0.0))
        sc = warm * sat * (1 - abs(light - 0.55))
        if sc > score:
            best, score = k, sc
    return best if score >= 0.5 else None


def cold_key(pal, keys=("a", "b", "c")):
    """Khoá màu lạnh rõ nhất (lục lam → xanh dương, đủ bão hoà) trong a/b/c, hoặc None."""
    import colorsys  # noqa: PLC0415
    best, score = None, 0.0
    for k in keys:
        v = str(pal.get(k) or "").lstrip("#")
        if len(v) != 6:
            continue
        hue, light, sat = colorsys.rgb_to_hls(*(int(v[i:i + 2], 16) / 255 for i in (0, 2, 4)))
        hue *= 360
        sc = (1.0 if 170 <= hue <= 250 else 0.0) * sat * (1 - abs(light - 0.55))
        if sc > score:
            best, score = k, sc
    return best if score >= 0.25 else None


def check(e, st=None):
    """Lỗi (list chuỗi) của một entry/preset: thiếu trường, block quá dài, chép nguyên văn từ bản gốc."""
    st = st or preset(e)
    errs = []
    for k in ("image_style_block", "video_motion_block", "avoid_block", "palette", "materials", "lighting", "camera",
              "text_style", "pacing", "transitions", "sfx_pack", "music", "voice_persona", "thumbnail", "good_for",
              "what_it_is_not", "category", "tier", "brand_fit", "tags", "voice_tags", "html", "source"):
        if not st.get(k):
            errs.append(f"thiếu {k}")
    if e["engine"] not in ENGINES:
        errs.append(f"engine '{e['engine']}' ∉ {ENGINES}")
    if e["brand_fit"] not in BRAND_FIT:
        errs.append(f"brand_fit '{e['brand_fit']}' ∉ {BRAND_FIT}")
    if st["palette"]["bg"].lower() not in ("#000000", "#000"):
        errs.append("nền không phải #000")
    for k in ("image_style_block", "video_motion_block", "avoid_block"):
        if len(words(st[k])) > MAX_BLOCK_WORDS:
            errs.append(f"{k} {len(words(st[k]))} từ > {MAX_BLOCK_WORDS}")
    r = raw(e["n"])
    if r:
        theirs = " ".join(str(r.get(k) or "") for k in ("description", "shown_here", "good_for", "prompt_full"))
        ours = " ".join(st[k] for k in ("image_style_block", "video_motion_block", "avoid_block"))
        bad = copied_phrases(ours, theirs)
        if bad:
            errs.append(f"chép nguyên văn atlas: {bad[:3]}")
    return errs


def build(write=True):
    """Sinh mọi preset. Trả về [(style_id, preset, lỗi)]."""
    out = []
    for e in entries():
        st = preset(e)
        errs = check(e, st)
        out.append((style_id(e), st, errs))
        if write and not errs:
            save_json(os.path.join(STYLES_DIR, f"{style_id(e)}.json"), st)
    return out


def ids(tiers=None, include_off_brand=True):
    return [style_id(e) for e in entries() if (tiers is None or e["tier"] in tiers)
            and (include_off_brand or e["brand_fit"] != "off-brand")]


def auto_ok(st):
    """Style atlas có được vào vòng chọn tự động không: bỏ off-brand, chỉ tier trong `auto_tiers`."""
    if st.get("variant") != "dark-stage" or "atlas" not in st:
        return True
    if st.get("brand_fit") == "off-brand":
        return False
    return int(st.get("tier") or 2) in (config().get("auto_tiers") or [1])


# ------------------------------------------------------------------ tài liệu
def index_md():
    cfg = config()
    src = cfg["source"]
    rows = []
    for e in entries():
        r = raw(e["n"]) or {}
        state = ("đủ" if r.get("prompt_full") else "thiếu prompt") if r else "chưa chụp"
        rows.append(f"| {e['n']:02d} | {e['name']} | {category(e['cat'])['name']} | {e.get('tag', '')} | "
                    f"{r.get('prompt_chars', 0) or '—'} | {state} | `{style_id(e)}` |")
    got = sum(1 for e in entries() if raw(e["n"]))
    full = sum(1 for e in entries() if (raw(e["n"]) or {}).get("prompt_full"))
    return "\n".join([
        "# 3D Style Atlas — bản chụp cục bộ", "",
        f"- Nguồn: **{src['name']}** — {src['publisher']} · {src['url']} · lấy ngày {src['captured']}.",
        f"- Điều khoản: HubSpot Website Terms of Use ({src['terms_url']}, sửa đổi lần cuối {src['terms_modified']}). "
        "Tóm tắt: nội dung trang chỉ được dùng cho mục đích **cá nhân, phi thương mại**; cấm sao chép, sửa đổi, tạo tác "
        "phẩm phái sinh, phân phối hay khai thác thương mại nội dung, cấm truy cập tự động nhiều hơn người dùng trình "
        "duyệt; HubSpot giữ bản quyền nội dung. → Bản gốc (`raw/`, `shots/`) chỉ lưu cục bộ, gitignore, không đưa vào "
        "prompt hay video; preset `styles/atlas-*.json` là bản viết lại bằng lời + mã của tool (chỉ lấy ý tưởng thị giác). "
        "Dùng cho kênh thương mại: xem mục \"Cần anh quyết định\" trong `docs/RUN_REPORT.md`.",
        f"- Đã chụp: **{got}/37** style (metadata), prompt toàn văn **{full}/37**. "
        "Cách chụp tiếp: `README.md` cùng thư mục.",
        "", "| # | Tên | Nhóm | Nhãn | Prompt (ký tự) | Trạng thái | Preset |", "|---|---|---|---|---|---|---|", *rows, ""])


def analysis_table():
    L = ["| # | Style | Nhóm | Engine | Look 3D | Hợp kênh | Tier | brand_fit | Trùng | Lý do |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for e in entries():
        L.append(f"| {e['n']:02d} | {e['name']} | {category(e['cat'])['vi']} | {e['engine']} | {kind_of(e['look3d'])} | "
                 f"{e['fit']}/5 | {e['tier']} | {e['brand_fit']} | {e.get('dup') or '—'} | {e.get('why', '')} |")
    return "\n".join(L)
