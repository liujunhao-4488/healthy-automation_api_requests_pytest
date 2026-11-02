/* ============================================================
   export_health_diet.js · 导出可提交的数据库快照
   ------------------------------------------------------------
   为什么需要这个脚本：
     仓库里 database/health_diet.sql 是 2026-09-17 的旧快照，
     而本地 MySQL 已经变成了新数据（125 道食谱、127 种食材、
     diet_record_detail 加了 4 列）。别人 clone 仓库导入旧文件，
     拿到的是 9 月的数据，和开发环境对不上。

   导出策略（只导结构 + 内容数据，不含个人隐私）：
     · 内容表：导出结构与数据
         recipe / recipe_ingredient / ingredient
         health_article / article_comment
     · 用户表：只导出结构（CREATE TABLE），不导任何行
         user / diet_record / diet_record_detail / diet_goal /
         health_info / health_info_history / notification /
         assistant_conversation / assistant_message /
         user_diet_preference / user_recipe_collect /
         user_article_collect / user_article_like / user_read_record

   为什么这样分：
     仓库是公开的（gitee.com/lingfeng-3680/health-diet-system）。
     用户表里有 188 个账号的真实手机号，饮食记录 8519 条、
     聊天记录 7115 条都属于健康隐私，不该进公开仓库。
     而食谱、食材、文章是产品内容，本来就该随仓库分发。

   脱敏处理：
     · health_article.author 里的真实人名「刘俊豪」替换为「健康管理编辑部」
     · 文章正文若出现该名字也一并替换

   用法：
     node export_health_diet.js            生成 database/health_diet.sql
     node export_health_diet.js --out xxx  指定输出路径
   ============================================================ */

const { execFile } = require('node:child_process')
const fs = require('node:fs')
const path = require('node:path')
const mysql = require('mysql2/promise')

const MYSQLDUMP = 'D:\\MYSQL\\bin\\mysqldump.exe'
const MYSQL = 'D:\\MYSQL\\bin\\mysql.exe'

const DB = {
  host: '127.0.0.1', port: 3306, user: 'root',
  password: process.env.MYSQL_PWD || '123456',
  database: 'health_diet'
}

/** 导出结构与数据的表 */
const CONTENT_TABLES = [
  'ingredient',
  'recipe',
  'recipe_ingredient',
  'health_article',
  'article_comment'
]

/** 只导出结构的表（含个人数据） */
const SCHEMA_ONLY_TABLES = [
  'user',
  'diet_record',
  'diet_record_detail',
  'diet_goal',
  'health_info',
  'health_info_history',
  'notification',
  'assistant_conversation',
  'assistant_message',
  'user_diet_preference',
  'user_recipe_collect',
  'user_article_collect',
  'user_article_like',
  'user_read_record'
]

/** 需要脱敏的字符串 */
const REDACTIONS = [
  ['刘俊豪', '健康管理编辑部']
]

function run(cmd, args, opts = {}) {
  return new Promise((resolve, reject) => {
    execFile(cmd, args, { maxBuffer: 64 * 1024 * 1024, ...opts }, (err, stdout, stderr) => {
      if (err) return reject(new Error(err.message + '\n' + (stderr || '')))
      resolve(stdout)
    })
  })
}

function runToFile(cmd, args, file) {
  return new Promise((resolve, reject) => {
    const { spawn } = require('node:child_process')
    const out = fs.createWriteStream(file, { encoding: 'utf8' })
    const p = spawn(cmd, args, { env: { ...process.env, MYSQL_PWD: DB.password } })
    let stderr = ''
    p.stdout.pipe(out)
    p.stderr.on('data', (d) => { stderr += d.toString() })
    p.on('error', reject)
    p.on('close', (code) => {
      out.end(() => {
        if (code !== 0) return reject(new Error(`mysqldump 退出码 ${code}\n${stderr}`))
        resolve()
      })
    })
  })
}

