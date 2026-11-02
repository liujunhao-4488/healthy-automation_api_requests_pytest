/* ============================================================
   services/adapters/user.js · 个人资料 / 饮食偏好适配层
   ------------------------------------------------------------
   后端契约：
     · GET  /user/profile           → { userId, username, email, phone, avatar, status, role, createTime, updateTime }
     · PUT  /user/profile           → 同上。只接受 username / phone / avatar，
                                      邮箱是登录凭据，没有修改接口。
     · GET  /user/diet-preference   → { dietType, allergies, dislikes, favorites, mealFrequency, snackPreference }
     · PUT  /user/diet-preference   → 同上（没有记录时自动插入）

   前端和后端的差异：
     1. 偏好里后端用逗号分隔的字符串，前端是数组，这里双向转换。
     2. 后端 snackPreference 是 Integer（1 开 / 0 关），前端用布尔。
     3. 后端没有「性别」字段，页面上不再提供该项。
     4. 时间可能是 "2026-11-02 22:37:26" 或 ISO "2026-11-02T22:37:26"，统一取日期部分。
   ============================================================ */

import { http } from '@/services/http'

function dateOnly(value) {
  const m = String(value || '').match(/^\d{4}-\d{2}-\d{2}/)
  return m ? m[0] : ''
}

/** 逗号 / 中文顿号都兼容；顺手去掉空项 */
function splitList(value) {
  return String(value || '')
    .split(/[,，、]/)
    .map((s) => s.trim())
    .filter(Boolean)
}

/* ---------------- 资料 ---------------- */

export function toProfile(be) {
  const u = be || {}
  return {
    userId: u.userId == null ? null : String(u.userId),
    username: u.username || '',
    email: u.email || '',
    phone: u.phone || '',
    avatar: u.avatar || '',
    status: Number(u.status) || 0,
    role: u.role || 'user',
    createTime: u.createTime || '',
    updateTime: u.updateTime || '',
    joined: dateOnly(u.createTime)
  }
}

export async function fetchProfile() {
  const res = await http.get('/user/profile')
  if (res.code !== 200) return res
  return { code: 200, message: res.message, data: toProfile(res.data) }
}

export async function saveProfile(patch) {
  const res = await http.put('/user/profile', patch)
  if (res.code !== 200) return res
  return { code: 200, message: res.message, data: toProfile(res.data) }
}

/* ---------------- 饮食偏好 ---------------- */

export function toPreference(be) {
  const p = be || {}
  return {
    diet: splitList(p.dietType),
    allergens: splitList(p.allergies),
    dislikes: splitList(p.dislikes),
    likes: splitList(p.favorites),
    mealsPerDay: Number(p.mealFrequency) || 3,
    snack: Number(p.snackPreference) === 1
  }
}

/** 页面上的偏好数组 → 后端字段 */
export function toPreferencePayload(prefs) {
  return {
    dietType: prefs.diet.join(','),
    allergies: prefs.allergens.join(','),
    dislikes: prefs.dislikes.join(','),
    favorites: prefs.likes.join(','),
    mealFrequency: prefs.mealsPerDay,
    snackPreference: prefs.snack ? 1 : 0
  }
}

export async function fetchDietPreference() {
  const res = await http.get('/user/diet-preference')
  if (res.code !== 200) return res
  return { code: 200, message: res.message, data: toPreference(res.data) }
}

export function saveDietPreference(prefs) {
  return http.put('/user/diet-preference', toPreferencePayload(prefs))
}
