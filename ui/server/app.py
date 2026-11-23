"""HTTP server của Studio UI: REST JSON (/api/…), luồng log SSE, file tĩnh của ui/web, file dự án (có Range).

Chỉ nghe 127.0.0.1. Chặn DNS rebinding (Host phải là localhost) và CSRF (POST cần header X-Studio-Client + JSON).
Không thư viện ngoài — http.server của Python."""
import json
import os
import re
import sys
import time
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from .services import catalog, files, jobs, projects, system, workspace

MANAGER = None
CSP = ("default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; style-src 'self' 'unsafe-inline'; "
       "font-src 'self' data:; connect-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self'")
ROUTES = []
MAX_UPLOAD = 2 * 1024 ** 3                     # clip Flow tối đa 2 GB
CLIP_EXT = (".mp4", ".mov", ".webm", ".mkv")


def route(method, pattern):
    rx = re.compile("^" + pattern + "$")

    def deco(fn):
        ROUTES.append((method, rx, fn))
        return fn
    return deco


class ApiError(Exception):
    def __init__(self, status, msg):
        super().__init__(msg)
        self.status, self.msg = status, msg


# ---------------------------------------------------------------- API
@route("GET", r"/api/health")
def health(h, q):
    return {"ok": True, "time": time.time()}


@route("GET", r"/api/overview")
def overview(h, q):
    last = MANAGER.last_by_slug()
    items = [p for p in projects.list_all(last) if not p.get("demo")]
    by = {}
    for p in items:
        by[p["status"]] = by.get(p["status"], 0) + 1
    done = [p for p in items if p.get("has_final")]
    recent6 = sorted(done, key=lambda x: -x["updated"])[:6]
    return {
        "counts": {"projects": len(items), "finished": len(done), "waiting": by.get("waiting_clips", 0) + by.get(
            "look_check", 0) + by.get("need_storyboard", 0), "running": sum(
            1 for j in MANAGER.list() if j["status"] in ("running", "queued"))},
        "by_status": by, "recent": items[:8], "jobs": MANAGER.list(6),
        "balance": {"flow": sum(1 for p in recent6 if p.get("uses_flow")), "code": sum(
            1 for p in recent6 if p.get("uses_flow") is False), "window": len(recent6)},
        "checks": system.checks(),
    }


@route("GET", r"/api/projects")
def list_projects(h, q):
    items = projects.list_all(MANAGER.last_by_slug())
    if q.get("demo") != "1":
        items = [p for p in items if not p.get("demo")]
    return {"items": items}


@route("GET", r"/api/projects/(?P<slug>[^/]+)")
def get_project(h, q, slug):
    try:
        return projects.detail(slug, MANAGER.last_by_slug().get(slug))
    except projects.NotFound as e:
        raise ApiError(404, f"Không có dự án '{slug}'.") from e


# ---------------------------------------------------------------- API v2 (UI công đoạn) — không đổi API cũ
def _slug(slug):
    if not workspace.slug_ok(slug):
        raise ApiError(404, f"Không có dự án '{slug}'.")
    return slug


@route("GET", r"/api/v2/projects/(?P<slug>[^/]+)/workspace")
def v2_workspace(h, q, slug):
    try:
        return workspace.workspace(_slug(slug), MANAGER.last_by_slug().get(slug))
    except projects.NotFound as e:
        raise ApiError(404, f"Không có dự án '{slug}'.") from e


@route("GET", r"/api/v2/projects/(?P<slug>[^/]+)/review")
def v2_review_get(h, q, slug):
    return workspace.review_get(_slug(slug))


@route("POST", r"/api/v2/projects/(?P<slug>[^/]+)/review")
def v2_review_post(h, q, slug):
    try:
        return workspace.review_post(_slug(slug), h.json_body())
    except (ValueError, TypeError) as e:
        raise ApiError(400, str(e)) from e


@route("GET", r"/api/v2/delivery")
def v2_delivery(h, q):
    return workspace.delivery()


@route("GET", r"/api/v2/atlas/(?P<n>\d{1,2})")
def v2_atlas(h, q, n):
    r = workspace.atlas_raw(int(n))
    if not r:
        raise ApiError(404, "Chưa có bản gốc trên máy này (vendor/3d-style-atlas/raw/).")
    return r


