"""Stage `script/storyboard`: sinh brief cho LLM (Claude Code / API / dán tay) để viết storyboard.json."""
import json
import os
import re

from .common import PROMPTS_DIR, StudioError, brand, channel, flow_models


LANG_NAMES = {"en": "English", "vi": "Vietnamese"}


def engine_help():
    """Beat của engine html/manim (vòng 7) — mô tả lấy từ PARAMS của từng engine, không viết tay ở đây."""
    from engines import html, manim  # noqa: PLC0415

    from . import textstyle  # noqa: PLC0415
    by = {}
    for sid in textstyle.list_styles():
        e = textstyle.load_style(sid).get("code_engine")
        if e in ("html", "manim"):
            by.setdefault(e, []).append(sid)
    out = ["**Motion-graphics engines (no Flow clip, no JavaScript).** Styles built in code use them: write "
           '`"mode": "code", "code": {{"scene": "<beat>", "params": {{...}}}}` for EVERY shot. Every beat also accepts '
           "`kicker`, `title`. **Icons** (`icon` fields) draw THIS video's objects in the style's palette. Name one "
           "(grouped by the channel's topic areas):\n"
           + "\n".join(f"  - {g}: {', '.join(items)}" for g, items in html.icon_groups().items())
           + "\n  Plain words map to the nearest icon (\"marathon\" → runner, \"bench press\" → barbell, \"pull request\" → "
           "branch, \"titanic\" → ship). Nothing close? Compose it: "
           "`\"icon\": {{\"parts\": [{{\"k\": \"circle\", \"x\": 0, \"y\": 0, \"r\": 0.6, \"role\": \"hot\"}}, "
           "{{\"k\": \"rect\", \"x\": -0.5, \"y\": 0.4, \"w\": 1, \"h\": 0.3, \"rad\": 0.1, \"role\": \"ink\"}}]}}` "
           "(k: circle|rect|poly{{pts}}|line{{pts}}|arc{{r,a0,a1}}; coordinates -1..1, y down). An unknown icon name is an "
           "error. `role` is hot | cold | accent | ink | dim. All on-screen strings must be short natural English."
           + _user_assets_help()]
    for name, mod in (("html", html), ("manim", manim)):
        beats = " · ".join(
            f"`{b}` — {mod.PARAMS[b][1]}" if b in mod.PARAMS else f"`{b}`"
            for b in mod.BEATS
        )
        out.append(f"Engine `{name}` (styles: {', '.join(by.get(name, [])) or '—'}): {beats}")
    lh = getattr(html, "LAYOUT_HELP", None) or {}        # mô tả bố cục (engines/html, nếu có) — không viết tay ở đây
    layouts = " · ".join(f"`{b}`: " + " | ".join(f"{o} ({lh[b][o]})" if (lh.get(b) or {}).get(o) else o for o in opts)
                         for b, opts in html.LAYOUTS.items())
    out.append("Html beat `layout` variants (omit `layout` and the tool picks one that fits the data and was not used in "
               f"this video or the channel's last videos; or pick one): {layouts}.")
    out.append('A beat the style engine lacks falls back to `html`. Force an engine with `"engine": "three|html|manim"`.')
    out.append(mix_help())
    return "\n\n".join(out).replace("{{", "{").replace("}}", "}")


def _user_assets_help():
    """Tài sản người dùng đang có (assets/user/svg|lottie|rive) — LLM chỉ được gọi đúng các tên này."""
    from . import userassets  # noqa: PLC0415

    have = {k: userassets.names(k) for k in userassets.KINDS}
    txt = ("\n  **User assets** (licensed files the owner imported; use them when they fit the idea): "
           "SVG icons → `\"icon\": \"svg:<name>\"` anywhere an icon goes (and `stage` prop `\"type\": \"svg:<name>\"` = "
           "extruded 3D); `scene` actor `\"lottie\": \"<name>\"` (colors: palette | <role> | keep) or "
           "`\"rive\": \"<name>\"` "
           "(animation | state_machine) = a ready-made animation playing in place of an icon (speed, loop, start s).")
    listing = "; ".join(f"{k}: {', '.join(v)}" for k, v in have.items() if v)
    return txt + (f" Available now — {listing}." if listing else " None imported yet: do not invent names.")


