"""Adapter chung cho mọi engine của `mode: code` (vòng 7) — một giao diện, bốn engine:

    three  — three.js toon 3D trong Edge/Chromium headless   (engines/three/,        GPU)
    html   — motion graphics Canvas 2D trong Edge/Chromium   (engines/html/,  CPU trình duyệt)
    manim  — sơ đồ vật lý/toán bằng Manim Community Edition  (engines/manim/, CPU, Cairo)
    board  — evidence board Python + OpenCV                   (engines/board/, CPU)

Hợp đồng: nhận một `ShotSpec` (shot nào, engine nào, cảnh/beat nào, tham số, số frame, style) → trả về `Clip`: thư mục
frame fNNNN.jpg đúng số frame, clip MP4 đúng thời lượng, kèm frame đầu/cuối (PNG) để nối mạch với shot bên cạnh
(vd làm ảnh Start/End cho shot Flow). Pipeline chỉ nói chuyện với adapter này (qua vidlib/codeshot.py) nên thêm engine
không phải sửa pipeline.

Mỗi engine là một lớp có: scenes() · rev(scene) · job(spec) → job.json · render(job, frames_dir, frames, log) → thống kê ·
meta(job) → {cues, texts} · text_crops(job, frames) → [(frame, chữ, ảnh cắt, texture phẳng)] cho QA OCR.
"""

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THREE_DIR = os.path.join(ROOT, "engines", "three")   # engine three.js (JS thuần, Edge headless)
ENGINE_NAMES = ("three", "html", "manim", "board")
FRAME_ENGINES = ("three", "html", "manim")  # engine xuất frame riêng cho từng shot (board có đường riêng: board.json)


@dataclass
class ShotSpec:
    sid: str  # id shot (C03, OUTRO…)
    engine: str  # three | html | manim | board
    scene: str  # cảnh (three) hoặc beat (html/manim)
    params: dict = field(default_factory=dict)
    frames: int = 60
    fps: int = 30
    width: int = 1080
    height: int = 1920
    style: str = "forward"
    work: str = ""  # thư mục làm việc của shot (job.json, frames/, clip.mp4)
    beat: str | None = None
    index: list | None = None  # [thứ tự shot, tổng số shot] — look dùng cho số mục "03 / 07"
    spine: dict | None = None  # engine html "một cú máy liền": {L, prev, next} (vidlib/spine.py)


@dataclass
class Clip:
    sid: str
    engine: str
    frames_dir: str
    n: int
    first_frame: str | None = None
    last_frame: str | None = None
    mp4: str | None = None
    stats: dict = field(default_factory=dict)

    def as_dict(self):
        return asdict(self)


def _hash_files(paths):
    h = hashlib.sha1()
    for p in sorted(paths):
        with open(p, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:12]


def src_files(directory, exts):
    out = []
    for dp, dn, fn in os.walk(directory):
        dn[:] = [d for d in dn if d != "__pycache__"]
        out += [os.path.join(dp, f) for f in fn if f.endswith(exts)]
    return out


def save_job(spec, job):
    from vidlib.common import save_json  # noqa: PLC0415

    os.makedirs(spec.work, exist_ok=True)
    p = os.path.join(spec.work, "job.json")
    save_json(p, job)
    return p


def load_job(job_path):
    with open(job_path, encoding="utf-8") as fh:
        return json.load(fh)


def job_hash(job):
    return hashlib.sha1(json.dumps(job, sort_keys=True).encode()).hexdigest()[:12]


def style_tokens(style, key):
    from vidlib import textstyle  # noqa: PLC0415

    return textstyle.load_style(style).get(key) or {}


def font_entries(style, key):
    """Font cho engine html/manim: font chữ chính của style + font mono (tuỳ chọn trong khối engine của style)."""
    from vidlib import textstyle  # noqa: PLC0415

    st = textstyle.load_style(style)
    tok = st.get(key) or {}
    main = tok.get("font") or st["font"]
    mono = tok.get("mono") or "RobotoMono-Variable.ttf"
    out = []
    for fam, fn in (("StyleFont", main), ("StyleMono", mono)):
        e = {"family": fam, "url": "/assets/fonts/" + fn, "file": fn}
        if "Variable" in fn:
            e["weight"] = "100 900"
        out.append(e)
    return out


