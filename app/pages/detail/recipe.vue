<template>
  <view class="page-shell safe-bottom">
    <view class="page-content detail-page">
      <view class="hero-card card">
        <view>
          <view class="hero-title">食谱详情</view>
          <view class="hero-desc">查看食谱营养信息、做法和收藏状态。</view>
        </view>
        <text class="hero-action" @click="loadDetail">刷新</text>
      </view>

      <view v-if="loading" class="card empty-card">
        <text>正在加载食谱详情...</text>
      </view>

      <view v-else-if="recipe" class="list-stack">
        <view class="card detail-card">
          <view class="detail-head">
            <view>
              <text class="detail-title">{{ recipe.name }}</text>
              <text class="detail-desc">{{ recipe.description }}</text>
            </view>
            <text class="detail-tag">{{ recipe.mealLabel }}</text>
          </view>

          <view class="metrics-grid">
            <view class="metric-item">
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

          <view class="action-row">
            <button class="primary-button action-btn" :disabled="recordLoading" @click="addToDietRecord">
              {{ recordLoading ? '添加中...' : '添加到饮食记录' }}
            </button>
          </view>
        </view>

        <view class="card detail-card">
          <view class="section-title">
            <text class="section-title__text">食材与做法</text>
          </view>
          <view v-if="recipe.ingredientsText" class="content-block">
            <text class="content-heading">食材</text>
            <text class="content-text">{{ recipe.ingredientsText }}</text>
          </view>
          <view class="content-block" :class="{ 'content-block-top': recipe.ingredientsText }">
            <text v-if="recipe.ingredientsText" class="content-heading">做法</text>
            <text class="content-text">{{ recipe.content }}</text>
          </view>
        </view>
      </view>

      <view v-else class="card empty-card">
        <text>未找到对应食谱</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import dietRecordApi from '@/api/dietRecord'
import recipeApi from '@/api/recipe'
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const loading = ref(false)
const recordLoading = ref(false)
const recipeId = ref('')
const recipeMealType = ref('')
const recipeServingFactor = ref(1)
const recipeRecommendedCalories = ref(0)
const recipeRecommendedProtein = ref(0)
const recipeRecommendedCarbs = ref(0)
const recipeRecommendedFat = ref(0)
const recipe = ref(null)

const mealTypeMap = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐'
}

const normalizeNumber = (value, digits = 0) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return '--'
  return digits > 0 ? number.toFixed(digits) : String(Math.round(number))
}

const formatIngredientLine = (item) => {
  const quantity = item.quantity ?? item.quantityValue
  const quantityText = quantity === null || quantity === undefined || quantity === ''
    ? ''
    : normalizeNumber(quantity, 1)
  const unitText = item.unit || ''
  return [item.name, `${quantityText}${unitText}`.trim()].filter(Boolean).join(' ')
}

const normalizeRecipe = (payload) => {
  const item = payload?.recipe || payload || {}
  const ingredients = Array.isArray(payload?.ingredients)
    ? payload.ingredients.filter((ingredient) => ingredient?.name)
    : Array.isArray(item.ingredients)
      ? item.ingredients.filter((ingredient) => ingredient?.name)
      : []

  return {
    ...item,
    ingredients,
    ingredientsText: ingredients.map(formatIngredientLine).filter(Boolean).join('\n'),
    name: item.name || item.recipeName || '未命名食谱',
    description: item.description || item.recommendationReason || item.tips || '暂无食谱描述',
    content: item.instructions || item.steps || item.method || item.content || '暂未提供详细做法。',
    mealLabel: mealTypeMap[item.mealType] || item.category || '推荐',
    calories: normalizeNumber(item.calories ?? item.totalCalories ?? item.caloriesPerServing),
    protein: normalizeNumber(item.protein, 1),
    carbs: normalizeNumber(item.carbs, 1),
    fat: normalizeNumber(item.fat, 1)
  }
}

const toNumber = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? number : 0
}

const addToDietRecord = async () => {
  if (!recipe.value?.id) {
    uni.showToast({ title: '当前食谱暂不支持记录', icon: 'none' })
    return
  }

  recordLoading.value = true
  try {
    const today = new Date().toISOString().slice(0, 10)
    const hasRecommended = Math.abs(recipeServingFactor.value - 1) > 0.05 && recipeRecommendedCalories.value > 0
    const payload = {
      date: today,
      mealType: recipeMealType.value || recipe.value.mealType || 'breakfast',
      notes: `来自食谱详情：${recipe.value.name}`,
      details: [
        {
          recipeId: recipe.value.id,
          foodName: recipe.value.name,
          amount: 1,
          unit: '份',
          calories: hasRecommended ? recipeRecommendedCalories.value : toNumber(recipe.value.calories),
          protein: hasRecommended ? recipeRecommendedProtein.value : toNumber(recipe.value.protein),
          carbs: hasRecommended ? recipeRecommendedCarbs.value : toNumber(recipe.value.carbs),
          fat: hasRecommended ? recipeRecommendedFat.value : toNumber(recipe.value.fat)
        }
      ]
    }

    const response = await dietRecordApi.submitRecord(payload)
    if (response.code !== 200) {
      throw new Error(response.message || '添加失败')
    }

    uni.showToast({ title: '已添加到饮食记录', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error.message || '添加失败', icon: 'none' })
  } finally {
    recordLoading.value = false
  }
}

const loadDetail = async () => {
  if (!recipeId.value) return
  loading.value = true
  try {
    const response = await recipeApi.getRecipeDetail(recipeId.value)
    recipe.value = response.code === 200 && response.data ? normalizeRecipe(response.data) : null
  } catch (error) {
    recipe.value = null
  } finally {
    loading.value = false
  }
}

onLoad((query) => {
  recipeId.value = query?.id || ''
  recipeMealType.value = query?.mealType || ''
  recipeServingFactor.value = Number(query?.servingFactor) || 1
  recipeRecommendedCalories.value = Number(query?.calories) || 0
  recipeRecommendedProtein.value = Number(query?.protein) || 0
  recipeRecommendedCarbs.value = Number(query?.carbs) || 0
  recipeRecommendedFat.value = Number(query?.fat) || 0
  loadDetail()
})
</script>

<style scoped lang="scss">
.detail-page {
  padding-top: 20rpx;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  padding: 32rpx;
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

.list-stack {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 22rpx;
}

.detail-card {
  padding: 28rpx;
}

.detail-head {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
}

.detail-title {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
  color: #2e342d;
}

.detail-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: #5b6159;
}

.detail-tag {
  flex-shrink: 0;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: #edf3e8;
  color: #486646;
  font-size: 22rpx;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 20rpx;
}

.metric-item {
  padding: 22rpx;
  border-radius: 24rpx;
  background: #f6f8f2;
}

.metric-label {
  display: block;
  font-size: 22rpx;
  color: #5b6159;
}

.metric-value {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  font-weight: 600;
  color: #2e342d;
}

.action-row {
  margin-top: 22rpx;
}

.action-btn {
  width: 100%;
}

.content-block-top {
  margin-top: 24rpx;
}

.content-heading {
  display: block;
  font-size: 26rpx;
  font-weight: 600;
  color: #2e342d;
}

.content-text {
  display: block;
  margin-top: 20rpx;
  font-size: 24rpx;
  line-height: 1.8;
  color: #2e342d;
  white-space: pre-wrap;
}

.empty-card {
  margin-top: 22rpx;
  padding: 36rpx 28rpx;
  text-align: center;
  color: #7c8578;
  font-size: 24rpx;
}
</style>