@route("GET", r"/api/v2/assets")
def v2_assets(h, q):
    return workspace.assets()


@route("GET", r"/api/v2/session")
def v2_session(h, q):
    return {"cost": workspace.session_cost(), "jobs": [j for j in MANAGER.list(20) if j["status"] in ("running", "queued")]}


def _run_sbedit(kind, params):
    try:
        job, rep = MANAGER.run_sync(kind, params)
    except jobs.JobError as e:
        raise ApiError(400, str(e)) from e
    if rep is None:
        lines, _ = job.since(0)
        msg = next((ln for ln in reversed(lines) if ln.strip() and not ln.startswith("—")), "Không nhận được kết quả.")
        rep = {"ok": job.exit_code == 0,
               "errors": [] if job.exit_code == 0 else [{"msg": msg, "path": "", "line": None}],
               "warnings": []}
    rep["job"] = job.meta()
    return rep


@route("POST", r"/api/v2/projects/(?P<slug>[^/]+)/sb/check")
def v2_sb_check(h, q, slug):
    from vidlib import sbedit, storyboard as sbm  # noqa: PLC0415
    p = projects.proj_dir(_slug(slug))
    body = h.json_body()
    text = body.get("text")
    try:
        if isinstance(text, str) and text.strip():
            data, start, notes = sbedit.extract_json(text)
            rep = sbedit.check(p, data, text, start)
            rep["notes"] = notes
            return rep
        cur = sbm.load(p)
        if cur is None:
            raise sbedit.SbError("Dự án chưa có storyboard.json.")
        raw = projects._read(sbm.path_of(p))
        return sbedit.check(p, cur, raw)
    except sbedit.SbError as e:
        return {**e.report, "ok": False}


@route("POST", r"/api/v2/projects/(?P<slug>[^/]+)/sb/import")
def v2_sb_import(h, q, slug):
    _slug(slug)
    body = h.json_body()
    rep = _run_sbedit("sb_import", {"target": slug, "text": body.get("text")})
    if (rep.get("ok") or rep.get("saved")) and body.get("resume"):
        dry = body.get("dry_run")
        if dry is None:
            dry = os.path.exists(os.path.join(projects.proj_dir(slug), "work", "DRYRUN"))
        try:
            rjob = MANAGER.submit("video", {"target": slug, "yes": True, "dry_run": bool(dry)})
            rep["resume_job"] = rjob.meta()
        except jobs.JobError as e:
            rep.setdefault("warnings", []).append({"msg": f"Đã lưu nhưng chưa tự chạy tiếp được: {e}", "path": ""})
    return rep


@route("POST", r"/api/v2/projects/(?P<slug>[^/]+)/sb/patch")
def v2_sb_patch(h, q, slug):
    _slug(slug)
    body = h.json_body()
    return _run_sbedit("sb_patch", {
        "target": slug,
        "shot": body.get("shot"),
        "set": body.get("set") or {},
        "unset": body.get("unset") or [],
    })


@route("GET", r"/api/v2/projects/(?P<slug>[^/]+)/sb/history")
def v2_sb_history(h, q, slug):
    from vidlib import sbedit  # noqa: PLC0415
    p = projects.proj_dir(_slug(slug))
    return {"items": sbedit.history(p)}


@route("POST", r"/api/v2/projects/(?P<slug>[^/]+)/sb/restore")
def v2_sb_restore(h, q, slug):
    _slug(slug)
    body = h.json_body()
    return _run_sbedit("sb_restore", {"target": slug, "id": body.get("id")})


@route("POST", r"/api/v2/projects/(?P<slug>[^/]+)/sb/preview")
def v2_sb_preview(h, q, slug):
    _slug(slug)
    body = h.json_body()
    return _run_sbedit("sb_preview", {"target": slug, "shot": body.get("shot"), "u": body.get("u", 0.5)})


@route("POST", r"/api/v2/ideas/(?P<batch>[^/]+)/import")
def v2_ideas_import(h, q, batch):
    body = h.json_body()
    return _run_sbedit("ideas_import", {"batch": batch, "text": body.get("text")})


@route("POST", r"/api/v2/env")
def v2_env_post(h, q):
    try:
        return system.save_env(h.json_body())
    except (ValueError, TypeError) as e:
        raise ApiError(400, str(e)) from e


