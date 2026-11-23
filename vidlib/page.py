"""scripts.html — bảng sản xuất cho Google Flow, sinh từ storyboard.json (đã compile).

Thứ tự thao tác mỗi cảnh: ① ảnh Start → ② ảnh End (nếu có) → ③ video → ④ lưu clip + tick.
Nhãn giao diện tiếng Việt; mọi prompt gửi Flow tiếng Anh.
Mở trang với ?selftest=1 để tự kiểm tra các nút copy + phím tắt (dùng cho headless browser).
"""
import html
import json
import os

from . import compiler, linter
from .common import ROOT, channel, syllables

CSS = r"""
:root{--bg:#0b0b0c;--panel:#141416;--panel2:#1b1b1f;--line:#2a2a31;--text:#f4f4f6;--muted:#9a9aa6;
--accent:#1849F7;--accent2:#3F6BFF;--ok:#3ccf7a;--warn:#ffb020;--err:#ff4d4d;--mono:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 "Be Vietnam Pro",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:20px 16px 120px}
header.top{position:sticky;top:0;z-index:5;background:rgba(11,11,12,.94);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);margin:0 -16px 18px;padding:12px 16px}
h1{font-size:22px;margin:0 0 2px;line-height:1.25}
h2{font-size:15px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:34px 0 10px}
.meta{display:flex;flex-wrap:wrap;gap:6px 14px;color:var(--muted);font-size:13.5px}
.meta b{color:var(--text)}
.bar{display:flex;align-items:center;gap:12px;margin-top:10px;flex-wrap:wrap}
.progress{flex:1;min-width:180px;height:10px;background:var(--panel2);border-radius:99px;overflow:hidden}
.progress i{display:block;height:100%;width:0;background:var(--accent2);transition:width .25s}
.pcount{font-weight:800;font-variant-numeric:tabular-nums}
button{font:inherit;font-weight:700;font-size:13.5px;background:var(--panel2);color:var(--text);border:1px solid var(--line);border-radius:9px;padding:7px 12px;cursor:pointer}
button:hover{border-color:var(--accent2)}
button.primary{background:var(--accent);border-color:var(--accent)}
button.ok{background:var(--ok);border-color:var(--ok);color:#06140c}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin:12px 0;scroll-margin-top:110px}
.card.focus{outline:2px solid var(--accent2);outline-offset:2px}
.card.done{opacity:.55}
.chead{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;margin-bottom:8px}
.cid{font-weight:900;font-size:20px;letter-spacing:.02em}
.chip{font-size:12px;font-weight:700;border:1px solid var(--line);border-radius:99px;padding:2px 9px;color:var(--muted)}
.badge{font-size:12.5px;font-weight:800;border-radius:7px;padding:3px 9px;background:var(--accent);color:#fff;letter-spacing:.03em}
.badge.ing{background:#6b2bd9}.badge.code{background:#333}
.dur{margin-left:auto;font-size:13px;color:var(--muted)}
.dur b{color:var(--text);font-size:15px}
.why{color:var(--muted);font-size:13px;margin:-2px 0 8px}
.vo{background:var(--panel2);border-left:3px solid var(--accent2);border-radius:8px;padding:8px 10px;margin:8px 0;font-size:14px}
.vo .k{color:var(--muted);font-size:12px;margin-right:6px}
.kt{display:inline-block;font-weight:800;font-size:12px;border-radius:6px;padding:1px 7px;margin:2px 4px 2px 0;background:#26262c}
.step{display:grid;grid-template-columns:34px minmax(0,1fr);gap:4px 10px;margin:12px 0 0}
.step>*{min-width:0}.wrap{overflow-wrap:anywhere}
.num{width:28px;height:28px;border-radius:50%;background:var(--panel2);border:1px solid var(--line);display:grid;place-items:center;font-weight:900}
.step.is-done .num{background:var(--ok);color:#06140c;border-color:var(--ok)}
.stitle{font-weight:800}
.sub{color:var(--muted);font-size:13px}
.file{font-family:var(--mono);font-size:12.5px;color:#9fb6ff;background:#141a33;border-radius:6px;padding:1px 6px}
pre{grid-column:2;white-space:pre-wrap;word-break:break-word;margin:6px 0 0;background:#0f0f12;border:1px solid var(--line);border-radius:10px;padding:10px 12px;font:12.8px/1.5 var(--mono);max-height:260px;overflow:auto}
.row{grid-column:2;display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:6px}
.how{grid-column:2;font-size:13px;color:var(--muted)}
.how b{color:var(--text)}
label.chk{display:inline-flex;gap:7px;align-items:center;font-weight:700;cursor:pointer}
label.chk input{width:18px;height:18px;accent-color:var(--ok)}
.issues li{margin:3px 0}.e{color:var(--err)}.w{color:var(--warn)}
.ok-t{color:var(--ok)}.warn-t{color:var(--warn)}
details summary{cursor:pointer;color:var(--muted);font-weight:700}
.keys{font-size:12.5px;color:var(--muted)}.keys kbd{font:12px var(--mono);border:1px solid var(--line);border-bottom-width:2px;border-radius:5px;padding:0 5px;color:var(--text)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px}
@media (max-width:560px){.dur{margin-left:0}.step{grid-template-columns:28px minmax(0,1fr)}.progress{min-width:120px}}
"""

