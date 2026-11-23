// #/_design — mọi token + component của UI (xem docs/DESIGN_SYSTEM.md). Dùng để soát khi sửa giao diện.
import { h } from '../core/dom.js';
import { Btn, St, Progress, Empty, Callout, Field, Seg, Table, toast, Panel } from '../ui/kit.js';

const COLORS = [['--s0', 'nền app'], ['--s1', 'panel'], ['--s2', 'ô nhập / hover'], ['--s3', 'nổi / chọn'], ['--s4', 'nhấn giữ'], ['--canvas', 'chỉ vùng video'],
  ['--line', 'viền'], ['--line-2', 'viền mạnh'], ['--t1', 'chữ chính'], ['--t2', 'chữ phụ'], ['--t3', 'chữ mờ'], ['--accent', 'accent (nút chính)'],
  ['--accent-text', 'chữ accent'], ['--ok', 'ok'], ['--warn', 'warn'], ['--err', 'error'], ['--proc', 'processing']];

export async function render() {
  const sw = (v) => h('div.col', { style: { gap: '4px', width: '120px' } }, h('div', { style: { height: '40px', background: `var(${v[0]})`, border: '1px solid var(--line-2)', borderRadius: 'var(--r2)' } }),
    h('span.mono', v[0]), h('span.dim', v[1]));
  const type = [['--fs-11', 'Nhãn / micro', '11px'], ['--fs-12', 'Phụ / mono số', '12px'], ['--fs-13', 'Cơ bản (UI)', '13px'], ['--fs-14', 'Nhấn', '14px'], ['--fs-16', 'Tiêu đề trang', '16px']];
  return h('div.page', h('div.pagehead', h('h1', 'Design system'), h('span.sub', 'tokens.css · components.css · ui/kit.js')),
    h('section.section', h('h2', 'Màu'), h('div.row.wrap', { style: { gap: '12px', marginTop: '8px' } }, COLORS.map(sw))),
    h('section.section', h('h2', 'Chữ'), h('div.col', { style: { marginTop: '8px' } }, type.map(([v, l, px]) => h('div.row', h('span.mono.dim', { style: { width: '90px' } }, px), h('span', { style: { fontSize: `var(${v})` } }, `${l} — Inter`))),
      h('div.row', h('span.mono.dim', { style: { width: '90px' } }, 'mono'), h('span.mono', '00:00:12:17 · C03 · 1080×1920 · −14.0 LUFS')))),
    h('section.section', h('h2', 'Nút (một nút chính mỗi màn hình)'), h('div.row.wrap', { style: { marginTop: '8px' } },
      Btn('Hành động chính', { kind: 'primary', ico: 'play', kbd: 'Ctrl↵' }), Btn('Phụ', { ico: 'copy' }), Btn('Ghost', { kind: 'ghost' }), Btn('Nguy hiểm', { kind: 'danger', ico: 'x' }),
      Btn('Nhỏ', { size: 'sm' }), Btn('Tắt', { disabled: true }), Btn('', { ico: 'help', title: 'Chỉ icon' }))),
    h('section.section', h('h2', 'Trạng thái'), h('div.row.wrap', { style: { marginTop: '8px' } }, St('Xanh', 'ok'), St('Vàng', 'warn'), St('Đỏ', 'err'), St('Đang chạy', 'running'), St('Trung tính', ''),
      h('span.chip', 'chip'), h('span.chip.eng.flow', 'Flow'), h('span.chip.eng.three', '3D'), h('span.chip.eng.html', '2D'), h('kbd', 'J'), h('kbd', 'K'), h('kbd', 'L'))),
    h('section.section', h('h2', 'Tiến độ (không spinner vô tận)'), h('div.col', { style: { width: '320px', marginTop: '8px' } }, Progress(0.42), Progress(1, { done: true }))),
    h('section.section', h('h2', 'Form'), h('div.row.wrap', { style: { marginTop: '8px', alignItems: 'flex-end' } },
      h('div', { style: { width: '240px' } }, Field('Ô nhập', h('input.input', { placeholder: 'placeholder' }), 'Gợi ý ngắn')),
      h('div', { style: { width: '200px' } }, Field('Chọn', h('select.select', h('option', 'Một'), h('option', 'Hai')))),
      Seg([{ value: 'a', label: 'Tự động' }, { value: 'b', label: 'Có Flow' }, { value: 'c', label: 'Toàn code' }], 'a', () => {}, { label: 'demo' }),
      h('label.check', h('input', { type: 'checkbox', checked: true }), 'Checkbox'))),
    h('section.section', h('h2', 'Callout / Empty / Toast'), h('div.col', { style: { marginTop: '8px', maxWidth: '640px' } },
      Callout('err', 'Cổng QA đỏ — chặn xuất', 'true peak: −0.4 dBTP (≤ −1)', [Btn('Sửa ở Edit', { size: 'sm' })]),
      Callout('warn', 'Thiếu 3 clip Flow', 'C04, C07, C09'), Callout('ok', 'Đã xuất 3 gói', 'Shorts · Reels · TikTok'),
      Empty('Trạng thái rỗng', 'Luôn kèm hành động kế tiếp cụ thể.', [Btn('Hành động kế', { kind: 'primary' })]),
      h('div', Btn('Hiện toast có Hoàn tác', { onClick: () => toast('Đã xoá comment', { action: () => toast('Đã hoàn tác', { kind: 'ok' }) }) })))),
    h('section.section', h('h2', 'Bảng (sắp xếp · lọc · chọn nhiều · ảo hoá > 200 hàng)'), h('div', { style: { height: '200px', marginTop: '8px', border: '1px solid var(--line)' } },
      Table({ rowKey: (r) => r.id, selectable: true, rows: Array.from({ length: 400 }, (_, i) => ({ id: `C${String(i + 1).padStart(2, '0')}`, n: (i * 37) % 97, st: ['ok', 'warn', 'err'][i % 3] })),
        columns: [{ key: 'id', label: 'Shot', render: (r) => h('span.mono', r.id) }, { key: 'n', label: 'Frame', num: true }, { key: 'st', label: 'Trạng thái', render: (r) => St(r.st, r.st) }] }))),
    h('section.section', h('h2', 'Panel'), h('div', { style: { maxWidth: '480px', marginTop: '8px' } }, Panel('Tiêu đề panel', h('p.muted', 'Viền mảnh thay bóng đổ; bo 4 px.'), [Btn('', { kind: 'ghost', ico: 'x', title: 'Đóng' })]))));
}
