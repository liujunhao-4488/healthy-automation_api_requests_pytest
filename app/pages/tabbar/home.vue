<template>
  <view class="page-shell safe-bottom">
    <view class="page-content home-page">
      <view class="hero-card card">
        <view class="hero-mark">智能饮食管理</view>
        <view class="hero-title">{{ greeting }}, {{ displayUsername }}</view>
        <view class="hero-desc">继续查看你的健康档案、饮食目标与今日推荐。</view>
      </view>

      <view class="summary-grid">
        <view class="summary-card soft-card">
          <text class="summary-label">当前体重</text>
          <text class="summary-value">{{ displayWeight }}</text>
          <text class="summary-meta">BMI {{ displayBmi }}</text>
        </view>
        <view class="summary-card soft-card">
          <text class="summary-label">饮食目标</text>
          <text class="summary-value">{{ goalLabel }}</text>
          <text class="summary-meta">{{ displayCalories }}</text>
        </view>
        <view class="summary-card soft-card">
          <text class="summary-label">未读通知</text>
          <text class="summary-value">{{ unreadCount }}</text>
          <text class="summary-meta">条提醒</text>
        </view>
      </view>

      <view class="section-block">
        <view class="section-title">
          <text class="section-title__text">快捷入口</text>
        </view>
        <view class="action-grid">
          <view class="action-card card" @click="switchTab('/pages/tabbar/recipes')">
            <text class="action-title">食谱推荐</text>
            <text class="action-desc">查看推荐、今日与自定义食谱</text>
          </view>
          <view class="action-card card" @click="switchTab('/pages/tabbar/record')">
            <text class="action-title">饮食记录</text>
            <text class="action-desc">补充今日饮食并查看趋势</text>
          </view>
          <view class="action-card card" @click="switchTab('/pages/tabbar/knowledge')">
            <text class="action-title">健康知识</text>
            <text class="action-desc">浏览推荐文章与科普内容</text>
          </view>
          <view class="action-card card" @click="openNotifications">
            <text class="action-title">消息中心</text>
            <text class="action-desc">查看系统通知与提醒消息</text>
          </view>
        </view>
      </view>

      <view class="section-block">
        <view class="section-title">
          <text class="section-title__text">健康摘要</text>
          <text class="section-title__meta" @click="openGoalSetup">编辑目标</text>
        </view>
        <view class="card info-card">
          <view class="info-row">
            <text>基础代谢</text>
            <text>{{ displayBmr }}</text>
          </view>
          <view class="info-row">
            <text>活动水平</text>
            <text>{{ activityLabel }}</text>
          </view>
          <view class="info-row">
            <text>目标体重</text>
            <text>{{ displayTargetWeight }}</text>
          </view>
          <view class="info-row no-border">
            <text>推荐说明</text>
            <text class="info-note">{{ recommendationNote }}</text>
          </view>
        </view>
      </view>

      <view class="section-block">
        <view class="section-title">
          <text class="section-title__text">今日推荐食谱</text>
          <text class="section-title__meta" @click="switchTab('/pages/tabbar/recipes')">查看更多</text>
        </view>
        <view v-if="todayRecipes.length" class="list-stack">
          <view v-for="(item, index) in todayRecipes" :key="item.id || `${item.mealType}-${index}`" class="card list-card" @click="openRecipe(item)">
            <view class="list-head">
              <text class="list-title">{{ item.name }}</text>
              <text class="list-tag">{{ item.mealLabel }}</text>
            </view>
            <text class="list-desc">{{ item.description }}</text>
            <view class="metric-row">
              <text>{{ item.calories }} kcal</text>
              <text>蛋白 {{ item.protein }} g</text>
            </view>
          </view>
        </view>
        <view v-else class="card empty-card">
          <text>{{ loading ? '加载中...' : '暂无今日推荐食谱' }}</text>
        </view>
      </view>

      <view class="section-block">
        <view class="section-title">
          <text class="section-title__text">推荐知识</text>
          <text class="section-title__meta" @click="switchTab('/pages/tabbar/knowledge')">查看更多</text>
        </view>
        <view v-if="recommendedArticles.length" class="list-stack">
          <view v-for="article in recommendedArticles" :key="article.id" class="card list-card" @click="openArticle(article)">
            <view class="list-head">
              <text class="list-title">{{ article.title }}</text>
              <text class="list-tag light">{{ article.category || '推荐' }}</text>
            </view>
            <text class="list-desc clamp-2">{{ article.summary }}</text>
          </view>
        </view>
        <view v-else class="card empty-card">
          <text>{{ loading ? '加载中...' : '暂无推荐文章' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import recipeApi from '@/api/recipe'
import healthKnowledgeApi from '@/api/healthKnowledge'
import notificationApi from '@/api/notification'
import { useUserStore } from '@/store/user'
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

const userStore = useUserStore()
const loading = ref(false)
const todayRecipes = ref([])
const recommendedArticles = ref([])
const unreadCount = ref(0)

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const displayUsername = computed(() => userStore.username || '用户')
const displayWeight = computed(() => userStore.healthInfo?.weight ? `${userStore.healthInfo.weight} kg` : '--')
const displayBmi = computed(() => userStore.healthInfo?.bmi || '--')
const displayBmr = computed(() => userStore.healthInfo?.bmr ? `${userStore.healthInfo.bmr} kcal` : '--')
const displayCalories = computed(() => userStore.dietGoal?.targetCalories ? `${userStore.dietGoal.targetCalories} kcal/日` : '未设置')
const displayTargetWeight = computed(() => userStore.dietGoal?.targetWeight ? `${userStore.dietGoal.targetWeight} kg` : '未设置')
const recommendationNote = computed(() => userStore.dietGoalMeta?.recommendationContext?.advice || '完善健康档案后，系统会生成更准确的饮食建议。')
const goalLabel = computed(() => goalLabelMap[userStore.dietGoal?.goalType] || '未设置')
const activityLabel = computed(() => activityMap[userStore.healthInfo?.activityLevel] || '未设置')

const goalLabelMap = {
  fat_loss: '减肥减脂',
  muscle_toning: '增肌塑形',
  weight_maintenance: '维持体重',
  healthy_weight_gain: '健康增重',
  blood_sugar_control: '控糖饮食',
  lipid_control: '控脂降脂',
  low_sodium: '控压低盐',
  pregnancy_nutrition: '孕妇营养',
  child_growth: '儿童成长',
  senior_wellness: '老年养生'
}

const activityMap = {
  sedentary: '久坐不动',
  lightly_active: '轻度活动',
  moderately_active: '中度活动',
  very_active: '高度活动',
  extra_active: '极高活动'
}

const normalizeNumber = (value, digits = 0) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return '--'
  return digits > 0 ? number.toFixed(digits) : String(Math.round(number))
}

const flattenRecipeGroups = (data) => {
  if (Array.isArray(data)) {
    return data.map((item) => ({
      ...item,
      mealType: item.mealType || '',
      mealLabel: mealTypeMap[item.mealType] || '推荐',
      name: item.name || item.recipeName || '未命名食谱',
      description: item.description || item.recommendationReason || '根据你的健康目标自动推荐。',
      calories: normalizeNumber(item.calories ?? item.totalCalories),
      protein: normalizeNumber(item.protein, 1)
    }))
  }

  const groups = []
  Object.entries(data || {}).forEach(([mealType, list]) => {
    ;(Array.isArray(list) ? list : []).forEach((item) => {
      groups.push({
        ...item,
        mealType,
        mealLabel: mealTypeMap[mealType] || '推荐',
        name: item.name || item.recipeName || '未命名食谱',
        description: item.description || item.recommendationReason || '根据你的健康目标自动推荐。',
        calories: normalizeNumber(item.calories ?? item.totalCalories),
        protein: normalizeNumber(item.protein, 1)
      })
    })
  })
  return groups
}

const mealTypeMap = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐'
}

