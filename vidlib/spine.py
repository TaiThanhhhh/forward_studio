"""Engine html — "một cú máy liền" (spine): cả chuỗi shot motion là các Ô trên một canvas lớn, camera bay liền từ ô này
sang ô kia qua điểm cắt (engines/html/core.js → spineCam). File này quyết định VỊ TRÍ các ô (kiểu bay giữa hai shot):

  pan_r / pan_l / pan_d / pan_u — lia ngang/dọc (zoom lùi nhẹ giữa chặng) · diag — chéo + nghiêng
  spin  — ô kế bên xoay 90°, camera xoay theo · dive — ô sau nằm TRONG vật ở giữa ô trước, camera lao vào
  pull  — ô trước nằm trong ô sau, camera kéo lùi ra
  vòng 10: orbit_tilt — vòng cung + nghiêng máy · push_through — xuyên qua vật (sâu hơn dive, vặn nhẹ)
  rack — đẩy vào một chi tiết lệch tâm (gợi ý đổi tiêu cự: `fx: rack`) · whip_rot — quật ngang + lộn vòng
  truck_parallax — dời ngang thấp (`fx: parallax`: engine có lớp sâu thì trượt thị sai) · spiral — xoáy vào

Thứ tự kiểu bay xáo theo từng video (hạt giống = slug) → hai video cùng style không bay giống nhau. Look có thể giới hạn
kiểu bay hợp ngữ pháp của nó (swiss chỉ lia thẳng theo lưới, sketchnote cuộn dọc như đọc sổ, scale-zoom lao vào/kéo ra).
Vòng 10: NHỚ LỊCH SỬ KÊNH — kiểu bay của các video gần nhất (vidlib/motionplan.recent_moves) bị đẩy xuống cuối, kiểu chưa
dùng được ưu tiên; dự án sinh trước `channel.json → motion.apply_since` giữ đúng bộ kiểu bay + thứ tự cũ (không đổi hình).
Mỗi shot chỉ cần biết ô TRƯỚC và ô SAU (tương đối với chính nó) → vẫn render từng shot riêng, song song, RESUME.
Shot Manim cũng nằm trong chuỗi: Manim dựng cả khung hình nên chặng bay được áp sau bằng warp affine (`travel_matrix`,
cùng công thức với core.js); với shot html, hàng xóm Manim là "ô ma" (camera bay qua, không vẽ lại nội dung).
"""

import hashlib
import math

from . import textstyle
from .common import channel