# ---------------------------------------------------------------------------------------------------------------------
class BrowserEngine:
    """Engine chạy trong trình duyệt headless (three, html) — dùng chung harness vidlib/coderender.py."""

    name = ""
    page = ""

    def render(self, job_path, frames_dir, frames=None, log=print, workers=None):
        from vidlib import coderender  # noqa: PLC0415

        return coderender.render(job_path, frames_dir, frames, workers=workers or self.workers(), log=log)

    def workers(self):
        return None

    def meta(self, job_path):
        from vidlib import coderender  # noqa: PLC0415

        return coderender.meta(job_path)

    def text_crops(self, job_path, frames):
        from vidlib import coderender  # noqa: PLC0415

        return coderender.text_crops(job_path, frames)


class ThreeEngine(BrowserEngine):
    name, page = "three", "engines/three/index.html"

    def scenes(self):
        d = os.path.join(THREE_DIR, "scenes")
        return sorted(os.path.splitext(f)[0] for f in os.listdir(d) if f.endswith(".js"))

    def rev(self, scene=None):
        eng = THREE_DIR
        files = [os.path.join(ROOT, "lib", "motion", "motion.js")]
        files += [os.path.join(eng, f) for f in os.listdir(eng) if f.endswith((".js", ".html"))]
        sd = os.path.join(eng, "scenes")
        files += [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".js") and (scene is None or f == f"{scene}.js")]
        return _hash_files(files)

    def job(self, spec):
        from vidlib import codeshot, textstyle  # noqa: PLC0415

        from vidlib import userassets  # noqa: PLC0415

        st = textstyle.load_style(spec.style)
        w, cp = codeshot.world(spec.style)
        job = {
            "scene": spec.scene,
            "params": userassets.resolve(spec.params or {}, "three"),   # "svg:<tên>" → icon_parts (ép khối)
            "frames": int(spec.frames),
            "fps": spec.fps,
            "width": spec.width,
            "height": spec.height,
            "world": w,
            "cast_palette": cp,
            "fonts": [{"family": "StyleFont", "url": "/assets/fonts/" + st["font"]}],
            "font_family": "StyleFont",
            "style": spec.style,
            "shot": spec.sid,
            "beat": spec.beat,
            "engine_rev": self.rev(spec.scene),
        }
        return save_job(spec, job)


def three_param_enums(scene):
    """{tham số: {giá trị hợp lệ}} đọc từ dòng `// params:` đầu file cảnh three.js (vd `beat = hook | air | pump`)."""
    import re  # noqa: PLC0415
    p = os.path.join(THREE_DIR, "scenes", f"{scene}.js")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as fh:
        head = [ln for ln in fh.read().splitlines()[:8] if ln.startswith("//") and "params:" in ln]
    out = {}
    for m in re.finditer(r"(\w+)\s*=\s*([\w-]+(?:\s*\|\s*[\w-]+)+)", head[0] if head else ""):
        out[m.group(1)] = {v.strip() for v in m.group(2).split("|")}
    return out


def three_param_names(scene):
    """Tên mọi tham số khai ở dòng `// params:` của cảnh three.js (vd scale: ball_g, cube_g, cubes…)."""
    import re  # noqa: PLC0415
    p = os.path.join(THREE_DIR, "scenes", f"{scene}.js")
    if not os.path.exists(p):
        return set()
    with open(p, encoding="utf-8") as fh:
        head = next((ln for ln in fh.read().splitlines()[:8] if ln.startswith("//") and "params:" in ln), "")
    body = head.split("params:", 1)[-1]
    body = re.sub(r"\([^)]*\)", "", body)              # bỏ chú thích trong ngoặc: "hot (0..1 độ đỏ của bi)"
    return {m.group(1) for m in re.finditer(r"(?:^|,)\s*([A-Za-z_]\w*)", body)}