const normalizeArticle = (item) => ({
  ...item,
  summary: String(item.summary || item.content || '暂无摘要').replace(/\s+/g, ' ').slice(0, 60)
})

const extractArticleList = (data) => {
  if (Array.isArray(data?.records)) {
    return data.records
  }

  if (Array.isArray(data?.list)) {
    return data.list
  }

  return Array.isArray(data) ? data : []
}

const loadRecommendedArticles = async () => {
  const recommendResponse = await healthKnowledgeApi.getRecommendedArticles({ page: 1, pageSize: 3 })
  let list = recommendResponse.code === 200 ? extractArticleList(recommendResponse.data) : []

  if (!list.length) {
    const listResponse = await healthKnowledgeApi.getKnowledgeList({ page: 1, pageSize: 3, sort: 'latest' })
    list = listResponse.code === 200 ? extractArticleList(listResponse.data) : []
  }

  return list.map(normalizeArticle).slice(0, 3)
}

const loadData = async () => {
  loading.value = true
  try {
    const [recipeResponse, articleList, notificationResponse] = await Promise.all([
      recipeApi.getTodayRecipes(),
      loadRecommendedArticles(),
      notificationApi.getNotifications()
    ])

    todayRecipes.value = recipeResponse.code === 200 ? flattenRecipeGroups(recipeResponse.data).slice(0, 3) : []
    recommendedArticles.value = articleList

    const notifications = notificationResponse.code === 200 && Array.isArray(notificationResponse.data)
      ? notificationResponse.data
      : []
    unreadCount.value = notifications.filter((item) => !item.isRead).length
  } catch (error) {
    todayRecipes.value = []
    recommendedArticles.value = []
    unreadCount.value = 0
  } finally {
    loading.value = false
  }
}

