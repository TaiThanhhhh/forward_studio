// Trạng thái cục bộ của người làm (localStorage, luôn bọc try/catch): bản nháp tự lưu, kích thước panel, mật độ,
// dự án đang mở, checklist Generate. Không chứa dữ liệu pipeline (cái đó luôn đọc lại từ server).
const NS = 'studio.v2.';

export function get(key, fallback = null) {
  try {
    const v = localStorage.getItem(NS + key);
    return v === null ? fallback : JSON.parse(v);
  } catch { return fallback; }
}

export function set(key, value) {
  try { localStorage.setItem(NS + key, JSON.stringify(value)); return true; } catch { return false; }
}

export function del(key) {
  try { localStorage.removeItem(NS + key); } catch { /* chế độ riêng tư */ }
}

/** Gắn autosave cho một form: gọi save(state) mỗi lần đổi (debounce 250 ms); trả về giá trị đã lưu. */
export function autosave(key, initial) {
  let t = null;
  const state = { ...initial, ...(get(key) || {}) };
  return {
    state,
    save(patch) {
      Object.assign(state, patch);
      clearTimeout(t);
      t = setTimeout(() => set(key, state), 250);
    },
    clear() { del(key); },
  };
}

// cache workspace theo dự án trong bộ nhớ: chuyển trang < 100 ms (hiện ngay bản cũ, làm mới nền)
const mem = new Map();
export const cache = {
  get: (k) => mem.get(k),
  set: (k, v) => mem.set(k, v),
  drop: (k) => mem.delete(k),
};