FOCUS = (0.0, 110.0)          # điểm "vật chính" của một ô so với tâm ô (beat html đặt vật ở giữa, hơi thấp)
MOVES = {
    "pan_r": {"x": 1200.0, "y": 0.0, "s": 1.0, "r": 0.0},
    "pan_l": {"x": -1200.0, "y": 0.0, "s": 1.0, "r": 0.0},
    "pan_d": {"x": 0.0, "y": 2040.0, "s": 1.0, "r": 0.0},
    "pan_u": {"x": 0.0, "y": -2040.0, "s": 1.0, "r": 0.0},
    "diag": {"x": 1180.0, "y": 1300.0, "s": 1.0, "r": 0.14},
    "spin": {"x": 1560.0, "y": 0.0, "s": 1.0, "r": math.pi / 2},
    "dive": {"x": FOCUS[0], "y": FOCUS[1], "s": 0.14, "r": 0.0},
    "pull": {"x": -FOCUS[0] / 0.14, "y": -FOCUS[1] / 0.14, "s": 1 / 0.14, "r": 0.0},
    # vòng 10 — chỉ là vị trí ô (x, y, s, r) nên core.js/travel_matrix chạy được ngay; `fx` là gợi ý cho engine có hỗ trợ
    "orbit_tilt": {"x": -1150.0, "y": 760.0, "s": 1.0, "r": -0.42},
    "push_through": {"x": FOCUS[0], "y": FOCUS[1], "s": 0.06, "r": 0.18},
    "rack": {"x": 260.0, "y": -420.0, "s": 0.62, "r": 0.0, "fx": "rack"},
    "whip_rot": {"x": 1500.0, "y": -380.0, "s": 1.0, "r": 2.2},
    "truck_parallax": {"x": -1320.0, "y": 240.0, "s": 1.0, "r": -0.05, "fx": "parallax"},
    "spiral": {"x": 900.0, "y": 900.0, "s": 0.5, "r": 1.2},
    # vòng 21 — chỉ đặt khi shot sau ghi `transition_in: "zoom_through"` (không nằm trong ALL): ô sau nằm TRONG một bộ
    # phận của ô trước (`through`); core.js tính vị trí/cỡ thật từ điểm neo (vẽ khô tất định) và cắt lỗ tròn.
    "portal": {"x": 0.0, "y": 110.0, "s": 0.06, "r": 0.0},
}
ZOOMS = {k for k, m in MOVES.items() if abs(m["s"] - 1) > 1e-6}      # kiểu bay đổi cỡ: không cho hai cái liền nhau
LEGACY_ALL = ["pan_r", "dive", "pan_d", "spin", "pull", "diag", "pan_l", "pan_u"]
ALL = LEGACY_ALL + ["orbit_tilt", "push_through", "rack", "whip_rot", "truck_parallax", "spiral"]
LEGACY_LOOK_MOVES = {          # ngữ pháp camera của từng look trước vòng 10 (dự án cũ giữ nguyên)
    "swiss": ["pan_r", "pan_d", "pan_l", "pan_d"],
    "sketch": ["pan_d"],
    "flow": ["pan_r", "pan_d", "pan_l", "pan_d"],
    "zoom": ["dive", "pull", "dive", "pan_r"],
    "picto": ["pan_r", "spin", "pan_l", "pan_d"],
    "hud": ["dive", "pan_r", "spin", "pull", "pan_d"],
    "synth": ["pan_d", "dive", "pan_u", "pull"],
    "iso": ["diag", "pan_r", "dive", "pan_d"],
    "spy": ["diag", "pan_l", "spin", "pan_r"],
    "gallery": ["pan_r", "pan_l"],
}
LOOK_MOVES = {                 # ngữ pháp camera của từng look (thiếu → dùng ALL)
    "swiss": ["pan_r", "pan_d", "pan_l", "pan_d"],
    "sketch": ["pan_d"],
    "flow": ["pan_r", "pan_d", "pan_l", "pan_d"],
    "zoom": ["dive", "pull", "push_through", "pan_r", "rack"],
    "picto": ["pan_r", "spin", "pan_l", "pan_d"],
    "hud": ["dive", "pan_r", "spin", "pull", "pan_d", "push_through", "rack"],
    "synth": ["pan_d", "dive", "pan_u", "pull", "whip_rot"],
    "iso": ["diag", "pan_r", "dive", "pan_d", "orbit_tilt", "truck_parallax"],
    "spy": ["diag", "pan_l", "spin", "pan_r", "whip_rot"],
    "gallery": ["pan_r", "pan_l", "truck_parallax"],
    # look 2D mới của vòng 10 (WP-H1) — chưa có look thì mục này không dùng tới
    "comic": ["pan_r", "pan_d", "whip_rot", "push_through", "pan_l"],
    "halftone": ["pan_r", "diag", "rack", "pan_d", "spiral"],
    "pixel16": ["pan_r", "pan_l", "pan_d", "pan_u"],
    "sprite8": ["pan_r", "pan_d", "pan_l", "pan_u"],
    "silhouette": ["truck_parallax", "pan_r", "pull", "pan_l"],
    "cutout": ["truck_parallax", "pan_r", "dive", "pan_d", "orbit_tilt"],
    "vox": ["pan_r", "pan_d", "pan_l", "rack", "truck_parallax"],
    "story": ["pan_r", "pan_d", "pan_l", "truck_parallax"],
}
LOOK_L = {"swiss": 7, "sketch": 12, "spy": 8, "boil": 10, "gallery": 12, "zoom": 11,   # nửa chặng bay (frame)
          "sprite8": 6, "pixel16": 7, "comic": 8, "cutout": 10, "silhouette": 11, "vox": 8, "story": 8}


