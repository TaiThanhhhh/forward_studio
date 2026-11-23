"""Hàng đợi job: chạy `studio.py …` (và vài script bảo trì) như tiến trình con, một job một lúc (render nặng GPU/CPU),
log trực tiếp cho UI (SSE), huỷ cả cây tiến trình, lưu lịch sử ở ui/.runtime/jobs/.

Chỉ lệnh trong danh sách trắng, tham số được kiểm tra; không bao giờ qua shell."""
import collections
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid

from vidlib.common import PROJECTS, ROOT, slugify

RUNTIME = os.path.join(ROOT, "ui", ".runtime", "jobs")
MAX_LINES = 6000
EXIT_STAGE = {0: "done", 10: "waiting_clips", 2: "need_storyboard", 3: "storyboard_invalid", 4: "confirm_map",
              5: "need_ideas", 6: "pick_idea", 11: "look_check", 12: "qa_failed"}
STAGE_RE = re.compile(r"^▶ (\w+)")
FRAC_RE = re.compile(r"(\d+)/(\d+) frame")
STAGE_ORDER = ["idea", "script", "storyboard", "prompts", "page", "clips", "ingest", "trim", "voice", "assemble", "text",
               "outro", "audio", "look", "code", "render", "thumbnails", "qa", "publish", "deliver", "version"]
FINAL_RE = re.compile(r"^::stage=(\w+) project=(.+)$")
VOICE_RE = re.compile(r"^[\w .'-]{1,60}$")
CTRL_RE = re.compile(r"[\x00-\x1f\x7f]")
SID_RE = re.compile(r"C\d{2,3}")
PATH_RE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*|\.\d{1,3}|\[\d{1,3}\])*")
# Job nhẹ (sửa storyboard/ideas, xem trước 1 frame): chạy NGAY ở làn riêng — không xếp sau một render 10 phút.
LIGHT = ("sb_import", "sb_patch", "sb_restore", "sb_preview", "ideas_import")
MAX_PAYLOAD = 4 * 1024 * 1024
# Key được nạp từ .env vào tiến trình con (SDK anthropic/genai chỉ đọc biến môi trường) — giá trị không bao giờ ra log.
ENV_KEYS = ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "ELEVENLABS_API_KEY")


def _check_target(target):
    """Ý tưởng một dòng hoặc slug dự án có sẵn. Chặn ký tự điều khiển (\\0 từng làm chết worker — AUD-701) và mọi thứ
    trông như đường dẫn tới thư mục ngoài projects/ (../ui từng làm pipeline ghi file vào ui/ — AUD-702)."""
    if not target or len(target) > 300 or target.startswith("-") or CTRL_RE.search(target):
        raise JobError("Ý tưởng/slug không hợp lệ (1–300 ký tự, một dòng, không ký tự điều khiển, không bắt đầu bằng '-').")
    if ".." in target or target.startswith("."):
        raise JobError("Ý tưởng/slug không được chứa '..' hay bắt đầu bằng '.'.")
    if os.path.isdir(os.path.join(PROJECTS, target)) and os.path.basename(target) == target:
        return target
    if os.path.isabs(target) or os.path.isdir(os.path.join(ROOT, target)) or os.path.isdir(target):
        raise JobError("Ý tưởng trông như đường dẫn thư mục — chỉ nhận ý tưởng (câu) hoặc slug trong projects/.")
    return target


class JobError(ValueError):
    pass


