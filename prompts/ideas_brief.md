# BRIEF — 10 video ideas for {channel_name}

Channel: {format_label}. Audience: native {language_name} speakers ({locale}). Black-background 2D experiment shorts,
{min_sec}–{max_sec}s. Theme / seed from the creator: **{theme}**
Channel universes:
{universes}

Give exactly **10** ideas. What makes an idea great for this format:
- One surprising experiment with a physical cause and effect you can SHOW ("what happens if…").
- Stakes that escalate in three steps, and a twist in the last line (ironic, set up earlier).
- Can be drawn as flat 2D on black (Flow) or built from simple 3D lab props (code engine): glasses, balls, scales,
  thermometers, gauges, chambers, flames, ice, a scientist character.
- Mix across physics, chemistry, the human body, everyday objects, extreme numbers, myths.
- Vary the narrative shape across the 10 ideas (at least 5 different shapes) and name it in `narrative`:
{narratives}
- For anything presented as true, verify the key fact with a web search first. Never present a viral myth as fact:
  label it honestly.
- No real living people as the butt of a joke, nothing graphic, nothing political.
- Avoid repeating the creator's recent topics: {recent}

Return ONLY valid JSON (no prose, no ```):
{{"theme": "{theme}", "ideas": [
  {{"title": "5–8 word curiosity title",
    "hook": "First spoken sentence: a paradox stated as fact (no question)",
    "twist": "The ironic payoff that ends the video, one line",
    "visual": ["2–3 big visual moments (a collapse, a reveal, a chase)"],
    "truth": "True | Disputed | Hypothetical",
    "narrative": "one shape id from the list above (the title should match it: countdown → '5 things…')",
    "truth_note": "one line: what is documented / disputed / imagined",
    "sources": ["https://…"],
    "code_shots": "which moments suit the code engine (scale, thermometer, gauge, diagram…), or none",
    "score": 0-10,
    "why": "one line: why it will retain viewers"}}
]}}
