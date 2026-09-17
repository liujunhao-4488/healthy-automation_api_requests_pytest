<template>
  <view class="page-shell safe-bottom">
    <view class="page-content recipes-page">
      <view class="hero-card card">
        <view>
          <view class="hero-title">食谱推荐</view>
          <view class="hero-desc">根据你的饮食目标查看今日推荐与自定义食谱。</view>
        </view>
        <text class="hero-action" @click="handleHeroAction">{{ heroActionText }}</text>
      </view>

      <view class="tab-row soft-card">
        <view
          v-for="item in tabs"
          :key="item.value"
          class="tab-pill"
          :class="{ active: currentTab === item.value }"
          @click="changeTab(item.value)"
        >
          {{ item.label }}
        </view>
      </view>

      <view class="summary-card soft-card">
        <view>
          <text class="summary-label">当前分类</text>
          <text class="summary-value">{{ currentTabLabel }}</text>
          <text class="summary-meta">{{ summaryMetaText }}</text>
        </view>
        <button v-if="currentTab === 'today'" class="change-button" :disabled="loading" @click="changeBatch">
          换一批
        </button>
      </view>

      <view v-if="loading" class="card empty-card">
        <text>{{ loadingText }}</text>
      </view>

      <view v-else-if="activeRecipes.length" class="list-stack">
        <view v-for="(recipe, index) in displayedRecipes" :key="recipe.id || index" class="card recipe-card">
          <view class="recipe-top" @click="openRecipe(recipe)">
            <view class="recipe-badge">
              <text>{{ recipe.mealLabel }}</text>
            </view>
            <view class="recipe-title-block">
              <text class="recipe-title">{{ recipe.name }}</text>
              <text class="recipe-desc clamp-2">{{ recipe.description }}</text>
            </view>
          </view>

          <view v-if="recipe.reason" class="reason-card">
            <text>{{ recipe.reason }}</text>
          </view>

          <view class="metrics-grid">
            <view class="metric-item primary-metric">
              <text class="metric-label">热量</text>
              <text class="metric-value">{{ recipe.calories }} kcal</text>
            </view>
            <view class="metric-item">
              <text class="metric-label">蛋白质</text>
              <text class="metric-value">{{ recipe.protein }} g</text>
            </view>
            <view class="metric-item">
              <text class="metric-label">碳水</text>
              <text class="metric-value">{{ recipe.carbs }} g</text>
            </view>
            <view class="metric-item">
              <text class="metric-label">脂肪</text>
              <text class="metric-value">{{ recipe.fat }} g</text>
            </view>
          </view>

          <view v-if="recipe.healthMetrics.length" class="health-row">
            <view v-for="metric in recipe.healthMetrics" :key="metric.label" class="health-pill">
              <text>{{ metric.label }}</text>
              <text>{{ metric.value }}</text>
            </view>
          </view>

          <view class="recipe-footer">
            <view class="recipe-meta">
              <text>{{ recipe.cookingTimeText }}</text>
              <text>{{ recipe.difficultyText }}</text>
            </view>
            <view class="action-row">
              <button class="secondary-button small-btn" @click="openRecipe(recipe)">详情</button>
              <button class="primary-button small-btn" @click="toggleCollect(recipe)">
                {{ isCollected(recipe) ? '已收藏' : '收藏' }}
              </button>
            </view>
          </view>
        </view>
      </view>

      <view v-else class="card empty-card">
        <text>{{ emptyText }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import recipeApi from '@/api/recipe'
import { useUserStore } from '@/store/user'
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

const userStore = useUserStore()
const loading = ref(false)
const currentTab = ref('today')
const todayRecipes = ref([])
const customRecipes = ref([])
const collectedIds = ref(new Set())
const batchIndex = ref(0)
const hasLoadedToday = ref(false)
const hasLoadedCustom = ref(false)
const batchSize = 3
const mainMealTypes = ['breakfast', 'lunch', 'dinner']

const tabs = [
  { label: '今日', value: 'today' },
  { label: '自定义', value: 'custom' }
]

const mealTypeMap = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐'
}

