"""Tài sản do người dùng đưa vào `assets/user/` và gọi bằng TÊN trong storyboard (không đường dẫn tuyệt đối):

  svg     assets/user/svg/<tên>.json    — nhập bằng `python studio.py svg <file.svg>` (SVGO + đo hình học → `parts`)
          storyboard: html `"icon": "svg:<tên>"` (mọi chỗ nhận icon) · three.js `stage` prop `"type": "svg:<tên>"` (ép khối)
  lottie  assets/user/lottie/<tên>.json | .lottie  — html `scene` actor `"lottie": "<tên>"` (dotLottie, vendor/dotlottie)
  rive    assets/user/rive/<tên>.riv               — html `scene` actor `"rive": "<tên>"` (Rive, vendor/rive)

Bản quyền: mỗi file kèm ghi chú nguồn/giấy phép (`--license` lúc nhập SVG; Lottie/Rive: file `<tên>.license.txt` cạnh nó).
QA cảnh báo khi thiếu (`license_notes`). Không tự tải tài sản từ mạng.

Kho THƯ VIỆN (vòng 10, vidlib/assets3d.py): "svg:<tên>" tìm SVG người dùng trước rồi tới assets/lib/svg; icon tên thường
mà đồ chơi kênh không có → SVG thư viện cùng tên; three.js prop "type": "model:<tên>" → model_url + model (glTF CC0).
"""

import copy
import hashlib
import json
import os
import shutil

from .common import ROOT, StudioError, save_json

KINDS = {"svg": (".json",), "lottie": (".json", ".lottie"), "rive": (".riv",)}


def folder(kind):
    return os.path.join(ROOT, "assets", "user", kind)


def find(kind, name):
    """Tên (hoặc đường dẫn tương đối repo) → đường dẫn tuyệt đối, None nếu không có."""
    if not name or not isinstance(name, str):
        return None
    cand = [os.path.join(folder(kind), name + ext) for ext in KINDS[kind]] + [os.path.join(folder(kind), name),
                                                                             os.path.join(ROOT, name)]
    return next((os.path.abspath(p) for p in cand if os.path.isfile(p) and p.lower().endswith(KINDS[kind])), None)


def names(kind):
    d = folder(kind)
    if not os.path.isdir(d):
        return []
    return sorted({os.path.splitext(f)[0] for f in os.listdir(d) if f.lower().endswith(KINDS[kind])})


def url_of(path):
    return "/" + os.path.relpath(path, ROOT).replace(os.sep, "/")


def svg_parts(name):
    """SVG người dùng (assets/user/svg) trước, SVG thư viện (assets/lib/svg, vidlib/assets3d) sau."""
    p = find("svg", name)
    if not p:
        from . import assets3d  # noqa: PLC0415
        return assets3d.svg_parts(name)
    with open(p, encoding="utf-8") as fh:
        return json.load(fh).get("parts") or []


def svg_known(name):
    """Có SVG tên này (người dùng hoặc thư viện) trên máy không — cho kiểm icon của engine html."""
    from . import assets3d  # noqa: PLC0415
    return bool(find("svg", name) or assets3d.svg_path(name))


def _model_name(v):
    return v[6:] if isinstance(v, str) and v.startswith("model:") else None


def _lib_icon(v):
    """Tên icon thường (không 'svg:') mà thư viện đồ chơi kênh KHÔNG có nhưng kho SVG thư viện có → tên thư viện."""
    if not isinstance(v, str) or ":" in v or not v.strip():
        return None
    from engines import html  # noqa: PLC0415

    from . import assets3d  # noqa: PLC0415
    if html.icon_for(v) is not None:
        return None                                   # thứ tự: icon kênh → SVG người dùng → SVG thư viện
    n = v.strip().lower()
    return n if (find("svg", n) or assets3d.svg_path(n)) else None


def _svg_name(v):
    return v[4:] if isinstance(v, str) and v.startswith("svg:") else None


# ---------------------------------------------------------------------------------------------------------------------
def resolve(params, engine):
    """Đổi tên tài sản trong params thành dữ liệu engine dùng được (gọi lúc dựng job.json — engine không đọc đĩa).
    html: "icon": "svg:x" → {"parts": […]}; actor lottie/rive → URL tài sản phục vụ qua server cục bộ.
    three: prop "type": "svg:x" → type "svgicon" + icon_parts."""
    out = copy.deepcopy(params or {})

    def walk(o):
        if isinstance(o, dict):
            for k, v in list(o.items()):
                n = _svg_name(v)
                if k == "icon" and n is not None:
                    o[k] = {"parts": svg_parts(n) or []}
                elif k == "icon" and _lib_icon(v):
                    o[k] = {"parts": svg_parts(_lib_icon(v)) or []}
                elif engine == "three" and k == "type" and n is not None:
                    o["type"], o["icon_parts"] = "svgicon", svg_parts(n) or []
                elif engine == "three" and k == "type" and _model_name(v) is not None:
                    from . import assets3d  # noqa: PLC0415 — "model:<tên>" → URL + meta (kho glTF thư viện)
                    o.update(assets3d.job_data(_model_name(v)) or {})
                elif engine == "html" and k in ("lottie", "rive") and isinstance(v, str):
                    p = find(k, v)
                    if p:
                        o[k + "_url"] = url_of(p)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(out)
    return out


