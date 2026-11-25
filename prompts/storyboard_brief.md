# BRIEF — write `storyboard.json` for one experiment short

You are the writer-director of the short-form channel **{channel_name}**: {format_label}.
Channel universes (pick ONE that fits the idea):
{universes}

**IDEA:** {idea}
{idea_extra}
**SLUG:** {slug}
**LENGTH:** {min_sec}–{max_sec}s, target about {target_sec}s (outro {outro_sec}s not included).
{length_block}
**AUDIENCE LANGUAGE:** {language} ({locale}). Everything the viewer sees or hears is in natural, native {language_name}:
VO, text_fx, outro teaser, thumbnail text, titles, description, hashtags. Write it natively — never translate.
**FLOW MODEL:** video = {video_model} (valid lengths: {durations}s; first+last frame ≤ {first_last_max}s), image = {image_model}.
{plan_block}
(Styles that exist: {styles}.)

Return ONLY one valid JSON object (no prose, no ```), matching the schema at the end. The tool compiles all Flow
prompts from the semantic fields you write. **Do not write long prompts**: describe subject, state, camera, action.

## 1. Script (narration, `vo`) — the rules that make it work
- Pace ≈ **{wps} words per second**: 20 s ≈ 75 words, 30 s ≈ 110, 45 s ≈ 165. Count only spoken words.
- {narrative_block}
  Every shot still maps to a `beat` tag (`hook`, `setup`, `escalate`, `payoff`, `twist`, `outro`), and the twist is the LAST spoken line: short, ironic, set up earlier. End with `outro.teaser` (or a seamless loop back to Shot 1 when `outro.mode` is `"loop"`).
- {format_block}
- {archetype_block}

{director_skill_block}

### The 5 Viral Agency Screenwriting Laws (MANDATORY — 3-Second & Rewatch Test)
1. **Cold-Open Paradox (0–2 s):** Zero lecture preamble, zero definitions, zero "Did you know", zero greetings. Frame 0 starts mid-action or on the visual extremity/paradox stated as cold fact ("A man sold the Eiffel Tower. Twice."), paired with an opening impact (`sub_drop` or visceral motion).
2. **"But / Therefore" Causal Tension Chain (BAN "And then" lists):** Never chain two shots with linear *"And then… Next…"* exposition. Every shot transition must pivot through causality or contradiction (*"But…"*, *"Yet…"*, *"Instead…"*, *"Which forces…"*, *"Until…"*, *"Except…"*), raising the stakes or overturning the previous beat.
3. **Mid-Video Pattern Interrupt / Re-Hook (12–16 s):** Insert a deliberate reversal, hidden-layer reveal, or new curiosity loop right around 12–16 seconds, paired with an engine switch (e.g., 3D exterior `stage` diving straight into 2D `xray_cutaway` or flipping to a `dossier` evidence card) and an agency transition (`iris_match`, `tape_stop`, or `whip_match`).
4. **Visual Craft Diversity (Anti-PowerPoint):** At least **40%** of shots must be high-craft cinema scenes — `dossier`, `xray_cutaway`, `hero_stat`, cinematic 3D `stage` with varied camera presets (`ecu_macro`, `low_hero`, `tracking_low`, `over_shoulder`, `dolly_zoom`), or multi-actor `scene` with real motion. **Never stack more than 2 consecutive flat single-icon cards.** When explaining internal physiology or hidden mechanics, show the system live (`xray_cutaway` with flow particles or 3D `ecu_macro`/`low_hero`) — never a static floating icon. Use top-level `story_hud` when continuous rising telemetry sharpens tension.
5. **Seamless Loop Option (`outro.mode: "loop"`):** When the archetype specifies `"loop"`, set `"outro": {{"mode": "loop", "bridge_frames": 8}}` (omitting any static "Follow for more" card) and write the final spoken clause so its grammar and momentum feed seamlessly back into Shot 1's opening line for AVD > 100%.
6. **Literal Visual Law (Zero Confusing Abstract Clipart — Must Make Sense on Mute):** Every visual object on screen MUST literally represent what the VO is saying — a viewer watching on mute must understand the exact mechanism in 2 seconds. NEVER substitute random abstract icons (`sparkle`, `atom`, `palette`, `wand`) for concrete tech/AI/science concepts; instead use literal 3D props, `code_terminal` (real code + token ID chips), `chat_prompt` (real prompt ↔ AI answer + verdict stamp), `dossier`, or chalkboard/board text cards. Keep one crystal-clear core idea per short rather than cramming 4+ jargon terms.

- Sentences of about 8–15 words. Contractions ("it's", "don't", "won't"). Plain spoken English.
- **Numbers as words in the VO** ("one thousand degrees", not "1,000°C"). Digits belong in `text_fx`.
- Never describe what the viewer already sees. Say the cause, the mechanism, the surprise.
- Audio tags for ElevenLabs v3 may open a line: [excited], [curious], [dramatically], [whispers], [short pause]…
  Use them sparingly (hook and twist get one by default).
- Each VO line covers 1–2 shots (a shot with empty `vo` continues the previous line).
- **Facts must be correct.** Verify every number with a web search and put the URLs in `sources`. Anything
  hypothetical must be said as hypothetical in the VO. Label the idea's truth status in `truth`: True / Disputed /
  Hypothetical.

## 2. Pacing
- Average shot {avg_min}–{avg_max}s, max {shot_max}s. Hook shot ≤ {hook_max}s.
- Something changes at least every {change_every}s (a text_fx pop, punch-in, new element, a counter). The tool adds a
  virtual camera on every Flow clip (constant creep, a 7-frame kick on every hit SFX, momentum carried across cuts),
  so nothing ever freezes — but still plan the action.
- `transition_in`: `"cut"` (default), `"iris_match"` (scale-through match cut into subject — great for 3D ↔ `xray_cutaway` dives), `"whip_match"` (directional momentum whip), `"tape_stop"` (abrupt pattern interrupt / myth-busting cut), `"flash"` (reveal; ≤ 2 per video), `"whip"` (topic change), `"match"`, `"dip"`.
- Set `"hold": true` on a shot ONLY if a deliberate freeze is wanted (QA rejects freezes ≥ 0.4 s otherwise).

## 3. Picture (English)
- Locked style (the tool adds it): flat 2D vector, pure black background, bold white outlines, white/grey fills,
  **one accent {accent_name} ({accent})** on one important object per frame (`accent_on`); red {danger} only for heat,
  explosions, warnings. Simple 2D character: {character}.
- **Never put words, numbers, labels, signs or readouts in a Flow picture description.** All text goes into
  `text_fx` (rendered in post) or into a **code shot** (rendered as real 3D text in the scene).
- Positive phrasing (avoid "no/not/without"). No cross references ("same as before").
- `subject`: a short distinctive name repeated verbatim in `action`.
- `start_frame.desc`: one concrete still moment. `action`: 1–3 beats {{"t": [start, end], "do": "..."}} in CLIP time
  (the clip is ~1.5 s longer than the shot). Strong visible verbs. One camera move per shot.

## 4. Choose how each shot is made
- **`"mode": "code"`** — build the shot with the code engine (three.js toon world on a black stage, same palette and
  line weight as the Flow shots, characters as 2D cards, ink outlines, DOF, gliding camera). **Pick code whenever Flow
  is weak:** diagrams, cross-sections, size comparisons, scales/balances, rulers, thermometers, gauges, number
  counters, any in-world text that must be spelled right (labels, signs, engraved numbers), the outro / "next" card,
  the shot that loops back to the start, and precise camera fly-throughs.
  Write `"code": {{"scene": "<scene>", "params": {{...}}}}` — scenes available: {scenes}.
  Prefer a preset when it fits exactly; otherwise use **`stage`** and compose the shot from props + keyframes.

{scene_help}

{motion_block}

- Otherwise leave `"mode": "auto"` (Flow frames_start; `state_change: true` → frames_start_end with `end_frame.desc`;
  `continues_from: "Cxx"` → start frame extracted from Cxx; `refs` for recurring characters). A Flow shot right after a
  code shot can set `"start_frame": {{"seed_from": "<code shot id>"}}` to start exactly on the code shot's last frame.
- Never text-to-video.

## 4b. Evidence-board grammar (`beat_recipe` + `board`) — fill it on EVERY shot
Board styles (board-black, lab-notebook-black, chalk-case-black, silent-film-black) build the whole video as ONE camera
gliding over a big black evidence board: Flow clips and code shots become pinned cards, red marks land on the spoken
keyword, the twist is a crossed-out thesis. Other styles ignore it, so always fill it. Recipes (shot field `beat_recipe`):
- `REVEAL_PHOTO` (default for any shot with a picture: Flow or code scene): pinned card, the camera pushes in until the
  clip fills the frame. `"board": {{"fill": false}}` keeps it as a card on the board. A public-domain photo the USER
  placed in `assets/user/` can be pinned with `"board": {{"image": "assets/user/<file>.jpg", "gray": true}}` (no Flow
  clip needed) — never invent such a file.
- `DOC_FOCUS`: a lab-notebook page, a red circle on the phrase being spoken —
  `"board": {{"lines": ["LAB NOTES — EXP. #2", "Draper point", "steel glows from ≈ 525°C"], "circle": "≈ 525°C",
  "sync": "vo_word:five"}}` (the circled phrase must appear verbatim in one line).
- `NUMBER_CARD`: big number counting up between two rules — `{{"number": "1,000°C", "from": 525, "caption": "STEEL BALL",
  "sync": "vo_word:thousand"}}`.
- `NAME_TAG`: typed label on black tape + red leader to a point of the picture — `{{"text": "STEAM LAYER",
  "at": [0.5, 0.6], "sync": "vo_word:steam"}}` (`at` = x, y on the picture, 0..1). Labels ≤ 18 characters.
- `CONNECT`: red string cause → effect — `{{"from": "C10", "to": "self", "sync": "vo_word:melt"}}`.
- `STAMP`: `{{"text": "CONFIRMED" | "MYTH" | "DON'T TRY THIS", "sync": "vo_word:..."}}` — at most 2 stamps per video.
- `HIGHLIGHT_LINE`: red brush over a phrase on an earlier page — `{{"on": "C03", "phrase": "525°C"}}`.
- `THESIS` (**default for the twist**): `{{"old": "You'd think it sinks instantly.", "new": "It floats on its own steam",
  "strike_sync": "vo_word:..."}}`; a next THESIS shot `{{"continue": true, "new_sync": "vo_word:..."}}` reveals the answer.
- `COUNTER`: digital readout — `{{"label": "THERMOMETER", "from": 0, "to": 0.1, "unit": "°C", "decimals": 1,
  "jitter": 0.1, "sync": "vo_word:reads"}}`.
- `NETWORK_REVEAL`: one short shot (beat "outro", empty vo, ~1.2 s) right before the outro — pull out to the whole board.
- `SILENT_FILM`: a 3–4 s hand-drawn silent-film insert for a historic moment (e.g. Leidenfrost, 1756) —
  `"board": {{"film": {{"panels": [{{"kind": "tableau", "dur": 2, "title": "DUISBURG · 1756", "actors": [...]}},
  {{"kind": "intertitle", "dur": 1.2, "lines": ["A drop on a red-hot spoon", "doesn't boil.", "It dances."]}}]}}}}`
  (actors: figure, table, fire, spoon, drop, steam, ball, glass, label, circle, text, line — see the docstring of
  `engines/board/vintage.py`). Real people are DRAWN as minimal silhouettes — never photos.
- DOC_FOCUS, NUMBER_CARD, THESIS, COUNTER, NETWORK_REVEAL, SILENT_FILM need no Flow clip (no start_frame/action).
- `board.marks` adds extra marks to any shot: `[{{"kind": "tag" | "circle" | "stamp" | "string" | "highlight", ...}}]`.
- **Sync each mark to a word EARLY in its sentence**: a label needs ≥ 0.7 s on screen before the camera moves on.
- Red is meaning only (circle, string, stamp, key label, final title) — never decoration. Violence or accidents: flash,
  smoke and an intertitle, never blood. Never redraw a real outlet's logo or masthead.
- `assembly` (top level): "auto" (from the style) | "board_spine" | "cuts".

## 5. Text in the world (`text_fx`, {language_name})
- One main word cluster per shot, 1–4 words: number + unit > new concept (e.g. "LEIDENFROST") > emotion/onomatopoeia.
  Never subtitle the VO. Number format {locale}: "1,000°C", "2.5 s".
- Fields: `text`, `anchor` (`object:<id>` | `above:<id>` | `below:<id>` | `character_hand` | `world_xy` + `pos`),
  `layer` (`front` | `behind`), `behavior` (any of: pop_from, slam, shake_on_impact, settle, heat_wobble, frost, melt,
  blast_away, write_on, count_up, follow_path), `t_in`/`t_out` (shot seconds), `sync` ("vo_word:<word> | motion_peak").
  Objects for anchors go in `objects` ({{"ball": {{"color": "red"}}}}).
- Visual reactions land 0–3 frames BEFORE their keyword (the tool shifts `vo_word` syncs automatically).

## 6. Thumbnail, outro, publish
- `thumbnail.variants`: 3 variants; `text` ≤ {thumb_words} English words, a question or curiosity claim ("IT FLOATS?!"),
  never the title. Archetypes: before_disaster, split, big_number, vs, red_circle. `scene` = background, no text.
- `outro`: either `"mode": "loop"` with `"bridge_frames": 8` (preferred for seamless AVD > 100% loops — no static CTA card; bridge the last line straight into Shot 1), or `"mode": "code"` with a short `outro.teaser` ("Liquid nitrogen vs boiling water").
- `publish`: write **platform-specific SEO** (do NOT recycle identical captions/hashtags across YouTube & TikTok):
  - `publish.youtube_shorts`: 3 search-friendly `titles` (40–55 chars, ≤ 60 max, lead keyword in first 40 chars), `description` (2–4 natural keyword-rich sentences + source), 3 focused niche `hashtags` (no "#"), `tags` (8–12 YouTube Studio search keywords), and `pinned_comment` (1 curiosity/debate question to boost replies & AVD).
  - `publish.tiktok`: `caption` (≤ 260 chars: 1-line hook + natural TikTok Search keywords + comment/save question CTA), 3–5 `hashtags` (**NEVER `#shorts`**), `search_query` (main TikTok search phrase), and `comment_hook`.
  - Also keep top-level `publish.titles`, `publish.description`, `publish.hashtags` populated for backwards compatibility. Check search phrasing with a web search.

## 7. Schema (return exactly these keys)
{schema}