def validate_three(scene, params):
    """Lỗi tham số của cảnh three.js có sẵn (giá trị ngoài danh sách → cảnh không có camera/kịch bản → crash lúc render)."""
    errs = []
    for k, allowed in three_param_enums(scene).items():
        v = (params or {}).get(k)
        if v is not None and str(v) not in allowed:
            errs.append(f"cảnh three.js '{scene}': {k} = '{v}' không hợp lệ (có: {' | '.join(sorted(allowed))}).")
    if scene == "stage":
        from vidlib import userassets  # noqa: PLC0415

        errs += stage_physics_errors(params) + [f"stage: {e}" for e in userassets.errors(params)]
        errs += stage_creature_errors(params)
        errs += stage_hybrid_errors(params)
    return errs


PHYSICS_FX = ("steam", "smoke", "sparks", "burst", "splash", "bubbles", "shockwave", "fire", "ring", "drops")


def physics_vocab():
    """{materials, kinds, shapes} đọc từ engines/three/physics.js (một nguồn sự thật cho JS và kiểm storyboard)."""
    import re  # noqa: PLC0415
    with open(os.path.join(THREE_DIR, "physics.js"), encoding="utf-8") as fh:
        src = fh.read()
    mats = src.split("export const MATERIALS = {", 1)[1].split("\n};", 1)[0]

    def arr(name):
        body = re.search(rf"export const {name} = \[([^\]]*)\]", src).group(1)
        return tuple(re.findall(r"'(\w+)'", body))

    return {"materials": tuple(re.findall(r"^\s{2}(\w+): \{", mats, re.M)), "kinds": arr("KINDS"), "shapes": arr("SHAPES")}


def stage_physics_errors(params):
    """Kiểm khối vật lý của cảnh `stage` (physics + props[].body) trước khi render — lỗi dữ liệu báo sớm, có gợi ý."""
    p, errs = params or {}, []
    voc = physics_vocab()
    num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)  # noqa: E731
    vec3 = lambda v: isinstance(v, list) and len(v) == 3 and all(num(x) for x in v)  # noqa: E731
    unit = lambda v: num(v) and 0 <= v <= 1  # noqa: E731
    ph = p.get("physics")
    if ph is not None and ph is not True and not isinstance(ph, dict):
        errs.append("stage: physics phải là object {gravity, slowmo, …}.")
    if isinstance(ph, dict):
        g = ph.get("gravity")
        if g is not None and not (num(g) or vec3(g)):
            errs.append("stage: physics.gravity là số (m/s², vd -9.81) hoặc [x,y,z].")
        for w in ph.get("slowmo") or []:
            u = (w or {}).get("u") if isinstance(w, dict) else None
            if not (isinstance(u, list) and len(u) == 2 and all(unit(x) for x in u) and u[0] < u[1]):
                errs.append("stage: physics.slowmo[].u phải là [u0, u1] trong 0..1, u0 < u1.")
            elif not (num(w.get("rate", 0.3)) and 0 < w.get("rate", 0.3) <= 1):
                errs.append("stage: physics.slowmo[].rate trong (0, 1] (0.25 = chậm 4 lần).")
        if ph.get("fx") not in (None, False) and ph.get("fx") not in PHYSICS_FX:
            errs.append(f"stage: physics.fx '{ph.get('fx')}' không có ({'|'.join(PHYSICS_FX)}).")
    for i, pr in enumerate(p.get("props") or []):
        b = (pr or {}).get("body")
        if b in (None, False):
            continue
        tag = f"stage: prop '{pr.get('id') or pr.get('type') or i}'"
        if pr.get("type") == "character":
            errs.append(f"{tag}: body không dùng cho nhân vật card 2D — dùng mannequin.")
            continue
        if b is True:
            continue
        if not isinstance(b, dict):
            errs.append(f"{tag}: body là true hoặc object {{kind, material, …}}.")
            continue
        kind = b.get("kind", "dynamic")
        for key, allowed in (("kind", voc["kinds"]), ("material", voc["materials"]), ("shape", voc["shapes"])):
            if key in b and b[key] not in allowed:
                errs.append(f"{tag}: body.{key} '{b[key]}' không có ({'|'.join(allowed)}).")
        if b.get("shape") == "mesh" and kind == "dynamic":
            errs.append(f"{tag}: body.shape 'mesh' (lõm) chỉ cho kind fixed/kinematic — vật động dùng hull.")
        for key in ("release", "hit_u"):
            if key in b and not unit(b[key]):
                errs.append(f"{tag}: body.{key} là u trong 0..1.")
        if ("release" in b or "hit_u" in b) and kind != "dynamic":
            errs.append(f"{tag}: body.release/hit_u chỉ cho kind dynamic.")
        for key in ("v", "spin"):
            if key in b and not vec3(b[key]):
                errs.append(f"{tag}: body.{key} là [x, y, z].")
        ranges = (("mass", 1e-6, 1e6), ("bounce", 0, 1), ("friction", 0, 10), ("drag", 0, 200), ("density", 1, 30000))
        for key, lo, hi in ranges:
            if key in b and not (num(b[key]) and lo <= b[key] <= hi):
                errs.append(f"{tag}: body.{key} ngoài khoảng {lo}..{hi}.")
        for k in b.get("push") or []:
            if not (isinstance(k, dict) and (unit(k.get("u")) or num(k.get("t"))) and vec3(k.get("v"))):
                errs.append(f"{tag}: body.push[] là {{u, v: [x, y, z]}}.")
        fx = b.get("fx")
        fxk = fx.get("kind") if isinstance(fx, dict) else fx
        if fx not in (None, False) and fxk not in PHYSICS_FX:
            errs.append(f"{tag}: body.fx '{fxk}' không có ({'|'.join(PHYSICS_FX)}).")
        if "sfx" in b and not (b["sfx"] is False or isinstance(b["sfx"], str)):
            errs.append(f"{tag}: body.sfx là tên âm (thud, impact…) hoặc false.")
    return errs


