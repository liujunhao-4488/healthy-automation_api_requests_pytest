/* ============================================================
   utils/mealPlanExport.js · 配餐计划导出
   ------------------------------------------------------------
   不引第三方依赖：
     · Word  → HTML 内容 + application/msword
     · Excel → HTML 表格 + application/vnd.ms-excel
     · PDF   → 打印窗口，浏览器「另存为 PDF」
   三份产物的表格数据同源，避免导出后对不上。
   ============================================================ */

const escapeHtml = (value) =>
  String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

const downloadBlob = (filename, content, type) => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const tableStyles = `
  body { font-family: "Microsoft YaHei", sans-serif; padding: 24px; color: #1f2937; background: #fff; }
  h1 { color: #173c2d; font-size: 22px; margin-bottom: 6px; }
  .meta { color: #5f7567; margin: 0 0 16px; font-size: 13px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { border: 1px solid #d8e3dc; padding: 10px 12px; text-align: left; vertical-align: top; font-size: 13px; }
  th { background: #f4faf6; color: #173c2d; }
  td.day { font-weight: 600; color: #173c2d; white-space: nowrap; }
  .kcal { color: #2f6b49; white-space: nowrap; }
`

const mealName = (meal) => meal?.name || meal?.recipeName || '--'

const planTableHtml = (days) => `
  <table>
    <thead>
      <tr>
        <th>天数</th>
        <th>早餐</th>
        <th>午餐</th>
        <th>晚餐</th>
        <th>当日热量</th>
      </tr>
    </thead>
    <tbody>
      ${days
        .map(
          (day) => `
        <tr>
          <td class="day">${escapeHtml(day.label)}</td>
          <td>${escapeHtml(mealName(day.breakfast))}</td>
          <td>${escapeHtml(mealName(day.lunch))}</td>
          <td>${escapeHtml(mealName(day.dinner))}</td>
          <td class="kcal">${escapeHtml(day.kcalText || '--')}</td>
        </tr>
      `
        )
        .join('')}
    </tbody>
  </table>
`

const exportTime = () => new Date().toLocaleString()

export function exportPlanToWord(filename, title, days) {
  const body = `
    <h1>${escapeHtml(title)}</h1>
    <p class="meta">导出时间：${escapeHtml(exportTime())} · 膳衡智能配餐</p>
    ${planTableHtml(days)}
  `
  downloadBlob(
    filename,
    `<html><head><meta charset="utf-8"><style>${tableStyles}</style></head><body>${body}</body></html>`,
    'application/msword'
  )
}

export function exportPlanToExcel(filename, title, days) {
  const body = `
    <h1>${escapeHtml(title)}</h1>
    <p class="meta">导出时间：${escapeHtml(exportTime())} · 膳衡智能配餐</p>
    ${planTableHtml(days)}
  `
  downloadBlob(
    filename,
    `<html><head><meta charset="utf-8"><style>${tableStyles}</style></head><body>${body}</body></html>`,
    'application/vnd.ms-excel'
  )
}

/** 打开新窗口打印，用户可在打印对话框里选择「另存为 PDF」 */
export function exportPlanToPdf(title, days) {
  const body = `
    <h1>${escapeHtml(title)}</h1>
    <p class="meta">导出时间：${escapeHtml(exportTime())} · 膳衡智能配餐</p>
    ${planTableHtml(days)}
  `
  const win = window.open('', '_blank', 'width=1024,height=768')
  if (!win) return false

  win.document.write(
    `<html><head><meta charset="utf-8"><title>${escapeHtml(title)}</title><style>${tableStyles}</style></head><body>${body}</body></html>`
  )
  win.document.close()
  win.focus()
  win.print()
  return true
}