JS = r"""
(function(){
const KEY='flowboard:'+document.body.dataset.slug;
let st={};try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){st={}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}}
function textOf(id){const el=document.getElementById(id);return el?el.innerText:''}
function flash(btn){if(!btn)return;btn.classList.add('ok');const o=btn.dataset.label||btn.innerText;btn.dataset.label=o;btn.innerText='Đã copy ✓';setTimeout(()=>{btn.classList.remove('ok');btn.innerText=o},1200)}
function fallback(t){const a=document.createElement('textarea');a.value=t;a.style.position='fixed';a.style.opacity='0';document.body.appendChild(a);a.select();let ok=false;try{ok=document.execCommand('copy')}catch(e){}a.remove();return ok}
window.copyText=function(t,btn){
  window.__lastCopy=t;
  const done=()=>flash(btn);
  try{if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(done,()=>{fallback(t);done()});return}}catch(e){}
  fallback(t);done();
};
function sceneText(card){
  const head='# '+card.dataset.shot+' · '+((card.querySelector('.badge')||{}).innerText||'')+' · '+((card.querySelector('.dur')||{}).innerText||'');
  return head+'\n\n'+Array.from(card.querySelectorAll('[data-part]')).map(el=>'### '+el.dataset.part+'\n'+el.innerText).join('\n\n');
}
document.addEventListener('click',e=>{
  const b=e.target.closest('button[data-copy],button[data-copy-scene],button[data-copy-text]');if(!b)return;
  if(b.dataset.copy)copyText(textOf(b.dataset.copy),b);
  else if(b.dataset.copyText)copyText(b.dataset.copyText,b);
  else copyText(sceneText(document.getElementById(b.dataset.copyScene)),b);
});
const cards=Array.from(document.querySelectorAll('.card[data-shot]'));
function refresh(){
  let n=0;cards.forEach(c=>{const box=c.querySelector('input.done');const d=box&&box.checked;c.classList.toggle('done',!!d);if(d)n++});
  const t=cards.length;document.querySelector('.pcount').textContent=n+'/'+t+' clip';
  document.querySelector('.progress i').style.width=(t?100*n/t:0)+'%';
}
cards.forEach(c=>{const box=c.querySelector('input.done');if(!box)return;const k=c.dataset.shot;
  if(box.dataset.present==='1')box.checked=true;else if(st[k])box.checked=true;
  box.addEventListener('change',()=>{st[k]=box.checked;save();refresh()})});
refresh();
let cur=-1;
function focusCard(i){if(!cards.length)return;cur=Math.max(0,Math.min(cards.length-1,i));cards.forEach(c=>c.classList.remove('focus'));
  const c=cards[cur];c.classList.add('focus');c.scrollIntoView({block:'start',behavior:'instant'in window?'instant':'auto'});}
document.addEventListener('keydown',e=>{
  const el=e.target;if((el&&el.matches&&el.matches('input,textarea'))||e.ctrlKey||e.metaKey||e.altKey)return;
  const k=e.key.toLowerCase();
  if(k==='j'){focusCard(cur+1);e.preventDefault()}
  else if(k==='k'){focusCard(cur-1);e.preventDefault()}
  else if(k==='c'&&cur>=0){const b=cards[cur].querySelector('button.copy-video');if(b){b.click();e.preventDefault()}}
});
window.__board={cards,focusCard,get cur(){return cur}};
if(new URLSearchParams(location.search).get('selftest')==='1'){
  const res={buttons:0,ok:0,fail:[]};
  document.querySelectorAll('button[data-copy]').forEach(b=>{res.buttons++;b.click();
    const want=textOf(b.dataset.copy);if(window.__lastCopy===want&&want.length>0)res.ok++;else res.fail.push(b.dataset.copy)});
  document.querySelectorAll('button[data-copy-scene]').forEach(b=>{res.buttons++;b.click();
    const c=document.getElementById(b.dataset.copyScene);const txt=window.__lastCopy||'';
    if(txt.includes('### ③')&&txt.includes(c.dataset.shot))res.ok++;else res.fail.push('scene:'+b.dataset.copyScene)});
  const ev=k=>document.dispatchEvent(new KeyboardEvent('keydown',{key:k,bubbles:true}));
  ev('j');ev('j');const afterJ=window.__board.cur;ev('k');const afterK=window.__board.cur;
  window.__lastCopy='';ev('c');
  const cardC=cards[afterK];const vid=cardC&&cardC.querySelector('button.copy-video');
  res.keys={afterJ,afterK,cCopied:!!(vid&&window.__lastCopy===textOf(vid.dataset.copy))};
  res.pass=res.fail.length===0&&res.ok===res.buttons&&afterJ===1&&afterK===0&&res.keys.cCopied;
  const out=document.createElement('pre');out.id='selftest';out.textContent=JSON.stringify(res);document.body.appendChild(out);
  document.title=(res.pass?'SELFTEST PASS ':'SELFTEST FAIL ')+document.title;
}
})();
"""