def creature_vocab():
    """{species, aliases, gaits, exprs, hairs, sets} đọc từ engines/three/creatures.js + props.js (một nguồn sự thật)."""
    import re  # noqa: PLC0415
    with open(os.path.join(THREE_DIR, "creatures.js"), encoding="utf-8") as fh:
        src = fh.read()
    with open(os.path.join(THREE_DIR, "props.js"), encoding="utf-8") as fh:
        psrc = fh.read()

    def arr(text, name):
        m = re.search(rf"export const {name} = \[([^\]]*)\]", text)
        return tuple(re.findall(r"'(\w+)'", m.group(1))) if m else ()

    body = src.split("export const SPECIES = {", 1)[1].split("\n};", 1)[0]
    ali = src.split("export const ALIASES = {", 1)[1].split("\n};", 1)[0]
    return {"species": tuple(re.findall(r"^\s{2}(\w+): \{", body, re.M)),
            "aliases": dict(re.findall(r"(\w+): '(\w+)'", ali)),
            "gaits": arr(src, "GAITS"), "exprs": arr(src, "EXPRS"), "hairs": arr(src, "HAIRS"), "sets": arr(psrc, "SETS")}


def stage_creature_errors(params):
    """Kiểm set + nhân vật 3D (creature/bí danh loài) của cảnh `stage`: loài/dáng/biểu cảm/tóc sai → lỗi có gợi ý."""
    import difflib  # noqa: PLC0415
    p, errs, voc = params or {}, [], creature_vocab()
    hint = lambda v, opts: (lambda m: f" — ý bạn là '{m[0]}'?" if m else "")(  # noqa: E731
        difflib.get_close_matches(str(v), list(opts), n=1, cutoff=0.6))
    num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)  # noqa: E731
    st = p.get("set")
    if st is not None and st not in voc["sets"]:
        errs.append(f"stage: set '{st}' không có ({'|'.join(voc['sets'])}){hint(st, voc['sets'])}.")
    if p.get("set_opts") is not None and not isinstance(p.get("set_opts"), dict):
        errs.append("stage: set_opts là object {r, seed, flowers, colors…}.")
    if p.get("blob") is not None and not (p["blob"] is False or (num(p["blob"]) and 0 <= p["blob"] <= 1)):
        errs.append("stage: blob là số 0..1 (độ đậm bóng tròn) hoặc false.")
    gaits, exprs = set(voc["gaits"]) | {"auto"}, set(voc["exprs"])
    for i, pr in enumerate(p.get("props") or []):
        if not isinstance(pr, dict):
            continue
        t = pr.get("type")
        if t != "creature" and t not in voc["aliases"]:
            continue
        tag = f"stage: prop '{pr.get('id') or t or i}'"
        sp = pr.get("species") or voc["aliases"].get(t) or "dog"
        sp = voc["aliases"].get(sp, sp)
        if sp not in voc["species"]:
            errs.append(f"{tag}: species '{pr.get('species')}' không có ({'|'.join(voc['species'])})"
                        f"{hint(pr.get('species'), list(voc['species']) + list(voc['aliases']))}.")
        for k in [pr] + [k for k in (pr.get("keys") or []) if isinstance(k, dict)]:
            if "gait" in k and k["gait"] not in gaits:
                errs.append(f"{tag}: gait '{k['gait']}' không có ({'|'.join(sorted(gaits))}){hint(k['gait'], gaits)}.")
            if "expr" in k and k["expr"] not in exprs:
                errs.append(f"{tag}: expr '{k['expr']}' không có ({'|'.join(voc['exprs'])}){hint(k['expr'], exprs)}.")
            lk = k.get("look")
            if lk is not None and lk != "camera" and not (isinstance(lk, list) and len(lk) == 3 and all(num(x) for x in lk)):
                errs.append(f"{tag}: look là [x, y, z] (điểm cần nhìn) hoặc \"camera\".")
        if "hair" in pr and pr["hair"] not in voc["hairs"]:
            errs.append(f"{tag}: hair '{pr['hair']}' không có ({'|'.join(voc['hairs'])}){hint(pr['hair'], voc['hairs'])}.")
        if "face" in pr and pr["face"] not in ("path", "fixed"):
            errs.append(f"{tag}: face là 'path' (quay theo đường đi) hoặc 'fixed'.")
        c = pr.get("color")
        if c is not None and not isinstance(c, (str, dict)):
            errs.append(f"{tag}: color là token/hex (thân) hoặc object {{body, belly, ear, …}}.")
    return errs


