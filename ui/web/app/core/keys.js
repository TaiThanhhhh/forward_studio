// Phím tắt toàn cục + theo trang. register('global'|'page', 'Ctrl+K', fn, 'Mô tả') — trang gọi clearPage() khi rời.
// Bảng phím tắt (?) đọc từ chính danh sách này nên luôn đúng.
const maps = { global: [], page: [] };

function norm(e) {
  const k = e.key.length === 1 ? e.key.toUpperCase() : e.key;
  const parts = [];
  if (e.ctrlKey || e.metaKey) parts.push('Ctrl');
  if (e.altKey) parts.push('Alt');
  if (e.shiftKey && !(k.length === 1 && /[^A-Z0-9]/.test(k) && k !== ' ')) parts.push('Shift');
  parts.push(k === ' ' ? 'Space' : k);
  return parts.join('+');
}

function typing(t) {
  return t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable);
}

export function register(scope, combo, fn, label, opts = {}) {
  maps[scope].push({ combo, fn, label, inInput: !!opts.inInput, group: opts.group || (scope === 'page' ? 'Trang này' : 'Chung') });
}

export function clearPage() { maps.page = []; }

export function list() { return [...maps.page, ...maps.global].filter((k) => k.label); }

window.addEventListener('keydown', (e) => {
  if (document.querySelector('.scrim') && e.key !== 'Escape' && !e.ctrlKey) return;   // modal mở: chỉ Esc/Ctrl
  const c = norm(e);
  const inInput = typing(e.target);
  for (const scope of ['page', 'global']) {
    const hit = maps[scope].find((k) => k.combo === c && (!inInput || k.inInput));
    if (hit) {
      const r = hit.fn(e);
      if (r !== false) e.preventDefault();
      return;
    }
  }
});

export const isMac = /Mac/.test(navigator.platform);
export const mod = isMac ? '⌘' : 'Ctrl';