const switchTab = (url) => {
  uni.switchTab({ url })
}

const openNotifications = () => {
  uni.navigateTo({ url: '/pages/detail/notifications' })
}

const openGoalSetup = () => {
  uni.navigateTo({ url: '/pages/onboarding/diet-goal' })
}

const openRecipe = (item) => {
  if (!item?.id) return
  const mealType = item.mealType || ''
  const servingFactor = item.servingFactor || 1
  const recommendedNutrition = item.recommendedNutrition
  const calories = recommendedNutrition?.calories ?? item.totalCalories ?? Number(item.calories)
  const protein = recommendedNutrition?.protein ?? Number(item.protein)
  const carbs = recommendedNutrition?.carbs ?? Number(item.carbs)
  const fat = recommendedNutrition?.fat ?? Number(item.fat)
  const params = [
    `id=${item.id}`,
    `mealType=${mealType}`,
    `servingFactor=${servingFactor}`,
    `calories=${calories || ''}`,
    `protein=${protein || ''}`,
    `carbs=${carbs || ''}`,
    `fat=${fat || ''}`
  ].join('&')
  uni.navigateTo({ url: `/pages/detail/recipe?${params}` })
}

const openArticle = (item) => {
  if (!item?.id) return
  uni.navigateTo({ url: `/pages/detail/article?id=${item.id}` })
}

onShow(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.home-page {
  padding-top: 20rpx;
}

.hero-card {
  padding: 36rpx 32rpx;
  background: linear-gradient(135deg, #f6fbf3 0%, #eef6eb 100%);
}

.hero-mark {
  display: inline-flex;
  padding: 12rpx 24rpx;
  border-radius: 999rpx;
  background: rgba(72, 102, 70, 0.12);
  color: #486646;
  font-size: 22rpx;
}

.hero-title {
  margin-top: 22rpx;
  font-size: 44rpx;
  font-weight: 700;
}

.hero-desc {
  margin-top: 12rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: #5b6159;
}

.summary-grid,
.action-grid {
  display: grid;
  gap: 18rpx;
}

.summary-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 24rpx;
}

.summary-card {
  padding: 24rpx;
}

.summary-label {
  display: block;
  font-size: 22rpx;
  color: #5b6159;
}

.summary-value {
  display: block;
  margin-top: 14rpx;
  font-size: 32rpx;
  font-weight: 700;
  color: #2e342d;
}

.summary-meta {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #7c8578;
}

.section-block {
  margin-top: 28rpx;
}

.action-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.action-card {
  padding: 28rpx 24rpx;
}

.action-title,
.list-title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #2e342d;
}

.action-desc,
.list-desc,
.info-note {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: #5b6159;
}

.info-card,
.list-card,
.empty-card {
  padding: 28rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 24rpx;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #edf1e8;
  font-size: 24rpx;
  color: #2e342d;
}

.info-row.no-border {
  border-bottom: none;
}

.list-stack {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.list-head,
.metric-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.list-tag {
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: #486646;
  color: #eff8eb;
  font-size: 22rpx;
}

.list-tag.light {
  background: #edf3e8;
  color: #486646;
}

.metric-row {
  margin-top: 16rpx;
  font-size: 22rpx;
  color: #6f776c;
}

.empty-card {
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