def mix_help():
    """Đoạn "trộn engine trong một video" — danh sách cảnh lấy từ engine thật (không viết tay tên cảnh)."""
    from engines import html  # noqa: PLC0415

    from . import codeshot, motionplan  # noqa: PLC0415
    c = motionplan.cfg()
    three = [s for s in codeshot.scenes("three") if s not in ("charsheet", "outro")]
    mech = [b for b in html.BEATS if b in set(c["mechanism_scenes"]) and b != "scene"]
    generic = [b for b in html.BEATS if b in set(c["generic_beats"])]
    data = [b for b in ("graph", "scale") if b in html.BEATS]
    lines = [
        "**MOTION MIX — mechanism first, numbers second** (one video mixes engines; the tool routes every shot and "
        "renders all of them in this style's palette and font; consecutive html shots fly as one continuous camera):",
        "  - For every fact ask *what physically happens?* and SHOW that — actors doing it, at the real rate/amount from "
        f"the script. Free staging: html `scene` (actors + depth + motion verbs). Mechanism beats, engine `html`: "
        f"{', '.join(f'`{b}`' for b in mech)}.",
        f"  - Physical action, bodies, animals, objects in space (hook, impact, payoff) → 3D, engine `three`: "
        f"{', '.join(f'`{s}`' for s in three)} (`stage` = any props/3D actors/fx from data).",
        f"  - A number ALONE gets a card ({', '.join(f'`{b}`' for b in generic)}) only when the comparison IS the point "
        f"— at most {float(c['generic_max_share']):.0%} of the shots — and then pick a layout whose motion is driven "
        f"by the value (see layouts). Curves and size ladders: {', '.join(f'`{b}`' for b in data)}.",
    ]
    from engines import manim  # noqa: PLC0415
    if manim.available():
        lines.append("  - Forces, equations, plotted functions → engine `manim` (`\"engine\": \"manim\"`): "
                     "`vectors`, `equation`, `graph`.")
    lines.append(f"  - At least {c['min_mechanism_shots']} shots show a mechanism. Change engine at a beat change "
                 "(setup → escalate → payoff), not every shot. `scale` and `outro` exist in both three and html: html "
                 "`scale` needs `items[]`.")
    lines.append(
        "\n**VISUAL BUDGET & STORYTELLING RULES (LESS IS MORE — Vox / Fern / Johnny Harris standard):**\n"
        "  - **1 Shot = 1 Single Visual Beat**: at most 1 Hero subject + 1 interacting mechanism (≤ 3 prominent actors "
        "in `scene`, ≤ 5 framed props in `stage`). If a sentence explains two mechanisms, split into 2 consecutive shots.\n"
        "  - **Show, Don't Type (Visual-First)**: Auto-captions (`studio_clean`, Zone C `y: 1340–1460`) already carry the "
        "spoken narration. Do NOT repeat the VO on screen. Keep on-screen text to at most 1 short anchor (≤ 4 words or "
        "one number + unit like `41.2°C`, `157 BPM`), and omit redundant `kicker`/`title`/`sub` on action shots.\n"
        "  - **Context Coherence & Grounded Physics**: every prop must physically belong in its environment. Never paste "
        "a giant floating thermometer or floating lungs onto an outdoor running track. Show overheating/strain directly "
        "on the actor via `heat: 0..1` (thermal core glow in both 2D `scene` and 3D `stage`), and cut to a dedicated "
        "clean dark-background anatomical cutaway shot when explaining internal organs.\n"
        "  - **Cinematic Adult Pacing & 3-Zone 9:16 Grid**: calm, authoritative ~3.0 wps narration, 2.4–3.8 s per shot "
        "(10–13 high-craft shots for a 40 s short) with continuous internal motion; keep all visual subjects and labels "
        "cleanly inside Zone B (`y: 390–1240`) so Zone C captions never touch characters or labels.\n"
        "\n**AGENCY CINEMA TOOLKIT (Round 13 — Anti-PowerPoint Craft):**\n"
        "  - **3 Cinema 2D Beats (engine `html`):**\n"
        "    - `dossier` *(LEMMiNO / Fern archival card)*: `{tag, stamp?, headline, evidence: [{k, v}], highlight, "
        "visual_icon?, cite?}` — structured dark-mode evidence card with animated highlighter sweep.\n"
        "    - `xray_cutaway` *(Zack D. Films / Fern anatomical cutaway)*: `{shell_icon, core_icon, flow: [{from, to, "
        "via?, count, color_role, speed}], pulse_rate?, callout_num?, callout_label?}` — 2-layer X-ray silhouette with "
        "live Bézier flow particles (blood, nerve signals, heat, oxygen).\n"
        "    - `hero_stat` *(Vox / Cleo Abram architectural stat)*: `{number, prefix?, suffix?, unit?, label, "
        "sub_bar?: {from, to}, bg_motif?: \"rings\"|\"bars\"|\"grid\"|\"wave\", role?}` — full-frame kinetic "
        "typography reacting to the number.\n"
        "  - **Persistent `story_hud` (top-level or per-shot):** `{kind: \"clock\"|\"temp\"|\"bpm\"|\"meter\"|\"chapter\", "
        "label, from, to, unit, role}` — ultra-clean telemetry bar in Zone A (`y: 260–310`) that smoothly interpolates "
        "across shots to build continuous rising stakes.\n"
        "  - **5 Cinematic 3D `stage` Camera Presets (`frame.preset`):** `ecu_macro` (extreme close-up hook), "
        "`low_hero` (dramatic low upward angle), `tracking_low` (low side-tracking motion), `over_shoulder` "
        "(perspective clash/target view), `dolly_zoom` (Vertigo tension push/FOV shift). Vary presets across 3D shots.\n"
        "  - **3 Agency Transitions (`transition_in`):** `iris_match` (scale-through match cut into the subject), "
        "`whip_match` (directional momentum whip), `tape_stop` (pattern interrupt / myth-busting cut)."
    )
    return "\n".join(lines)