def stage_hybrid_errors(params):
    """Kiểm prop hybrid (`card2d`, `multiplane`), `overlay2d` và `do` (verbs) của cảnh `stage` (WP-X)."""
    from lib import motion as mo  # noqa: PLC0415

    p, errs = params or {}, []
    props = p.get("props") or []
    ids = {pr.get("id") for pr in props if isinstance(pr, dict) and pr.get("id")}
    for i, pr in enumerate(props):
        if not isinstance(pr, dict):
            continue
        tag = f"stage: prop '{pr.get('id') or pr.get('type') or i}'"
        if pr.get("do") is not None:
            if not isinstance(pr["do"], list):
                errs.append(f"{tag}: do phải là danh sách [{{u, verb, dur?, args?}}].")
            else:
                errs.extend(f"{tag}: {e}" for e in mo.verb_errors(pr["do"], where="do"))
        if pr.get("type") == "multiplane":
            lys = pr.get("layers")
            if not isinstance(lys, list) or not lys:
                errs.append(f"{tag}: multiplane cần layers: [{{draw|icon|text, z, …}}].")
    ov = p.get("overlay2d")
    if ov is not None:
        if not isinstance(ov, list):
            errs.append("stage: overlay2d phải là danh sách [{text, of?, z?}].")
        else:
            for k, it in enumerate(ov):
                if not isinstance(it, dict):
                    errs.append(f"stage: overlay2d[{k}] phải là object.")
                    continue
                if it.get("z") not in (None, "front", "back"):
                    errs.append(f"stage: overlay2d[{k}].z chỉ nhận 'front' hoặc 'back'.")
                if it.get("of") and ids and it["of"] not in ids:
                    errs.append(f"stage: overlay2d[{k}].of '{it['of']}' không khớp prop id nào ({', '.join(sorted(ids))}).")
    return errs


