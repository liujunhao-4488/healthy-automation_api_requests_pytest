/* ============================================================
   composables/useToast.js · 轻提示
   ------------------------------------------------------------
   对应静态版 UI.toast(message, type)。
   状态放在模块作用域，全站共用一个队列，任何组件都能调。
   ============================================================ */
import { ref } from 'vue'

/** 当前在屏幕上的提示列表：[{ id, message, type, leaving }] */
export const toasts = ref([])

let seq = 0

/**
 * 弹一条提示
 * @param {string} message 文案
 * @param {'success'|'error'} [type] 传 'error' 显示红色感叹号
 */
export function toast(message, type) {
  const id = ++seq
  toasts.value = toasts.value.concat([{ id, message, type, leaving: false }])

  // 2.6s 后开始淡出，再过 220ms 从列表移除（和静态版节奏一致）
  setTimeout(() => {
    const item = toasts.value.find((t) => t.id === id)
    if (item) item.leaving = true
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, 220)
  }, 2600)
}

export function useToast() {
  return { toasts, toast }
}