def _tile(move):
    """Vị trí ô theo kiểu bay (chỉ x, y, s, r — `fx` là gợi ý, thêm vào khi có để engine hỗ trợ đọc)."""
    m = MOVES[move]
    return {k: m[k] for k in ("x", "y", "s", "r")} | ({"fx": m["fx"]} if m.get("fx") else {})


def inverse(t):
    """Ô A tương đối với ô B, khi biết B tương đối với A (phép đồng dạng: dời + xoay + co giãn)."""
    s, r = 1.0 / t["s"], -t["r"]
    cr, sr = math.cos(r), math.sin(r)
    x, y = -t["x"] * s, -t["y"] * s
    return {"x": x * cr - y * sr, "y": x * sr + y * cr, "s": s, "r": r}


def enabled(style):
    if not channel().get("code_render", {}).get("html_spine", True):
        return False
    return (textstyle.load_style(style).get("html") or {}).get("spine", True) is not False


def look_of(style):
    return (textstyle.load_style(style).get("html") or {}).get("look", "flat")


def _archetype_moves(archetype):
    if not archetype:
        return []
    if isinstance(archetype, (list, tuple)):
        return [m for m in archetype if m in MOVES]
    if isinstance(archetype, str):
        from . import narratives  # noqa: PLC0415
        return [m for m in narratives.archetype_moves(archetype) if m in MOVES]
    return []


def pool_for(style, prefer=None, legacy=False, archetype=None):
    """Kho kiểu bay: ngữ pháp của look, giao với kiểu bay hợp archetype (config/archetypes.json → moves) và dạng kịch
    bản (config/narratives.json → moves) nếu còn lại ít nhất một. legacy=True: bộ kiểu bay trước vòng 10 (dự án cũ)."""
    looks, every = (LEGACY_LOOK_MOVES, LEGACY_ALL) if legacy else (LOOK_MOVES, ALL)
    pool = looks.get(look_of(style), every)
    arch_moves = _archetype_moves(archetype)
    if arch_moves:
        arch_pool = [m for m in arch_moves if m in pool and m in MOVES]
        if arch_pool:
            if prefer:
                both_all = [m for m in arch_pool if m in prefer]
                if both_all:
                    return both_all
            return arch_pool
    if prefer:
        both = [m for m in prefer if m in pool and m in MOVES]
        if both:
            return both
    return pool


def _fresh_first(pool, avoid, seed_text):
    """Đẩy kiểu bay vừa dùng ở các video gần nhất xuống cuối. avoid = {move: trọng số gần đây}. Còn ≥ 2 kiểu chưa dùng →
    chỉ bay bằng các kiểu đó; ít hơn → giữ cả kho, xếp kiểu ít dùng lên trước (bằng nhau thì xáo theo video)."""
    uniq = list(dict.fromkeys(pool))
    fresh = [m for m in uniq if not avoid.get(m)]
    if len(fresh) >= 2:
        return fresh, True
    h = int(hashlib.sha1(str(seed_text).encode()).hexdigest()[:8], 16)
    return sorted(uniq, key=lambda m: (avoid.get(m, 0.0), (uniq.index(m) + h) % len(uniq))), False


