// Undo/redo cho thao tác cục bộ trên UI (đổi thứ tự shot, checklist, xoá comment…): push({label, undo, redo}).
// Ctrl+Z / Ctrl+Shift+Z gắn ở main.js. Thao tác đã chạy thành job (render) không undo được — UI hỏi xác nhận trước.
const past = [];
const future = [];
let onChange = () => {};

export function push(action) {
  past.push(action);
  if (past.length > 100) past.shift();
  future.length = 0;
  onChange();
}

export async function undo() {
  const a = past.pop();
  if (!a) return null;
  await a.undo();
  future.push(a);
  onChange();
  return a.label;
}

export async function redo() {
  const a = future.pop();
  if (!a) return null;
  await a.redo();
  past.push(a);
  onChange();
  return a.label;
}

export function reset() { past.length = 0; future.length = 0; onChange(); }
export function watch(fn) { onChange = fn; }
export const canUndo = () => past.length > 0;
export const canRedo = () => future.length > 0;