MODE_CLASS = {"frames_start": "", "frames_start_end": "", "ingredients": "ing", "code": "code"}
CIRCLED = ["①", "②", "③", "④"]


def e(x):
    return html.escape(str(x if x is not None else ""))


class _Ids:
    def __init__(self):
        self.n = 0

    def __call__(self, prefix="p"):
        self.n += 1
        return f"{prefix}{self.n}"


def _exists(proj, rel):
    return bool(rel) and os.path.exists(os.path.join(proj, rel))


def _file(rel, ok=None):
    mark = "" if ok is None else (' <span class="ok-t">✓ đã có</span>' if ok else "")
    return f'<span class="file">{e(rel)}</span>{mark}'


def _pre(ids, text, part=None):
    pid = ids()
    attr = f' data-part="{e(part)}"' if part else ""
    return pid, f'<pre id="{pid}"{attr}>{e(text)}</pre>'


def _badge(s, sb):
    mode = s.get("mode_resolved")
    if mode == "ingredients":
        return f'<span class="badge ing">INGREDIENTS · {e(" + ".join(s.get("refs") or []))}</span>'
    return f'<span class="badge {MODE_CLASS.get(mode, "")}">{e(compiler.MODE_LABEL.get(mode, mode))}</span>'


def _onscreen(s):
    out = []
    for o in s.get("onscreen") or []:
        k = o.get("kind")
        if k == "counter":
            txt = f"{o.get('from', 0)}→{o.get('value')} {o.get('unit', '')}"
        else:
            txt = o.get("text", "")
        out.append(f'<span class="kt">{e(k)} @{o.get("t", 0):g}s: {e(txt)}</span>')
    return "".join(out)


