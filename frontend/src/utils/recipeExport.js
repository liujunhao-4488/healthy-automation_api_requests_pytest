import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

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

const sharedStyles = `
  body { font-family: "Microsoft YaHei", sans-serif; padding: 24px; color: #1f2937; background: #ffffff; }
  h1, h2, h3 { color: #173c2d; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; }
  th, td { border: 1px solid #d8e3dc; padding: 10px; text-align: left; vertical-align: top; }
  th { background: #f4faf6; }
  .meta { color: #5f7567; margin-bottom: 8px; }
  .recipe-card { border: 1px solid #d8e3dc; border-radius: 16px; padding: 18px; margin: 16px 0; background: linear-gradient(180deg, #ffffff 0%, #f7fbf8 100%); page-break-inside: avoid; }
  .recipe-top { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 12px; }
  .meal-badge { display: inline-block; padding: 4px 10px; border-radius: 999px; background: #edf7f0; color: #2f6b49; font-size: 12px; margin-bottom: 8px; }
  .score-badge { min-width: 88px; padding: 10px 12px; border-radius: 14px; background: #173c2d; color: #ffffff; text-align: center; }
  .score-badge span { display: block; font-size: 12px; opacity: 0.85; color: #ffffff; }
  .score-badge strong { display: block; font-size: 20px; line-height: 1.2; color: #ffffff; }
  .nutrition-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 12px 0; }
  .nutrition-item { border: 1px solid #d8e3dc; border-radius: 12px; padding: 10px 12px; background: #ffffff; }
  .nutrition-item span { display: block; color: #6b7f72; font-size: 12px; margin-bottom: 6px; }
  .nutrition-item strong { font-size: 16px; color: #173c2d; }
  .recipe-meta-row { display: flex; flex-wrap: wrap; gap: 16px; margin: 10px 0; color: #4e6357; }
  .reason-box { margin-top: 12px; padding: 12px 14px; border-radius: 12px; background: #edf7f0; color: #244a35; line-height: 1.7; }
  .ingredient-box { margin-top: 12px; color: #4e6357; line-height: 1.7; }
  .plan-card { border: 1px solid #d8e3dc; border-radius: 16px; padding: 18px; margin: 16px 0; background: linear-gradient(180deg, #ffffff 0%, #f6faf7 100%); page-break-inside: avoid; }
  .plan-card-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 14px; }
  .plan-day-badge { display: inline-block; padding: 4px 10px; border-radius: 999px; background: #edf7f0; color: #2f6b49; font-size: 12px; }
  .plan-meal-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
  .plan-meal-card { border: 1px solid #d8e3dc; border-radius: 12px; padding: 12px 14px; background: #ffffff; }
  .plan-meal-card span { display: block; color: #6b7f72; font-size: 12px; margin-bottom: 6px; }
  .plan-meal-card strong { color: #173c2d; font-size: 15px; }
`;

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
        <style>${sharedStyles}</style>
      </head>
      <body>${bodyHtml}</body>
    </html>
  `);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
  return true;
};

const healthMetricsHtml = (row) => {
  const metrics = [
    { label: '膳食纤维', value: row.fiber, unit: 'g' },
    { label: '含糖量', value: row.sugar, unit: 'g' },
    { label: '钠', value: row.sodium, unit: 'mg' },
    { label: 'GI', value: row.gi, unit: '' }
  ].filter((metric) => metric.value !== undefined && metric.value !== null && metric.value !== '' && metric.value !== '--');

  if (!metrics.length) {
    return '';
  }

  return `
    <div class="nutrition-grid">
      ${metrics
        .map(
          (metric) => `
            <div class="nutrition-item">
              <span>${escapeHtml(metric.label)}</span>
              <strong>${escapeHtml(metric.value)}${metric.unit ? ` ${escapeHtml(metric.unit)}` : ''}</strong>
            </div>
          `
        )
        .join('')}
    </div>
  `;
};

const recipeCardsHtml = (rows) =>
  rows
    .map(
      (row) => `
        <section class="recipe-card">
          <div class="recipe-top">
            <div>
              <span class="meal-badge">${escapeHtml(row.mealLabel || row.category || row.mealType || '--')}</span>
              <h3>${escapeHtml(row.name)}</h3>
              <p class="meta">${escapeHtml(row.description || '根据当前目标生成的推荐食谱')}</p>
            </div>
            <div class="score-badge">
              <span>匹配度</span>
              <strong>${escapeHtml(row.score || '--')}</strong>
            </div>
          </div>
          <div class="nutrition-grid">
            <div class="nutrition-item"><span>热量</span><strong>${escapeHtml(row.calories ?? '--')} kcal</strong></div>
            <div class="nutrition-item"><span>蛋白质</span><strong>${escapeHtml(row.protein ?? '--')} g</strong></div>
            <div class="nutrition-item"><span>碳水</span><strong>${escapeHtml(row.carbs ?? '--')} g</strong></div>
            <div class="nutrition-item"><span>脂肪</span><strong>${escapeHtml(row.fat ?? '--')} g</strong></div>
          </div>
          ${healthMetricsHtml(row)}
          <div class="recipe-meta-row">
            <span>烹饪时间：${escapeHtml(row.cookingTime ?? '--')} 分钟</span>
            <span>难度：${escapeHtml(row.difficulty ?? '--')}</span>
          </div>
          <div class="reason-box">推荐理由：${escapeHtml(row.reason || '--')}</div>
          <div class="ingredient-box">食材摘要：${escapeHtml(row.ingredientsSummary || '--')}</div>
        </section>
      `
    )
    .join('');

const recipeDetailTableHtml = (rows) => `
  <table>
    <thead>
      <tr>
        <th>餐次</th>
        <th>食谱名称</th>
        <th>匹配度</th>
        <th>热量(kcal)</th>
        <th>蛋白质(g)</th>
        <th>碳水(g)</th>
        <th>脂肪(g)</th>
        <th>膳食纤维(g)</th>
        <th>含糖量(g)</th>
        <th>钠(mg)</th>
        <th>GI</th>
        <th>烹饪时间</th>
        <th>难度</th>
        <th>推荐理由</th>
        <th>食材摘要</th>
      </tr>
    </thead>
    <tbody>
      ${rows
        .map(
          (row) => `
            <tr>
              <td>${escapeHtml(row.mealLabel || row.category || row.mealType || '--')}</td>
              <td>${escapeHtml(row.name)}</td>
              <td>${escapeHtml(row.score || '--')}</td>
              <td>${escapeHtml(row.calories ?? '--')}</td>
              <td>${escapeHtml(row.protein ?? '--')}</td>
              <td>${escapeHtml(row.carbs ?? '--')}</td>
              <td>${escapeHtml(row.fat ?? '--')}</td>
              <td>${escapeHtml(row.fiber ?? '--')}</td>
              <td>${escapeHtml(row.sugar ?? '--')}</td>
              <td>${escapeHtml(row.sodium ?? '--')}</td>
              <td>${escapeHtml(row.gi ?? '--')}</td>
              <td>${escapeHtml(row.cookingTime ?? '--')}</td>
              <td>${escapeHtml(row.difficulty ?? '--')}</td>
              <td>${escapeHtml(row.reason || '--')}</td>
              <td>${escapeHtml(row.ingredientsSummary || '--')}</td>
            </tr>
          `
        )
        .join('')}
    </tbody>
  </table>
