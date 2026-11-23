"""Stage `idea`: 10 ý tưởng theo format của cartoon-short-kit (title, hook nghịch lý, twist, khoảnh khắc thị giác,
nhãn True / Disputed / Hypothetical), người dùng chọn → pipeline chạy tiếp. --auto-pick: chọn ý tưởng điểm cao nhất.

  python studio.py ideas "<chủ đề>"                → ideas/<slug>/brief.md, dừng need_ideas (LLM viết ideas.json)
  python studio.py ideas <slug>                    → in bảng, dừng pick_idea
  python studio.py ideas <slug> --pick 3[,7]       → tạo dự án cho ý tưởng 3 (và 7) rồi chạy /video
  python studio.py ideas <slug> --auto-pick        → chọn điểm cao nhất (hoà: True > Disputed > Hypothetical)
"""
import os
import re

from . import lang, narratives, styles
from .common import PROJECTS, PROMPTS_DIR, ROOT, StudioError, channel, load_json, save_json, slugify

IDEAS_DIR = os.path.join(ROOT, "ideas")
TRUTH = ("True", "Disputed", "Hypothetical")
EXIT = {"need_ideas": 5, "pick_idea": 6}


def batch_dir(arg):
    p = os.path.join(IDEAS_DIR, arg)
    if os.path.isdir(p):
        return p, arg, False
    s = slugify(arg)
    return os.path.join(IDEAS_DIR, s), arg, not os.path.isdir(os.path.join(IDEAS_DIR, s))


def brief(theme):
    cfg = channel()
    with open(os.path.join(PROMPTS_DIR, "ideas_brief.md"), encoding="utf-8") as f:
        tpl = f.read()
    rec = [slug for _, slug, _ in styles.history()[:8]]
    unis = "\n".join(f"- {k}) {n}: {desc}" for k, (n, desc) in cfg["universes"].items() if k in cfg["universe"])
    vals = {"channel_name": cfg["name"], "format_label": cfg["format_label"], "language_name": "English"
            if lang.language().startswith("en") else lang.language(), "locale": lang.locale(), "theme": theme,
            "min_sec": cfg["duration"]["min_sec"], "max_sec": cfg["duration"]["max_sec"], "universes": unis,
            "recent": ", ".join(rec) or "—",
            "narratives": "\n".join(f"  - `{k}` — {v['shape']}" for k, v in narratives.config()["narratives"].items())}
    text = re.sub(r"\{(\w+)\}", lambda m: str(vals.get(m.group(1), m.group(0))), tpl)
    return text.replace("{{", "{").replace("}}", "}")


def validate(data):
    errs = []
    ideas = data.get("ideas") or []
    if len(ideas) != 10:
        errs.append(f"cần đúng 10 ý tưởng (có {len(ideas)}).")
    for k, it in enumerate(ideas, 1):
        for key in ("title", "hook", "twist", "visual", "truth"):
            if not it.get(key):
                errs.append(f"#{k}: thiếu '{key}'.")
        if it.get("truth") not in TRUTH:
            errs.append(f"#{k}: truth phải là {' / '.join(TRUTH)}.")
        if it.get("hook", "").rstrip().endswith("?"):
            errs.append(f"#{k}: hook phải là nghịch lý nói như sự thật, không phải câu hỏi.")
        n = len((it.get("title") or "").split())
        if n and not 4 <= n <= 9:
            errs.append(f"#{k}: title {n} từ (nên 5–8).")
    return errs


def table(ideas):
    rows = []
    for k, it in enumerate(ideas, 1):
        vis = it["visual"] if isinstance(it["visual"], str) else " / ".join(it["visual"])
        shape = f" · {it['narrative']}" if it.get("narrative") else ""
        rows.append(f"  {k:>2}. [{it.get('score', '?')}] {it['title']}  ({it['truth']}{shape})\n"
                    f"      hook : {it['hook']}\n      twist: {it['twist']}\n      hình : {vis}")
    return "\n".join(rows)


def best(ideas):
    order = {t: i for i, t in enumerate(TRUTH)}
    return max(range(len(ideas)), key=lambda i: (float(ideas[i].get("score") or 0), -order.get(ideas[i].get("truth"), 9)))


def make_project(it):
    slug = slugify(it["title"])
    proj = os.path.join(PROJECTS, slug)
    os.makedirs(proj, exist_ok=True)
    ip = os.path.join(proj, "idea.txt")
    if not os.path.exists(ip):
        with open(ip, "w", encoding="utf-8", newline="\n") as f:
            f.write(it["title"] + "\n")
    save_json(os.path.join(proj, "idea.json"), it)
    return slug


def run(arg, pick=None, auto_pick=False, log=print, run_video=None):
    d, theme, new = batch_dir(arg)
    os.makedirs(d, exist_ok=True)
    jp = os.path.join(d, "ideas.json")
    if not os.path.exists(jp):
        bp = os.path.join(d, "brief.md")
        with open(bp, "w", encoding="utf-8", newline="\n") as f:
            f.write(brief(theme))
        log(f"Chưa có ideas.json. Brief: {os.path.relpath(bp, ROOT)} → viết {os.path.relpath(jp, ROOT)} rồi chạy lại.")
        log(f"::stage=need_ideas project={d}")
        return EXIT["need_ideas"]
    data = load_json(jp)
    errs = validate(data)
    if errs:
        raise StudioError("ideas.json còn lỗi:\n  ✖ " + "\n  ✖ ".join(errs))
    ideas = data["ideas"]
    log(f"10 ý tưởng — {data.get('theme', theme)}\n" + table(ideas))
    picks = []
    if pick:
        picks = [int(x) - 1 for x in str(pick).split(",") if x.strip()]
        if any(not 0 <= i < len(ideas) for i in picks):
            raise StudioError(f"--pick phải trong 1–{len(ideas)}.")
    elif auto_pick:
        picks = [best(ideas)]
        log(f"  → --auto-pick chọn #{picks[0] + 1}: {ideas[picks[0]]['title']} (điểm {ideas[picks[0]].get('score')})")
    if not picks:
        log("Chọn: python studio.py ideas " + os.path.basename(d) + " --pick <số>[,<số>]   (hoặc --auto-pick)")
        log(f"::stage=pick_idea project={d}")
        return EXIT["pick_idea"]
    rc = 0
    for i in picks:
        slug = make_project(ideas[i])
        save_json(jp, {**data, "picked": sorted(set((data.get("picked") or []) + [i + 1]))})
        log(f"▶ dự án {slug}")
        if run_video:
            rc = run_video([slug])
    return rc