def _card(sb, s, proj, ids, model, clip_map):
    sid = s["id"]
    mode = s.get("mode_resolved")
    refs = s.get("refs") or []
    gen = s.get("gen_sec")
    present = clip_map.get(sid) is not None
    head = (f'<div class="chead"><span class="cid">{e(sid)}</span><span class="chip">{e(s.get("beat"))}</span>'
            f'{_badge(s, sb)}<span class="dur">dùng <b>{s["target_sec"]:g}s</b>'
            + (f' · tạo trong Flow: <b>{gen}s</b>' if gen else "") + '</span></div>'
            f'<div class="why">{e(s.get("mode_reason", ""))}</div>')
    vo = ""
    fxs = ", ".join(f.get("text", "") for f in (s.get("text_fx") or []) if f.get("text"))
    if s.get("vo") or s.get("onscreen") or fxs:
        vo = ('<div class="vo">' + (f'<span class="k">VO</span>{e(s.get("vo"))}<br>' if s.get("vo") else "")
              + (f'<span class="k">Chữ</span>{e(fxs)}' if fxs else (f'<span class="k">Chữ</span>{_onscreen(s)}'
                                                                   if s.get("onscreen") else "")) + '</div>')
    steps = []
    if mode == "code":
        c = s.get("code") or {}
        what = (f'Cảnh engine <b>{e(c["scene"])}</b> (three.js, cùng palette/nét với shot Flow) · tham số '
                f'{e(", ".join(f"{k}={v}" for k, v in (c.get("params") or {}).items()) or "mặc định")}') \
            if c.get("scene") else "Đồ hoạ 2D vẽ bằng code."
        steps.append('<div class="step is-done"><div class="num">✓</div><div><div class="stitle">Dựng bằng code — '
                     f'không cần Flow</div><div class="sub">{what}</div></div></div>')
        return (f'<section class="card" id="card-{e(sid)}" data-shot="{e(sid)}">{head}{vo}{"".join(steps)}</section>')
    # ① start
    sf = s["start_frame"]
    start_ok = _exists(proj, sf["file"])
    ref_txt = (f'Khi tạo ảnh, đính kèm ảnh ref {", ".join(_file(f"refs/{r}.png", _exists(proj, f"refs/{r}.png")) for r in refs)}'
               f' vào {e(sb["flow"]["image_model"])} (Ingredients của ảnh). ') if refs else ""
    if mode == "ingredients":
        steps.append(f'<div class="step is-done"><div class="num">{CIRCLED[0]}</div><div><div class="stitle">Không cần ảnh Start</div>'
                     f'<div class="sub">Cảnh này dùng Ingredients: nhân vật lấy từ ảnh ref, bố cục để Flow tự do.</div></div></div>')
    elif sf.get("seed_from"):
        src = sf["seed_from"]
        steps.append(
            f'<div class="step{" is-done" if start_ok else ""}"><div class="num">{CIRCLED[0]}</div><div>'
            f'<div class="stitle">Ảnh Start: KHÔNG cần tự tạo — lấy từ clip {e(src)}</div>'
            f'<div class="sub">Cảnh này nối tiếp {e(src)}, nên ảnh mở đầu phải trùng khung cuối của {e(src)} '
            f'(tool bỏ đoạn cuối clip bị chậm dần). '
            + (f"Đã có sẵn: {_file(sf['file'], True)} — dùng ảnh này làm Start ở bước ③." if start_ok else
               f"Cách làm: (1) làm xong {e(src)}, lưu vào clips/ · (2) chạy lại lệnh /video · "
               f"(3) tool tự tạo {_file(sf['file'])} → dùng làm Start ở bước ③.")
            + '</div></div></div>')
    else:
        pid, pre = _pre(ids, sf.get("prompt", ""), "① Ảnh Start")
        steps.append(
            f'<div class="step{" is-done" if start_ok else ""}"><div class="num">{CIRCLED[0]}</div><div>'
            f'<div class="stitle">Ảnh Start</div><div class="sub">{ref_txt}Tạo ảnh dọc 9:16, chọn bản đẹp nhất, lưu thành '
            f'{_file(sf["file"], start_ok)}</div></div>{pre}<div class="row"><button data-copy="{pid}">Copy prompt ảnh Start</button>'
            f'</div></div>')
    # ② end
    if mode == "frames_start_end":
        ef = s["end_frame"]
        end_ok = _exists(proj, ef["file"])
        pid, pre = _pre(ids, ef.get("prompt", ""), "② Ảnh End")
        steps.append(
            f'<div class="step{" is-done" if end_ok else ""}"><div class="num">{CIRCLED[1]}</div><div>'
            f'<div class="stitle">Ảnh End</div><div class="sub">{ref_txt}Mẹo: tạo từ ảnh Start (đính kèm ảnh Start làm ref) để '
            f'giữ đúng bố cục. Lưu thành {_file(ef["file"], end_ok)}</div></div>{pre}'
            f'<div class="row"><button data-copy="{pid}">Copy prompt ảnh End</button></div></div>')
    # ③ video
    pid, pre = _pre(ids, s.get("video_prompt", ""), "③ Video")
    if mode == "ingredients":
        how = (f'Flow → <b>Video</b> → <b>Ingredients</b>: đính kèm {", ".join(_file(f"refs/{r}.png") for r in refs)}')
    elif mode == "frames_start_end":
        how = (f'Flow → <b>Video</b> → <b>Frames</b>: Start = {_file(sf["file"])}, End = {_file(s["end_frame"]["file"])}')
    else:
        how = f'Flow → <b>Video</b> → <b>Frames</b>: Start = {_file(sf["file"])} (để trống End)'
    how += f' · model <b>{e(model)}</b> · độ dài <b>{gen}s</b> · <b>9:16</b>'
    steps.append(
        f'<div class="step{" is-done" if present else ""}"><div class="num">{CIRCLED[2]}</div><div>'
        f'<div class="stitle">Video</div><div class="how">{how}</div></div>{pre}'
        f'<div class="row"><button class="primary copy-video" data-copy="{pid}">Copy prompt video</button>'
        f'<button data-copy-scene="card-{e(sid)}">Copy cả cảnh</button></div></div>')
    # ④ save
    steps.append(
        f'<div class="step{" is-done" if present else ""}"><div class="num">{CIRCLED[3]}</div><div>'
        f'<div class="stitle">Tải về, đặt tên {_file(s["clip_file"].split("/")[-1])} trong {_file("clips/")}</div>'
        f'<div class="sub">Để nguyên tên Flow đặt cũng được: tool map theo thứ tự tải về và in bảng để bạn xác nhận. '
        f'Tiếng của Flow sẽ bị bỏ khi ghép.</div>'
        f'<div class="row"><label class="chk"><input type="checkbox" class="done" data-present="{1 if present else 0}"> '
        f'Đã xong{" (đã thấy file)" if present else ""}</label></div></div></div>')
    return f'<section class="card" id="card-{e(sid)}" data-shot="{e(sid)}">{head}{vo}{"".join(steps)}</section>'