class HtmlEngine(BrowserEngine):
    name, page = "html", "engines/html/index.html"

    def scenes(self):
        from engines import html  # noqa: PLC0415

        return list(html.BEATS)

    def rev(self, scene=None):
        return _hash_files(
            src_files(os.path.join(ROOT, "engines", "html"), (".js", ".html"))
            + [os.path.join(ROOT, "lib", "motion", "motion.js")]
        )

    def workers(self):
        from engines import html  # noqa: PLC0415

        return html.workers()

    def job(self, spec):
        from vidlib import lang  # noqa: PLC0415
        from vidlib.common import channel  # noqa: PLC0415

        look = {
            k: v for k, v in style_tokens(spec.style, "html").items() if not k.startswith("_") and k not in ("font", "mono")
        }
        from vidlib import userassets  # noqa: PLC0415

        params = userassets.resolve(spec.params or {}, "html")    # "svg:<tên>" → parts · lottie/rive → URL
        if spec.index and "index" not in params:
            params["index"] = spec.index
        job = {
            "engine": "html",
            "page": self.page,
            "scene": spec.scene,
            "params": params,
            "frames": int(spec.frames),
            "fps": spec.fps,
            "width": spec.width,
            "height": spec.height,
            "look": look,
            "fonts": font_entries(spec.style, "html"),
            "safe": {k: v for k, v in channel().get("safe_zone", {}).items() if not k.startswith("_")},
            "locale": lang.locale().replace("_", "-"),
            "style": spec.style,
            "shot": spec.sid,
            "beat": spec.beat,
            "engine_rev": self.rev(),
        }
        return save_job(spec, with_spine(job, spec))


