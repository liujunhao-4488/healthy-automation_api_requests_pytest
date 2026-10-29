/* ============================================================
   services/http.js · 真实后端请求封装
   ------------------------------------------------------------
   和后端约定的统一信封：{ code, message, data }
     · 成功        HTTP 200 + code 200
     · 业务失败    HTTP 400 + code 400 + message（Controller 自己 catch 后返回）
     · 参数校验失败 HTTP 400 + code 400 + message（GlobalExceptionHandler 返回）

   所以这里**不抛异常**，一律把信封原样交回去，
   页面继续用 `res.code !== 200` 判断 —— 和之前走 mock 时的写法一模一样，
   页面代码一行都不用改。

   为什么用 fetch 而不是 axios：
   第二版是零依赖的（连 Element Plus 都没引），没必要为这一个功能加 200KB。
   接口形状已经固定，将来真要换 axios 只改这一个文件。

   token 的单一真源是 store 里的 session（持久化在 localStorage 的 sh_session），
   这里直接读，不另存一份 —— 两份 token 迟早会不同步（第一版就是两份，
   所以还得专门写个 clearPersistedAuth 一起清）。
   ============================================================ */

const BASE = '/api'
const SESSION_KEY = 'sh_session'
const TIMEOUT = 12000

/** 从已持久化的会话里取 token，页面刷新后依然有效 */
function readToken() {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return ''
    const s = JSON.parse(raw)
    return (s && s.token) || ''
  } catch (e) {
    return ''
  }
}

/** 把 query 对象拼成 ?a=1&b=2，空值自动跳过 */
function buildQuery(query) {
  if (!query) return ''
  const p = new URLSearchParams()
  Object.keys(query).forEach((k) => {
    const v = query[k]
    if (v !== undefined && v !== null && v !== '') p.append(k, v)
  })
  const s = p.toString()
  return s ? '?' + s : ''
}

/**
 * 发一个请求
 * @param {string} path  以 / 开头的接口路径，如 '/auth/login'
 * @param {object} opts  { method, body, query, timeout }
 * @returns {Promise<{code:number, message:string, data:any}>}
 */
export async function request(path, { method = 'GET', body, query, timeout = TIMEOUT } = {}) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeout)

  const headers = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const token = readToken()
  if (token) headers.Authorization = 'Bearer ' + token

  let res
  try {
    res = await fetch(BASE + path + buildQuery(query), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: ctrl.signal
    })
  } catch (e) {
    clearTimeout(timer)
    const aborted = e && e.name === 'AbortError'
    return {
      code: -1,
      message: aborted ? '请求超时，请稍后重试' : '连接后端失败，请确认后端已在 8081 启动',
      data: null
    }
  }
  clearTimeout(timer)

  // token 失效：单独给 401，页面/守卫据此送回登录页
  if (res.status === 401) {
    return { code: 401, message: '登录已过期，请重新登录', data: null }
  }

  let json = null
  try {
    json = await res.json()
  } catch (e) {
    json = null
  }

  if (!json || typeof json !== 'object') {
    return { code: -2, message: '后端返回格式异常（HTTP ' + res.status + '）', data: null }
  }
  // 后端信封本身就带 code；万一被网关/容器拦掉（Spring 默认错误页），补一层兜底
  if (json.code === undefined) {
    return {
      code: res.status,
      message: json.message || '请求失败（HTTP ' + res.status + '）',
      data: json.data === undefined ? null : json.data
    }
  }
  return json
}

/** 便捷方法，语义更清楚一点 */
export const http = {
  get: (path, query) => request(path, { method: 'GET', query }),
  post: (path, body) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  del: (path, query) => request(path, { method: 'DELETE', query })
}