const currentTabLabel = computed(() => tabs.find((item) => item.value === currentTab.value)?.label || '今日')
const heroActionText = computed(() => (currentTab.value === 'today' ? '重新生成' : '刷新'))
const activeRecipes = computed(() => (currentTab.value === 'today' ? todayRecipes.value : customRecipes.value))
const todayMealGroups = computed(() => {
  const groups = {
    breakfast: [],
    lunch: [],
    dinner: [],
    other: []
  }

  todayRecipes.value.forEach((recipe) => {
    const key = mainMealTypes.includes(recipe.mealType) ? recipe.mealType : 'other'
    groups[key].push(recipe)
  })

  return groups
})
const todayBatchCount = computed(() => {
  const groupLengths = mainMealTypes.map((type) => todayMealGroups.value[type].length)
  const maxMainMeals = Math.max(0, ...groupLengths)
  const fallbackCount = Math.ceil(todayRecipes.value.length / batchSize)
  return Math.max(maxMainMeals, fallbackCount, 1)
})
const summaryMetaText = computed(() => {
  if (currentTab.value === 'today') {
    return todayBatchCount.value > 1
      ? `候选 ${todayRecipes.value.length} 道，当前第 ${batchIndex.value + 1} 批`
      : `候选 ${todayRecipes.value.length} 道，暂无更多批次`
  }
  return `收藏 ${collectedIds.value.size} 道食谱`
})
const loadingText = computed(() => (currentTab.value === 'today' ? '正在加载今日推荐食谱...' : '正在加载自定义食谱...'))
const emptyText = computed(() => (currentTab.value === 'today' ? '当前暂无今日推荐食谱' : '当前暂无自定义食谱'))

const displayedRecipes = computed(() => {
  if (currentTab.value !== 'today') {
    return customRecipes.value
  }

  const selected = []
  const selectedKeys = new Set()

  mainMealTypes.forEach((type) => {
    const group = todayMealGroups.value[type]
    if (!group.length) return
    const recipe = group[batchIndex.value % group.length]
    const key = recipe.id || `${recipe.name}-${recipe.mealType}`
    if (selectedKeys.has(key)) return
    selectedKeys.add(key)
    selected.push(recipe)
  })

  if (selected.length < batchSize) {
    todayRecipes.value.forEach((recipe) => {
      if (selected.length >= batchSize) return
      const key = recipe.id || `${recipe.name}-${recipe.mealType}`
      if (selectedKeys.has(key)) return
      selectedKeys.add(key)
      selected.push(recipe)
    })
  }

  return selected
})

const normalizeNumber = (value, digits = 0) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return '--'
  return digits > 0 ? number.toFixed(digits) : String(Math.round(number))
}

const buildHealthMetrics = (item) => {
  const metrics = [
    { label: '糖', value: item.sugar ?? item.totalSugar, unit: 'g', digits: 1 },
    { label: '钠', value: item.sodium ?? item.totalSodium, unit: 'mg', digits: 0 },
    { label: 'GI', value: item.gi ?? item.glycemicIndex, unit: '', digits: 0 },
    { label: '纤维', value: item.fiber ?? item.totalFiber, unit: 'g', digits: 1 }
  ]

  return metrics
    .filter((metric) => Number.isFinite(Number(metric.value)) && Number(metric.value) > 0)
    .map((metric) => ({
      label: metric.label,
      value: `${normalizeNumber(metric.value, metric.digits)}${metric.unit}`
    }))
}

const normalizeRecipe = (item, mealType) => ({
  ...item,
  mealType,
  mealLabel: mealTypeMap[mealType || item.mealType] || item.category || '推荐',
  name: item.name || item.recipeName || '未命名食谱',
  description: item.description || item.summary || '根据当前目标自动筛选的推荐结果。',
  reason: item.recommendationReason || item.recommendReason || item.reason || '',
  calories: normalizeNumber(item.calories ?? item.totalCalories ?? item.caloriesPerServing),
  protein: normalizeNumber(item.protein, 1),
  carbs: normalizeNumber(item.carbs, 1),
  fat: normalizeNumber(item.fat, 1),
  healthMetrics: buildHealthMetrics(item),
  cookingTimeText: item.cookingTime ? `${item.cookingTime} 分钟` : '时间未标注',
  difficultyText: item.difficulty || '难度未标注'
})

const flattenRecipes = (data) => {
  if (data?.data) {
    return flattenRecipes(data.data)
  }

  if (data?.recommendations) {
    return flattenRecipes(data.recommendations)
  }

  if (data?.result) {
    return flattenRecipes(data.result)
  }

  if (Array.isArray(data?.list)) {
    return data.list.map((item) => normalizeRecipe(item, item.mealType || ''))
  }

  if (Array.isArray(data?.records)) {
    return data.records.map((item) => normalizeRecipe(item, item.mealType || ''))
  }

  if (Array.isArray(data)) {
    return data.map((item) => normalizeRecipe(item, item.mealType || ''))
  }

  const result = []
  Object.entries(data || {}).forEach(([mealType, list]) => {
    ;(Array.isArray(list) ? list : []).forEach((item) => {
      result.push(normalizeRecipe(item, mealType))
    })
  })
  return result
}