def _issues(issues):
    if not issues:
        return '<p class="ok-t">✓ Linter: không có lỗi.</p>'
    items = "".join(f'<li class="{"e" if i["level"] == "error" else "w"}">[{e(i["where"])}] {e(i["msg"])}</li>'
                    for i in issues if i["level"] != "info")
    n_err = sum(i["level"] == "error" for i in issues)
    return (f'<details{" open" if n_err else ""}><summary>Linter: {n_err} lỗi, {len(issues) - n_err} cảnh báo</summary>'
            f'<ul class="issues">{items}</ul></details>')


def build(sb, proj, issues=None, clip_map=None, out_path=None):
    """sb: storyboard đã compile. clip_map: {shot_id: path} clip đã có (từ ingest.scan)."""
    ids = _Ids()
    clip_map = clip_map or {}
    issues = issues if issues is not None else linter.lint(sb)
    cfg = channel()
    name, caps = compiler.video_caps(sb)
    flow_shots = [s for s in sb["shots"] if s.get("mode_resolved") != "code"]
    total = sum(s["target_sec"] for s in sb["shots"])
    outro = cfg["outro"]["duration_sec"] if sb.get("outro", {}).get("enabled") else 0
    dep = (f' <span class="warn-t">(sẽ bị gỡ {e(caps.get("removal_date"))})</span>'
           if caps.get("status") == "deprecated" else "")
    sb_id = ids()
    style_pre = f'<pre id="{sb_id}" hidden>{e(compiler.style_bible(sb))}</pre>'
    # Ingredients
    ing_html = []
    for ing in sb.get("ingredients", []):
        ok = _exists(proj, ing["file"])
        pid, pre = _pre(ids, ing.get("image_prompt", ""))
        ing_html.append(
            f'<div class="card"><div class="chead"><span class="cid">{e(ing["id"])}</span>'
            f'<span class="chip">ảnh 1:1 · {e(sb["flow"]["image_model"])}</span></div>'
            f'<div class="sub">Lưu thành {_file(ing["file"], ok)} — dùng làm ref khi tạo ảnh Start/End.</div>'
            f'<div class="step"><div class="num">✦</div><div class="stitle">Prompt ảnh ref</div>{pre}'
            f'<div class="row"><button data-copy="{pid}">Copy prompt {e(ing["id"])}</button></div></div></div>')
    # Tạo 1 lần
    once = []
    bg_rel = cfg["outro"]["bg_clip"]
    if not os.path.exists(os.path.join(ROOT, bg_rel)):
        pid, pre = _pre(ids, sb.get("outro", {}).get("bg_prompt", ""))
        once.append(
            f'<div class="card"><div class="chead"><span class="cid">Nền outro</span><span class="chip">tuỳ chọn · 1 lần cho cả kênh</span>'
            f'</div><div class="sub">Video 4s, chế độ Frames hoặc text-free tuỳ ý. Lưu thành {_file(bg_rel)} (thư mục gốc tool). '
            f'Không có file này thì outro dùng nền đen vẽ bằng code.</div><div class="step"><div class="num">✦</div>'
            f'<div class="stitle">Prompt video nền outro</div>{pre}<div class="row"><button data-copy="{pid}">Copy prompt outro</button>'
            f'</div></div></div>')
    # Thumbnails
    th = []
    for v in sb.get("thumbnail", {}).get("variants", []):
        p1, pre1 = _pre(ids, v.get("bg_prompt", ""))
        p2, pre2 = _pre(ids, v.get("bg_prompt_vertical", ""))
        f1 = v["file"]
        f2 = f1.replace(".png", "_v.png")
        label = v.get("text") or v.get("number") or ""
        th.append(
            f'<div class="card"><div class="chead"><span class="cid">{e(v["id"])}</span><span class="chip">{e(v["archetype"])}</span>'
            f'<span class="dur">chữ (code thêm sau): <b>{e(label)}</b></span></div>'
            f'<div class="grid2"><div><div class="sub">Nền 16:9 → {_file(f1, _exists(proj, f1))}</div>{pre1}'
            f'<div class="row"><button data-copy="{p1}">Copy nền 16:9</button></div></div>'
            f'<div><div class="sub">Nền 9:16 → {_file(f2, _exists(proj, f2))}</div>{pre2}'
            f'<div class="row"><button data-copy="{p2}">Copy nền 9:16</button></div></div></div></div>')
    # VO
    vo_lines = [s["vo"].strip() for s in sb["shots"] if s.get("vo", "").strip()]
    vo_html = ""
    if vo_lines:
        pid, pre = _pre(ids, "\n\n".join(vo_lines))
        syl = sum(syllables(x) for x in vo_lines)
        vo_html = (f'<h2>Lời đọc (ElevenLabs)</h2><div class="card"><div class="sub">{len(vo_lines)} câu · {syl} âm tiết. '
                   f'Giữ dòng trống giữa các câu (tool tách câu theo khoảng lặng). Lưu thành {_file("audio/vo.mp3", _exists(proj, "audio/vo.mp3"))} '
                   f'— hoặc từng câu {_file("audio/vo_01.mp3")}, {_file("vo_02.mp3")}… Tool tự cắt lặng và tăng tốc '
                   f'{cfg["vo"]["speed"]}×.</div><div class="step"><div class="num">✦</div><div class="stitle">Kịch bản đọc</div>{pre}'
                   f'<div class="row"><button data-copy="{pid}">Copy lời đọc</button></div></div></div>')
    cards = "".join(_card(sb, s, proj, ids, name, clip_map) for s in sb["shots"])
    slug = sb.get("slug") or os.path.basename(proj)
    doc = (
        '<!doctype html><html lang="vi"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{e(sb.get("title") or slug)} · Flow</title><style>{CSS}</style></head>'
        f'<body data-slug="{e(slug)}"><div class="wrap">'
        f'<header class="top"><h1>{e(sb.get("title") or sb.get("topic"))}</h1>'
        f'<div class="meta"><span>Thời lượng <b>{total:.1f}s</b> + outro {outro:g}s</span>'
        f'<span>Video: <b>{e(name)}</b>{dep}</span><span>Ảnh: <b>{e(sb["flow"]["image_model"])}</b></span>'
        f'<span>{len(flow_shots)} clip Flow · {len(sb.get("ingredients", []))} ingredient</span></div>'
        f'<div class="bar"><div class="progress"><i></i></div><span class="pcount">0/{len(flow_shots)} clip</span>'
        f'<button data-copy="{sb_id}">Copy style bible</button></div>'
        f'<div class="keys" style="margin-top:6px"><kbd>J</kbd>/<kbd>K</kbd> chuyển cảnh · <kbd>C</kbd> copy prompt video của cảnh đang chọn</div>'
        f'</header>{style_pre}'
        f'<p class="sub">Flow không có nút tắt tiếng: prompt đã có block im lặng, và tool <b>luôn bỏ tiếng</b> clip khi ghép. '
        f'Frames và Ingredients là hai chế độ riêng: ảnh ref dùng ở bước tạo <b>ảnh</b>, ảnh Start/End dùng ở bước tạo <b>video</b>.</p>'
        f'{_issues(issues)}'
        + (f'<h2>Bước 0 · Ingredients: tạo trước</h2>{"".join(ing_html)}' if ing_html else "")
        + f'<h2>Các cảnh ({len(sb["shots"])})</h2>{cards}'
        + vo_html
        + (f'<h2>Tạo 1 lần</h2>{"".join(once)}' if once else "")
        + (f'<h2>Thumbnail: ảnh nền (không chữ)</h2><p class="sub">Chữ, mũi tên, vòng khoanh do tool vẽ bằng code. '
           f'Chưa có nền thì tool lấy frame từ clip.</p>{"".join(th)}' if th else "")
        + f'<h2>Xong?</h2><div class="card"><div class="sub">Thả clip vào {_file(f"projects/{slug}/clips/")} rồi chạy lại '
        f'<span class="file">/video {e(slug)}</span> (hoặc <span class="file">python studio.py video {e(slug)}</span>).</div></div>'
        f'</div><script>{JS}</script></body></html>')
    out_path = out_path or os.path.join(proj, "scripts.html")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)
    return out_path


