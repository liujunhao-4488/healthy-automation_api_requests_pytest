/* ============================================================
   services/adapters/placeholder.js · 缺图时的统一占位符
   ------------------------------------------------------------
   背景：后端 Recipe.imageUrl **193 条全是 null**，根本没有图。
   早先的做法是按 id 取模轮换本地 4 张真实菜品照，问题是
   「瘦牛肉藜麦饭」会配上三文鱼的图 —— 图文不符比缺图更糟，
   截图放进论文/PPT 也容易被看出破绽。所以统一换成占位符。

   为什么用 data URI 而不是 assets 里的 .svg 文件：
     · 不新增构建产物、不占一次网络请求、永远不会 404；
     · encodeURIComponent 后约 700 字节，可以忽略；
     · 食材 / 文章模块将来缺图也能直接复用这一个常量。

   构图约束（很重要）：四处容器都是 object-fit: cover，比例各不相同 ——
     列表卡片 4:3、详情主图 16:8、收藏缩略图、后台表格缩略图
   所以图形必须集中在正中央：16:8 时按宽度铺满会裁掉上下各 50px，
   图标（y 60~200）和「暂无图片」（y 218）都落在安全区内。
   ============================================================ */

const SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">
<rect width="400" height="300" fill="#f1f7f3"/>
<circle cx="200" cy="128" r="68" fill="#e3efe8"/>
<g fill="none" stroke="#a9bdae" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
<path d="M158 126 Q200 116 242 126"/>
<path d="M158 126 Q174 174 200 174 Q226 174 242 126"/>
<path d="M186 190 Q200 195 214 190"/>
</g>
<text x="200" y="219" text-anchor="middle" font-family="PingFang SC, Microsoft YaHei, Hiragino Sans GB, sans-serif" font-size="13" letter-spacing="1" fill="#a9bdae">暂无图片</text>
</svg>`

/** 直接可用的占位图地址 */
export const NO_IMAGE = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(SVG)

/**
 * 有真图就用真图，没有就占位符。
 * 兼容绝对地址、协议相对地址和 data URI；相对路径（如 /uploads/x.jpg）
 * 原样返回 —— 将来后端真给图时，只要 vite 代理把 /uploads 也转发即可。
 */
export function withFallbackImage(url) {
  if (!url || typeof url !== 'string') return NO_IMAGE
  const s = url.trim()
  return s || NO_IMAGE
}