const uniqueRecipes = (list) => {
  const seen = new Set()
  const result = []
  list.forEach((recipe) => {
    const key = recipe.id || `${recipe.name}-${recipe.mealType}`
    if (seen.has(key)) return
    seen.add(key)
    result.push(recipe)
  })
  return result
}

const loadCollectedRecipes = async () => {
  try {
    const response = await recipeApi.getCollectedRecipes()
    if (response.code === 200 && Array.isArray(response.data)) {
      collectedIds.value = new Set(
        response.data.map((item) => Number(item.id)).filter((item) => Number.isFinite(item))
      )
      return
    }
  } catch (error) {
  }

  collectedIds.value = new Set()
}

const loadTodayCandidates = async ({ force = false } = {}) => {
  if (hasLoadedToday.value && todayRecipes.value.length && !force) {
    return
  }

  loading.value = true
  try {
    let candidates = []

    try {
      const candidateResponse = await recipeApi.getRecommendations({
        breakfastCount: 8,
        lunchCount: 8,
        dinnerCount: 8
      })
      if (candidateResponse.code === 200) {
        candidates = flattenRecipes(candidateResponse)
      }
    } catch (error) {
      candidates = []
    }

    if (!candidates.length) {
      const todayResponse = await recipeApi.getTodayRecipes()
      candidates = todayResponse.code === 200 ? flattenRecipes(todayResponse) : []
    }

    if (!candidates.length) {
      const allResponse = await recipeApi.getAllRecipes()
      candidates = allResponse.code === 200 ? flattenRecipes(allResponse) : []
    }

    todayRecipes.value = uniqueRecipes(candidates)
    batchIndex.value = 0
    hasLoadedToday.value = true
  } catch (error) {
    todayRecipes.value = []
    batchIndex.value = 0
    hasLoadedToday.value = false
    if (!userStore.hasHealthInfo || !userStore.hasDietGoal) {
      uni.showToast({ title: '请先完善健康档案和饮食目标', icon: 'none' })
    }
  } finally {
    loading.value = false
  }
}

const loadCustomRecipes = async ({ force = false } = {}) => {
  if (hasLoadedCustom.value && customRecipes.value.length && !force) {
    return
  }

  loading.value = true
  try {
    const response = await recipeApi.getCustomRecipes()
    customRecipes.value = response.code === 200 ? flattenRecipes(response.data) : []
    batchIndex.value = 0
    hasLoadedCustom.value = true
  } catch (error) {
    customRecipes.value = []
    hasLoadedCustom.value = false
  } finally {
    loading.value = false
  }
}

const loadCurrentTab = async ({ force = false } = {}) => {
  if (currentTab.value === 'custom') {
    await loadCustomRecipes({ force })
    return
  }
  await loadTodayCandidates({ force })
}

const changeTab = async (value) => {
  if (currentTab.value === value) return
  currentTab.value = value
  batchIndex.value = 0
  await loadCurrentTab()
}

const changeBatch = async () => {
  if (todayBatchCount.value > 1) {
    batchIndex.value = (batchIndex.value + 1) % todayBatchCount.value
    return
  }

  await loadTodayCandidates({ force: true })
  if (todayBatchCount.value <= 1) {
    uni.showToast({ title: '暂无更多推荐', icon: 'none' })
  }
}

const handleHeroAction = () => {
  loadCurrentTab({ force: true })
}

const isCollected = (recipe) => collectedIds.value.has(Number(recipe.id))

const toggleCollect = async (recipe) => {
  const recipeId = Number(recipe.id)
  if (!Number.isFinite(recipeId)) {
    uni.showToast({ title: '当前食谱暂不支持收藏', icon: 'none' })
    return
  }

  try {
    const response = isCollected(recipe)
      ? await recipeApi.cancelCollectRecipe(recipeId)
      : await recipeApi.collectRecipe(recipeId)

    if (response.code !== 200) {
      throw new Error(response.message || '操作失败')
    }

    const next = new Set(collectedIds.value)
    if (response.data?.collected) {
      next.add(recipeId)
    } else {
      next.delete(recipeId)
    }
    collectedIds.value = next
    uni.showToast({ title: response.data?.collected ? '已收藏' : '已取消', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error.message || '操作失败', icon: 'none' })
  }
}

