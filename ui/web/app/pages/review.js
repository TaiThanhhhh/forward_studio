// 6 · Review — player lớn, comment gắn timecode + vẽ khoanh lên frame, so 2 version (wipe A/B / cạnh nhau),
// trạng thái Approved / Changes requested. Comment lưu ở projects/<slug>/review/review.json (tự lưu, xoá có hoàn tác).
// Hành động chính: Thêm comment (N) — rồi Duyệt.
import { h, clear } from '../core/dom.js';
import { api, projectFile } from '../core/api.js';
import * as keys from '../core/keys.js';
import * as store from '../core/store.js';
import * as undo from '../core/undo.js';
import { tc, ago } from '../core/format.js';
import { Btn, St, Split, Empty, Seg, toast } from '../ui/kit.js';
import { Player } from '../ui/media.js';

export async function render(ctx) {
  const w = ctx.ws;
  if (!w.has_final) {
    return h('div.page', Empty('Chưa có bản render để duyệt', 'Review mở khi có out/final.mp4 (mỗi lần qua cổng QA sinh một version vNNN).', [
      Btn('Chạy tiếp', { kind: 'primary', ico: 'play', onClick: () => ctx.run('video', { target: ctx.slug, yes: true, dry_run: !!ctx.ws.dry_run }) })]));
  }
  const versions = [{ id: 'latest', file: 'out/final.mp4', label: `mới nhất${w.manifest && w.manifest.version ? ' · ' + w.manifest.version : ''}` },
    ...(w.versions || []).slice().reverse().map((v) => ({ id: v.id, file: v.file, label: `${v.id}${v.verdict ? ' · QA ' + v.verdict : ''}` }))];
  let review = w.review || { status: 'pending', comments: [] };
  let verA = 'latest', verB = versions[1] ? versions[1].id : null;
  let mode = store.get('review.mode', 'single');
  const fileOf = (id) => (versions.find((v) => v.id === id) || versions[0]).file;
  const player = Player(projectFile(ctx.slug, fileOf(verA), w.updated), { ink: true });
  const listEl = h('ul.list', { 'aria-label': 'Comment' });
  const draftKey = `review.draft.${ctx.slug}`;
  const text = h('textarea.textarea', { rows: 3, placeholder: 'Ghi chú tại timecode hiện tại… (Ctrl+Enter gửi)', 'aria-label': 'Nội dung comment', value: store.get(draftKey, '') });
  text.value = store.get(draftKey, '');
  text.addEventListener('input', () => store.set(draftKey, text.value));
  const tcLabel = h('span.mono', tc(0));
  player.onTime((t) => { tcLabel.textContent = tc(t); });
  let drawing = false;
  const drawBtn = Btn('Vẽ khoanh', { size: 'sm', ico: 'pen', kbd: 'D', aria: { 'aria-pressed': 'false' }, onClick: () => setDraw(!drawing) });
  const setDraw = (v) => { drawing = v; player.ink.on(v); drawBtn.setAttribute('aria-pressed', String(v)); drawBtn.classList.toggle('primary', v); };
  const statusEl = h('div.row');

  const op = async (body) => { review = await api.reviewOp(ctx.slug, body); drawList(); drawStatus(); return review; };
  const add = async () => {
    const t = text.value.trim();
    if (!t) { text.focus(); return; }
    const drawing0 = player.ink.take();
    try {
      await op({ op: 'add', t: player.t(), text: t, drawing: drawing0, version: verA });
      text.value = ''; store.set(draftKey, ''); setDraw(false);
      toast(`Đã thêm comment tại ${tc(player.t())}`, { kind: 'ok' });
    } catch (e) { toast(e.message, { kind: 'err' }); }
  };
  const del = async (c) => {
    await op({ op: 'delete', id: c.id });
    const act = { label: `Xoá comment ${tc(c.t)}`, undo: () => op({ op: 'restore', id: c.id }), redo: () => op({ op: 'delete', id: c.id }) };
    undo.push(act);
    toast('Đã xoá comment', { action: () => undo.undo(), actionLabel: 'Hoàn tác' });
  };
  const drawList = () => {
    clear(listEl);
    const cs = review.comments || [];
    player.setMarkers(cs.map((c) => ({ t: c.t, done: c.resolved })));
    if (!cs.length) listEl.append(h('li', h('span.dim', 'Chưa có comment. Dừng ở frame cần sửa, gõ ghi chú (có thể vẽ khoanh), Ctrl+Enter.')));
    for (const c of cs) {
      listEl.append(h('li.clickable', { tabindex: 0, on: { click: (e) => { if (e.target.closest('button')) return; player.seek(c.t); player.ink.show(c.drawing); }, keydown: (e) => e.key === 'Enter' && player.seek(c.t) } },
        h('div.col.grow', { style: { gap: '2px' } },
          h('div.row', h('span.mono', tc(c.t)), c.drawing && c.drawing.length ? h('span.chip', 'có khoanh') : null, h('span.dim', c.version), c.resolved ? St('đã xử lý', 'ok') : null),
          h('span', { style: { textDecoration: c.resolved ? 'line-through' : 'none', color: c.resolved ? 'var(--t3)' : 'var(--t1)' } }, c.text)),
        Btn('', { size: 'sm', kind: 'ghost', ico: 'check', title: c.resolved ? 'Mở lại' : 'Đánh dấu đã xử lý', onClick: () => op({ op: 'resolve', id: c.id }) }),
        Btn('', { size: 'sm', kind: 'ghost', ico: 'x', title: 'Xoá (có hoàn tác)', onClick: () => del(c) })));
    }
  };
  const drawStatus = () => {
    clear(statusEl);
    const st = review.status || 'pending';
    statusEl.append(St(({ pending: 'Chờ duyệt', approved: 'Approved', changes: 'Changes requested' })[st], st === 'approved' ? 'ok' : st === 'changes' ? 'warn' : ''),
      Btn('Cần sửa', { size: 'sm', onClick: () => op({ op: 'status', status: 'changes', version: verA }) }),
      Btn('Duyệt', { kind: 'primary', size: 'sm', ico: 'check', onClick: () => op({ op: 'status', status: 'approved', version: verA }) }));
  };

  // ---- so sánh 2 version
  const compareHost = h('div', { style: { flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' } });
  let videoB = null;
  const buildStage = () => {
    clear(compareHost);
    if (mode === 'single' || !verB) { compareHost.append(player.el); videoB = null; return; }
    videoB = h('video', { src: projectFile(ctx.slug, fileOf(verB)), muted: true, preload: 'auto', 'aria-label': `Version ${verB}` });
    if (mode === 'side') {
      const stage = player.el.querySelector('.player');
      stage.style.gap = '2px';
      stage.append(h('div.player', { style: { height: '100%' } }, videoB));
      compareHost.append(player.el);
    } else {
      const stage = player.el.querySelector('.player');
      const wrap = h('div', { style: { position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', clipPath: 'inset(0 0 0 50%)' } }, videoB);
      videoB.style.maxHeight = '100%'; videoB.style.maxWidth = '100%';
      const bar = h('div.wipe', { style: { left: '50%' }, role: 'slider', 'aria-label': 'Vị trí wipe A/B', tabindex: 0, 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-valuenow': 50 });
      stage.append(wrap, bar);
      bar.addEventListener('pointerdown', (e) => {
        bar.setPointerCapture(e.pointerId);
        const mv = (ev) => { const r = stage.getBoundingClientRect(); const x = Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)); bar.style.left = `${x * 100}%`; wrap.style.clipPath = `inset(0 0 0 ${x * 100}%)`; };
        bar.addEventListener('pointermove', mv); bar.addEventListener('pointerup', () => bar.removeEventListener('pointermove', mv), { once: true });
      });
      compareHost.append(player.el);
    }
    const sync = () => { if (videoB && Math.abs(videoB.currentTime - player.video.currentTime) > 0.04) videoB.currentTime = player.video.currentTime; };
    player.video.addEventListener('play', () => videoB && videoB.play());
    player.video.addEventListener('pause', () => { if (videoB) { videoB.pause(); sync(); } });
    player.video.addEventListener('seeked', sync);
    player.video.addEventListener('ratechange', () => { if (videoB) videoB.playbackRate = player.video.playbackRate; });
  };
  const selA = h('select.select', { 'aria-label': 'Version A', style: { width: '180px' }, on: { change: () => { verA = selA.value; player.src(projectFile(ctx.slug, fileOf(verA))); } } },
    versions.map((v) => h('option', { value: v.id }, `A: ${v.label}`)));
  const selB = h('select.select', { 'aria-label': 'Version B', style: { width: '180px' }, disabled: versions.length < 2, on: { change: () => { verB = selB.value; buildStage(); } } },
    versions.slice(1).map((v) => h('option', { value: v.id }, `B: ${v.label}`)));
  const modeSeg = Seg([{ value: 'single', label: 'Một' }, { value: 'wipe', label: 'Wipe A/B' }, { value: 'side', label: 'Cạnh nhau' }], mode, (v) => { mode = v; store.set('review.mode', v); route(); }, { label: 'Chế độ so sánh' });
  const route = () => { location.reload(); };     // đổi chế độ: dựng lại trang gọn nhất (player giữ phím tắt riêng)

  keys.register('page', 'N', () => { player.video.pause(); text.focus(); return true; }, 'Comment mới tại timecode hiện tại');
  keys.register('page', 'D', () => setDraw(!drawing), 'Bật/tắt vẽ khoanh');
  keys.register('page', 'Ctrl+Enter', () => add(), 'Gửi comment', { inInput: true });
  keys.register('page', 'M', () => { const cs = review.comments || []; const t = player.t(); const nx = cs.find((c) => c.t > t + 0.05) || cs[0]; if (nx) { player.seek(nx.t); player.ink.show(nx.drawing); } }, 'Tới comment kế');
  drawList(); drawStatus(); buildStage();
  const side = h('div', { style: { display: 'flex', flexDirection: 'column', height: '100%' } },
    h('section.section', h('div.row', h('h2', 'Comment'), h('span.grow'), tcLabel), h('div.col', { style: { marginTop: '8px' } }, text,
      h('div.row', drawBtn, h('span.grow'), Btn('Thêm comment', { kind: 'primary', size: 'sm', ico: 'send', kbd: `${keys.mod}↵`, onClick: add })))),
    h('div', { style: { flex: 1, overflow: 'auto' } }, listEl),
    h('section.section.dim', { style: { borderTop: '1px solid var(--line)' } }, (review.history || []).slice(-3).reverse().map((x) => h('div', `${({ approved: 'Approved', changes: 'Changes requested', pending: 'Chờ duyệt' })[x.status]} · ${x.version} · ${x.at.slice(0, 16).replace('T', ' ')}`))));
  return h('div.page.fill',
    h('div.pagehead', h('h1', 'Review'), selA, modeSeg, mode !== 'single' ? selB : null, h('span.grow'), statusEl),
    Split([compareHost, side], { id: 'review', sizes: [null, 360] }));
}