def scene_help():
    return _three_help() + "\n\n" + engine_help()


def _three_help():
    """Dòng '// params:' + dòng mô tả đầu của mỗi engines/three/scenes/*.js → gợi ý cho LLM."""
    from . import codeshot  # noqa: PLC0415
    out = []
    for name in codeshot.scenes():
        if name in ("charsheet", "stage"):
            continue
        with open(os.path.join(codeshot.SCENES_DIR, f"{name}.js"), encoding="utf-8") as f:
            head = [ln[2:].strip() for ln in f.read().splitlines()[:6] if ln.startswith("//")]
        par = next((h for h in head if h.startswith("params:")), "")
        out.append(f"`{name}` — {par or head[0] if head else ''}")
    with open(os.path.join(codeshot.SCENES_DIR, "stage.js"), encoding="utf-8") as f:
        stage = []
        for ln in f.read().splitlines():
            if not ln.startswith("//"):
                break
            stage.append(ln[2:].rstrip())
    return ("Preset scenes (fixed layout, only params): " + " · ".join(out) + "\n\n"
            "**`stage` — the GENERAL code scene for ANY idea** (no JavaScript: compose it from data). Use it whenever "
            "no preset fits. Keep the layout TALL for 9:16 (stack things vertically, ≤ ~1.4 m wide); leave `camera` empty "
            "to auto-frame everything; put in-world words on `sign`/`text` props (spelled exactly, no digits in VO):\n```\n"
            + "\n".join(stage) + "\n```")


def plan_block(plan):
    """Đoạn brief nói cho LLM: style hôm nay (có Flow hay toàn code), engine, giọng — để kịch bản viết đúng loại shot."""
    from . import styles, textstyle, voices  # noqa: PLC0415
    if not plan or not plan.get("style"):
        return ('**STYLE:** "auto" — write `"style": "auto"`; the tool picks a style that fits the topic.')
    sid = plan["style"]
    st = textstyle.load_style(sid)
    eng = styles.engine(sid)
    alt = ", ".join(plan.get("alternatives") or [])
    head = (f'**STYLE FOR THIS VIDEO:** `{sid}` — {st.get("name", sid)}. Write `"style": "{sid}"`. '
            f"(Picked for this topic: {plan.get('reason', '')}"
            + (f"; close alternatives: {alt}" if alt else "") + ". The user can override with --style.)")
    if not plan.get("uses_flow"):
        body = ("**NO-FLOW DAY — every shot is built in code.** Every shot: `\"mode\": \"code\"` with "
                + ("a three.js scene (§4)" if eng == "three"
                   else f"a motion-graphics beat of engine `{eng}` (§4, list below)")
                + ". Write NO `start_frame`, `action`, `refs` or `ingredients`. Tell the story with the beats: one beat per "
                  "shot, 2–4 s each, a new visual every shot. **Stage 1–3 key physical/action moments with `scene`** "
                  "(multiple actors moving via `keys`, `arrows`, `fx`, `labels`) so the video shows things happening — "
                  "never repeat the same template chain (`title → counter → process → callout → compare`) or rely only on "
                  "single-icon cards. Template beats already have multiple layouts (auto-rotated by the tool). Choose "
                  "icons that show THIS topic (named icons or `{\"parts\": [...]}` drawn from shapes). All on-screen "
                  "strings short natural English.")
    elif (st.get("assembly") or "") == "board_spine":
        body = ("**FLOW DAY on the evidence board** — Flow clips become pinned cards; fill `beat_recipe` + `board` on every "
                "shot (§4b). Board-native recipes (DOC_FOCUS, NUMBER_CARD, THESIS, COUNTER…) need no Flow clip.")
    else:
        body = ("**FLOW DAY** — most shots are Google Flow clips (§3, `\"mode\": \"auto\"`). Use code shots only where Flow "
                "is weak: three.js scenes, or motion-graphics beats (`counter`, `graph`, `compare`, `scale`, `process`, "
                "`callout`) which render in this style's palette and font.")
    v = plan.get("voice") or {}
    voice = (f"\n**VOICE:** {v.get('name', voices.short(v))} (tags: {', '.join(v.get('tags', []))}). Write the narration "
             "for this voice: match its energy; audio tags only where they fit.") if v.get("id") else ""
    look = (st.get("flow") or {}).get("look") or ""
    persona = f"\nLook: {look}" if look else ""
    return head + "\n" + body + persona + voice