`;

const planCardsHtml = (days) =>
  days
    .map(
      (day) => `
        <section class="plan-card">
          <div class="plan-card-head">
            <div>
              <span class="plan-day-badge">${escapeHtml(day.label)}</span>
              <h3>${escapeHtml(day.label)} 食谱计划</h3>
            </div>
          </div>
          <div class="plan-meal-grid">
            <div class="plan-meal-card">
              <span>早餐</span>
              <strong>${escapeHtml(day.breakfast?.name || day.breakfast?.recipeName || '--')}</strong>
            </div>
            <div class="plan-meal-card">
              <span>午餐</span>
              <strong>${escapeHtml(day.lunch?.name || day.lunch?.recipeName || '--')}</strong>
            </div>
            <div class="plan-meal-card">
              <span>晚餐</span>
              <strong>${escapeHtml(day.dinner?.name || day.dinner?.recipeName || '--')}</strong>
            </div>
          </div>
        </section>
      `
    )
    .join('');

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

const downloadPdfFromHtml = async (filename, title, bodyHtml) => {
  const container = document.createElement('div');
  container.style.position = 'fixed';
  container.style.left = '-10000px';
  container.style.top = '0';
  container.style.width = '794px';
  container.style.background = '#ffffff';
  container.style.zIndex = '-1';
  container.innerHTML = `
    <div class="pdf-export-root">
      <style>${sharedStyles}</style>
      <h1>${escapeHtml(title)}</h1>
      <p class="meta">导出时间：${escapeHtml(new Date().toLocaleString())}</p>
      ${bodyHtml}
    </div>
  `;
  document.body.appendChild(container);

  try {
    await new Promise((resolve) => window.requestAnimationFrame(resolve));
    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff'
    });

    const pdf = new jsPDF('p', 'mm', 'a4');
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const imgWidth = pageWidth;
    const pageHeightInCanvas = (canvas.width * pageHeight) / pageWidth;

    let renderedHeight = 0;
    let pageIndex = 0;

    while (renderedHeight < canvas.height) {
      const pageCanvas = document.createElement('canvas');
      pageCanvas.width = canvas.width;
      pageCanvas.height = Math.min(pageHeightInCanvas, canvas.height - renderedHeight);

      const context = pageCanvas.getContext('2d');
      context.drawImage(
        canvas,
        0,
        renderedHeight,
        canvas.width,
        pageCanvas.height,
        0,
        0,
        canvas.width,
        pageCanvas.height
      );

      const pageData = pageCanvas.toDataURL('image/png');
      if (pageIndex > 0) {
        pdf.addPage();
      }
      pdf.addImage(
        pageData,
        'PNG',
        0,
        0,
        imgWidth,
        (pageCanvas.height * imgWidth) / pageCanvas.width
      );

      renderedHeight += pageCanvas.height;
      pageIndex += 1;
    }

    pdf.save(filename);
  } finally {
    document.body.removeChild(container);
  }
};

export const exportRecipesToWord = (filename, title, rows) => {
  const html = `
    <h1>${escapeHtml(title)}</h1>
    <p class="meta">导出时间：${escapeHtml(new Date().toLocaleString())}</p>
    ${recipeCardsHtml(rows)}
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
        ${recipeDetailTableHtml(rows)}
      </body>
    </html>
  `;
  downloadBlob(filename, html, 'application/vnd.ms-excel');
};

export const exportRecipesToPdf = async (title, rows) =>
  downloadPdfFromHtml(`${title}.pdf`, title, recipeCardsHtml(rows));

export const exportPlanToPdf = async (title, days) =>
  downloadPdfFromHtml(`${title}.pdf`, title, planCardsHtml(days));

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