def sequence(n, style, seed_text, prefer=None, avoid=None, legacy=False, archetype=None):
    """n kiểu bay cho n-1 điểm nối (xáo theo video, không lặp liền nhau, không hai cú đổi cỡ — dive/pull/push_through…
    — liền nhau). avoid = {move: trọng số} của các video gần nhất (motionplan.recent_moves): kiểu chưa dùng đi trước."""
    pool = pool_for(style, prefer, legacy, archetype=archetype)
    h = int(hashlib.sha1(str(seed_text).encode()).hexdigest()[:8], 16)
    k = h % len(pool)
    if avoid:
        pool, only_fresh = _fresh_first(pool, avoid, seed_text)
        k = h % len(pool) if only_fresh else 0        # kho lẫn kiểu cũ: bắt đầu từ kiểu ít dùng nhất
    zooms = {"dive", "pull"} if legacy else ZOOMS
    out = []
    for i in range(max(0, n)):
        idx = (k + i * (1 + h % 3)) % len(pool)
        m = pool[idx]
        if out and (m == out[-1] or (m in zooms and out[-1] in zooms)) and len(pool) > 1:
            cands = [pool[(idx + j) % len(pool)] for j in range(1, len(pool))]
            m = next((c for c in cands if c != out[-1] and not (c in zooms and out[-1] in zooms)),
                     next((c for c in cands if c != out[-1]), m))
        out.append(m)
    return out


def _tease(x):
    x = min(1.0, max(0.0, x))
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def _interp(a, b, e, same):
    """Bản Python của interp() trong engines/html/core.js — zoom theo log, vị trí theo 1/z, lia thì chùng zoom giữa chặng."""
    lz = math.log(a["z"]) + (math.log(b["z"]) - math.log(a["z"])) * e
    z = math.exp(lz)
    w = (1 / a["z"] - 1 / z) / (1 / a["z"] - 1 / b["z"]) if abs(a["z"] - b["z"]) > 1e-4 else e
    return {"cx": a["cx"] + (b["cx"] - a["cx"]) * w, "cy": a["cy"] + (b["cy"] - a["cy"]) * w,
            "z": z * (1 - 0.16 * math.sin(math.pi * e)) if same else z, "rot": a["rot"] + (b["rot"] - a["rot"]) * e}


def travel_matrix(sp, f, n, width, height):
    """Ma trận affine 2×3 (ảnh của chính shot → màn hình) ở frame f nếu f nằm trong chặng bay, không thì None.
    Cho engine dựng sẵn cả khung hình (Manim): cùng kiểu bay, cùng công thức với engine html, chỉ không vẽ ô hàng xóm."""
    if not sp:
        return None
    L = max(4, int(sp.get("L", 9)))
    me = {"cx": 0.0, "cy": 0.0, "z": 1.0, "rot": 0.0}

    def at(t):
        return {"cx": t["x"], "cy": t["y"], "z": 1 / t["s"], "rot": t["r"]}
    prv, nxt = sp.get("prev"), sp.get("next")
    if prv and f < L:
        t = prv["tile"]
        cam = _interp(at(t), me, _tease((f + L) / (2 * L)), abs(t["s"] - 1) < 1e-3)
    elif nxt and f >= n - L:
        t = nxt["tile"]
        cam = _interp(me, at(t), _tease((f - (n - L)) / (2 * L)), abs(t["s"] - 1) < 1e-3)
    else:
        return None
    z, r = cam["z"], -cam["rot"]
    a, b, c, d = z * math.cos(r), -z * math.sin(r), z * math.sin(r), z * math.cos(r)
    cx, cy = width / 2, height / 2
    # màn hình = C + A·(p − C − cam)
    px, py = cx + cam["cx"], cy + cam["cy"]
    return [[a, b, cx - (a * px + b * py)], [c, d, cy - (c * px + d * py)]]


def _portal_cuts(run, entry):
    """{chỉ số shot trong chuỗi: through} cho các shot ghi `zoom_through` mà cả hai phía là html thật (không phải ô ma)."""
    out = {}
    for i in range(1, len(run)):
        sh, psh = run[i][1], run[i - 1][1]
        if sh.get("transition_in") != "zoom_through":
            continue
        if entry(sh).get("ghost") or entry(psh).get("ghost"):
            continue
        out[i] = sh.get("through") or "center"
    return out


