const escapeHtml = (value) =>
  String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

const downloadBlob = (filename, content, type) => {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const openPrintWindow = (title, bodyHtml) => {
  const printWindow = window.open('', '_blank', 'width=1024,height=768');
  if (!printWindow) {
    return false;
  }

  printWindow.document.write(`
    <html>
      <head>
        <meta charset="utf-8" />
        <title>${escapeHtml(title)}</title>
        <style>
          body { font-family: "Microsoft YaHei", sans-serif; padding: 24px; color: #1f2937; }
          h1, h2, h3 { color: #173c2d; }
          table { width: 100%; border-collapse: collapse; margin: 16px 0; }
          th, td { border: 1px solid #d8e3dc; padding: 10px; text-align: left; }
          th { background: #f4faf6; }
          .meta { color: #5f7567; margin-bottom: 8px; }
          .card { border: 1px solid #d8e3dc; border-radius: 12px; padding: 16px; margin: 14px 0; }
        </style>
      </head>
      <body>${bodyHtml}</body>
    </html>
  `);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
  return true;
};

const recipeTableHtml = (rows) => `
  <table>
    <thead>
      <tr>
        <th>名称</th>
        <th>分类</th>
        <th>热量(kcal)</th>
        <th>蛋白质(g)</th>
        <th>碳水(g)</th>
        <th>脂肪(g)</th>
        <th>烹饪时间(分钟)</th>
        <th>难度</th>
      </tr>
    </thead>
    <tbody>
      ${rows
        .map(
          (row) => `
            <tr>
              <td>${escapeHtml(row.name)}</td>
              <td>${escapeHtml(row.category || row.mealType || '--')}</td>
              <td>${escapeHtml(row.calories ?? row.totalCalories ?? '--')}</td>
              <td>${escapeHtml(row.protein ?? '--')}</td>
              <td>${escapeHtml(row.carbs ?? '--')}</td>
              <td>${escapeHtml(row.fat ?? '--')}</td>
              <td>${escapeHtml(row.cookingTime ?? '--')}</td>
              <td>${escapeHtml(row.difficulty ?? '--')}</td>
            </tr>
          `
        )
        .join('')}
    </tbody>
  </table>
`;

export const exportRecipesToWord = (filename, title, rows) => {
  const html = `
    <h1>${escapeHtml(title)}</h1>
    <p class="meta">导出时间：${escapeHtml(new Date().toLocaleString())}</p>
    ${recipeTableHtml(rows)}
  `;
  downloadBlob(filename, `<html><head><meta charset="utf-8"></head><body>${html}</body></html>`, 'application/msword');
};

export const exportRecipesToExcel = (filename, title, rows) => {
  const html = `
    <html>
      <head><meta charset="utf-8"></head>
      <body>
        <h1>${escapeHtml(title)}</h1>
        <p>导出时间：${escapeHtml(new Date().toLocaleString())}</p>
        ${recipeTableHtml(rows)}
      </body>
    </html>
  `;
  downloadBlob(filename, html, 'application/vnd.ms-excel');
};

export const exportRecipesToPdf = (title, rows) =>
  openPrintWindow(
    title,
    `<h1>${escapeHtml(title)}</h1><p class="meta">导出时间：${escapeHtml(
      new Date().toLocaleString()
    )}</p>${recipeTableHtml(rows)}`
  );

export const exportPlanToPdf = (title, days) =>
  openPrintWindow(
    title,
    `
      <h1>${escapeHtml(title)}</h1>
      <p class="meta">导出时间：${escapeHtml(new Date().toLocaleString())}</p>
      ${days
        .map(
          (day) => `
            <div class="card">
              <h3>${escapeHtml(day.label)}</h3>
              <p>早餐：${escapeHtml(day.breakfast?.name || '--')}</p>
              <p>午餐：${escapeHtml(day.lunch?.name || '--')}</p>
              <p>晚餐：${escapeHtml(day.dinner?.name || '--')}</p>
            </div>
          `
        )
        .join('')}
    `
  );

const planTableHtml = (days) => `
  <table>
    <thead>
      <tr>
        <th>天数</th>
        <th>早餐</th>
        <th>午餐</th>
        <th>晚餐</th>
      </tr>
    </thead>
    <tbody>
      ${days
        .map(
          (day) => `
            <tr>
              <td>${escapeHtml(day.label)}</td>
              <td>${escapeHtml(day.breakfast?.name || day.breakfast?.recipeName || '--')}</td>
              <td>${escapeHtml(day.lunch?.name || day.lunch?.recipeName || '--')}</td>
              <td>${escapeHtml(day.dinner?.name || day.dinner?.recipeName || '--')}</td>
            </tr>
          `
        )
        .join('')}
    </tbody>
  </table>
`;

export const exportPlanToWord = (filename, title, days) => {
  const html = `
    <h1>${escapeHtml(title)}</h1>
    <p class="meta">导出时间：${escapeHtml(new Date().toLocaleString())}</p>
    ${planTableHtml(days)}
  `;
  downloadBlob(filename, `<html><head><meta charset="utf-8"></head><body>${html}</body></html>`, 'application/msword');
};

export const exportPlanToExcel = (filename, title, days) => {
  const html = `
    <html>
      <head><meta charset="utf-8"></head>
      <body>
        <h1>${escapeHtml(title)}</h1>
        <p>导出时间：${escapeHtml(new Date().toLocaleString())}</p>
        ${planTableHtml(days)}
      </body>
    </html>
  `;
  downloadBlob(filename, html, 'application/vnd.ms-excel');
};