@route("GET", r"/api/v2/catalog/schema")
def v2_catalog_schema(h, q):
    return catalog.schema()


@route("POST", r"/api/projects/(?P<slug>[^/]+)/clips/(?P<sid>C\d{2})")
def upload_clip(h, q, slug, sid):
    """Tải clip Flow cho một shot → projects/<slug>/clips/<SID>.<ext> (ingest nhận theo tên file)."""
    try:
        p = projects.proj_dir(slug)
    except projects.NotFound as e:
        raise ApiError(404, "Không có dự án.") from e
    name = unquote(h.headers.get("X-Filename") or "clip.mp4")
    ext = os.path.splitext(name)[1].lower() or ".mp4"
    if ext not in CLIP_EXT:
        raise ApiError(400, f"Chỉ nhận {', '.join(CLIP_EXT)}.")
    n = int(h.headers.get("Content-Length") or 0)
    if n <= 0 or n > MAX_UPLOAD:
        raise ApiError(400, "Kích thước file không hợp lệ.")
    if MANAGER and any(j["slug"] == slug and j["status"] in ("queued", "running") for j in MANAGER.list(200)):
        raise ApiError(409, "Dự án đang có job chạy — đợi xong rồi tải clip (tránh pipeline đọc clip đang ghi dở).")
    d = os.path.join(p, "clips")
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, sid + ext)
    left = n
    with open(dst + ".part", "wb") as fh:          # nhận HẾT file mới trước (AUD-705) …
        while left > 0:
            chunk = h.rfile.read(min(1 << 20, left))
            if not chunk:
                break
            fh.write(chunk)
            left -= len(chunk)
    if left:
        os.remove(dst + ".part")
        raise ApiError(400, "Tải lên bị ngắt — clip cũ vẫn giữ nguyên.")
    for f in os.listdir(d):                       # … rồi mới thay clip cũ của shot này
        if os.path.splitext(f)[0].upper() == sid and f.lower().endswith(CLIP_EXT) and f != sid + ext:
            os.remove(os.path.join(d, f))
    os.replace(dst + ".part", dst)
    return {"ok": True, "file": f"clips/{sid}{ext}"}


@route("POST", r"/api/projects/(?P<slug>[^/]+)/reveal")
def reveal(h, q, slug):
    """Mở thư mục dự án trong Explorer/Finder (máy cục bộ)."""
    try:
        p = projects.proj_dir(slug)
    except projects.NotFound as e:
        raise ApiError(404, "Không có dự án.") from e
    if os.name == "nt":
        os.startfile(p)  # noqa: S606 — đường dẫn đã kiểm tra nằm trong projects/
    elif sys.platform == "darwin":
        import subprocess  # noqa: PLC0415
        subprocess.Popen(["open", p])
    else:
        import subprocess  # noqa: PLC0415
        subprocess.Popen(["xdg-open", p])
    return {"ok": True}


@route("GET", r"/api/styles")
def get_styles(h, q):
    return {"items": catalog.style_list()}


@route("GET", r"/api/voices")
def get_voices(h, q):
    return {"items": catalog.voice_list()}


@route("GET", r"/api/narratives")
def get_narratives(h, q):
    return catalog.narrative_list(q.get("topic", ""))


@route("GET", r"/api/stages")
def get_stages(h, q):
    return catalog.stages()


@route("GET", r"/api/models")
def get_models(h, q):
    from vidlib.common import channel, flow_models  # noqa: PLC0415
    fm = flow_models()
    return {"items": list(fm.get("video_models", {})), "default": channel()["flow"]["video_model"]}


@route("GET", r"/api/plan")
def get_plan(h, q):
    topic = (q.get("topic") or "").strip()
    if not topic:
        raise ApiError(400, "Thiếu topic.")
    flow = {"1": True, "0": False}.get(q.get("flow", ""))
    try:
        return catalog.plan(topic, flow=flow, style=q.get("style"), narrative=q.get("narrative"))
    except Exception as e:  # noqa: BLE001 — StudioError (style không có…)
        raise ApiError(400, str(e)) from e


