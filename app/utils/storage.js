export const STORAGE_KEYS = {
  token: 'health-token',
  user: 'health-user',
  recentAccounts: 'health-recent-accounts',
  ingredientHistory: 'health-ingredient-assistant-history'
}

const safeParse = (value, fallback = null) => {
  if (!value) {
    return fallback
  }

  try {
    return JSON.parse(value)
  } catch (error) {
    return fallback
  }
}

export const storage = {
  get(key, fallback = '') {
    const value = uni.getStorageSync(key)
    return value === '' || value === undefined || value === null ? fallback : value
  },
  set(key, value) {
    uni.setStorageSync(key, value)
  },
  remove(key) {
    uni.removeStorageSync(key)
  },
  getJSON(key, fallback = null) {
    return safeParse(this.get(key, ''), fallback)
  },
  setJSON(key, value) {
    this.set(key, JSON.stringify(value))
  }
}

export const getToken = () => storage.get(STORAGE_KEYS.token, '')
export const setToken = (token) => storage.set(STORAGE_KEYS.token, token || '')
export const clearToken = () => storage.remove(STORAGE_KEYS.token)

export const getStoredUser = () => storage.getJSON(STORAGE_KEYS.user, null)
export const setStoredUser = (payload) => storage.setJSON(STORAGE_KEYS.user, payload)
export const clearStoredUser = () => storage.remove(STORAGE_KEYS.user)

export const getRecentAccounts = () => storage.getJSON(STORAGE_KEYS.recentAccounts, [])
export const setRecentAccounts = (accounts) => storage.setJSON(STORAGE_KEYS.recentAccounts, accounts)

export const buildIngredientHistoryKey = (user) => {
  const identifier = user?.userId || user?.email || 'guest'
  return `${STORAGE_KEYS.ingredientHistory}:${identifier}`
}

export const getIngredientHistory = (user) => {
  return storage.getJSON(buildIngredientHistoryKey(user), [])
}

export const setIngredientHistory = (user, history) => {
  storage.setJSON(buildIngredientHistoryKey(user), Array.isArray(history) ? history : [])
}