def errors(params):
    """Tên tài sản không có trên đĩa → lỗi kèm danh sách tên đang có."""
    errs = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                n = _svg_name(v)
                if k in ("icon", "type") and n is not None and not svg_known(n):
                    errs.append(f"SVG '{n}' không có (người dùng: {', '.join(names('svg')) or '—'}; thư viện: tìm bằng "
                                f"`python studio.py assets search {n} --svg`) — hoặc nhập: "
                                f"`python studio.py svg <file.svg> --name {n}`.")
                elif k == "type" and _model_name(v) is not None:
                    from . import assets3d  # noqa: PLC0415
                    errs.extend(assets3d.prop_errors(o))
                elif k in ("lottie", "rive") and isinstance(v, str) and not find(k, v):
                    errs.append(f"{k} '{v}' không có trong assets/user/{k}/ (có: {', '.join(names(k)) or '—'}).")
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(params)
    return errs


def license_notes(params):
    """[(loại, tên, ghi chú giấy phép | None)] của mọi tài sản người dùng mà params dùng — cho QA/sổ quyền."""
    out = []

    def note(kind, name):
        p = find(kind, name)
        if not p:
            return None
        if kind == "svg":
            with open(p, encoding="utf-8") as fh:
                return (json.load(fh).get("license") or "").strip() or None
        txt = os.path.splitext(p)[0] + ".license.txt"
        if os.path.isfile(txt):
            with open(txt, encoding="utf-8") as fh:
                return fh.read().strip() or None
        return None

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                n = _svg_name(v)
                if k in ("icon", "type") and n is not None:
                    from . import assets3d  # noqa: PLC0415
                    out.append(("svg", n, note("svg", n) or assets3d.svg_license(n)))
                elif k == "type" and _model_name(v) is not None:
                    from . import assets3d  # noqa: PLC0415
                    out.append(("model", _model_name(v), assets3d.model_license(_model_name(v))))
                elif k in ("lottie", "rive") and isinstance(v, str):
                    out.append((k, v, note(k, v)))
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(params)
    return out


# ---------------------------------------------------------------------------------------------------------------------
def svg_to_parts(text, role="auto", budget=1800):
    """Chuỗi SVG → {parts, stats}: SVGO + đo hình học trong Edge headless (engines/html/svgimport.js)."""
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    from . import coderender  # noqa: PLC0415

    if role not in ("auto", "ink", "hot", "cold", "accent", "dim"):
        raise StudioError("--role là auto|ink|hot|cold|accent|dim.")
    c = coderender.cfg()
    with coderender.serve() as port, sync_playwright() as p:
        b, pg, _ = coderender._open(p, f"http://127.0.0.1:{port}/engines/html/svgimport.html", c["channel"], c["gpu"])
        try:
            return pg.evaluate("([t, o]) => window.svgToParts(t, o)", [text, {"role": role, "budget": budget}])
        finally:
            b.close()


def svg_batch(items, role="auto", budget=1800, log=print):
    """[(tên, chuỗi SVG)] → {tên: {parts, stats} | {error}} — MỘT trình duyệt cho cả lô (nhập kho SVG thư viện)."""
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    from . import coderender  # noqa: PLC0415

    out = {}
    if not items:
        return out
    c = coderender.cfg()
    with coderender.serve() as port, sync_playwright() as p:
        b, pg, _ = coderender._open(p, f"http://127.0.0.1:{port}/engines/html/svgimport.html", c["channel"], c["gpu"])
        try:
            for i, (name, text) in enumerate(items):
                try:
                    out[name] = pg.evaluate("([t, o]) => window.svgToParts(t, o)", [text, {"role": role, "budget": budget}])
                except Exception as ex:  # noqa: BLE001 — một file hỏng không dừng cả lô
                    out[name] = {"error": str(ex).splitlines()[0][:200]}
                if (i + 1) % 100 == 0:
                    log(f"    {i + 1}/{len(items)} SVG")
        finally:
            b.close()
    return out


def import_svg(src, name=None, role="auto", license_note="", budget=1800, log=print):
    """File SVG → assets/user/svg/<tên>.json ({parts, license, nguồn, sha256}) + bản gốc <tên>.svg."""
    if not os.path.isfile(src):
        raise StudioError(f"Không có file SVG: {src}")
    name = name or os.path.splitext(os.path.basename(src))[0].lower().replace(" ", "-")
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    res = svg_to_parts(text, role, budget)
    if not res["parts"]:
        raise StudioError("SVG không có hình tô/viền nào dùng được.")
    os.makedirs(folder("svg"), exist_ok=True)
    out = os.path.join(folder("svg"), f"{name}.json")
    save_json(out, {"name": name, "source": os.path.basename(src), "license": license_note,
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "role": role,
                    "stats": res["stats"], "parts": res["parts"]})
    if os.path.abspath(src) != os.path.abspath(os.path.join(folder("svg"), f"{name}.svg")):
        shutil.copyfile(src, os.path.join(folder("svg"), f"{name}.svg"))
    st = res["stats"]
    log(f"✔ svg:{name} — {len(res['parts'])} mảnh · {st['subpaths']} subpath · {st['points']} điểm · SVGO "
        f"{st['bytes_in']}→{st['bytes_svgo']} byte → {os.path.relpath(out, ROOT)}"
        + ("" if license_note else "\n  ⚠ chưa ghi nguồn/giấy phép (--license \"…\") — QA sẽ nhắc."))
    return out