async function main() {
  const outArgIdx = process.argv.indexOf('--out')
  const outFile = outArgIdx > -1
    ? path.resolve(process.argv[outArgIdx + 1])
    : path.join(__dirname, 'health_diet.sql')

  const tmpSchema = outFile + '.schema.tmp'
  const tmpContent = outFile + '.content.tmp'

  console.log('导出目标：' + outFile)
  console.log('\n步骤 1/4：导出内容表结构与数据...')
  /*
   * mysqldump 参数顺序很重要：
   *   mysqldump [options] 库名 [表名...]
   * 不能用 --databases —— 那会把后面的参数全当成「库名」，
   * 于是报 Unknown database 'ingredient'。
   * 这里手动补 CREATE DATABASE / USE，保证导入时不需要预先建库。
   */
  await runToFile(MYSQLDUMP, [
    '-u', DB.user,
    '--single-transaction', '--no-tablespaces',
    '--default-character-set=utf8mb4',
    '--skip-extended-insert',
    DB.database,
    ...CONTENT_TABLES
  ], tmpContent)

  console.log('步骤 2/4：导出用户表结构（不含数据）...')
  await runToFile(MYSQLDUMP, [
    '-u', DB.user,
    '--no-data', '--no-tablespaces',
    '--default-character-set=utf8mb4',
    DB.database,
    ...SCHEMA_ONLY_TABLES
  ], tmpSchema)

  console.log('步骤 3/4：合并并脱敏...')
  let contentSql = fs.readFileSync(tmpContent, 'utf8')
  let schemaSql = fs.readFileSync(tmpSchema, 'utf8')

  /* 取 schema 导出的「表结构部分」。
     不能写死 '--\n-- Table structure...' —— Windows 下 mysqldump 输出的是
     CRLF（\r\n），字面量 '\n' 匹配不到，结果 schemaBody 变成空字符串，
     14 张用户表会整个丢掉（第一次导出就踩了这个坑）。
     这里按「第一行以 '-- Table structure for table' 开头」定位，兼容两种换行。 */
  const schemaLines = schemaSql.split(/\r?\n/)
  const firstIdx = schemaLines.findIndex((l) => l.trim().startsWith('-- Table structure for table'))
  const schemaBody = firstIdx > -1 ? schemaLines.slice(firstIdx).join('\n') : ''

  if (!schemaBody) {
    throw new Error('未能从 schema 导出中定位表结构部分，请检查 mysqldump 输出格式')
  }
  const schemaTableCount = (schemaBody.match(/^CREATE TABLE `/gm) || []).length
  console.log(`   schema 部分含 ${schemaTableCount} 张表`)
  if (schemaTableCount < SCHEMA_ONLY_TABLES.length) {
    throw new Error(
      `用户表结构导出不全：期望 ${SCHEMA_ONLY_TABLES.length} 张，实际 ${schemaTableCount} 张`
    )
  }

  /* 补上建库与切换库语句。
     mysqldump 不加 --databases 时不会输出 CREATE DATABASE / USE，
     空库导入会报「No database selected」。 */
  const header = [
    '-- ============================================================',
    '-- health-diet-system 数据库快照',
    `-- 导出于 ${new Date().toISOString().slice(0, 10)}`,
    '-- ------------------------------------------------------------',
    '-- 导入方式：',
    '--   mysql -uroot -p < database/health_diet.sql',
    '-- ------------------------------------------------------------',
    '-- 内容表（含数据）：ingredient / recipe / recipe_ingredient /',
    '--                   health_article / article_comment',
    '-- 用户相关表：仅表结构，不含账号、饮食记录、聊天记录等隐私数据',
    '-- ============================================================',
    '',
    'SET NAMES utf8mb4;',
    'SET FOREIGN_KEY_CHECKS = 0;',
    '',
    'CREATE DATABASE IF NOT EXISTS `health_diet`',
    '  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;',
    'USE `health_diet`;',
    ''
  ].join('\n')

  // 去掉 dump 自带的头部注释（保留 SET 语句）
  contentSql = contentSql.replace(/^\/\*![\s\S]*?\*\/;\n/m, '')
  contentSql = contentSql.replace(/^--[\s\S]*?-- Host:[\s\S]*?\n\n/, '')

  let merged = header + '\n' + contentSql + '\n\n' +
    '-- ============================================================\n' +
    '-- 用户相关表：仅保留表结构，不含任何个人数据\n' +
    '-- （账号、饮食记录、聊天记录等涉及隐私，不进入公开仓库）\n' +
    '-- ============================================================\n\n' +
    schemaBody + '\n\nSET FOREIGN_KEY_CHECKS = 1;\n'

  // 脱敏
  let redacted = 0
  for (const [from, to] of REDACTIONS) {
    const n = merged.split(from).length - 1
    if (n > 0) { merged = merged.split(from).join(to); redacted += n }
  }

  fs.writeFileSync(outFile, merged, 'utf8')
  fs.unlinkSync(tmpSchema)
  fs.unlinkSync(tmpContent)

  console.log(`   脱敏替换 ${redacted} 处`)

  console.log('步骤 4/4：校验导出结果...')
  const sizeMB = (fs.statSync(outFile).size / 1024 / 1024).toFixed(2)
  console.log(`   文件大小 ${sizeMB} MB`)

  // 统计各表 INSERT 行数
  const counts = {}
  for (const t of [...CONTENT_TABLES, ...SCHEMA_ONLY_TABLES]) {
    const re = new RegExp('INSERT INTO `' + t + '`', 'g')
    counts[t] = (merged.match(re) || []).length
  }
  console.log('\n各表导出情况：')
  for (const t of CONTENT_TABLES) {
    console.log(`   ✅ ${t.padEnd(22)} 数据 ${counts[t]} 行`)
  }
  for (const t of SCHEMA_ONLY_TABLES) {
    const bad = counts[t] > 0
    console.log(`   ${bad ? '❌' : '✅'} ${t.padEnd(22)} ${bad ? '意外含 ' + counts[t] + ' 行数据！' : '仅结构'}`)
  }

  // 安全断言：用户表不能有数据
  const leaked = SCHEMA_ONLY_TABLES.filter((t) => counts[t] > 0)
  if (leaked.length) {
    console.error('\n❌ 隐私检查未通过，以下表含数据：' + leaked.join('、'))
    process.exit(1)
  }

  // 脱敏断言
  for (const [from] of REDACTIONS) {
    if (merged.includes(from)) {
      console.error(`\n❌ 脱敏未完成：文件里仍有「${from}」`)
      process.exit(1)
    }
  }

  // 关键内容断言
  const conn = await mysql.createConnection(DB)
  const [[r]] = await conn.query('SELECT COUNT(*) n FROM recipe WHERE status=1')
  const [[i]] = await conn.query('SELECT COUNT(DISTINCT name) n FROM ingredient WHERE status=1')
  const [[a]] = await conn.query('SELECT COUNT(*) n FROM health_article')
  await conn.end()

  console.log('\n与数据库对照：')
  console.log(`   上架食谱 ${r.n} 道  /  导出文件 recipe INSERT ${counts['recipe']} 行`)
  console.log(`   食材 ${i.n} 种  /  导出文件 ingredient INSERT ${counts['ingredient']} 行`)
  console.log(`   文章 ${a.n} 篇  /  导出文件 health_article INSERT ${counts['health_article']} 行`)

  if (counts['recipe'] < r.n) {
    console.error('❌ 食谱导出不全')
    process.exit(1)
  }

  console.log('\n✅ 导出完成，隐私检查通过')
}

main().catch((e) => { console.error(e); process.exit(1) })