class Job:
    def __init__(self, kind, argv, title, slug=None, script=None, params=None):
        self.id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        self.kind, self.argv, self.title, self.slug, self.script = kind, argv, title, slug, script
        self.params = params or {}        # để "Chạy lại" từ UI
        self.status = "queued"          # queued | running | finished | failed | cancelled | interrupted
        self.stage = None               # dòng ::stage= cuối (done, waiting_clips, look_check…)
        self.current = None             # stage đang chạy (dòng ▶)
        self.exit_code = None
        self.created, self.started, self.ended = time.time(), None, None
        self.lines = collections.deque(maxlen=MAX_LINES)
        self.offset = 0                 # số dòng đã rơi khỏi deque (để SSE đánh số liên tục)
        self.cond = threading.Condition()
        self.proc = None
        self.progress = None            # 0..1 ước từ dòng ▶ stage + "N/M frame" (không phải spinner vô tận)
        self.frac = None                # (n, m) frame của stage hiện tại
        self.first_stage = None
        self.stdin = None               # dữ liệu gửi vào stdin (storyboard dán vào…) — KHÔNG lưu vào lịch sử job
        self.light = kind in LIGHT

    def meta(self):
        return {"id": self.id, "kind": self.kind, "argv": self.argv, "title": self.title, "slug": self.slug,
                "params": self.params,
                "status": self.status, "stage": self.stage, "current": self.current, "exit_code": self.exit_code,
                "created": self.created, "started": self.started, "ended": self.ended,
                "lines": self.offset + len(self.lines), "progress": self.progress, "eta": self.eta(),
                "frames": list(self.frac) if self.frac else None, "light": self.light}

    def eta(self):
        if self.status != "running" or not self.progress or self.progress < 0.03 or not self.started:
            return None
        el = time.time() - self.started
        return round(el / self.progress * (1 - self.progress), 1)

    def _track(self, line):
        m = STAGE_RE.match(line)
        if m and m.group(1) in STAGE_ORDER:
            self.frac = None
            if self.first_stage is None:
                self.first_stage = m.group(1)
        f = FRAC_RE.search(line)
        if f and int(f.group(2)) > 0:
            self.frac = (int(f.group(1)), int(f.group(2)))
        cur = self.current if self.current in STAGE_ORDER else None
        if cur:
            a = STAGE_ORDER.index(self.first_stage or cur)
            span = max(1, len(STAGE_ORDER) - a)
            k = STAGE_ORDER.index(cur) - a
            inner = (self.frac[0] / self.frac[1]) if self.frac else 0.0
            self.progress = round(min(0.99, max(0.0, (k + inner) / span)), 3)

    def push(self, line):
        with self.cond:
            if len(self.lines) == self.lines.maxlen:
                self.offset += 1
            self.lines.append(line)
            m = STAGE_RE.match(line)
            if m:
                self.current = m.group(1)
            self._track(line)
            m = FINAL_RE.match(line.strip())
            if m:
                self.stage = m.group(1)
                if self.kind == "video":
                    self.slug = os.path.basename(m.group(2).strip())
            self.cond.notify_all()

    def since(self, n):
        """(dòng từ số thứ tự n, số tiếp theo)."""
        with self.cond:
            start = max(n, self.offset)
            items = list(self.lines)[start - self.offset:]
            return items, start + len(items)