def with_spine(job, spec):
    """"Một cú máy liền" (vidlib/spine.py): ghi spine vào job + frame QA đọc chữ lúc camera đứng yên (ngoài chặng bay)."""
    if spec.spine:
        job["spine"] = spec.spine
        lw = int(spec.spine.get("L", 9))
        job["qa_frames"] = sorted({max(0, min(spec.frames - 1, lw + (spec.frames - 2 * lw) // 2)),
                                   max(0, spec.frames - lw - 2)})
    return job


class ManimEngine:
    name = "manim"

    def scenes(self):
        from engines import manim as m  # noqa: PLC0415

        return list(m.BEATS)

    def rev(self, scene=None):
        return _hash_files(src_files(os.path.join(ROOT, "engines", "manim"), (".py",)))

    def job(self, spec):
        from engines import manim as m  # noqa: PLC0415

        return save_job(spec, with_spine(m.job(spec, self.rev()), spec))

    def render(self, job_path, frames_dir, frames=None, log=print, workers=None):
        from engines import manim as m  # noqa: PLC0415

        return m.render(job_path, frames_dir, log=log)

    def meta(self, job_path):
        from engines import manim as m  # noqa: PLC0415

        return m.meta(job_path)

    def text_crops(self, job_path, frames):
        from engines import manim as m  # noqa: PLC0415

        return m.text_crops(job_path, frames)


class BoardEngine:
    """Engine board dựng từ `board.json` (vidlib/boardplan.py sinh từ storyboard + timeline + VO) — một camera cho cả video
    nên không có job riêng từng shot. Adapter bọc `engines.board.render` để cùng trả về Clip: spec.params =
    {"board": <board.json>, "f0": frame đầu, "f1": frame cuối (không gồm)}."""

    name = "board"

    def scenes(self):
        from vidlib.storyboard import RECIPES  # noqa: PLC0415

        return list(RECIPES)

    def rev(self, scene=None):
        return _hash_files(src_files(os.path.join(ROOT, "engines", "board"), (".py",)))

    def job(self, spec):
        return save_job(
            spec,
            {
                "engine": "board",
                "scene": spec.scene,
                "params": spec.params,
                "frames": int(spec.frames),
                "fps": spec.fps,
                "shot": spec.sid,
                "engine_rev": self.rev(),
            },
        )

    def render(self, job_path, frames_dir, frames=None, log=print, workers=None):
        import time  # noqa: PLC0415

        from engines.board import render as brender  # noqa: PLC0415

        p = load_job(job_path)["params"]
        t0 = time.time()
        brender.frames(p["board"], int(p["f0"]), int(p["f1"]), frames_dir)
        n = int(p["f1"]) - int(p["f0"])
        dt = time.time() - t0
        return {
            "frames": n,
            "rendered": n,
            "sec": round(dt, 2),
            "sec_per_frame": round(dt / max(1, n), 3),
            "workers": 1,
            "gl": "opencv",
        }

    def meta(self, job_path):
        return {"cues": [], "texts": []}

    def text_crops(self, job_path, frames):
        return []


_ENGINES = {"three": ThreeEngine(), "html": HtmlEngine(), "manim": ManimEngine(), "board": BoardEngine()}


def get(name):
    if name not in _ENGINES:
        raise ValueError(f"Không có engine '{name}' (có: {', '.join(_ENGINES)}).")
    return _ENGINES[name]


def engine_of_job(job_path):
    return load_job(job_path).get("engine") or "three"


def have_all(frames_dir, n):
    return all(os.path.exists(os.path.join(frames_dir, f"f{f:04d}.jpg")) for f in range(n))


def encode(frames_dir, n, fps, out, crf=None):
    """Thư mục frame → MP4 đúng n frame (đúng thời lượng n/fps). Ghi tạm rồi đổi tên; ffmpeg lỗi → ném lỗi."""
    from vidlib import encode as enc  # noqa: PLC0415
    from vidlib.common import ffbin, replace_retry  # noqa: PLC0415

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tmp = out + ".part.mp4"
    subprocess.run(
        [ffbin("ffmpeg"), "-y", "-v", "error", "-framerate", str(fps), "-start_number", "0",
         "-i", os.path.join(frames_dir, "f%04d.jpg"), "-frames:v", str(n), "-vf", enc.JPEG_TO_YUV,
         *enc.video_args("intermediate", fps, crf), "-r", str(fps), *enc.mux_args(), tmp],
        check=True, timeout=max(120, n * 2),
    )
    replace_retry(tmp, out)
    return out


def render_clip(spec, mp4=True, log=print, workers=None):
    """ShotSpec → Clip (frame đủ + MP4 đúng thời lượng + frame đầu/cuối).
    RESUME: frame đã có của cùng job không render lại."""
    from PIL import Image  # noqa: PLC0415

    eng = get(spec.engine)
    job_path = eng.job(spec)
    frames_dir = os.path.join(spec.work, "frames")
    stats = {"rendered": 0}
    stamp = os.path.join(frames_dir, "_job.hash")
    same = os.path.exists(stamp) and open(stamp).read().strip() == job_hash(load_job(job_path))
    if not (same and have_all(frames_dir, spec.frames)):
        stats = eng.render(job_path, frames_dir, None, log=log, workers=workers)
    clip = Clip(spec.sid, spec.engine, frames_dir, int(spec.frames), stats=stats)
    for attr, f in (("first_frame", 0), ("last_frame", spec.frames - 1)):
        dst = os.path.join(spec.work, f"{attr.split('_')[0]}.png")
        Image.open(os.path.join(frames_dir, f"f{f:04d}.jpg")).convert("RGB").save(dst)
        setattr(clip, attr, dst)
    if mp4:
        clip.mp4 = encode(frames_dir, spec.frames, spec.fps, os.path.join(spec.work, "clip.mp4"))
    return clip