def export_text(sb, path):
    """Bản .txt toàn bộ prompt (để dán chỗ khác / soát diff)."""
    out = ["STYLE BIBLE", compiler.style_bible(sb), ""]
    for ing in sb.get("ingredients", []):
        out += [f"===== {ing['id']} → {ing['file']} =====", ing.get("image_prompt", ""), ""]
    for s in sb["shots"]:
        out.append(f"===== {s['id']} · {s.get('mode_resolved')} · {s.get('gen_sec')}s =====")
        if s["start_frame"].get("prompt"):
            out += ["--- ① Ảnh Start → " + s["start_frame"]["file"], s["start_frame"]["prompt"]]
        if s["end_frame"].get("prompt"):
            out += ["--- ② Ảnh End → " + s["end_frame"]["file"], s["end_frame"]["prompt"]]
        if s.get("video_prompt"):
            out += ["--- ③ Video → " + s["clip_file"], s["video_prompt"]]
        out.append("")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    return path


def write_json_prompts(sb, path):
    data = {s["id"]: {"mode": s.get("mode_resolved"), "gen_sec": s.get("gen_sec"),
                      "start": s["start_frame"].get("prompt"), "end": s["end_frame"].get("prompt"),
                      "video": s.get("video_prompt")} for s in sb["shots"]}
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path