class Manager:
    def __init__(self):
        self.jobs = collections.OrderedDict()
        self.queue = collections.deque()
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.fast = collections.deque()
        self.fast_wake = threading.Event()
        self.preview_slot = threading.Semaphore(1)       # một Edge xem trước một lúc
        os.makedirs(RUNTIME, exist_ok=True)
        self._load()
        threading.Thread(target=self._worker, daemon=True, name="studio-jobs").start()
        threading.Thread(target=self._worker, args=(True,), daemon=True, name="studio-jobs-fast").start()

    # ------------------------------------------------------------ dựng lệnh (danh sách trắng)
    def build(self, kind, p):
        from vidlib import narratives, pipeline, styles  # noqa: PLC0415
        from vidlib.common import flow_models  # noqa: PLC0415
        if kind == "video":
            target = _check_target(str(p.get("target") or "").strip())
            argv = ["video", target, "--no-open"]
            for flag in ("dry_run", "look_ok", "yes", "tts_force", "accept_qa"):
                if p.get(flag):
                    argv.append("--" + flag.replace("_", "-"))
            for key, opt in (("from", "--from"), ("only", "--only")):
                if p.get(key):
                    st = pipeline.ALIASES.get(str(p[key]).lower(), str(p[key]).lower())
                    if st not in pipeline.STAGES:
                        raise JobError(f"Stage '{p[key]}' không có.")
                    argv += [opt, st]
            if p.get("style") and p["style"] != "auto":
                if p["style"] not in styles.available():
                    raise JobError(f"Style '{p['style']}' không có.")
                argv += ["--style", p["style"]]
            if p.get("narrative") and p["narrative"] != "auto":
                if p["narrative"] not in narratives.ids():
                    raise JobError(f"Dạng kịch bản '{p['narrative']}' không có.")
                argv += ["--narrative", p["narrative"]]
            if p.get("voice") and p["voice"] != "auto":
                if not VOICE_RE.match(str(p["voice"])):
                    raise JobError("Tên giọng không hợp lệ.")
                argv += ["--voice", str(p["voice"])]
            if p.get("flow") is True:
                argv.append("--flow")
            elif p.get("flow") is False:
                argv.append("--no-flow")
            if p.get("ai"):
                if p["ai"] not in ("claude", "gemini"):
                    raise JobError("--ai chỉ nhận claude | gemini.")
                argv += ["--ai", p["ai"]]
            if p.get("model"):
                if p["model"] not in flow_models().get("video_models", {}):
                    raise JobError(f"Model Flow '{p['model']}' không có.")
                argv += ["--model", p["model"]]
            if p.get("platforms"):
                from vidlib import deliver  # noqa: PLC0415
                try:
                    names = deliver.preset_names(str(p["platforms"]))
                except Exception as e:  # noqa: BLE001
                    raise JobError(str(e)) from e
                argv += ["--platforms", ",".join(names)]
            slug = target if os.path.isdir(os.path.join(PROJECTS, target)) else slugify(target)
            return argv, ("Dựng video · " + target[:60]), slug, None
        if kind == "ideas":
            theme = str(p.get("theme") or "").strip()
            if not theme or len(theme) > 200 or CTRL_RE.search(theme) or theme.startswith("-"):
                raise JobError("Chủ đề không hợp lệ.")
            argv = ["ideas", theme]
            if p.get("pick"):
                if not re.fullmatch(r"\d{1,2}(,\d{1,2})*", str(p["pick"])):
                    raise JobError("pick dạng 3 hoặc 3,7.")
                argv += ["--pick", str(p["pick"])]
            elif p.get("auto_pick"):
                argv.append("--auto-pick")
            return argv, "Ý tưởng · " + theme[:60], None, None
        if kind == "trim":
            target = _check_target(str(p.get("target") or "").strip())
            sid = str(p.get("shot") or "")
            if not os.path.isdir(os.path.join(PROJECTS, target)) or not re.fullmatch(r"C\d{2}", sid):
                raise JobError("Cần dự án có sẵn và mã shot dạng C03.")
            if p.get("auto"):
                return ["trim", target, sid, "--auto"], f"Bỏ trim tay {sid} · {target}", target, None
            try:
                a, b = float(p.get("in")), float(p.get("out"))
            except (TypeError, ValueError) as e:
                raise JobError("in/out phải là số giây.") from e
            if not 0 <= a < b <= 60:
                raise JobError("Cần 0 ≤ in < out ≤ 60 giây.")
            argv = ["trim", target, sid, "--in", f"{a:.3f}", "--out", f"{b:.3f}"]
            return argv, f"Trim {sid} {a:.2f}–{b:.2f}s", target, None
        if kind in ("rerender_shot", "reorder", "redo_voice"):
            target = _check_target(str(p.get("target") or "").strip())
            if not os.path.isdir(os.path.join(PROJECTS, target)):
                raise JobError("Chỉ áp dụng cho dự án có sẵn.")
            dry = ["--dry-run"] if p.get("dry_run") else []
            if kind == "rerender_shot":
                sid = str(p.get("shot") or "")
                if not re.fullmatch(r"(C\d{2}|OUTRO)", sid):
                    raise JobError("Mã shot dạng C03.")
                return ["rerender", target, sid, *dry], f"Render lại {sid} · {target}", target, None
            if kind == "reorder":
                order = str(p.get("order") or "")
                if not re.fullmatch(r"C\d{2}(,C\d{2}){0,98}", order):
                    raise JobError("Thứ tự dạng C02,C01,C03.")
                return ["shots", target, "--order", order], f"Đổi thứ tự shot · {target}", target, None
            return (["video", target, "--from", "voice", "--tts-force", "--no-open", "--yes", *dry],
                    f"Tạo lại giọng đọc · {target}", target, None)
        if kind == "deliver":
            target = _check_target(str(p.get("target") or "").strip())
            if not os.path.isdir(os.path.join(PROJECTS, target)):
                raise JobError("Chỉ xuất gói cho dự án có sẵn.")
            from vidlib import deliver  # noqa: PLC0415
            try:
                names = deliver.preset_names(str(p.get("platforms") or "default"))
            except Exception as e:  # noqa: BLE001
                raise JobError(str(e)) from e
            return ["deliver", target, "--platforms", ",".join(names)], "Xuất gói nền tảng · " + target, target, None
        if kind in LIGHT:
            return self._build_light(kind, p)
        if kind == "tool":
            name = p.get("name")
            style = p.get("style")
            if style and style not in styles.available():
                raise JobError(f"Style '{style}' không có.")
            tools = {
                "style_cards": (["styles", "--cards"], None, "Sinh thẻ style (.md)"),
                "style_gallery": (["styles", "--gallery"], None, "Bảng xem mọi style"),
                "props3d_sheet": ([style] if style else [], "scripts/props3d_sheet.py", "Bảng đạo cụ 3D"),
                "html_sheet": ([style or "flat-vector-black"], "scripts/html_sheet.py", "Contact sheet engine html"),
                "smoke": ([], "scripts/smoke.py", "Smoke test mọi đường dựng"),
                "doctor": (["doctor"], None, "Kiểm môi trường (doctor)"),
                "atlas_frames": ([], "scripts/atlas_frames.py", "Style frame preset 3D Style Atlas"),
            }
            if name not in tools:
                raise JobError(f"Công cụ '{name}' không có.")
            argv, script, title = tools[name]
            return argv, title + (f" · {style}" if style else ""), None, script
        raise JobError(f"Loại job '{kind}' không có.")

    def _build_light(self, kind, p):
        """sb_* / ideas_import → `studio.py sb …` / `studio.py ideas import …`; nội dung đi qua stdin, không qua argv."""
        if kind == "ideas_import":
            batch = str(p.get("batch") or "")
            if not re.fullmatch(r"[A-Za-z0-9_][\w.-]{0,120}", batch) or ".." in batch:
                raise JobError("Tên lô ý tưởng không hợp lệ.")
            if not os.path.isdir(os.path.join(ROOT, "ideas", batch)):
                raise JobError(f"Không có lô ý tưởng '{batch}'.")
            return ["ideas", "import", batch, "-"], f"Dán ideas.json · {batch}", None, None
        target = _check_target(str(p.get("target") or "").strip())
        if not os.path.isdir(os.path.join(PROJECTS, target)):
            raise JobError("Chỉ áp dụng cho dự án có sẵn.")
        if kind == "sb_import":
            return ["sb", "import", target, "-", "--note", "dán từ UI"], f"Lưu storyboard · {target}", target, None
        if kind == "sb_restore":
            bid = str(p.get("id") or "")
            if not re.fullmatch(r"[\w-]{6,40}", bid):
                raise JobError("Id bản lưu không hợp lệ.")
            return ["sb", "restore", target, bid], f"Khôi phục storyboard {bid} · {target}", target, None
        sid = str(p.get("shot") or "").upper()
        if sid and not SID_RE.fullmatch(sid):
            raise JobError("Mã shot dạng C03.")
        if kind == "sb_preview":
            try:
                u = float(p.get("u", 0.5))
            except (TypeError, ValueError) as e:
                raise JobError("u là số 0..1.") from e
            if not sid or not 0 <= u <= 1:
                raise JobError("Xem trước cần shot (C03) và u trong 0..1.")
            return ["sb", "preview", target, sid, "--u", f"{u:.3f}"], f"Xem trước {sid} @ {u:.2f}", target, None
        sets, unsets = p.get("set") or {}, p.get("unset") or []
        if not isinstance(sets, dict) or not isinstance(unsets, list) or not (sets or unsets):
            raise JobError("sb_patch cần set {đường: giá trị} và/hoặc unset [đường].")
        for path in [*sets, *unsets]:
            if not isinstance(path, str) or len(path) > 200 or not PATH_RE.fullmatch(path):
                raise JobError(f"Đường dẫn trường không hợp lệ: {path!r}.")
        argv = ["sb", "patch", target, "--json", "-"] + (["--shot", sid] if sid else [])
        return argv, f"Sửa {sid or 'storyboard'} · {target}", target, None

    @staticmethod
    def _stdin(kind, p):
        if kind in ("sb_import", "ideas_import"):
            text = p.get("text")
            if not isinstance(text, str) or not text.strip():
                raise JobError("Chưa có nội dung JSON.")
            if len(text) > MAX_PAYLOAD:
                raise JobError("Nội dung quá lớn (> 4 MB).")
            return text
        if kind == "sb_patch":
            return json.dumps({"set": p.get("set") or {}, "unset": p.get("unset") or []}, ensure_ascii=False)
        return None

    def submit(self, kind, params):
        params = params or {}
        argv, title, slug, script = self.build(kind, params)
        stdin = self._stdin(kind, params)
        with self.lock:
            busy = [j for j in self.jobs.values() if slug and j.slug == slug and j.status in ("queued", "running")]
            if kind == "sb_preview":
                busy = [j for j in busy if j.kind == "sb_preview"]          # xem trước chỉ đọc → song song với job khác
            elif kind in LIGHT:
                busy = [j for j in busy if j.kind != "sb_preview"]
            if busy:
                raise JobError("Dự án này đang có job chạy/chờ — đợi xong hoặc huỷ trước."
                               + (" (Không ghi storyboard khi pipeline đang đọc nó.)" if kind in LIGHT else ""))
            # job nhẹ: không lưu nội dung dán vào lịch sử (lớn, có thể riêng tư) và không "Chạy lại"
            job = Job(kind, argv, title, slug, script, params={} if kind in LIGHT else dict(params))
            job.stdin = stdin
            self.jobs[job.id] = job
            if kind == "sb_preview":
                threading.Thread(target=self._run_one, args=(job,), daemon=True, name="studio-preview").start()
            elif kind in LIGHT:
                self.fast.append(job.id)
            else:
                self.queue.append(job.id)
            self._trim()
        self._save(job)
        (self.fast_wake if kind in LIGHT else self.wake).set()
        return job

    def run_sync(self, kind, params, timeout=180):
        """Chạy job nhẹ và CHỜ xong (API lưu storyboard / sửa shot trả kết quả ngay). → (job, kết quả ::sbedit)."""
        job = self.submit(kind, params)
        t0 = time.time()
        with job.cond:
            while job.status in ("queued", "running") and time.time() - t0 < timeout:
                job.cond.wait(timeout=1)
        return job, last_result(job)

    def cancel(self, jid):
        job = self.jobs.get(jid)
        if not job:
            return None
        with self.lock:
            if job.status == "queued":
                self.queue = collections.deque(x for x in self.queue if x != jid)
                job.status, job.ended = "cancelled", time.time()
                job.push("✖ Đã huỷ trước khi chạy.")
        if job.status == "running" and job.proc:
            job.push("✖ Đang huỷ (dừng cả tiến trình con)…")
            _kill_tree(job.proc)
            job.status = "cancelled"
        self._save(job)
        return job

    # ------------------------------------------------------------ chạy
    def _worker(self, fast=False):
        wake, q = (self.fast_wake, self.fast) if fast else (self.wake, self.queue)
        while True:
            wake.wait(2)
            wake.clear()
            while True:
                with self.lock:
                    jid = q.popleft() if q else None
                if not jid:
                    break
                job = self.jobs.get(jid)
                if job and job.status == "queued":
                    self._run_one(job)

    def _run_one(self, job):
        try:
            if job.kind == "sb_preview":
                with self.preview_slot:
                    self._run(job)
            else:
                self._run(job)
        except Exception as e:  # noqa: BLE001 — một job hỏng không được giết worker (AUD-701)
            job.push(f"✖ Lỗi nội bộ khi chạy job: {e!r}")
            job.status, job.exit_code, job.ended = "failed", -1, time.time()
            job.proc = None
            self._save(job)
        with job.cond:
            job.cond.notify_all()

    def _run(self, job):
        cmd = [sys.executable, "-u", job.script or "studio.py", *job.argv]
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
        from vidlib.common import env as env_file  # noqa: PLC0415
        for k in ENV_KEYS:                       # key trong .env → biến môi trường tiến trình con (--ai claude|gemini)
            if not env.get(k) and env_file(k):
                env[k] = env_file(k)
        kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        job.status, job.started = "running", time.time()
        job.push("$ python " + " ".join(_quote(a) for a in [job.script or "studio.py", *job.argv]))
        self._save(job)
        try:
            job.proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        stdin=subprocess.PIPE if job.stdin is not None else subprocess.DEVNULL,
                                        text=True, encoding="utf-8", errors="replace", **kw)
            if job.stdin is not None:
                threading.Thread(target=_feed, args=(job.proc, job.stdin), daemon=True).start()
                job.stdin = None
            for line in job.proc.stdout:
                job.push(line.rstrip("\r\n"))
            rc = job.proc.wait()
        except (OSError, ValueError) as e:
            job.push(f"✖ Không chạy được: {e}")
            rc = -1
        job.exit_code, job.ended = rc, time.time()
        if job.status != "cancelled":
            job.stage = job.stage or EXIT_STAGE.get(rc)
            job.status = "finished" if rc in EXIT_STAGE else "failed"
            if rc == 0:
                job.progress = 1.0
        if job.light and job.status != "cancelled":
            job.status = "finished" if rc in (0, 3) else "failed"     # 3 = dữ liệu sai (đã báo lỗi theo trường)
        job.push(f"— kết thúc · exit {rc} · {job.ended - job.started:.1f}s")
        job.proc = None
        self._save(job)

    # ------------------------------------------------------------ truy vấn
    def list(self, limit=60):
        return [j.meta() for j in reversed(self.jobs.values())][:limit]

    def last_by_slug(self):
        out = {}
        for j in self.jobs.values():
            if j.slug:
                out[j.slug] = j.meta()
        return out

    def get(self, jid):
        return self.jobs.get(jid)

    # ------------------------------------------------------------ lưu
    def _save(self, job):
        meta = job.meta()
        with open(os.path.join(RUNTIME, f"{job.id}.json"), "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False)
        if job.status not in ("queued", "running"):
            with open(os.path.join(RUNTIME, f"{job.id}.log"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(job.lines))

    def _load(self):
        metas = []
        for f in os.listdir(RUNTIME):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(RUNTIME, f), encoding="utf-8") as fh:
                        metas.append(json.load(fh))
                except (OSError, ValueError):
                    continue
        for m in sorted(metas, key=lambda x: x.get("created", 0))[-120:]:
            j = Job(m["kind"], m["argv"], m["title"], m.get("slug"), params=m.get("params"))
            j.id, j.stage, j.current, j.exit_code = m["id"], m.get("stage"), m.get("current"), m.get("exit_code")
            j.created, j.started, j.ended = m.get("created"), m.get("started"), m.get("ended")
            j.status = "interrupted" if m.get("status") in ("queued", "running") else m.get("status")
            lp = os.path.join(RUNTIME, f"{j.id}.log")
            if os.path.exists(lp):
                with open(lp, encoding="utf-8") as fh:
                    for ln in fh.read().splitlines()[-MAX_LINES:]:
                        j.lines.append(ln)
            self.jobs[j.id] = j

    def _trim(self, keep=120):
        while len(self.jobs) > keep:
            jid, j = next(iter(self.jobs.items()))
            if j.status in ("queued", "running"):
                break
            self.jobs.pop(jid)
            for ext in (".json", ".log"):
                try:
                    os.remove(os.path.join(RUNTIME, jid + ext))
                except OSError:
                    pass


def _feed(proc, text):
    try:
        proc.stdin.write(text)
        proc.stdin.close()
    except (OSError, ValueError):
        pass


def last_result(job):
    """Kết quả có cấu trúc của `studio.py sb …` (dòng cuối `::sbedit {json}`), hoặc None."""
    lines, _ = job.since(0)
    for ln in reversed(lines):
        if ln.startswith("::sbedit "):
            try:
                return json.loads(ln[len("::sbedit "):])
            except ValueError:
                return None
    return None


def _quote(a):
    return f'"{a}"' if (" " in a or not a) else a


def _kill_tree(proc):
    """Dừng pipeline + worker render (Edge headless, ffmpeg) của nó."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, check=False)
        else:
            import signal  # noqa: PLC0415
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except OSError:
        proc.kill()