def build(idea, slug, video_model=None, proj=None, plan=None):
    from . import codeshot, lang, motionplan, narratives, styles  # noqa: PLC0415
    from .common import duration_profile  # noqa: PLC0415
    cfg = channel()
    extra = ""
    d0 = {}
    ij = os.path.join(proj, "idea.json") if proj else None
    if ij and os.path.exists(ij):
        with open(ij, encoding="utf-8") as f:
            d0 = json.load(f)
        extra = "\n".join(f"**{k.upper()}:** {d0[k]}" for k in ("hook", "twist", "visual", "truth") if d0.get(k))
    fm = flow_models()
    vm = video_model or cfg["flow"]["video_model"]
    caps = fm["video_models"][vm]
    im = cfg["flow"]["image_model"]
    p = cfg["pacing"]
    prof = duration_profile((plan or {}).get("length_profile"))
    if prof["name"] == "deep":
        length_block = (
            "**MINI DEEP-DIVE MODE (65–90s · TikTok Creator Rewards 1min+ & YouTube Extended Shorts):**\n"
            f"- Set `\"length_profile\": \"deep\"` and `\"format\": {{\"target_sec\": {prof['target_sec']}}}`.\n"
            "- Total spoken duration MUST exceed **62 seconds** (~210–255 spoken words across 18–24 visual shots) "
            "so the video qualifies for **TikTok Creator Rewards (>1 min)** while staying inside YouTube Shorts.\n"
            "- Use a **3-Act Micro-Documentary Arc** with **2 Re-Hooks**:\n"
            "  1. Act 1 (0–20s): Cold-open paradox hook + immediate stakes.\n"
            "  2. **Re-Hook #1 (~20s)**: Twist the assumption (*'But that's not even the crazy part…'* / engine switch).\n"
            "  3. Act 2 (20–48s): Deep mechanism breakdown with concrete literal visuals/numbers.\n"
            "  4. **Re-Hook #2 (~48s)**: Real-world consequence or second layer reveal.\n"
            "  5. Act 3 (48–75s+): Payoff + ironic final twist + seamless loop back to Shot 1."
        )
    else:
        length_block = (
            f"**STANDARD SHORT MODE ({prof['min_sec']}–{prof['max_sec']}s):** "
            "Tight single-idea paradox with 1 mid-video re-hook around 12–16s."
        )
    b = brand()
    with open(os.path.join(PROMPTS_DIR, "storyboard_brief.md"), encoding="utf-8") as f:
        tpl = f.read()
    with open(os.path.join(PROMPTS_DIR, "storyboard_schema.json"), encoding="utf-8") as f:
        schema = f.read()
    unis = "\n".join(f"- {k}) {n}: {desc}" for k, (n, desc) in cfg["universes"].items() if k in cfg["universe"])
    vals = {
        "channel_name": cfg["name"], "format_label": cfg["format_label"], "universes": unis, "idea": idea, "slug": slug,
        "min_sec": prof["min_sec"], "max_sec": prof["max_sec"], "target_sec": prof["target_sec"],
        "outro_sec": cfg["outro"]["duration_sec"], "video_model": vm,
        "durations": ", ".join(str(x) for x in caps["durations_sec"]),
        "first_last_max": caps.get("first_last_max_sec", "—"), "image_model": im,
        "hook_max": p["hook_max_sec"], "vo_speed": cfg["vo"]["speed"], "avg_min": prof["shot_avg_min"],
        "avg_max": prof["shot_avg_max"], "shot_max": prof["shot_max_sec"], "change_every": p["change_every_sec"],
        "length_block": length_block,
        "accent_name": b["accent_name"], "accent": b["colors"]["accent"], "danger": b["colors"]["danger"],
        "character": b["character"], "max_refs": fm["image_models"].get(im, {}).get("max_refs", 1),
        "thumb_words": cfg["thumbnail"]["max_words"], "schema": schema.replace("<slug>", slug),
        "idea_extra": extra, "language": lang.language(), "locale": lang.locale(),
        "language_name": LANG_NAMES.get(lang.language()[:2], lang.language()), "wps": lang.pace(),
        "style": (plan or {}).get("style") or cfg.get("styles", {}).get("default", "auto"),
        "styles": ", ".join(styles.available()), "plan_block": plan_block(plan),
        "narrative_block": narratives.block((plan or {}).get("narrative")),
        "format_block": narratives.format_block((plan or {}).get("format_family")).replace("{", "{{").replace("}", "}}"),
        "archetype_block": narratives.archetype_block((plan or {}).get("archetype")).replace("{", "{{").replace("}", "}}"),
        "scenes": ", ".join(s for s in codeshot.scenes() if s != "charsheet"), "scene_help": scene_help(),
        # §4c motion: cơ chế cho chủ đề + không lặp video trước + verb (ngoặc nhân đôi để qua bước gộp {{ }} bên dưới)
        "motion_block": motionplan.brief_block(idea, slug, plan, proj, d0).replace("{", "{{").replace("}", "}}"),
    }
    return re.sub(r"\{(\w+)\}", lambda m: str(vals.get(m.group(1), m.group(0))), tpl).replace("{{", "{").replace("}}", "}")


