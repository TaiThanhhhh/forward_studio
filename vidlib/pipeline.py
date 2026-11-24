"""Pipeline một lệnh, có trạng thái, chạy lại được (idempotent).

idea → script → storyboard → prompts → page → [CHỜ CLIP TỪ FLOW] → ingest → trim → voice → assemble → text → outro
→ audio → look → code → render → thumbnails → publish → qa

- Tự nhận biết stage dựa vào file đang có + dấu vân tay đầu vào (work/state.json) → chạy tiếp từ đó.
- --from X : làm lại X và mọi bước sau.   --only X : chỉ làm X (bước trước chỉ chạy nếu thiếu dữ liệu).
- --dry-run: không cần Flow/ElevenLabs — sinh clip/lời đọc/nhạc GIẢ cho phần còn thiếu, không mở trình duyệt.
Điểm dừng chờ người: tạo clip trong Flow · xem contact sheet trước khi render đầy đủ (look_check, bỏ qua bằng --look-ok).
Shot `mode: code` (và outro) dựng bằng engine three.js (engines/three/) — không cần Flow.
Engine thứ hai của `mode: code` là engine board (engines/board/, Python/OpenCV): shot có `beat_recipe` thuần board
(DOC_FOCUS, NUMBER_CARD, THESIS…) và — với assembly `board_spine` — CẢ video là một camera chạy liên tục trên bảng,
clip Flow / cảnh three.js được ghim như thẻ (vidlib/boardplan.py → work/board/board.json).
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

from . import audio as audiolib
from . import (boardplan, boardqa, brief, codeshot, compiler, fakes, ingest, lang, linter, mix, motion, narratives, outro,
               page, qa, render, spine, styles, textfx, textstyle, thumbs, timeline, tts, vcam, vo, voices)
from . import storyboard as sbm
from .common import (BRAND_DIR, CONFIG_DIR, FPS, PROJECTS, PROMPTS_DIR, ROOT, StudioError, channel, env, flow_models,
                     load_json, save_json, save_text, slugify, valid_media)

STAGES = ["idea", "script", "storyboard", "prompts", "page", "clips", "ingest", "trim", "voice", "assemble", "text",
          "outro", "audio", "look", "code", "render", "thumbnails", "qa", "publish", "deliver"]
ALIASES = {"thumbnail": "thumbnails", "thumbs": "thumbnails", "cover": "thumbnails", "html": "page",
           "scripts": "page", "prompt": "prompts", "mix": "audio", "build": "render", "caption": "text",
           "captions": "text", "srt": "text", "vo": "voice", "tts": "voice", "stills": "look", "contact": "look",
           "preview": "look", "code3d": "code"}
EXIT = {"done": 0, "waiting_clips": 10, "need_storyboard": 2, "storyboard_invalid": 3, "lint_failed": 3,
        "confirm_map": 4, "look_check": 11, "preview": 0, "qa_failed": 12}


class Stop(Exception):
    def __init__(self, stage, msg=""):
        super().__init__(msg)
        self.stage = stage


def resolve_stage(name):
    if not name:
        return None
    n = ALIASES.get(name.lower(), name.lower())
    if n not in STAGES:
        raise StudioError(f"Stage '{name}' không có. Các stage: {', '.join(STAGES)}.")
    return n


def project_for(arg):
    """Ý tưởng hoặc slug/đường dẫn → (thư mục dự án, ý tưởng, mới tạo?)."""
    if os.path.isdir(arg) and os.path.exists(os.path.join(arg, "idea.txt")):
        p = os.path.abspath(arg)
        return p, open(os.path.join(p, "idea.txt"), encoding="utf-8").read().strip(), False
    for cand in (arg, slugify(arg)):
        p = os.path.join(PROJECTS, cand)
        if os.path.isdir(p):
            ip = os.path.join(p, "idea.txt")
            idea = open(ip, encoding="utf-8").read().strip() if os.path.exists(ip) else arg
            return p, idea, False
    return os.path.join(PROJECTS, slugify(arg)), arg, True


def _fp(*parts):
    h = hashlib.sha1()
    for p in parts:
        if isinstance(p, str) and os.path.exists(p):
            if os.path.isdir(p):
                for root, _, files in sorted(os.walk(p)):
                    for f in sorted(files):
                        fp = os.path.join(root, f)
                        st = os.stat(fp)
                        h.update(f"{fp}:{st.st_size}:{st.st_mtime_ns}".encode())
            else:
                st = os.stat(p)
                h.update(f"{p}:{st.st_size}:{st.st_mtime_ns}".encode())
        else:
            h.update(json.dumps(p, sort_keys=True, ensure_ascii=False, default=str).encode())
    return h.hexdigest()[:16]


def _parse_hud_clock(val):
    """Đọc mốc đồng hồ ('MM:SS', 'HH:MM:SS' hoặc số giây) → (seconds, show_hours, is_clock_str) hoặc None."""
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val), False, False
    if not isinstance(val, str):
        return None
    s = val.strip()
    if ":" in s:
        parts = s.split(":")
        try:
            nums = [float(p) for p in parts]
        except ValueError:
            return None
        if len(nums) == 2:
            return nums[0] * 60.0 + nums[1], False, True
        if len(nums) == 3:
            return nums[0] * 3600.0 + nums[1] * 60.0 + nums[2], True, True
        return None
    try:
        return float(s), False, False
    except ValueError:
        return None


def _fmt_hud_clock(sec, show_hours=False):
    tot = max(0, int(round(sec)))
    h = tot // 3600
    m = (tot % 3600) // 60
    s = tot % 60
    if show_hours or h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _hud_decimals(a, b, given=None):
    if given is not None and not isinstance(given, bool):
        try:
            return max(0, min(3, int(given)))
        except (TypeError, ValueError):
            pass

    def _d(v):
        s = str(v)
        return min(2, len(s.split(".")[1])) if "." in s else 0

    return max(_d(a), _d(b))


def interpolate_story_hud(sb, tl, shot, seg):
    """Tính `story_hud` nội suy tuyến tính trên trục nội dung [0..content_end] cho một shot code.
    Trả về None nếu là outro, shot tắt `"story_hud": false`, hoặc cả storyboard lẫn shot đều không khai story_hud."""
    if seg is None or seg.get("sid") == "OUTRO" or not shot or shot.get("beat") == "outro":
        return None
    if shot.get("story_hud") is False:
        return None
    top_hud = sb.get("story_hud") if isinstance((sb or {}).get("story_hud"), dict) else None
    shot_hud = shot.get("story_hud") if isinstance(shot.get("story_hud"), dict) else None
    if not top_hud and not shot_hud:
        return None
    content_segs = [s for s in (tl or {}).get("segments", []) if s.get("sid") != "OUTRO"]
    content_end = max((int(s.get("start_f", 0)) + int(s.get("n", 0)) for s in content_segs), default=1)
    content_end = max(1, content_end)
    p0 = max(0.0, min(1.0, int(seg.get("start_f", 0)) / content_end))
    p1 = max(p0, min(1.0, (int(seg.get("start_f", 0)) + int(seg.get("n", 0))) / content_end))

    out = dict(top_hud or {})
    if shot_hud:
        out.update(shot_hud)
    has_shot_range = bool(shot_hud and ("from" in shot_hud or "to" in shot_hud))
    has_shot_prog = bool(shot_hud and ("progress_from" in shot_hud or "progress_to" in shot_hud))

    base_p0 = float((top_hud or {}).get("progress_from", 0.0))
    base_p1 = float((top_hud or {}).get("progress_to", 1.0))
    if not has_shot_prog:
        out["progress_from"] = round(base_p0 + (base_p1 - base_p0) * p0, 4)
        out["progress_to"] = round(base_p0 + (base_p1 - base_p0) * p1, 4)

    if not has_shot_range and top_hud and ("from" in top_hud or "to" in top_hud):
        kind = str(out.get("kind") or "meter").lower()
        raw_a = top_hud.get("from", top_hud.get("to"))
        raw_b = top_hud.get("to", top_hud.get("from"))
        if kind == "clock":
            pa, pb = _parse_hud_clock(raw_a), _parse_hud_clock(raw_b)
            if pa and pb:
                va, hrs_a, str_a = pa
                vb, hrs_b, str_b = pb
                v0 = va + (vb - va) * p0
                v1 = va + (vb - va) * p1
                if str_a or str_b:
                    out["from"] = _fmt_hud_clock(v0, hrs_a or hrs_b)
                    out["to"] = _fmt_hud_clock(v1, hrs_a or hrs_b)
                else:
                    out["from"] = round(v0, 2)
                    out["to"] = round(v1, 2)
        else:
            try:
                va, vb = float(raw_a), float(raw_b)
            except (TypeError, ValueError):
                pass
            else:
                dec = _hud_decimals(raw_a, raw_b, out.get("decimals"))
                if "decimals" not in out:
                    out["decimals"] = dec
                out["from"] = round(va + (vb - va) * p0, max(dec, 2))
                out["to"] = round(va + (vb - va) * p1, max(dec, 2))
    return out


class Run:
    def __init__(self, arg, frm=None, only=None, dry=False, model=None, ai=None, yes=False, no_open=False, log=print,
                 look_ok=False, tts_force=False, style=None, voice=None, flow=None, narrative=None, accept_qa=False,
                 platforms=None, captions=None, archetype=None):
        self.proj, self.idea, self.new = project_for(arg)
        self.slug = os.path.basename(self.proj)
        self.frm, self.only = resolve_stage(frm), resolve_stage(only)
        self.dry, self.model, self.ai, self.yes, self.no_open = dry, model, ai, yes, no_open
        self.look_ok, self.tts_force = look_ok, tts_force
        self.want_style, self.want_voice, self.want_flow = style, voice, flow   # cờ --style / --voice / --flow|--no-flow
        self.want_narrative = narrative                                       # cờ --narrative
        self.want_archetype = archetype                                       # cờ --archetype (Vòng 13)
        self.want_captions = captions                  # cờ --captions (capcut_pop/pill/box, vox_highlight, off)
        self.accept_qa = accept_qa                     # --accept-qa: người làm duyệt tay video bị cổng QA chặn
        self.platforms = platforms                     # --platforms youtube_shorts,tiktok… (mặc định delivery.default)
        self.log = log
        self.work = os.path.join(self.proj, "work")
        self.state_path = os.path.join(self.work, "state.json")
        self.state = load_json(self.state_path, {})
        self.notes = []
        self.code_stats = {}
        self.code_cues = []

    # ---------------------------------------------------------------- helpers
    def p(self, *a):
        return os.path.join(self.proj, *a)

    def forced(self, stage):
        if self.only:
            return stage == self.only
        return bool(self.frm) and STAGES.index(stage) >= STAGES.index(self.frm)

    def after_only(self, stage):
        """True nếu --only đã xong và stage này nằm SAU nó → dừng."""
        if not self.only:
            return False
        return STAGES.index(stage) >= STAGES.index(self.only)

    def fresh(self, stage, fp, outputs):
        """Đã làm với đúng đầu vào này VÀ đầu ra còn dùng được (không chỉ "tồn tại": file 48 byte sau khi bị ngắt
        không còn được coi là mới — AUD-203/805)."""
        return (not self.forced(stage) and self.state.get(stage) == fp
                and all(valid_media(o) for o in outputs))

    def mark(self, stage, fp):
        self.state[stage] = fp
        save_json(self.state_path, self.state)

    def head(self, stage, msg=""):
        self.log(f"▶ {stage}{(' · ' + msg) if msg else ''}")

    def ingested(self, sid):
        p = ingest.ingested(self.proj, sid)
        return p if os.path.exists(p) else None

    def code_shots(self):
        return [s for s in self.csb["shots"] if s.get("mode_resolved") == "code" and codeshot.is_3d(s)]

    def is_loop_outro(self):
        return timeline.is_seamless_loop(getattr(self, "csb", None) or getattr(self, "sb", None))

    def outro_code(self):
        o = self.csb.get("outro", {})
        return (o.get("enabled", True) and o.get("mode", "code") == "code"
                and not self.is_loop_outro() and not self.spine())

    def spine(self):
        return self.sb.get("assembly_resolved") == "board_spine"

    def board_ids(self):
        return [s["id"] for s in self.csb["shots"] if codeshot.is_board(s)]

    # ---------------------------------------------------------------- stages
    def s_idea(self):
        os.makedirs(self.proj, exist_ok=True)
        for d in ("clips", "frames", "refs", "audio", "thumbnails", "out", "qa", "work"):
            os.makedirs(self.p(d), exist_ok=True)
        ip = self.p("idea.txt")
        if not os.path.exists(ip):
            with open(ip, "w", encoding="utf-8", newline="\n") as f:
                f.write(self.idea + "\n")
            self.head("idea", f"tạo dự án {os.path.relpath(self.proj, ROOT)}")

    def make_plan(self):
        """plan.json: style + giọng + dạng kịch bản + archetype đạo diễn chọn TRƯỚC khi viết kịch bản."""
        pp = self.p("plan.json")
        plan = load_json(pp, {}) if os.path.exists(pp) else {}
        idea = load_json(self.p("idea.json"), {}) if os.path.exists(self.p("idea.json")) else {}
        if plan and self.want_style is None and self.want_flow is None and self.want_voice is None:
            dirty = False
            if self.want_narrative is not None or "narrative" not in plan:     # plan.json cũ (trước khi có dạng kịch bản)
                plan.update(narratives.plan(self.idea, self.slug, want=self.want_narrative, idea=idea))
                dirty = True
            if self.want_archetype is not None or "archetype" not in plan:     # plan.json cũ (trước Vòng 13)
                plan.update(narratives.plan_archetype(self.idea, self.slug, want=self.want_archetype, idea=idea))
                dirty = True
            if "format_family" not in plan:                                   # plan.json cũ (trước Vòng 14)
                plan.update(narratives.plan_format(self.idea, self.slug, idea=idea))
                dirty = True
            if dirty:
                save_json(pp, plan)
            return plan
        plan = styles.plan(self.idea, self.slug, flow=self.want_flow, style=self.want_style)
        v, why = voices.resolve({"voice": self.want_voice or "auto", "style_resolved": plan["style"],
                                 "language": lang.language()}, self.slug)
        if v:
            plan["voice"], plan["voice_reason"] = v, why or "chỉ định tay (--voice)"
        plan.update(narratives.plan(self.idea, self.slug, want=self.want_narrative, idea=idea))
        plan.update(narratives.plan_archetype(self.idea, self.slug, want=self.want_archetype, idea=idea))
        plan.update(narratives.plan_format(self.idea, self.slug, idea=idea))
        save_json(pp, plan)
        return plan

    def apply_cli_overrides(self):
        """--style / --voice khi đã có storyboard: ghi vào storyboard.json (nguồn sự thật) để lần sau vẫn giữ."""
        if self.want_narrative is not None:
            self.log("  ⚠ --narrative chỉ có tác dụng khi CHƯA có storyboard (lời đọc đã viết theo dạng cũ). "
                     "Muốn đổi: xoá storyboard.json để viết lại.")
        if self.want_style is None and self.want_voice is None:
            if self.want_flow is not None:
                self.log("  ⚠ --flow/--no-flow chỉ có tác dụng khi CHƯA có storyboard (kịch bản đã viết theo style cũ). "
                         "Muốn đổi: --style <id> hoặc xoá storyboard.json để viết lại.")
            return
        raw = sbm.load(self.proj)
        if self.want_style is not None and raw.get("style") != self.want_style:
            raw["style"] = self.want_style
            raw.pop("style_resolved", None)
            self.log(f"  · --style → storyboard.style = {self.want_style}")
        if self.want_voice is not None and raw.get("voice") != self.want_voice:
            raw["voice"] = self.want_voice
            raw.pop("voice_resolved", None)
            self.log(f"  · --voice → storyboard.voice = {self.want_voice}")
        sbm.save(self.proj, raw)

    def s_storyboard(self):
        sp = sbm.path_of(self.proj)
        if os.path.exists(sp):
            self.apply_cli_overrides()
        if not os.path.exists(sp):
            plan = self.make_plan()
            kind = "có Flow" if plan["uses_flow"] else "toàn code, không Flow"
            self.log(f"  · kế hoạch: style {plan['style']} ({kind}) — "
                     f"{plan['reason']}" + (f" · giọng {voices.short(plan['voice'])}" if plan.get("voice") else ""))
            if plan.get("narrative"):
                self.log(f"  · dạng kịch bản: {plan['narrative']} ({narratives.get(plan['narrative'])['name']}) — "
                         f"{plan.get('narrative_reason', '')}")
            if plan.get("archetype") and narratives.get_archetype(plan["archetype"]):
                self.log(f"  · archetype đạo diễn: {plan['archetype']} "
                         f"({narratives.get_archetype(plan['archetype'])['name']}) — "
                         f"{plan.get('archetype_reason', '')}")
            if plan.get("format_family") and narratives.get_format(plan["format_family"]):
                self.log(f"  · format family: {plan['format_family']} "
                         f"({narratives.get_format(plan['format_family'])['name']}) — "
                         f"{plan.get('format_reason', '')}")
            text = brief.build(self.idea, self.slug, self.model, self.proj, plan=plan)
            bp = self.p("brief.md")
            with open(bp, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            if not self.ai:
                raise Stop("need_storyboard",
                           f"Chưa có storyboard.json. Brief cho LLM: {os.path.relpath(bp, ROOT)}\n"
                           f"  • Trong Claude Code: /video tự viết storyboard từ brief rồi chạy tiếp.\n"
                           f"  • Ngoài Claude Code: thêm --ai claude (cần ANTHROPIC_API_KEY) hoặc dán brief.md vào app "
                           f"Claude/Gemini, lưu JSON trả về thành {os.path.relpath(sp, ROOT)} rồi chạy lại.")
            self.head("storyboard", f"nhờ {self.ai} viết storyboard")
            raw = brief.ask(self.ai, text)
            from . import cost  # noqa: PLC0415
            cost.record(self.proj, "llm", **brief.LAST_USAGE)
            save_text(self.p("brief_response.txt"), raw)      # AUD-206: lưu phản hồi LLM trước khi parse
            data = brief.strip_json(raw)
            data["slug"] = self.slug
            sbm.save(self.proj, data)
        raw = sbm.load(self.proj)
        sb = sbm.normalize(raw, self.model)
        sb["slug"] = self.slug
        lang.set_project_language(sb.get("language"))
        textstyle_cache_clear()
        plan = load_json(self.p("plan.json"), {}) if os.path.exists(self.p("plan.json")) else {}
        if sb.get("style") == "auto" and not sb.get("style_resolved") and plan.get("style") in styles.available():
            sb["style_resolved"] = plan["style"]          # style đã chọn lúc viết brief → kịch bản và hình khớp nhau
        errs, warns = sbm.validate(sb)
        style, note = styles.resolve(sb, self.slug)
        if style not in styles.available():
            errs.append(f"style '{style}' không có trong styles/ (có: {', '.join(styles.available())}).")
        elif styles.info(style)["code_only"]:
            non = [s["id"] for s in sb["shots"] if not s.get("code")]
            if non:
                errs.append(f"style '{style}' dựng TOÀN BỘ bằng code — các shot sau chưa có 'code': {', '.join(non)}.")
        sb["style_resolved"] = style
        if style in styles.available():
            sb["assembly_resolved"] = boardplan.assembly(sb, style)
            if sb["assembly_resolved"] == "board_spine":
                fx = [s["id"] for s in sb["shots"] if s.get("text_fx") and not s["board"].get("marks")]
                if fx:
                    warns.append("board_spine: text_fx của " + ", ".join(fx) + " được đổi thành nhãn băng dính trên "
                                 "bảng (muốn chủ động hơn: dùng beat_recipe NAME_TAG / board.marks).")
        if note:
            warns.append(note)
        if sb.get("voice", "auto") == "auto" and not sb.get("voice_resolved"):
            old = (load_json(self.p("audio", "vo_alignment.json"), {}) or {}).get("voice") \
                if os.path.exists(self.p("audio", "vo_alignment.json")) else None
            if old and old.get("id"):        # video làm trước vòng 7b: giữ đúng giọng + tốc độ cũ (không gọi TTS lại)
                sb["voice_resolved"] = {**old, "auto_pick": True, "legacy": True}
            elif (plan.get("voice") or {}).get("id"):
                sb["voice_resolved"] = {**plan["voice"], "auto_pick": True}
        voice, vnote = voices.resolve(sb, self.slug)
        if voice:
            sb["voice_resolved"] = voice
        if vnote:
            (errs if voice is None else warns).append(vnote)
        nid, nnote = narratives.resolve(sb, plan)
        if nid:
            sb["narrative_resolved"] = nid
        if nnote:
            warns.append(nnote)
        aid, anote = narratives.resolve_archetype(sb, plan)
        if aid:
            sb["archetype_resolved"] = aid
        if anote:
            warns.append(anote)
        fid, fnote = narratives.resolve_format(sb, plan)
        if fid:
            sb["format_family_resolved"] = fid
        if fnote:
            warns.append(fnote)
        if errs:
            raise Stop("storyboard_invalid", "storyboard.json còn lỗi:\n  ✖ " + "\n  ✖ ".join(errs))
        self.sb = sb
        for w in warns:
            self.log("  ⚠ " + w)
        self.write_script()

    def write_script(self):
        """Stage `script`: bản đọc dễ của kịch bản (sinh từ storyboard — không phải nguồn)."""
        words = sum(lang.word_count(tts.strip_tags(s.get("vo", ""))) for s in self.sb["shots"])
        L = [f"# {self.sb.get('title') or self.sb['topic']}", "",
             f"_Hook:_ {self.sb.get('hook', '')}  ·  style `{self.sb['style_resolved']}`  ·  {words} từ ≈ "
             f"{words / lang.pace():.1f}s đọc ({lang.pace()} từ/giây)", ""]
        for s in self.sb["shots"]:
            fxs = " · ".join(f.get("text", "") for f in (s.get("text_fx") or []))
            mode = " `code`" if s.get("code") else ""
            L.append(f"- **{s['id']}** `{s['beat']}`{mode} {s['target_sec']:g}s — {s.get('vo') or '·'}"
                     + (f"  \n  _chữ:_ {fxs}" if fxs else ""))
        L += ["", f"**Outro:** {lang.copy('next_prefix')} {self.sb.get('outro', {}).get('teaser', '')}", "", "Nguồn:"]
        L += [f"- {x}" for x in self.sb.get("sources", [])]
        with open(self.p("script.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(L) + "\n")

    def s_prompts(self):
        no_clip = [s["id"] for s in self.sb["shots"]
                   if not os.path.exists(self.p(s.get("clip_file") or f"clips/{s['id']}.mp4"))
                   and not self.ingested(s["id"])]
        self.csb = compiler.compile_all(self.sb, auto_code_ids=no_clip)
        for s in self.csb["shots"]:
            if s.get("code", {}) and s["code"].get("auto_reason") and s["id"] in no_clip:
                self.log(f"  · {s['id']}: {s['code']['auto_reason']}")
        self.issues = linter.lint(self.csb)
        fp = _fp(self.csb, os.path.join(PROMPTS_DIR, "blocks"), os.path.join(CONFIG_DIR, "flow-models.json"))
        raw = sbm.load(self.proj)
        merged = dict(self.csb)
        merged["shots"] = [dict(s) for s in self.csb["shots"]]
        if raw != merged:
            sbm.save(self.proj, merged)
        page.export_text(self.csb, self.p("prompts.txt"))
        page.write_json_prompts(self.csb, os.path.join(self.work, "prompts.json"))
        n_err = len(linter.errors(self.issues))
        if self.state.get("prompts") != fp or n_err:
            n_code = sum(s.get("mode_resolved") == "code" for s in self.csb["shots"])
            self.head("prompts", f"{len(self.csb['shots'])} cảnh ({n_code} code) · "
                                 f"model {self.csb['flow']['video_model']} · "
                                 f"{n_err} lỗi, {len(self.issues) - n_err} cảnh báo")
            if self.issues:
                self.log(linter.format_issues(self.issues))
        self.mark("prompts", fp)

    def scan(self):
        extra = [self.p("clips", "_dryrun")] if self.dry else []
        self.rows = ingest.scan(self.proj, self.csb, extra)
        self.clip_map = ingest.as_dict(self.rows)

    def s_page(self, quiet=False):
        self.scan()
        self.seed_from_code()
        real = {k: v for k, v in self.clip_map.items() if "_dryrun" not in v}  # clip giả không tính là "đã xong"
        out = page.build(self.csb, self.proj, self.issues, real)
        if not quiet:
            self.head("page", os.path.relpath(out, ROOT))
        if linter.errors(self.issues):
            raise Stop("lint_failed", "Linter còn lỗi — sửa storyboard.json (trường do người viết) rồi chạy lại.")

    def seed_from_code(self):
        """Shot Flow nối liền với shot code: ảnh Start = frame CUỐI của shot code trước, ảnh End = frame ĐẦU của shot
        code sau (end_frame.seed_from). Hai đường dựng tham chiếu lẫn nhau, không chạy song song mỗi bên một kiểu."""
        shots = {s["id"]: s for s in self.csb["shots"]}
        for s in self.csb["shots"]:
            if s.get("mode_resolved") == "code":
                continue
            for which, pos in (("start_frame", "last"), ("end_frame", "first")):
                src = (s.get(which) or {}).get("seed_from")
                if not src or src not in shots or not codeshot.is_3d(shots[src]):
                    continue
                n = int(round(shots[src]["target_sec"] * FPS))
                dst = self.p(s[which]["file"])
                job = codeshot.job_for(self.proj, self.csb, shots[src], n, self.sb["style_resolved"])
                key = f"{codeshot.coderender.job_hash(load_json(job))}:{pos}"
                seeds = load_json(os.path.join(self.work, "seeds.json"), {})
                if os.path.exists(dst) and seeds.get(f"{s['id']}:{which}") == key:
                    continue
                codeshot.export_frame(self.proj, src, n - 1 if pos == "last" else 0, dst)
                seeds[f"{s['id']}:{which}"] = key
                save_json(os.path.join(self.work, "seeds.json"), seeds)
                self.log(f"  ✔ {which.replace('_frame', '')} {s['id']} = frame {pos} của shot code {src} → "
                         f"{s[which]['file']}")

    def make_dry_data(self):
        d = self.p("clips", "_dryrun")
        missing = [s for s in self.csb["shots"] if s.get("mode_resolved") != "code" and s["id"] not in self.clip_map]
        for k, s in enumerate(missing):
            path = os.path.join(d, f"{s['id']}.mp4")
            if os.path.exists(path):
                continue
            g = float(s["gen_sec"])
            kw = dict(duration=g, head_sec=0.3 + 0.1 * (k % 4), decel_sec=0.6 + 0.1 * (k % 3),
                      hold_sec=0.15 + 0.05 * (k % 3),
                      label=f"{s['id']} · CLIP GIẢ", seed=k)
            if s["id"] == "C04" or (k == 3 and g >= 5):
                kw["cut_at"] = g * 0.82  # một scene cut giữa clip để kiểm tra
            fakes.make_clip(path, **kw)
        if missing:
            self.log(f"  · dry-run: sinh {len(missing)} clip giả (có đầu tĩnh, đuôi giảm tốc, audio rác) → clips/_dryrun/")
        if not audiolib.music_file(self.proj) and not mix.cfg()["music"].get("synth_if_missing"):
            fakes.make_music(self.p("audio", "music.wav"), seconds=70, bpm=120)
            self.log("  · dry-run: sinh nhạc giả 120 BPM → audio/music.wav")
        with open(self.p("work", "DRYRUN"), "w", encoding="utf-8") as f:
            f.write("Dữ liệu trong clips/_dryrun (và audio/vo.wav nếu có) là GIẢ.\n")
        self.scan()

    def s_clips(self):
        if self.dry:
            self.make_dry_data()
        flow = [s["id"] for s in self.csb["shots"] if s.get("mode_resolved") != "code"]
        have = [sid for sid in flow if sid in self.clip_map]
        if ingest.needs_confirm(self.rows):
            self.log("  Map clip theo thời gian tải về:\n" + ingest.table(self.rows))
            ok = self.yes or self.dry
            if not ok and sys.stdin and sys.stdin.isatty():
                try:
                    ok = input("  Đúng chưa? (Y/n): ").strip().lower() in ("", "y", "yes", "c", "co", "có")
                except (EOFError, OSError):
                    ok = False
            if not ok:
                raise Stop("confirm_map", "Xác nhận bảng map ở trên: chạy lại với --yes nếu đúng, hoặc đổi tên file thành "
                                          "C01.mp4… / sửa clips/_map.json.")
            ingest.save_map(self.proj, self.rows)
        missing = [sid for sid in flow if sid not in self.clip_map]
        if missing:
            self.s_ingest()
            self.s_trim()
            self.s_page(quiet=True)
            ing = [i for i in self.csb.get("ingredients", []) if not os.path.exists(self.p(i["file"]))]
            msg = [f"⏸ CHỜ CLIP TỪ FLOW — đã có {len(have)}/{len(flow)} clip (shot code không cần Flow)",
                   f"  1. Mở scripts.html: {self.p('scripts.html')}",
                   "     Làm từng cảnh theo thứ tự ① ảnh Start → ② ảnh End → ③ video → ④ lưu clip (phím J/K, C)."]
            if ing:
                msg.append("  2. Tạo trước ảnh ref (Ingredients): " + ", ".join(i["file"] for i in ing))
            msg += [f"  3. Thả clip vào {self.p('clips')} (tên C01.mp4… hoặc để nguyên tên Flow).",
                    f"  4. Chạy lại: /video {self.slug}   (hoặc: python studio.py video {self.slug})",
                    f"  Còn thiếu: {', '.join(missing)}"]
            if not self.no_open:
                open_file(self.p("scripts.html"))
            raise Stop("waiting_clips", "\n".join(msg))
        self.head("clips", f"đủ {len(flow)}/{len(flow)} clip Flow" + (f" · {len(self.csb['shots']) - len(flow)} shot code"
                                                                      if len(flow) < len(self.csb["shots"]) else ""))

    def s_ingest(self):
        rep = ingest.ingest(self.proj, self.rows, lambda m: self.log(m))
        self.ingest_report = {sid: rep[sid] for sid in rep if sid in self.clip_map}

    def s_trim(self):
        cache_dir = os.path.join(self.work, "analysis")
        analyses = {}
        for sid in self.clip_map:
            vid = self.ingested(sid)
            if not vid:
                continue
            cp = os.path.join(cache_dir, f"{sid}.json")
            key = f"{os.path.getmtime(vid):.0f}:{_fp(channel()['trim'])}"
            cached = load_json(cp, {})
            if cached.get("_key") == key and not self.forced("trim"):
                analyses[sid] = cached
                continue
            a = motion.analyze(vid)
            a["_key"] = key
            save_json(cp, a)
            analyses[sid] = a
        self.analyses = analyses
        self.trims = motion.plan_trims(self.proj, self.csb, analyses, os.path.join(self.work, "trim.json"))
        os.makedirs(self.p("qa", "trim"), exist_ok=True)
        for sid, tr in self.trims.items():
            qa.trim_plot(sid, analyses[sid], tr, self.p("qa", "trim", f"{sid}.png"))
            if tr["short"]:
                self.notes.append(f"{sid}: vùng chuyển động sạch ngắn hơn cần ({tr['out'] - tr['in']:.2f}s nguồn cho "
                                  f"{sbm.shot(self.csb, sid)['target_sec']}s) → sẽ hơi chậm lại.")
        made = motion.seed_frames(self.proj, self.csb, self.trims, lambda sid: ingest.ingested(self.proj, sid))
        for sid, src, t in made:
            self.log(f"  ✔ ảnh Start {sid} = frame {t:.2f}s của {src} (trước vùng giảm tốc)")
        if self.trims:
            self.head("trim", f"{len(self.trims)} clip · đồ thị qa/trim/")

    def s_voice(self):
        """Lời đọc: VO người dùng (audio/vo.*) được giữ nguyên; không có thì tạo bằng ElevenLabs (có cache)."""
        lines = vo.vo_lines(self.csb)
        if not lines:
            return
        kind, src = vo.find_vo(self.proj, len(lines))
        made_by_tts = bool(src and kind == "single" and tts.load_alignment(self.proj, src))
        if kind and not made_by_tts:
            self.head("voice", f"dùng lời đọc có sẵn: {os.path.relpath(src if isinstance(src, str) else src[0], self.proj)}")
            return
        if self.dry and not made_by_tts:
            fakes.make_vo(self.p("audio", "vo.wav"), [ln["text"] for ln in lines])
            self.log("  · dry-run: sinh lời đọc giả → audio/vo.wav (không gọi ElevenLabs)")
            return
        if not env(tts.voice_cfg().get("api_key_env", "ELEVENLABS_API_KEY")):
            if made_by_tts:
                self.log("  ⚠ không có ELEVENLABS_API_KEY — giữ audio/vo.mp3 cũ (có thể lệch lời mới)")
                return
            self.notes.append("Không có lời đọc: thiếu ELEVENLABS_API_KEY và chưa có audio/vo.*.")
            self.log("  ⚠ không có ELEVENLABS_API_KEY và chưa có audio/vo.* → dựng không có lời đọc")
            return
        ap = tts.synthesize(self.proj, [{"text": ln["raw"], "beat": ln["beat"]} for ln in lines], log=self.log,
                            force=self.tts_force, voice=self.csb.get("voice_resolved"))
        a = load_json(ap, {})
        self.head("voice", f"ElevenLabs {a.get('model_id')} · giọng {voices.short(a.get('voice') or {})} · "
                           f"{a.get('duration', 0):.1f}s · {a.get('words_per_sec')} từ/giây")

    def render_inputs_fp(self):
        # Lời đọc sinh ra (vo.*) không nằm trong dấu vân tay: nó được quyết định bởi csb + config/voice.json (đã có ở
        # đây) → lần chạy sau TTS không render lại vô cớ (AUD-202). Chỉ âm thanh người dùng đưa vào (nhạc…) được tính.
        user_audio = sorted(f for f in glob.glob(self.p("audio", "*")) if not os.path.basename(f).startswith("vo"))
        return _fp(self.csb, load_json(os.path.join(self.work, "trim.json"), {}), *user_audio, _board_src_fp(),
                   code_rev(), os.path.join(CONFIG_DIR, "voice.json"),
                   os.path.join(CONFIG_DIR, "channel.json"), os.path.join(CONFIG_DIR, "mix.json"), BRAND_DIR,
                   os.path.join(ROOT, "styles"), os.path.join(ROOT, "assets", "brand"), os.path.join(ROOT, "assets", "sfx"),
                   codeshot.engine_rev(), sorted(os.listdir(ingest.ingest_dir(self.proj)))
                   if os.path.isdir(ingest.ingest_dir(self.proj)) else [])

    def s_assemble(self):
        self.vo = vo.process(self.proj, self.csb, log=self.log)
        beats = None
        self.music = audiolib.music_file(self.proj)
        self.bpm = None
        if self.music:
            m = audiolib.sfxlib.decode(self.music, mono=True)
            self.bpm, beats = audiolib.detect_beats(m, channel()["audio"]["sample_rate"])
        o = self.csb.get("outro", {})
        outro_sec = 0.0 if self.is_loop_outro() else (channel()["outro"]["duration_sec"] if o.get("enabled", True) else 0.0)
        if self.spine() and outro_sec:
            outro_sec = boardplan.cfg().get("outro_sec", outro_sec)
        self.tl = timeline.build(self.csb, self.vo, beats, outro_sec)
        if self.spine():  # một camera liên tục: không còn điểm cắt — chuyển cảnh là camera/flash/glitch của board
            for seg in self.tl["segments"]:
                seg["transition"] = "glitch" if seg["sid"] == "OUTRO" else (
                    "flash" if seg["transition"] == "flash" else "cut")
        self.notes += self.tl["notes"]
        save_json(os.path.join(self.work, "timeline.json"), self.tl)
        self.head("assemble", f"{self.tl['duration']:.1f}s · {len(self.tl['segments'])} đoạn · "
                              f"{self.tl['auto_punches']} punch-in tự chèn"
                  + (f" · nhạc {self.bpm} BPM" if self.bpm else "")
                  + (f" · VO ({self.vo['timing']})" if self.vo else " · không VO"))

    def s_text(self):
        """Chữ trong thế giới phim (text_fx, Tầng 1) + .srt + job/metadata của shot code."""
        from . import autocaptions  # noqa: PLC0415

        style = self.sb["style_resolved"]
        cap_preset = autocaptions.resolve_preset(self.csb, self.want_captions, style)
        self.cap_preset = cap_preset
        self.csb["_captions_on"] = cap_preset != "off"
        layout_grid = channel().get("layout_grid") or {
            "header": [250, 370],
            "stage": [390, 1240],
            "captions": [1340, 1460],
        }
        self.csb["_layout_grid"] = layout_grid
        self.events = [] if self.spine() else textfx.build_events(self.csb, self.tl, self.vo,
                                                                   getattr(self, "analyses", {}), self.trims, style)
        self.text_report = textfx.timing_report(self.events)
        self.text_sfx = textfx.sfx_events(self.events)
        save_json(os.path.join(self.work, "captions.json"), self.text_report)
        if self.vo:
            qa.write_srt(self.vo, self.p("out", "captions.srt"))
        segs = {s["sid"]: s for s in self.tl["segments"]}
        self.code_jobs, self.code_cues = {}, []
        oshot = None
        if self.outro_code() and "OUTRO" in segs:
            o = self.csb.get("outro", {})
            params = {"teaser": o.get("teaser") or lang.copy("endscreen_title"), "next_prefix": lang.copy("next_prefix"),
                      "follow": o.get("follow_text") or lang.copy("follow"), **(o.get("params") or {})}
            oshot = {"id": "OUTRO", "beat": "outro", "code": {"scene": o.get("scene", "outro"), "params": params}}
        # engine html: các shot motion liền nhau = một cú máy liền (vidlib/spine.py); render.py bỏ transition giữa chúng
        codeshot.assign_layouts(self.csb, style, [oshot])   # biến thể bố cục xoay vòng (engine html)
        arch_id = self.csb.get("archetype_resolved") or (
            self.csb.get("archetype") if self.csb.get("archetype") not in (None, "", "auto") else None
        )
        if arch_id:
            extra_map = {"OUTRO": oshot} if oshot else {}
            all_shots = {s["id"]: s for s in self.csb.get("shots", [])}
            all_shots.update(extra_map)
            shot_ids = [s["id"] for s in self.csb.get("shots", [])]

            def _in_run(sh):
                return codeshot.is_3d(sh) and codeshot.engine_of(sh, style) in codeshot.SPINE_ENGINES

            def _entry(sh):
                if codeshot.engine_of(sh, style) != "html":
                    return {"scene": sh["code"]["scene"], "params": {}, "ghost": True}
                p = dict((sh.get("code") or {}).get("params") or {})
                if sh["id"] in shot_ids and "index" not in p:
                    p["index"] = [shot_ids.index(sh["id"]) + 1, len(shot_ids)]
                return {"scene": sh["code"]["scene"], "params": p}

            self.html_spine = spine.context(
                self.tl["segments"], all_shots, style,
                self.csb.get("slug") or self.csb.get("topic", ""), _in_run, _entry,
                prefer=narratives.moves(self.csb.get("narrative_resolved")),
                archetype=arch_id,
            )
        else:
            self.html_spine = codeshot.spine_context(self.csb, self.tl, style, {"OUTRO": oshot} if oshot else None)
        for s in self.csb["shots"]:
            s["spine_html"] = s["id"] in self.html_spine
        shots_by_id = {s["id"]: s for s in self.csb["shots"]}
        for s in self.code_shots():
            seg = segs.get(s["id"])
            if seg:
                self.code_jobs[s["id"]] = codeshot.job_for(self.proj, self.csb, s, seg["n"], style,
                                                           self.html_spine.get(s["id"]))
        if oshot:
            self.code_jobs["OUTRO"] = codeshot.job_for(self.proj, self.csb, oshot, segs["OUTRO"]["n"], style,
                                                       self.html_spine.get("OUTRO"))
        for sid, job in self.code_jobs.items():
            jdata = load_json(job, {})
            want_cap = bool(self.csb["_captions_on"]) and sid != "OUTRO"
            hud_val = interpolate_story_hud(self.csb, self.tl, shots_by_id.get(sid), segs.get(sid))
            if isinstance(jdata, dict) and jdata:
                changed = False
                if jdata.get("captions_on") != want_cap or jdata.get("layout_grid") != layout_grid:
                    jdata["captions_on"] = want_cap
                    jdata["layout_grid"] = layout_grid
                    changed = True
                if hud_val is not None:
                    if jdata.get("story_hud") != hud_val:
                        jdata["story_hud"] = hud_val
                        changed = True
                elif "story_hud" in jdata:
                    jdata.pop("story_hud", None)
                    changed = True
                if changed:
                    save_json(job, jdata)
            meta = self._code_meta(sid, job)
            t0 = segs[sid]["start_f"] / FPS
            pack = textstyle.load_style(style).get("sfx_pack") or {}    # gói SFX của style: cue chung → âm cụ thể
            self.code_cues += [(round(t0 + c["f"] / FPS, 3), pack.get(c["name"], c["name"])) for c in meta.get("cues", [])]
            self.code_texts = getattr(self, "code_texts", {})
            self.code_texts[sid] = meta.get("texts", [])
        self.board = None
        if self.spine() or self.board_ids():
            media = boardplan.media_sources(self.proj, self.csb, self.tl, self.trims, self.ingested, extract=False)
            self.board_path, self.board = boardplan.build(self.proj, self.csb, self.tl, self.vo, style, media)
            self.code_cues += [(c["t"], c["name"]) for c in self.board["cues"]]
            for n in self.board["qa"]["notes"]:
                self.log("  ⚠ board: " + n)
        self.head("text", f"{len(self.events)} chữ text_fx · {len(self.code_jobs)} shot code"
                  + (f" · board.json ({self.board['assembly']}: {len(self.board['items'])} vật, "
                     f"{len(self.board['marks'])} dấu đỏ/nhãn, {len(self.board['cues'])} cue)" if self.board else "")
                  + (" · out/captions.srt" if self.vo else ""))

    def _code_meta(self, sid, job):
        mp = os.path.join(codeshot.code_dir(self.proj, sid), "meta.json")
        h = codeshot.coderender.job_hash(load_json(job))
        m = load_json(mp, {})
        if m.get("_hash") != h:
            m = codeshot.meta(job)
            m["_hash"] = h
            save_json(mp, m)
        return m

    def s_outro(self):
        if self.is_loop_outro():
            bf = int((self.csb.get("outro") or {}).get("bridge_frames") or 8)
            self.head("outro", f"Shorts: seamless_loop ({bf}f bridge về frame 0, bỏ thẻ outro tĩnh)")
            return
        es = self.p("out", "endscreen_16x9.mp4")
        fp = _fp(self.csb.get("outro", {}), channel()["outro"], channel().get("copy"), os.path.join(ROOT, "assets", "brand"))
        if self.fresh("outro", fp, [es]):
            return
        outro.render_endscreen(self.csb, es, self.p("out", "endscreen_16x9_guide.png"))
        self.mark("outro", fp)
        self.head("outro", "Shorts: " + ("TITLE_GLITCH trên bảng (engine board)" if self.spine() else
                                          "cảnh code engine" if self.outro_code() else "template 2D")
                  + " · YouTube: out/endscreen_16x9.mp4 (+ guide)")

    def s_audio(self):
        self.mix = audiolib.mix(self.proj, self.csb, self.tl, self.vo, self.text_sfx, self.music,
                                os.path.join(self.work, "mix.wav"), self.code_cues)
        lv = self.mix["levels"]
        self.head("audio", f"{len(self.mix['sfx'])} SFX · nhạc: {self.mix['music'] or 'không'}"
                           + (f" (dừng ở twist {self.mix['music_stop']:.2f}s)" if self.mix.get("music_stop") else "")
                           + f" · nhạc {lv.get('music_db_vs_voice', '—')} dB / SFX {lv.get('sfx_db_vs_voice', '—')} dB "
                             f"so với giọng (gated RMS) · mode {lv['mode']}")

    def directions(self):
        sids = [s["id"] for s in self.csb["shots"] if s.get("mode_resolved") != "code"]
        return vcam.directions_from_clips(self.trims, self.ingested, sids)

    def s_look(self):
        """Contact sheet stills (giữa mỗi shot + 2 phía mỗi điểm cắt) TRƯỚC khi render đầy đủ — để tự xem lại."""
        sheet = self.p("qa", "look", "sheet.jpg")
        fp = self.render_inputs_fp()
        for sid in self.code_jobs:   # shot code: chỉ render frame cần cho sheet
            seg = next(s for s in self.tl["segments"] if s["sid"] == sid)
            codeshot.render_stills(self.proj, sid, [0, seg["n"] // 2, seg["n"] - 1])
        if self.spine():
            return self.look_board(sheet, fp)
        if self.board:
            self.board_shot_frames(stills=True)
        stills_at = {}
        for k, seg in enumerate(self.tl["segments"]):
            stills_at[seg["start_f"]] = f"{seg['sid']} ▸đầu"
            stills_at[seg["start_f"] + seg["n"] // 2] = f"{seg['sid']} giữa"
            if k + 1 < len(self.tl["segments"]):
                stills_at[seg["start_f"] + seg["n"] - 1] = f"{seg['sid']} cuối◂"
        self.cams = vcam.plan(self.tl, self.csb, [(x["t"], x["name"]) for x in self.mix["sfx"]], self.directions())
        layer = textfx.Layer(self.csb, textfx.build_events(self.csb, self.tl, self.vo, getattr(self, "analyses", {}),
                                                           self.trims, self.sb["style_resolved"]))
        from . import autocaptions  # noqa: PLC0415

        cap_preset = getattr(self, "cap_preset", None) or autocaptions.resolve_preset(
            self.csb, self.want_captions, self.sb["style_resolved"]
        )
        cap_layer = autocaptions.Layer(self.vo, cap_preset, self.sb["style_resolved"]) if cap_preset != "off" else None
        items = render.look_stills(self.proj, self.csb, self.tl, layer, self.trims, self.ingested, self.cams,
                                   stills_at, captions=cap_layer)
        render.sheet(items, sheet, cols=6)
        self.look_metrics = qa.look_metrics(self.proj, self.csb, self.tl, items)
        save_json(os.path.join(self.work, "look.json"), self.look_metrics)
        self.head("look", f"{os.path.relpath(sheet, ROOT)} · {len(items)} still · " + qa.look_summary(self.look_metrics))
        if self.state.get("look") != fp and not (self.look_ok or self.dry or self.yes):
            self.state["look_pending"] = fp
            save_json(self.state_path, self.state)
            raise Stop("look_check", f"Xem contact sheet trước khi render đầy đủ: {sheet}\n"
                                     f"  Đạt → chạy lại với --look-ok · Sai → sửa storyboard/cảnh code rồi chạy lại.")
        self.mark("look", fp)

    def look_board(self, sheet, fp):
        """board_spine: still ở đầu/giữa/cuối mỗi beat + đúng lúc mỗi dấu đỏ/nhãn vừa hiện (kiểm lệch từ khoá)."""
        from PIL import Image  # noqa: PLC0415

        from engines.board import color as bcol  # noqa: PLC0415
        from engines.board.scene import Scene  # noqa: PLC0415
        boardplan.media_sources(self.proj, self.csb, self.tl, self.trims, self.ingested, extract=True, log=self.log)
        at = {}
        for seg in self.tl["segments"]:
            at.setdefault(seg["start_f"] + 3, f"{seg['sid']} ▸đầu")
            at.setdefault(seg["start_f"] + seg["n"] // 2, f"{seg['sid']} giữa")
            at.setdefault(seg["start_f"] + seg["n"] - 2, f"{seg['sid']} cuối◂")
        for m in self.board["qa"]["marks"]:
            at[m["onset_f"] + 7] = f"{m['sid']} {m['what'][:18]}"
        sc = Scene(self.board)
        items = []
        os.makedirs(self.p("qa", "look", "board"), exist_ok=True)
        for fa in sorted(at):
            fa = min(fa, self.tl["frames"] - 1)
            im = Image.fromarray(bcol.to_rgb(sc.frame(fa)))
            im.save(self.p("qa", "look", "board", f"f{fa:05d}.jpg"), quality=90)
            sid = next((s["sid"] for s in self.tl["segments"] if s["start_f"] <= fa < s["start_f"] + s["n"]), "")
            items.append((f"{at[fa]} {fa / FPS:.1f}s", im, sid, "board"))
        render.sheet(items, sheet, cols=6)
        q = boardqa.run(self.board, sc.frame, self.p("qa", "board"))  # QA trên frame engine, TRƯỚC render đầy đủ
        save_json(os.path.join(self.work, "board_qa_look.json"), q)
        self.look_metrics = {"rows": [], "board": True, "marks": self.board["qa"]["marks"]}
        save_json(os.path.join(self.work, "look.json"), self.look_metrics)
        self.head("look", f"{os.path.relpath(sheet, ROOT)} · {len(items)} still board")
        for k, (v, ok) in boardqa.summary_checks(q).items():
            self.log(f"  {'✔' if ok else '✖'} {k}: {v}")
        if self.state.get("look") != fp and not (self.look_ok or self.dry or self.yes):
            self.state["look_pending"] = fp
            save_json(self.state_path, self.state)
            raise Stop("look_check", f"Xem contact sheet trước khi render đầy đủ: {sheet}\n"
                                     "  Đạt → chạy lại với --look-ok · Sai → sửa storyboard (beat_recipe/board) "
                                     "rồi chạy lại.")
        self.mark("look", fp)

    def board_shot_frames(self, stills=False):
        """assembly `cuts`: shot board thuần render thành frame riêng (work/board/frames/<sid>/) như shot code."""
        import cv2  # noqa: PLC0415

        from engines.board import render as brender  # noqa: PLC0415
        from engines.board.scene import Scene  # noqa: PLC0415
        sc = None
        for sid in self.board_ids():
            seg = next((s for s in self.tl["segments"] if s["sid"] == sid), None)
            if not seg:
                continue
            d = codeshot.board_frames_dir(self.proj, sid)
            key = self.board_key()
            if codeshot.have_all_dir(d, seg["n"]) and load_json(os.path.join(d, "_key.json"), {}).get("k") == key:
                continue
            if stills:
                os.makedirs(d, exist_ok=True)
                sc = sc or Scene(self.board)
                for j in (0, seg["n"] // 2, seg["n"] - 1):
                    cv2.imwrite(os.path.join(d, f"f{j:04d}.jpg"), sc.frame(seg["start_f"] + j))
                continue
            brender.frames(self.board_path, seg["start_f"], seg["start_f"] + seg["n"], d)
            save_json(os.path.join(d, "_key.json"), {"k": key})

    def board_key(self):
        return _fp(self.board, _board_src_fp())

    def s_code(self):
        if self.board and not self.spine():
            self.board_shot_frames()
        for sid in self.code_jobs:
            seg = next(s for s in self.tl["segments"] if s["sid"] == sid)
            if codeshot.have_all(self.proj, sid, seg["n"]):
                continue
            self.log(f"  · render shot code {sid}: {seg['n']} frame")
            st = codeshot.render_shot(self.proj, sid, log=self.log)
            self.code_stats[sid] = st
        if self.code_jobs:
            done = {k: v for k, v in self.code_stats.items() if v.get("sec_per_frame")}
            msg = ", ".join(f"{k} {v['rendered']}f {v['sec_per_frame']}s/f×{v['workers']}w" for k, v in done.items())
            self.head("code", f"{len(self.code_jobs)} shot code" + (f" · {msg}" if msg else " · đã có đủ frame (RESUME)"))
            save_json(os.path.join(self.work, "code_stats.json"), self.code_stats)

    def s_render(self):
        final = self.p("out", "final.mp4")
        vid = os.path.join(self.work, "video.mp4")
        if self.spine():
            from engines.board import render as brender  # noqa: PLC0415
            boardplan.media_sources(self.proj, self.csb, self.tl, self.trims, self.ingested, extract=True, log=self.log)
            bc = boardplan.cfg()
            st = brender.render_full(self.board_path, vid, workers=bc.get("workers", 0), crf=bc.get("crf", 17))
            self.board_stats = st
            save_json(os.path.join(self.work, "board_stats.json"), st)
            self.render_events = []
            self.rinfo = {"kinds": {"board": len(self.board["items"])}, "samples": [], "first_frame": None, "stills": []}
            self.loud = mix.master(vid, os.path.join(self.work, "mix.wav"), final)
            self.head("render", f"{os.path.relpath(final, ROOT)} · engine board {st['workers']} tiến trình · "
                                f"{st['sec_per_frame']} s/frame · {self.loud['output_lufs']} LUFS / TP "
                                f"{self.loud['output_tp']} dBTP")
            return
        if not getattr(self, "cams", None):
            self.cams = vcam.plan(self.tl, self.csb, [(x["t"], x["name"]) for x in self.mix["sfx"]], self.directions())
        self.render_events = textfx.build_events(self.csb, self.tl, self.vo, getattr(self, "analyses", {}), self.trims,
                                                 self.sb["style_resolved"])
        layer = textfx.Layer(self.csb, self.render_events)
        from . import autocaptions  # noqa: PLC0415

        cap_preset = getattr(self, "cap_preset", None) or autocaptions.resolve_preset(
            self.csb, self.want_captions, self.sb["style_resolved"]
        )
        cap_layer = autocaptions.Layer(self.vo, cap_preset, self.sb["style_resolved"]) if cap_preset != "off" else None
        self.rinfo = render.render(self.proj, self.csb, self.tl, layer, self.trims, self.ingested, self.cams, vid,
                                   captions=cap_layer)
        self.loud = mix.master(vid, os.path.join(self.work, "mix.wav"), final)
        self.head("render", f"{os.path.relpath(final, ROOT)} · nguồn {self.rinfo['kinds']} · "
                            f"{self.loud['output_lufs']} LUFS / TP {self.loud['output_tp']} dBTP "
                            f"(gain {self.loud['gain_db']} dB)")

    def s_thumbnails(self):
        self.thumbs, sheet = thumbs.make_all(self.proj, self.csb, self.trims, self.ingested)
        self.head("thumbnails", f"{len(self.thumbs)} biến thể · {os.path.relpath(sheet, ROOT)}")

    def s_publish(self):
        path, warns = qa.write_publish(self.csb, self.p("publish.md"))
        for w in warns:
            self.log("  ⚠ " + w)
        self.notes += warns
        self.head("publish", os.path.relpath(path, ROOT))

    def s_qa(self):
        cuts = qa.cut_strips(self.rinfo["samples"], self.p("qa", "cuts")) if getattr(self, "rinfo", None) else []
        final = self.p("out", "final.mp4")
        from . import qagate, rights  # noqa: PLC0415
        info, checks = qa.check_final(final)
        checks.update(qagate.spec_checks(final))                         # BT.709, tv, yuv420p, faststart, bitrate…
        loud = mix.measure(final) or {}
        checks.update(qagate.audio_checks(loud, mix.cfg()["master"]["lufs"],
                                          float((channel().get("qa") or {}).get("true_peak_max", -1.0))))
        ing = load_json(os.path.join(ingest.ingest_dir(self.proj), "_ingest.json"), {})
        low = [f"{k} {v['src_size'][0]}x{v['src_size'][1]}" for k, v in ing.items()
               if isinstance(v, dict) and v.get("src_size") and min(v["src_size"]) < 720]
        if ing and not self.dry:
            checks["nguồn Flow ≥ 720p (tải bản 1080p từ Flow)"] = (", ".join(low[:4]) or "đạt", not low or None)
        holds = qa.hold_spans(self.csb, self.tl)
        fz = qa.freeze_black(final, holds, textstyle.load_style(self.sb["style_resolved"]).get("qa_black_pic_th"))
        checks["freeze ≥ 0.4s (ngoài hold)"] = (f"{len(fz['freezes_bad'])} đoạn", not fz["freezes_bad"])
        blacks = fz["blacks"]
        if self.spine():  # TITLE_GLITCH cố ý về đen ở frame cuối → không tính
            blacks = [b for b in blacks if b[0] < info["duration"] - 0.25]
        checks["black frame"] = (f"{len(blacks)} đoạn", not blacks)
        from . import motiongate  # noqa: PLC0415 — chặn video "như slide" (tỉ lệ khung hình chuyển động nhanh)
        mg = motiongate.measure(final)
        save_json(os.path.join(self.work, "motion_gate.json"), mg)
        checks["chuyển động (không như slide)"] = motiongate.verdict(mg)
        bq = None
        if self.spine() and getattr(self, "board", None):  # QA board trên frame GIẢI MÃ từ video cuối
            vf = boardqa.VideoFrames(final, boardqa.frames_needed(self.board), self.board["width"], self.board["height"])
            bq = boardqa.run(self.board, vf, self.p("qa", "board"))
            save_json(os.path.join(self.work, "board_qa.json"), bq)
            checks.update(boardqa.summary_checks(bq))
        qa.qa_sheet(final, self.p("qa", "qa_sheet.jpg"))
        ocr_rep = qa.ocr_report(getattr(self, "render_events", []), self.proj, self.code_jobs,
                                getattr(self, "code_texts", {}), self.p("qa", "text_fx"))
        if ocr_rep["total"]:
            g_ok = sum(r["glyph_ok"] for r in ocr_rep["rows"])
            checks["chữ đúng chính tả (chuỗi code + đủ glyph)"] = (f"{g_ok}/{ocr_rep['total']}", g_ok == ocr_rep["total"])
            if ocr_rep["available"]:
                checks["OCR đọc được (giống ≥ 70%)"] = (f"{ocr_rep['ok']}/{ocr_rep['total']}",
                                                       ocr_rep["ok"] == ocr_rep["total"])
        checks.update(qa.studio_checks(self.csb, ocr_rep, captions_on=bool(self.csb.get("_captions_on", True))))
        self.rights_report, rrows = rights.write_project(self.proj, self.csb, self.dry)
        checks.update(rrows)
        rows = qagate.classify(checks)
        self.gate = qagate.summary(rows)
        segs = [s for s in self.tl["segments"] if s["sid"] != "OUTRO"]
        ctx = {
            "title": self.csb.get("title") or self.csb["topic"], "dry_run": self.dry, "style": self.sb["style_resolved"],
            "duration": info["duration"], "n_shots": len(segs),
            "outro_sec": sum(s["dur"] for s in self.tl["segments"] if s["sid"] == "OUTRO"),
            "avg_shot": sum(s["dur"] for s in segs) / max(len(segs), 1),
            "kinds": getattr(self, "rinfo", {}).get("kinds", {}), "auto_punches": self.tl["auto_punches"],
            "loudness": (f"vào {self.loud['input_lufs']} LUFS → gain tuyến tính {self.loud['gain_db']} dB → "
                         f"{self.loud['output_lufs']} LUFS, TP {self.loud['output_tp']} dBTP") if getattr(self, "loud", None)
            else "—",
            "checks": checks, "ingest": getattr(self, "ingest_report", {}) or
            load_json(os.path.join(ingest.ingest_dir(self.proj), "_ingest.json"), {}),
            "trims": self.trims, "cuts": cuts, "gate": self.gate, "rows": rows,
            "vo_notes": (self.vo or {}).get("notes", ["Không có lời đọc."]),
            "vo_lines": [dict(ln, shot_ids=[self.csb["shots"][i]["id"] for i in ln["shots"]])
                         for ln in (self.vo or {}).get("lines", [])],
            "text_events": self.text_report, "mix": self.mix, "thumbs": getattr(self, "thumbs", []),
            "notes": self.notes, "issues": [i for i in self.issues if i["level"] != "info"],
            "freeze": fz, "ocr": ocr_rep, "board_qa": bq, "board_stats": getattr(self, "board_stats", None) or load_json(
                os.path.join(self.work, "board_stats.json"), {}),
            "look": getattr(self, "look_metrics", None) or load_json(
                os.path.join(self.work, "look.json"), {}), "code_stats": self.code_stats or load_json(
                os.path.join(self.work, "code_stats.json"), {}),
        }
        qa.write_report(self.p("qa", "report.md"), ctx)
        qa.write_html(self.p("qa", "report.html"), ctx, self.proj)
        save_json(os.path.join(self.work, "qa.json"), {"checks": {k: [str(v[0]), v[1]] for k, v in checks.items()},
                                                       "rows": rows, "verdict": self.gate["verdict"], "gate": self.gate,
                                                       "cuts": cuts, "ok": self.gate["verdict"] != "red", "freeze": fz,
                                                       "ocr": ocr_rep})
        word = {"green": "XANH", "yellow": "VÀNG", "red": "ĐỎ"}[self.gate["verdict"]]
        self.head("qa", f"{word} · {self.gate['red']} đỏ · {self.gate['yellow']} vàng · {self.gate['green']} xanh · "
                        f"{os.path.relpath(self.p('qa', 'report.html'), ROOT)}")
        for it in self.gate["red_items"]:
            self.log("  ⛔ " + it)
        return self.gate["verdict"]

    def s_deliver(self):
        """Gói theo nền tảng (Shorts/Reels/TikTok/16:9) — chỉ chạy khi cổng QA không đỏ (hoặc --accept-qa)."""
        from . import deliver, manifest  # noqa: PLC0415
        ai = (getattr(self, "rights_report", None) or {}).get("ai") or {}
        res = deliver.build(self.proj, self.platforms, meta=manifest.metadata_tags(self.csb, ai), log=self.log, sb=self.csb)
        self.deliver_res = res
        reds = [f"{r['label']}: {row['label']} = {row['value']}" for r in res.values() for row in r["rows"]
                if row["level"] == "red"]
        self.head("deliver", " · ".join(f"{r['label']} {r['verdict']}" for r in res.values()))
        if reds and not self.accept_qa:
            raise Stop("qa_failed", "⛔ Gói nền tảng không đạt spec:\n  • " + "\n  • ".join(reds))
        self.append_publish_kit(res, ai)

    def append_publish_kit(self, res, ai):
        """publish.md: nhãn AI theo nền tảng (AUD-1201) + checklist trước khi đăng (AUD-1202) + đường dẫn gói."""
        p = self.p("publish.md")
        cur = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
        cur = cur.split("\n## Nhãn AI", 1)[0].rstrip() + "\n"
        need = ai.get("need") or {}
        L = ["", "## Nhãn AI (bắt buộc kiểm trước khi đăng)", "",
             f"- Thành phần AI: {', '.join(ai.get('components') or []) or 'không (toàn bộ dựng bằng code)'}",
             f"- YouTube: {need.get('youtube', '—')}", f"- TikTok: {need.get('tiktok', '—')}",
             f"- Instagram: {need.get('instagram', '—')}"]
        if ai.get("description_line"):
            L.append(f"- Dòng cho mô tả: `{ai['description_line']}`")
        L += ["", "## Gói theo nền tảng", ""]
        for r in res.values():
            L.append(f"- **{r['label']}** ({r['verdict']}): `{r['video']}` · bìa `{r['cover']}`"
                     + (f" · `{r['caption']}`" if r.get("caption") else "")
                     + (" · `captions.srt`" if r["srt"] else "") + f" — {r['ai_label']}")
        L += ["", "## Checklist trước khi đăng", "",
              "- [ ] Xem hết video ở tốc độ thật, có tiếng (lỗi khựng, chữ sai, tiếng click)",
              "- [ ] Cổng QA không đỏ (`qa/report.html`); mục vàng đã đọc và chấp nhận",
              "- [ ] Bật nhãn AI theo đúng từng nền tảng (mục trên)",
              "- [ ] Tiêu đề ≤ 60 ký tự, mô tả 2 câu + nguồn/nhãn sự thật (True/Disputed/Hypothetical)",
              "- [ ] Bìa đúng nền tảng (gói ở trên), chữ trên bìa đọc được ở cỡ nhỏ",
              "- [ ] Phụ đề `.srt` đã tải lên (YouTube/TikTok)",
              "- [ ] Quyền sử dụng: không có mục đỏ trong `out/rights.json` (gói ElevenLabs/Flow đã xác nhận)",
              "- [ ] Ghi lại version đã đăng (`out/manifest.json → version`)", ""]
        save_text(p, cur + "\n".join(L))

    def s_version(self, verdict, keep=True):
        """out/manifest.json (+ version vNNN khi qua cổng) — AUD-1101/1102."""
        from . import cost, manifest  # noqa: PLC0415
        for sid, st in (self.code_stats or {}).items():
            if isinstance(st, dict) and st.get("sec"):
                cost.record(self.proj, "render", engine=st.get("engine", "code"), sec=st["sec"], shot=sid)
        if getattr(self, "board_stats", None) and self.board_stats.get("sec"):
            cost.record(self.proj, "render", engine="board", sec=self.board_stats["sec"])
        gate = getattr(self, "gate", {}) or {}
        qa_info = {"verdict": verdict, "accepted_by_hand": bool(self.accept_qa and verdict == "red"),
                   **{k: v for k, v in gate.items() if k in ("red", "yellow", "green", "red_items")}}
        extra = {"deliver": {k: v["verdict"] for k, v in (getattr(self, "deliver_res", None) or {}).items()},
                 "provenance": (getattr(self, "rights_report", None) or {}).get("ai")}
        kw = {"plan": load_json(self.p("plan.json"), {}), "qa": qa_info, "cost": cost.summary(self.proj),
              "engine_rev": codeshot.engine_rev(), "extra": extra}
        if not keep:
            save_json(self.p("out", "manifest.json"), manifest.build(self.proj, self.csb, **kw))
            return None
        v, m = manifest.write(self.proj, self.csb, **kw)
        save_json(self.p("out", "provenance.json"), {"version": v, "ai": extra["provenance"],
                                                     "git": m["git"], "tool": m["versions"]["tool"]})
        self.head("version", f"{v} · out/versions/{v}/ · manifest + provenance")
        return v

    # ---------------------------------------------------------------- run
    def run(self):
        if self.dry:      # dự án chạy thử: ghi dấu NGAY để UI "Chạy tiếp" giữ chế độ giả (không gọi ElevenLabs)
            os.makedirs(self.work, exist_ok=True)
            save_text(self.p("work", "DRYRUN"), "dry-run (dữ liệu giả)")
        try:
            self.s_idea()
            self.s_storyboard()
            self.s_prompts()
            if self.after_only("prompts"):
                return self.finish("done")
            self.s_page()
            if self.after_only("page"):
                return self.finish("done")
            self.s_clips()
            self.s_ingest()
            self.s_trim()
            self.s_page(quiet=True)  # cập nhật trạng thái clip/seed trên trang
            if self.after_only("trim"):
                return self.finish("done")
            fp = self.render_inputs_fp()
            final = self.p("out", "final.mp4")
            heavy = STAGES[STAGES.index("voice"):]
            if self.only == "thumbnails":
                self.trims = getattr(self, "trims", {})
                self.s_thumbnails()
                return self.finish("done")
            if (self.fresh("render", fp, [final, self.p("qa", "report.html")]) and self.state.get("qa") == fp
                    and not any(self.forced(s) for s in heavy) and not self.tts_force):
                self.head("render", "đã mới nhất + đã qua cổng QA — bỏ qua (dùng --from render để làm lại)")
                return self.finish("done")
            self.s_voice()
            self.s_assemble()
            self.s_text()
            if self.after_only("text"):
                return self.finish("done")
            self.s_outro()
            self.s_audio()
            if self.after_only("audio"):
                return self.finish("done")
            self.s_look()
            if self.after_only("look"):
                return self.finish("done")
            self.s_code()
            if self.after_only("code"):
                return self.finish("done")
            self.s_render()
            self.mark("render", fp)
            if self.after_only("render"):
                return self.finish("done")
            self.s_thumbnails()
            verdict = self.s_qa()
            if verdict == "red" and not self.accept_qa:
                self.state.pop("qa", None)                          # lần sau vẫn chạy lại QA (AUD-902)
                save_json(self.state_path, self.state)
                self.s_version(verdict, keep=False)
                reds = self.gate["red_items"]
                raise Stop("qa_failed", "⛔ Cổng QA ĐỎ — chưa xuất publish.md / gói nền tảng:\n  • " + "\n  • ".join(reds)
                           + f"\n  Xem {os.path.relpath(self.p('qa', 'report.html'), ROOT)}. Sửa rồi chạy lại; hoặc "
                           "duyệt tay bằng --accept-qa (ghi vào manifest).")
            self.mark("qa", fp)
            if self.after_only("qa"):
                return self.finish("done")
            self.s_publish()
            self.s_deliver()
            self.s_version(verdict)
            return self.finish("done")
        except Stop as st:
            self.log(str(st))
            return self.finish(st.stage)

    def finish(self, stage):
        if stage == "done":
            final = self.p("out", "final.mp4")
            if os.path.exists(final):
                self.log(f"✔ Xong: {final}")
        self.log(f"::stage={stage} project={self.proj}")
        return EXIT.get(stage, 1)


def code_rev():
    """Hash NỘI DUNG mã ảnh hưởng tới hình/tiếng của video (AUD-201/803/101): vidlib/*.py, lib/motion/*,
    engines/adapter.py + engines/board/*.py, prompts/blocks; tên + cỡ font; phiên bản ffmpeg."""
    h = hashlib.sha1()
    for pat in ("vidlib/*.py", "lib/motion/*.py", "lib/motion/*.js", "engines/adapter.py", "engines/board/*.py",
                "prompts/blocks/*.txt"):
        for f in sorted(glob.glob(os.path.join(ROOT, pat))):
            h.update(os.path.relpath(f, ROOT).encode())
            with open(f, "rb") as fh:
                h.update(fh.read())
    for f in sorted(glob.glob(os.path.join(ROOT, "assets", "fonts", "*"))):
        h.update(f"{os.path.basename(f)}:{os.path.getsize(f)}".encode())
    h.update(_ffmpeg_version().encode())
    return h.hexdigest()[:12]


_FFV = []


def _ffmpeg_version():
    if not _FFV:
        from .common import ffbin  # noqa: PLC0415
        try:
            r = subprocess.run([ffbin("ffmpeg"), "-version"], capture_output=True, text=True, timeout=20)
            _FFV.append((r.stdout.splitlines() or [""])[0])
        except (OSError, subprocess.SubprocessError):
            _FFV.append("?")
    return _FFV[0]


def _board_src_fp():
    """Hash mã engine board (chỉ *.py, bỏ __pycache__) — đổi engine thì render lại."""
    d = os.path.join(ROOT, "engines", "board")
    h = hashlib.sha1()
    for f in sorted(os.listdir(d)):
        if f.endswith(".py"):
            with open(os.path.join(d, f), "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()[:12]


def textstyle_cache_clear():
    from . import textstyle  # noqa: PLC0415 — style phụ thuộc ngôn ngữ dự án (font_vi)
    textstyle.load_style.cache_clear()


def open_file(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:  # noqa: BLE001 — mở trình duyệt chỉ là tiện ích
        pass


def status(arg, log=print):
    proj, idea, new = project_for(arg)
    if new:
        raise StudioError(f"Chưa có dự án '{arg}'.")
    log(f"Dự án: {proj}\nÝ tưởng: {idea}")
    sb = sbm.load(proj)
    if not sb:
        log("  ✖ chưa có storyboard.json")
        return
    sb = compiler.compile_all(sbm.normalize(sb))
    rows = ingest.scan(proj, sb)
    have = ingest.as_dict(rows)
    flow = [s["id"] for s in sb["shots"] if s.get("mode_resolved") != "code"]
    log(f"  Model: {sb['flow']['video_model']} · {len(flow)} clip Flow · có {len([f for f in flow if f in have])}"
        f" · style {sb.get('style_resolved') or sb.get('style')}")
    for s in sb["shots"]:
        if s.get("mode_resolved") == "code":
            st = "◆ code"
        else:
            has_start = os.path.exists(os.path.join(proj, s["start_frame"]["file"]))
            st = "✔ clip" if s["id"] in have else ("◐ ảnh Start" if has_start
                                                   else "✖ chưa có")
        log(f"   {s['id']}  {st:<12} {s.get('mode_resolved'):<17} {s.get('gen_sec') or '':>3}s  {s.get('vo', '')[:50]}")
    for f in ("out/final.mp4", "thumbnails/contact-sheet.png", "qa/report.html", "publish.md"):
        log(f"  {'✔' if os.path.exists(os.path.join(proj, f)) else '·'} {f}")


def list_models(log=print):
    fm = flow_models()
    log(f"Capability Flow (kiểm chứng {fm['verified_at']}) — sửa ở config/flow-models.json")
    for name, c in fm["video_models"].items():
        tag = " (mặc định)" if name == channel()["flow"]["video_model"] else ""
        dep = f" · GỠ {c['removal_date']}" if c.get("removal_date") else ""
        log(f"  {name}{tag}: {c['durations_sec'][0]}–{c['durations_sec'][-1]}s · frames {c['frames']} · "
            f"ingredients ≤{c['ingredients_max']}{dep}")