def _with_portals(moves, portals, pool):
    """Đặt `portal` vào điểm nối có zoom_through; kiểu bay đổi cỡ đứng sát cạnh → đổi sang lia (không hai cú đổi cỡ liền)."""
    moves = list(moves)
    for i in portals:
        moves[i - 1] = "portal"
    flat = [m for m in pool if m not in ZOOMS] or ["pan_r", "pan_d"]
    for j, m in enumerate(moves):
        if m == "portal":
            continue
        if m in ZOOMS and ((j > 0 and moves[j - 1] == "portal") or (j + 1 < len(moves) and moves[j + 1] == "portal")):
            moves[j] = next((f for f in flat if (j == 0 or f != moves[j - 1])), flat[0])
    return moves


CALM = ["pan_r", "pan_d", "pan_l", "truck_parallax", "pan_u"]     # vòng 22: explainer — bay ngang/dọc, không lao/xoáy


def context(segments, shots, style, seed_text, is_html, entry, prefer=None, archetype=None, calm=False):
    """{sid: spine} cho mọi shot nằm trong một chuỗi liền nhau. segments = timeline (thứ tự + số frame),
    shots = {sid: shot}, is_html(shot) → bool (shot thuộc chuỗi: engine html, hoặc manim dưới dạng "ô ma"),
    entry(shot) → {scene, params[, ghost]} (params đã có index), prefer = kiểu bay hợp dạng kịch bản (narratives.moves),
    archetype = phong cách đạo diễn (config/archetypes.json → moves) được ưu tiên khi có."""
    if not enabled(style):
        return {}
    base_L = LOOK_L.get(look_of(style), 9)
    from . import motionplan  # noqa: PLC0415 — lịch sử kênh (đọc projects/*, không ghi)
    legacy = motionplan.legacy(seed_text)
    avoid = {} if legacy else motionplan.recent_moves(seed_text)
    runs, cur = [], []
    for seg in segments:
        sh = shots.get(seg["sid"])
        if sh is not None and is_html(sh):
            cur.append((seg, sh))
        else:
            if cur:
                runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    out = {}
    for ri, run in enumerate(runs):
        if len(run) < 2:
            continue
        moves = sequence(len(run) - 1, style, f"{seed_text}:{ri}", CALM if calm else prefer, avoid, legacy,
                         archetype=None if calm else archetype)
        if calm:                                   # profile explainer: chỉ bay êm (ngang/dọc/thị sai) giữa các shot
            moves = [m if m in CALM else CALM[j % len(CALM)] for j, m in enumerate(moves)]
        portals = _portal_cuts(run, entry)
        moves = _with_portals(moves, portals, pool_for(style, prefer, legacy, archetype=archetype))
        # shot ngắn: chặng bay ngắn lại, không chồng nhau
        run_L = max(4, min(base_L, min(int(seg["n"]) for seg, _ in run) // 3))
        for i, (seg, _sh) in enumerate(run):
            sp = {"L": run_L, "move_in": moves[i - 1] if i else None, "move_out": moves[i] if i < len(run) - 1 else None}
            if i > 0:
                pseg, psh = run[i - 1]
                tile = inverse(MOVES[moves[i - 1]])
                if i in portals:
                    tile = {**tile, "portal": True, "at": portals[i]}
                sp["prev"] = {**entry(psh), "n": int(pseg["n"]), "tile": tile}
            if i < len(run) - 1:
                nseg, nsh = run[i + 1]
                tile = _tile(moves[i])
                if i + 1 in portals:
                    tile = {**tile, "portal": True, "at": portals[i + 1]}
                sp["next"] = {**entry(nsh), "n": int(nseg["n"]), "tile": tile}
            out[seg["sid"]] = sp
    return out