def strip_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b < 0:
        raise StudioError("Câu trả lời của AI không chứa JSON.")
    return json.loads(text[a:b + 1])


LAST_USAGE = {}     # token của lần gọi gần nhất → pipeline ghi vào work/cost.json


def ask(provider, prompt):
    """Gọi API (cần key trong biến môi trường; không lưu key vào repo)."""
    if provider == "claude":
        import anthropic  # noqa: PLC0415 — chỉ cần khi dùng --ai claude
        model = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
        # Output JSON dài → streaming để tránh timeout; effort "high" (mặc định của Opus 5.5 là medium);
        # fallback phía server khi bị từ chối nhầm.
        with anthropic.Anthropic().beta.messages.stream(
                model=model, max_tokens=64000, output_config={"effort": "high"},
                betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                messages=[{"role": "user", "content": prompt}]) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "refusal":
            raise StudioError("Claude từ chối yêu cầu — thử diễn đạt lại ý tưởng.")
        if msg.stop_reason == "max_tokens":
            raise StudioError("Câu trả lời bị cắt (max_tokens) — rút gọn ý tưởng hoặc thử lại.")
        u = getattr(msg, "usage", None)
        LAST_USAGE.update({"provider": "claude", "model": model, "tokens_in": getattr(u, "input_tokens", 0) or 0,
                           "tokens_out": getattr(u, "output_tokens", 0) or 0})
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    if provider == "gemini":
        from google import genai  # noqa: PLC0415

        from . import aireview  # noqa: PLC0415
        from .common import env  # noqa: PLC0415
        api_key = env("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise StudioError("Thiếu GEMINI_API_KEY trong .env (lấy miễn phí/credit Pro tại https://aistudio.google.com/apikey).")
        try:
            client = genai.Client(api_key=api_key, http_options={"retry_options": {"attempts": 1}})
        except TypeError:
            client = genai.Client(api_key=api_key)
        pref = os.environ.get("GEMINI_TEXT_MODEL")
        candidates = [pref] if pref else list(aireview.FALLBACK_MODELS)
        used_model = candidates[0]
        interaction = None
        for idx, cand in enumerate(candidates):
            used_model = cand
            try:
                interaction = client.interactions.create(model=cand, input=prompt)
                break
            except Exception as ex:  # noqa: BLE001
                if idx + 1 < len(candidates) and aireview._is_transient_err(ex):
                    continue
                raise StudioError(f"Gemini API lỗi với `{cand}`: {ex}") from ex
        usage = getattr(interaction, "usage", None)
        LAST_USAGE.update({
            "provider": "gemini",
            "model": used_model,
            "tokens_in": getattr(usage, "total_input_tokens", 0) or 0,
            "tokens_out": getattr(usage, "total_output_tokens", 0) or 0,
        })
        text = getattr(interaction, "output_text", None) or ""
        if not text:
            raise StudioError("Gemini không trả về nội dung văn bản — thử lại hoặc đổi GEMINI_TEXT_MODEL.")
        return text
    raise StudioError(f"--ai {provider} không hỗ trợ (dùng claude hoặc gemini).")
