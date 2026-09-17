import { defineStore } from 'pinia'
import {
  STORAGE_KEYS,
  clearStoredUser,
  clearToken,
  getIngredientHistory,
  getRecentAccounts,
  getStoredUser,
  setIngredientHistory,
  setRecentAccounts,
  setStoredUser,
  setToken
} from '@/utils/storage'

const createEmptyState = () => ({
  userId: null,
  username: '',
  email: '',
  phone: '',
  avatar: '',
  role: 'user',
  token: '',
  healthInfo: null,
  healthAnalysis: null,
  dietGoal: null,
  dietGoalMeta: null,
  healthHistory: [],
  recipeRecommendations: null,
  ingredientAssistantHistory: []
})

const normalizeHealthSnapshot = (info) => ({
  date: new Date().toISOString(),
  weight: info?.weight ?? null,
  bmi: info?.bmi ?? null,
  bmr: info?.bmr ?? null
})

export const isHealthProfileComplete = (info) =>
  Boolean(info && info.age && info.gender && info.height && info.weight && info.activityLevel)

const loadState = () => {
  const persisted = getStoredUser()
  if (!persisted) {
    return createEmptyState()
  }

  return {
    ...createEmptyState(),
    ...persisted,
    ingredientAssistantHistory: getIngredientHistory(persisted)
  }
}

export const useUserStore = defineStore('user', {
  state: () => loadState(),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin',
    hasHealthInfo: (state) => !!state.healthInfo,
    hasDietGoal: (state) => !!state.dietGoal,
    hasCompletedHealthProfile: (state) => isHealthProfileComplete(state.healthInfo),
    recentAccounts: () => getRecentAccounts()
  },
  actions: {
    persistState() {
      setStoredUser({
        userId: this.userId,
        username: this.username,
        email: this.email,
        phone: this.phone,
        avatar: this.avatar,
        role: this.role,
        token: this.token,
        healthInfo: this.healthInfo,
        healthAnalysis: this.healthAnalysis,
        dietGoal: this.dietGoal,
        dietGoalMeta: this.dietGoalMeta,
        healthHistory: this.healthHistory,
        recipeRecommendations: this.recipeRecommendations,
        ingredientAssistantHistory: this.ingredientAssistantHistory
      })
    },
    setUser(user) {
      this.userId = user.userId
      this.username = user.username || ''
      this.email = user.email || ''
      this.phone = user.phone || ''
      this.avatar = user.avatar || ''
      this.role = user.role || 'user'
      this.token = user.token || ''
      this.ingredientAssistantHistory = getIngredientHistory({
        userId: this.userId,
        email: this.email
      })
      setToken(this.token)
      this.persistState()
    },
    updateProfile(profile) {
      this.username = profile.username ?? this.username
      this.email = profile.email ?? this.email
      this.phone = profile.phone ?? this.phone
      this.avatar = profile.avatar ?? this.avatar
      this.role = profile.role ?? this.role
      this.persistState()
    },
    setHealthInfo(info) {
      this.healthInfo = info || null
      if (info) {
        const snapshot = normalizeHealthSnapshot(info)
        const previous = this.healthHistory[this.healthHistory.length - 1]
        const changed = !previous || previous.weight !== snapshot.weight || previous.bmi !== snapshot.bmi || previous.bmr !== snapshot.bmr
        if (changed) {
          this.healthHistory = [...this.healthHistory.slice(-9), snapshot]
        }
      }
      this.persistState()
    },
    setHealthAnalysis(analysis) {
      this.healthAnalysis = analysis || null
      this.persistState()
    },
    setDietGoal(goal) {
      this.dietGoal = goal || null
      this.persistState()
    },
    setDietGoalMeta(meta) {
      this.dietGoalMeta = meta || null
      this.persistState()
    },
    setRecipeRecommendations(data) {
      this.recipeRecommendations = data || null
      this.persistState()
    },
    setIngredientAssistantHistory(history) {
      this.ingredientAssistantHistory = Array.isArray(history) ? history : []
      setIngredientHistory({ userId: this.userId, email: this.email }, this.ingredientAssistantHistory)
      this.persistState()
    },
    saveRecentAccount(account) {
      if (!account?.email || !account?.password) {
        return
      }

      const next = [
        {
          email: account.email,
          password: account.password,
          username: account.username || '',
          role: account.role || 'user',
          lastLoginAt: new Date().toISOString()
        },
        ...getRecentAccounts().filter((item) => item.email !== account.email)
      ].slice(0, 5)

      setRecentAccounts(next)
    },
    removeRecentAccount(email) {
      const next = getRecentAccounts().filter((item) => item.email !== email)
      setRecentAccounts(next)
    },
    logout() {
      Object.assign(this, createEmptyState())
      clearToken()
      clearStoredUser()
      uni.removeStorageSync(STORAGE_KEYS.user)
    }
  }
})