const openRecipe = (recipe) => {
  if (!recipe?.id) return
  const mealType = recipe.mealType || ''
  const servingFactor = recipe.servingFactor || 1
  const recommendedNutrition = recipe.recommendedNutrition
  const calories = recommendedNutrition?.calories ?? recipe.totalCalories ?? Number(recipe.calories)
  const protein = recommendedNutrition?.protein ?? Number(recipe.protein)
  const carbs = recommendedNutrition?.carbs ?? Number(recipe.carbs)
  const fat = recommendedNutrition?.fat ?? Number(recipe.fat)
  const params = [
    `id=${recipe.id}`,
    `mealType=${mealType}`,
    `servingFactor=${servingFactor}`,
    `calories=${calories || ''}`,
    `protein=${protein || ''}`,
    `carbs=${carbs || ''}`,
    `fat=${fat || ''}`
  ].join('&')
  uni.navigateTo({ url: `/pages/detail/recipe?${params}` })
}

onShow(async () => {
  await loadCollectedRecipes()
  await loadCurrentTab()
})
</script>

<style scoped lang="scss">
.recipes-page {
  padding-top: 20rpx;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  padding: 32rpx;
  align-items: flex-start;
}

.hero-title {
  font-size: 40rpx;
  font-weight: 700;
}

.hero-desc {
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #5b6159;
}

.hero-action {
  color: #486646;
  font-size: 24rpx;
}

.tab-row {
  display: flex;
  gap: 14rpx;
  padding: 12rpx;
  margin-top: 22rpx;
}

.tab-pill {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 72rpx;
  border-radius: 999rpx;
  background: transparent;
  color: #5b6159;
  font-size: 24rpx;
}

.tab-pill.active {
  background: #486646;
  color: #eff8eb;
}

.summary-card {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  align-items: center;
  margin-top: 22rpx;
  padding: 26rpx 28rpx;
}

.summary-label,
.metric-label {
  display: block;
  font-size: 22rpx;
  color: #5b6159;
}

.summary-value {
  display: block;
  margin-top: 10rpx;
  font-size: 32rpx;
  font-weight: 700;
}

.summary-meta {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #7c8578;
}

.change-button {
  flex-shrink: 0;
  padding: 18rpx 26rpx;
  border-radius: 999rpx;
  background: #486646;
  color: #eff8eb;
  font-size: 24rpx;
}

.list-stack {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 22rpx;
}

.recipe-card {
  padding: 28rpx;
  border: 1rpx solid rgba(72, 102, 70, 0.08);
}

.recipe-top {
  display: flex;
  gap: 18rpx;
  align-items: flex-start;
}

.recipe-badge {
  width: 86rpx;
  height: 86rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #486646 0%, #6f8f61 100%);
  color: #eff8eb;
  font-size: 22rpx;
  font-weight: 700;
  flex-shrink: 0;
}

.recipe-title-block {
  flex: 1;
  min-width: 0;
}

.recipe-title {
  display: block;
  font-size: 32rpx;
  line-height: 1.45;
  font-weight: 700;
  color: #20291f;
}

.recipe-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: #5b6159;
}

.reason-card {
  margin-top: 18rpx;
  padding: 18rpx 20rpx;
  border-radius: 22rpx;
  background: #f3f7ef;
  color: #52624c;
  font-size: 23rpx;
  line-height: 1.6;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 20rpx;
}

.metric-item {
  padding: 20rpx;
  border-radius: 24rpx;
  background: #f6f8f2;
}

.primary-metric {
  background: #edf5e8;
}

.metric-value {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  font-weight: 600;
  color: #2e342d;
}

.health-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 18rpx;
}

.health-pill {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: #fff7e8;
  color: #7d5c22;
  font-size: 21rpx;
}

.recipe-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18rpx;
  margin-top: 22rpx;
  padding-top: 18rpx;
  border-top: 1rpx solid #eef3ea;
}

.recipe-meta {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  color: #7c8578;
  font-size: 21rpx;
}

.action-row {
  display: flex;
  gap: 12rpx;
}

.small-btn {
  width: 132rpx;
  height: 72rpx;
  font-size: 24rpx;
}

.empty-card {
  margin-top: 22rpx;
  padding: 36rpx 28rpx;
  text-align: center;
  color: #7c8578;
  font-size: 24rpx;
}

.clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
