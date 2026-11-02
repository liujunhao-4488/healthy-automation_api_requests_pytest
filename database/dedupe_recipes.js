/* ============================================================
   dedupe_recipes.js · 食谱去重（软删除）
   ------------------------------------------------------------
   背景：
     2026-11-02 重建食谱时，只有 38 个模板却要铺满 180 条，
     脚本按 [0.9, 1.0, 1.1, 1.2] 缩放份量重复使用同一模板，
     结果同一道菜存了 4~5 条（名字相同、热量不同）。
     实测：193 条只有 65 个不同菜名，平均重复度 2.97。

   为什么用软删除（status=0）而不是 DELETE：
     · diet_record_detail 有 33833 条明细引用了这些食谱
     · user_recipe_collect 有 2275 条收藏引用
     · 三个外键都是 ON DELETE RESTRICT，物理删除会直接失败；
       强行级联删除则会破坏用户的历史饮食记录和收藏 —— 不可接受。
     status=0 保留 id 与全部关联，前端 fetchAllRecipes 已按
     status !== 0 过滤，列表页不再显示重复项。

   保留规则（每组同名食谱）：
     1) 优先保留手写食谱（id < 600000），那是最原始、最可信的数据；
     2) 否则保留热量最接近该组中位数的一条，代表「标准份量」；
     3) 若中位数并列，取 id 最小者，保证结果稳定可复现。

   用法：
     node dedupe_recipes.js --dry   只打印，不改库
     node dedupe_recipes.js         实际执行
   ============================================================ */

const mysql = require('mysql2/promise')

const DRY = process.argv.includes('--dry')
const DB = {
  host: '127.0.0.1',
  port: 3306,
  user: 'root',
  password: process.env.MYSQL_PWD || '123456',
  database: 'health_diet',
  charset: 'utf8mb4'
}

async function main() {
  const conn = await mysql.createConnection(DB)

  const [rows] = await conn.query(
    `SELECT id, name, total_calories, category, create_time
       FROM recipe WHERE status=1 ORDER BY name, id`
  )
  console.log(`当前上架食谱 ${rows.length} 条`)

  // 按名字分组
  const groups = new Map()
  for (const r of rows) {
    if (!groups.has(r.name)) groups.set(r.name, [])
    groups.get(r.name).push(r)
  }

  const keep = []
  const drop = []

  for (const [name, list] of groups) {
    if (list.length === 1) {
      keep.push(list[0])
      continue
    }

    // 1) 手写优先
    const handWritten = list.filter((r) => r.id < 600000)
    let chosen
    if (handWritten.length) {
      chosen = handWritten[0]
    } else {
      // 2) 热量最接近中位数
      const cals = list.map((r) => Number(r.total_calories) || 0).sort((a, b) => a - b)
      const mid =
        cals.length % 2
          ? cals[(cals.length - 1) / 2]
          : (cals[cals.length / 2 - 1] + cals[cals.length / 2]) / 2
      chosen = list
        .slice()
        .sort((a, b) => {
          const da = Math.abs((Number(a.total_calories) || 0) - mid)
          const db = Math.abs((Number(b.total_calories) || 0) - mid)
          return da - db || a.id - b.id // 距离相同取 id 小的
        })[0]
    }

    keep.push(chosen)
    for (const r of list) {
      if (r.id !== chosen.id) drop.push(r)
    }
  }

  console.log(`\n去重后：保留 ${keep.length} 条，软删除 ${drop.length} 条`)
  console.log(`菜名数：${groups.size} 个（去重后每个菜名 1 条）`)

  // 打印示例
  console.log('\n=== 重复组处理示例（前 6 组）===')
  let shown = 0
  for (const [name, list] of groups) {
    if (list.length <= 1 || shown >= 6) continue
    const k = keep.find((x) => x.name === name)
    console.log(`  ${name}`)
    for (const r of list) {
      const mark = r.id === k.id ? '✅ 保留' : '  删除'
      console.log(`    ${mark}  id=${r.id}  ${Math.round(r.total_calories)}kcal  ${r.category || '—'}`)
    }
    shown++
  }

  if (DRY) {
    console.log('\n[--dry] 仅预演，未改库')
    await conn.end()
    return
  }

  // ---- 执行软删除 ----
  if (!drop.length) {
    console.log('\n没有需要删除的记录')
    await conn.end()
    return
  }

  await conn.beginTransaction()
  try {
    const ids = drop.map((r) => r.id)
    // 分批 update，避免 SQL 过长
    const BATCH = 100
    for (let i = 0; i < ids.length; i += BATCH) {
      const chunk = ids.slice(i, i + BATCH)
      const ph = chunk.map(() => '?').join(',')
      await conn.query(`UPDATE recipe SET status=0, update_time=NOW() WHERE id IN (${ph})`, chunk)
    }
    await conn.commit()
    console.log(`\n✅ 已将 ${ids.length} 条重复食谱软删除（status=0）`)
    console.log('   关联的饮食记录与收藏保留不变')
  } catch (e) {
    await conn.rollback()
    console.error('❌ 回滚:', e.message)
    throw e
  }

  // 结果核对
  const [[stat]] = await conn.query(
    `SELECT COUNT(*) total, COUNT(DISTINCT name) names, SUM(status=0) off
       FROM recipe`
  )
  console.log(`\n=== 结果 ===`)
  console.log(`  全部食谱：${stat.total} 条（上架 ${stat.total - stat.off} / 下架 ${stat.off}）`)
  console.log(`  上架中不同菜名：${stat.names} 个`)

  const [[up]] = await conn.query(
    `SELECT COUNT(*) n, COUNT(DISTINCT name) names FROM recipe WHERE status=1`
  )
  console.log(`  上架 ${up.n} 条，菜名 ${up.names} 个 —— ${up.n === up.names ? '✅ 无重名' : '❌ 仍有重名'}`)

  await conn.end()
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
