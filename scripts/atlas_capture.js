// 3D Style Atlas — chụp prompt toàn văn của cả 37 style (anh tự chạy, ~2 phút).
//
// 1. Mở https://www.futurepedia.io/resources/3d-style-atlas/view, tự qua bước xác minh nếu có.
// 2. F12 → Console → dán toàn bộ file này → Enter. Đừng bấm gì trong lúc chạy.
// 3. Xong sẽ tải về `atlas-capture.json` (mọi style: metadata + prompt nguyên văn).
// 4. python scripts/atlas_import.py --from "%USERPROFILE%\Downloads\atlas-capture.json"
//
// Cách làm: tạm bọc Clipboard.write/writeText của trang để đọc chuỗi mà nút "Copy prompt" của chính trang tạo ra
// (không gọi API riêng của site), mở từng thẻ theo bộ lọc nhóm, nghỉ ~1,5 s giữa các style, xong thì khôi phục hàm gốc.
// Tuỳ chọn modal để mặc định (No voiceover, Storyboard first bật, ô chủ đề trống).
(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const P = Clipboard.prototype;
  const orig = { wt: P.writeText, w: P.write };
  const got = {};
  let cur = null;
  const take = (t) => { if (cur && t) got[cur.number] = { ...cur, prompt_full: String(t) }; };
  P.writeText = function (t) { take(t); return Promise.resolve(); };
  P.write = async function (items) {
    for (const it of items) if (it.types.includes('text/plain')) take(await (await it.getType('text/plain')).text());
  };
  const dialog = () => [...document.querySelectorAll('[role=dialog]')].find((d) => /^#\d+\s*·/.test(d.innerText.trim()));
  const meta = () => {
    const dlg = dialog();
    if (!dlg) return null;
    const lines = dlg.innerText.replace(/\r/g, '').split('\n').map((s) => s.trim()).filter(Boolean);
    const m = lines[0].match(/^#(\d+)\s*·\s*(.+)$/);
    const get = (lab) => { const l = lines.find((x) => x.startsWith(lab + ':')); return l ? l.slice(lab.length + 1).trim() : ''; };
    const iShown = lines.findIndex((x) => x.startsWith('Shown here:'));
    return { number: m ? +m[1] : 0, category: m ? m[2] : '', name: lines[1] || '', tag: lines[2] || '',
      description: lines.slice(3, iShown > 0 ? iShown : 4).join(' '), shown_here: get('Shown here'), good_for: get('Good for'),
      source_url: location.origin + location.pathname, captured_at: new Date().toISOString(),
      capture_method: 'scripts/atlas_capture.js (DevTools, user-run): modal Copy prompt -> Clipboard hook; default options' };
  };
  const esc = () => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  try {
    const chips = [...document.querySelectorAll('button')].filter((b) => /^[A-Z][a-z ]+ \d+$/.test(b.innerText.trim()) && !/^All/.test(b.innerText.trim()));
    for (const chip of chips) {
      chip.click();
      await sleep(2500);
      const cards = [...document.querySelectorAll('[role=button]')].filter((e) => /#\d{2}\n/.test(e.innerText));
      for (const card of cards) {
        card.click();
        await sleep(1800);
        cur = meta();
        const dlg = dialog();
        const btn = dlg && [...dlg.querySelectorAll('button')].find((b) => b.innerText.trim() === 'Copy prompt');
        if (cur && btn) {
          btn.click();
          for (let k = 0; k < 25 && !got[cur.number]; k++) await sleep(200);
        }
        console.log(`[atlas] #${cur && cur.number} ${cur && cur.name}: ${got[cur && cur.number] ? got[cur.number].prompt_full.length + ' ký tự' : 'KHÔNG LẤY ĐƯỢC'}`);
        esc();
        await sleep(1500);
      }
    }
  } finally {
    P.writeText = orig.wt;
    P.write = orig.w;
    console.log('[atlas] đã khôi phục Clipboard.write/writeText gốc:', String(P.write).includes('[native code]'));
  }
  const list = Object.values(got).sort((a, b) => a.number - b.number);
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(list, null, 1)], { type: 'application/json' }));
  a.download = 'atlas-capture.json';
  a.click();
  console.log(`[atlas] xong: ${list.length}/37 style → atlas-capture.json`);
})();