@route("GET", r"/api/ideas")
def get_ideas(h, q):
    from vidlib.common import load_json  # noqa: PLC0415
    d = files.ROOTS["ideas"]
    out = []
    if os.path.isdir(d):
        for b in sorted(os.listdir(d)):
            bp = os.path.join(d, b, "brief.md")
            jp = os.path.join(d, b, "ideas.json")
            if not os.path.isdir(os.path.join(d, b)):
                continue
            data = load_json(jp, {}) if os.path.exists(jp) else {}
            mt = os.path.getmtime(jp) if os.path.exists(jp) else (os.path.getmtime(bp) if os.path.exists(bp) else 0)
            out.append({"batch": b, "theme": data.get("theme") or b, "ready": bool(data.get("ideas")),
                        "picked": data.get("picked") or [], "ideas": data.get("ideas") or [],
                        "brief": os.path.exists(bp),
                        "brief_md": projects._read(bp)[:40000] if os.path.exists(bp) else "",
                        "updated": mt})
    return {"items": sorted(out, key=lambda x: -x["updated"])}


@route("GET", r"/api/jobs")
def list_jobs(h, q):
    return {"items": MANAGER.list()}


@route("POST", r"/api/jobs")
def create_job(h, q):
    body = h.json_body()
    try:
        job = MANAGER.submit(body.get("kind"), body.get("params") or {})
    except jobs.JobError as e:
        raise ApiError(400, str(e)) from e
    return {"job": job.meta()}


@route("GET", r"/api/jobs/(?P<jid>[\w-]+)")
def get_job(h, q, jid):
    job = MANAGER.get(jid)
    if not job:
        raise ApiError(404, "Không có job.")
    lines, nxt = job.since(int(q.get("from", 0) or 0))
    return {"job": job.meta(), "lines": lines, "next": nxt}


@route("POST", r"/api/jobs/(?P<jid>[\w-]+)/cancel")
def cancel_job(h, q, jid):
    job = MANAGER.cancel(jid)
    if not job:
        raise ApiError(404, "Không có job.")
    return {"job": job.meta()}


