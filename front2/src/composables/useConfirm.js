/* ============================================================
   composables/useConfirm.js · 二次确认弹窗
   ------------------------------------------------------------
   对应静态版 UI.confirm(message, onConfirm, opts)。
   改成 Promise 写法，调用处可以 await：

     const ok = await confirmDialog('确定删除？', { danger: true })
     if (ok) { ... }
   ============================================================ */
import { reactive } from 'vue'

export const confirmState = reactive({
  open: false,
  title: '确认操作',
  message: '',
  okText: '确认',
  danger: false,
  resolve: null
})

export function confirmDialog(message, opts = {}) {
  return new Promise((resolve) => {
    // 上一个还没关就先结掉，避免 Promise 悬空
    if (confirmState.resolve) confirmState.resolve(false)

    confirmState.title = opts.title || '确认操作'
    confirmState.message = message
    confirmState.okText = opts.okText || '确认'
    confirmState.danger = !!opts.danger
    confirmState.resolve = resolve
    confirmState.open = true
  })
}

/** 由 ConfirmDialog 组件调用：settle(true/false) 关闭并返回结果 */
export function settleConfirm(result) {
  const r = confirmState.resolve
  confirmState.open = false
  confirmState.resolve = null
  if (r) r(result)
}
