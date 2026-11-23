// 5 · Edit — xem trước tại chỗ + timeline (video shot · chữ text_fx · VO · nhạc · SFX) + inspector bên phải.
// Space/J/K/L/←/→ như NLE; I/O đặt vùng; "Trim theo I/O" ghi điểm vào/ra tay cho shot Flow rồi dựng lại.
// Hành động chính: Render lại shot đang chọn.
import { h, clear } from '../core/dom.js';
import { projectFile } from '../core/api.js';
import * as keys from '../core/keys.js';
import * as store from '../core/store.js';
import { tc } from '../core/format.js';
import { Btn, St, Split, Empty, confirm, Field } from '../ui/kit.js';
import { Player, Timeline } from '../ui/media.js';

export async function render(ctx) {
  const w = ctx.ws;
  const tl = w.timeline || {};
  const segs = tl.segments || [];
  if (!w.has_final || !segs.length) {
    return h('div.page', Empty('Chưa có bản dựng', 'Edit cần out/final.mp4 + timeline. Chạy pipeline (hoặc chạy thử với dữ liệu giả) trước.', [
      Btn('Chạy tiếp', { kind: 'primary', ico: 'play', onClick: () => ctx.run('video', { target: ctx.slug, yes: true, dry_run: !!ctx.ws.dry_run }) }),
      Btn('Chạy thử (dữ liệu giả)', { onClick: () => ctx.run('video', { target: ctx.slug, dry_run: true, yes: true }) })]));
  }
  const fps = tl.fps || 30;
  const by = Object.fromEntries((w.shots_detail || []).map((s) => [s.id, s]));
  const duration = tl.duration || segs.reduce((a, s) => Math.max(a, (s.start_f + s.n) / fps), 0);
  let sel = store.get(`edit.sel.${ctx.slug}`) || segs[0].sid;
  const player = Player(projectFile(ctx.slug, 'out/final.mp4', w.updated), {});
  const stem = (n) => (w.stems || []).find((p) => p.endsWith(`${n}.wav`));
  const lanes = [
    { name: 'Video', selectable: true, items: segs.map((s) => ({ id: s.sid, start: s.start_f / fps, end: (s.start_f + s.n) / fps, label: s.sid,
      cls: (by[s.sid] && by[s.sid].engine) || (s.sid === 'OUTRO' ? 'html' : ''), title: `${s.sid} · ${(s.n / fps).toFixed(2)}s · ${s.transition}` })) },
    { name: 'Chữ', selectable: true, items: (w.captions || []).map((c, i) => ({ id: `T${i}`, start: c.start, end: c.end, label: c.text, cls: 'text', title: `${c.text} · ${c.kind} · ${c.shot}` })) },
    { name: 'VO', kind: 'wave', url: stem('voice') ? projectFile(ctx.slug, stem('voice')) : (w.vo.takes[0] ? projectFile(ctx.slug, w.vo.takes[0].file) : null), color: '#a8a8a8' },
    { name: 'Nhạc', kind: 'wave', url: stem('music') ? projectFile(ctx.slug, stem('music')) : null, color: '#6f6f6f' },
    { name: 'SFX', kind: 'wave', url: stem('sfx') ? projectFile(ctx.slug, stem('sfx')) : null, color: '#d6a01e' },
  ];
  const insp = h('div');
  const timeline = Timeline({ duration, lanes, selected: sel, onSelect: (id) => select(id), onSeek: (t) => player.seek(t) });
  player.onTime((t) => {
    timeline.at(t);
    const s = segs.find((x) => t >= x.start_f / fps && t < (x.start_f + x.n) / fps);
    if (s && player.video.paused === false && s.sid !== sel && store.get('edit.follow', true)) select(s.sid, false);
  });
  const select = (id, seek = true) => {
    sel = id; store.set(`edit.sel.${ctx.slug}`, id);
    timeline.select(id);
    drawInsp();
    const s = segs.find((x) => x.sid === id);
    if (seek && s) player.seek(s.start_f / fps);
  };
  const rerender = async (id) => {
    if (!await confirm(`Render lại ${id}?`, 'Chỉ dựng lại shot này, rồi ghép lại video + QA + version mới.', { ok: 'Render lại' })) return;
    ctx.run('rerender_shot', { target: ctx.slug, shot: id }, `Đang render lại ${id}`);
  };
  const drawInsp = () => {
    clear(insp);
    if (sel && sel.startsWith('T')) {
      const c = (w.captions || [])[+sel.slice(1)];
      if (!c) return;
      insp.append(h('section.section', h('div.row', h('h2', 'Chữ'), St(c.kind, '')), h('p', { style: { margin: '8px 0', fontSize: '16px' } }, c.text),
        h('dl.gridform', h('dt', 'Shot'), h('dd.mono', c.shot), h('dt', 'Vào'), h('dd.mono', tc(c.start)), h('dt', 'Ra'), h('dd.mono', tc(c.end)),
          h('dt', 'Neo'), h('dd.mono', c.anchor || '—'), h('dt', 'Lớp'), h('dd', c.layer || '—'), h('dt', 'Hiệu ứng'), h('dd', (c.behavior || []).join(', ') || '—'),
          h('dt', 'Đồng bộ'), h('dd', c.sync || '—'))),
      h('section.section.dim', 'Chữ được sinh từ storyboard (text_fx) — sửa nội dung ở Script/Board rồi dựng lại.'));
      return;
    }
    const seg = segs.find((x) => x.sid === sel);
    const s = by[sel] || {};
    const tr = (w.trims || {})[sel];
    const io = player.inOut();
    const tIn = h('input.input.mono', { type: 'number', step: '0.01', min: 0, value: tr ? tr.in : '', 'aria-label': 'Điểm vào trong clip (giây)' });
    const tOut = h('input.input.mono', { type: 'number', step: '0.01', min: 0, value: tr ? tr.out : '', 'aria-label': 'Điểm ra trong clip (giây)' });
    insp.append(h('section.section', h('div.row', h('h2.mono', sel), s.engine ? h(`span.chip.eng.${s.engine}`, s.engine) : null, h('span.grow'), seg ? h('span.mono.dim', `${seg.n} frame`) : null),
      h('dl.gridform', { style: { marginTop: '8px' } }, h('dt', 'Bắt đầu'), h('dd.mono', seg ? tc(seg.start_f / fps) : '—'), h('dt', 'Dài'), h('dd.mono', seg ? `${(seg.n / fps).toFixed(2)}s` : '—'),
        h('dt', 'Chuyển cảnh'), h('dd', seg ? seg.transition : '—'), h('dt', 'Punch-in'), h('dd', seg && seg.punches && seg.punches.length ? `${seg.punches.length}` : '—'),
        h('dt', 'Lời đọc'), h('dd', s.vo || '—'))),
    s.engine === 'flow' ? h('section.section', h('div.label', 'Trim trong clip Flow'),
      tr ? h('p.dim', { style: { margin: '4px 0 8px' } }, `Hiện: ${tr.in}–${tr.out}s · tốc độ ×${tr.speed} · ${tr.how}`) : null,
      h('div.row', Field('Vào (s)', tIn), Field('Ra (s)', tOut)),
      h('div.row', { style: { marginTop: '8px' } },
        Btn('Lấy từ I/O', { size: 'sm', title: 'Dùng điểm I/O trên player (quy đổi về giây trong clip)', onClick: () => {
          if (!seg || io.in === null || io.out === null || !tr) return;
          const sp = tr.speed || 1, base = seg.start_f / fps;
          tIn.value = (tr.in + (io.in - base) * sp).toFixed(2); tOut.value = (tr.in + (io.out - base) * sp).toFixed(2);
        } }),
        Btn('Trim theo số này', { kind: 'primary', size: 'sm', onClick: async () => {
          const a = parseFloat(tIn.value), b = parseFloat(tOut.value);
          if (!(a >= 0 && b > a)) return;
          if (!await confirm(`Trim ${sel} ${a.toFixed(2)}–${b.toFixed(2)}s?`, 'Ghi điểm vào/ra tay vào storyboard rồi dựng lại từ stage trim.', { ok: 'Trim + dựng lại' })) return;
          ctx.run('trim', { target: ctx.slug, shot: sel, in: a, out: b }, `Đang trim ${sel}`);
        } }),
        tr && tr.how === 'manual' ? Btn('Về auto-trim', { size: 'sm', kind: 'ghost', onClick: () => ctx.run('trim', { target: ctx.slug, shot: sel, auto: true }) }) : null)) : null,
    h('section.section.row.wrap', sel !== 'OUTRO' ? Btn('Render lại shot', { kind: 'primary', ico: 'refresh', kbd: 'R', onClick: () => rerender(sel) }) : null,
      Btn('Mở ở Board', { onClick: () => ctx.go('board') })));
  };
  keys.register('page', 'R', () => sel && !sel.startsWith('T') && sel !== 'OUTRO' && rerender(sel), 'Render lại shot đang chọn');
  keys.register('page', 'Ctrl+ArrowRight', () => { const i = segs.findIndex((x) => x.sid === sel); if (i < segs.length - 1) select(segs[i + 1].sid); }, 'Shot kế');
  keys.register('page', 'Ctrl+ArrowLeft', () => { const i = segs.findIndex((x) => x.sid === sel); if (i > 0) select(segs[i - 1].sid); }, 'Shot trước');
  setTimeout(() => select(sel), 50);
  const left = h('div', { style: { display: 'flex', flexDirection: 'column', height: '100%' } }, player.el);
  return h('div.page.fill',
    h('div.pagehead', h('h1', 'Edit'), h('span.sub', `${segs.length} đoạn · ${tc(duration)} · ${fps} fps`), h('span.grow'),
      h('span.dim', 'I/O đặt vùng · Ctrl+←/→ đổi shot')),
    h('div', { style: { flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' } },
      Split([left, insp], { id: 'edit', sizes: [null, 340] }), timeline));
}