@route("GET", r"/api/system")
def get_system(h, q):
    return {"checks": system.checks(), "config": system.config_summary()}


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "StudioUI/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):                 # yên lặng — log job mới là thứ quan trọng
        if os.environ.get("STUDIO_UI_DEBUG"):
            sys.stderr.write(f"{self.address_string()} - {fmt % args}\n")

    def json_body(self):
        if "application/json" not in (self.headers.get("Content-Type") or ""):
            raise ApiError(415, "Cần Content-Type: application/json.")
        n = int(self.headers.get("Content-Length") or 0)
        if n > 1 << 20:
            raise ApiError(413, "Body quá lớn.")
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError as e:
            raise ApiError(400, "JSON không hợp lệ.") from e

    def end_headers(self):
        # AUD-703: không cho trang khác nhúng UI (clickjacking), không đoán MIME, không gửi referrer
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP)
        super().end_headers()

    def _host_ok(self):
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        return host in ("127.0.0.1", "localhost", "::1")

    def _send_json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _dispatch(self, method):
        if not self._host_ok():
            return self._send_json({"error": "Host không hợp lệ."}, 403)
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        path = u.path
        if method == "POST" and self.headers.get("X-Studio-Client") != "web":
            return self._send_json({"error": "Thiếu header X-Studio-Client."}, 403)
        if path.startswith("/api/jobs/") and path.endswith("/events") and method == "GET":
            return self._sse(path.split("/")[3], int(q.get("from", 0) or 0))
        if path == "/api/file" and method in ("GET", "HEAD"):
            return self._file(q.get("root", ""), q.get("path", ""), head=method == "HEAD")
        if path == "/api/v2/thumb" and method in ("GET", "HEAD"):
            return self._thumb(q.get("root", ""), q.get("path", ""), q.get("w", "240"), head=method == "HEAD")
        if path.startswith("/api/"):
            for m, rx, fn in ROUTES:
                mt = rx.match(path)
                if m == method and mt:
                    try:
                        return self._send_json(fn(self, q, **{k: unquote(v) for k, v in mt.groupdict().items()}))
                    except ApiError as e:
                        return self._send_json({"error": e.msg}, e.status)
                    except Exception as e:  # noqa: BLE001
                        traceback.print_exc()
                        return self._send_json({"error": f"Lỗi máy chủ: {e}"}, 500)
            return self._send_json({"error": "Không có API này."}, 404)
        if method in ("GET", "HEAD"):
            return self._static(path, head=method == "HEAD")
        return self._send_json({"error": "Phương thức không hỗ trợ."}, 405)

    def do_GET(self):  # noqa: N802
        self._dispatch("GET")

    def do_HEAD(self):  # noqa: N802
        self._dispatch("HEAD")

    def do_POST(self):  # noqa: N802
        self._dispatch("POST")

    # ---- file
    def _static(self, path, head=False):
        if path in ("/", ""):
            path = "/index.html"
        if path.startswith("/fonts/"):
            base, rel = files.FONT_DIR, path[len("/fonts/"):]
        else:
            base, rel = files.WEB_DIR, path
        try:
            p = files.safe_join(base, unquote(rel))
        except files.Forbidden:
            return self._send_json({"error": "Cấm."}, 403)
        if not os.path.isfile(p):
            return self._send_json({"error": "Không có file."}, 404)
        self._stream(p, head, cache="no-cache")

    def _thumb(self, root, rel, w, head=False):
        """Ảnh nhỏ (JPEG, rộng w ≤ 640) có cache theo mtime — lưới shot/style không tải PNG 1080×1920."""
        try:
            p = files.resolve(root, rel)
        except files.Forbidden:
            return self._send_json({"error": "Cấm."}, 403)
        if not os.path.isfile(p) or not p.lower().endswith((".png", ".jpg", ".jpeg")):
            return self._send_json({"error": "Không có ảnh."}, 404)
        try:
            out = files.thumbnail(p, max(32, min(640, int(w or 240))))
        except Exception:  # noqa: BLE001
            return self._send_json({"error": "Không đọc được ảnh."}, 415)
        self._stream(out, head, cache="max-age=600")

    def _file(self, root, rel, head=False):
        try:
            p = files.resolve(root, rel)
        except files.Forbidden:
            return self._send_json({"error": "Cấm."}, 403)
        if not os.path.isfile(p):
            return self._send_json({"error": "Không có file."}, 404)
        self._stream(p, head, cache="no-cache")

    def _stream(self, p, head=False, cache="no-cache"):
        size = os.path.getsize(p)
        rng = files.parse_range(self.headers.get("Range"), size)
        start, end = rng if rng else (0, size - 1)
        self.send_response(HTTPStatus.PARTIAL_CONTENT if rng else HTTPStatus.OK)
        self.send_header("Content-Type", files.content_type(p))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(max(0, end - start + 1)))
        self.send_header("Cache-Control", cache)
        self.send_header("Last-Modified", self.date_time_string(int(os.path.getmtime(p))))
        if rng:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if head or size == 0:
            return
        with open(p, "rb") as fh:
            fh.seek(start)
            left = end - start + 1
            try:
                while left > 0:
                    chunk = fh.read(min(1 << 16, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

    # ---- SSE: log job trực tiếp
    def _sse(self, jid, frm):
        job = MANAGER.get(jid)
        if not job:
            return self._send_json({"error": "Không có job."}, 404)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        n = frm
        try:
            while True:
                lines, n2 = job.since(n)
                if lines:
                    payload = json.dumps({"lines": lines, "next": n2}, ensure_ascii=False)
                    self.wfile.write(f"event: lines\ndata: {payload}\n\n".encode())
                    n = n2
                self.wfile.write(f"event: meta\ndata: {json.dumps(job.meta(), ensure_ascii=False)}\n\n".encode())
                self.wfile.flush()
                if job.status not in ("queued", "running"):
                    lines, n2 = job.since(n)
                    if lines:
                        self.wfile.write(f"event: lines\ndata: {json.dumps({'lines': lines, 'next': n2})}\n\n".encode())
                    self.wfile.write(b"event: end\ndata: {}\n\n")
                    self.wfile.flush()
                    return
                with job.cond:
                    job.cond.wait(timeout=10)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            return


def serve(port=8765, open_browser=True):
    global MANAGER
    MANAGER = jobs.Manager()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.daemon_threads = True
    url = f"http://127.0.0.1:{port}/"
    print(f"Studio UI: {url}  (Ctrl+C để dừng)", flush=True)
    if open_browser:
        import webbrowser  # noqa: PLC0415
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Dừng Studio UI.")
    finally:
        httpd.server_close()

