<template>
  <view class="page-shell safe-bottom">
    <view class="page-content goal-page">
      <view class="hero-block">
        <view class="hero-title">设置饮食目标</view>
        <view class="hero-desc">系统会结合你的健康档案、目标体重和周期，自动生成热量与营养比例建议。</view>
      </view>

      <view class="card form-card">
        <view class="form-item">
          <text class="form-label">目标类型</text>
          <view class="goal-grid">
            <view
              v-for="option in goalOptions"
              :key="option.value"
              class="goal-card"
              :class="{ active: form.goalType === option.value }"
              @click="selectGoal(option.value)"
            >
              <text class="goal-name">{{ option.label }}</text>
              <text class="goal-tip">{{ option.tip }}</text>
            </view>
          </view>
        </view>

        <view class="grid-2">
          <view class="form-item">
            <text class="form-label">当前体重</text>
            <view class="metric-card soft-card">
              <text class="metric-value">{{ currentWeightText }}</text>
            </view>
          </view>
          <view class="form-item">
            <text class="form-label">目标体重(kg)</text>
            <view class="input-card">
              <input v-model="form.targetWeight" placeholder="可选填写" type="digit" />
            </view>
          </view>
        </view>

        <view class="grid-2">
          <view class="form-item">
            <text class="form-label">开始日期</text>
            <picker mode="date" :value="form.startDate" @change="(e) => setDate('startDate', e.detail.value)">
              <view class="input-card picker-card">
                <text>{{ form.startDate || '请选择开始日期' }}</text>
              </view>
            </picker>
          </view>
          <view class="form-item">
            <text class="form-label">结束日期</text>
            <picker mode="date" :value="form.endDate" @change="(e) => setDate('endDate', e.detail.value)">
              <view class="input-card picker-card">
                <text>{{ form.endDate || '请选择结束日期' }}</text>
              </view>
            </picker>
          </view>
        </view>

        <view class="form-item">
          <view class="switch-row soft-card">
            <view>
              <text class="switch-title">开启每日提醒</text>
              <text class="switch-desc">按设定时间提醒你关注当日饮食目标。</text>
            </view>
            <switch :checked="form.reminderEnabled === 1" color="#486646" @change="handleReminderSwitch" />
          </view>
        </view>

        <view v-if="form.reminderEnabled === 1" class="form-item">
          <text class="form-label">提醒时间</text>
          <picker mode="time" :value="displayReminderTime" @change="handleTimeChange">
            <view class="input-card picker-card">
              <text>{{ displayReminderTime || '请选择提醒时间' }}</text>
            </view>
          </picker>
        </view>

        <view class="recommend-card soft-card">
          <view class="recommend-head">
            <view>
              <text class="recommend-title">系统推荐</text>
              <text class="recommend-desc">会根据你的健康信息自动更新</text>
            </view>
            <text class="recommend-action" @click="generateRecommendation">重新生成</text>
          </view>

          <view class="metric-panel highlight">
            <text class="metric-label">推荐热量</text>
            <text class="metric-main">{{ displayNumber(recommendedGoal.targetCalories, 'kcal') }}</text>
          </view>

          <view class="grid-2 compact-grid">
            <view class="metric-panel">
              <text class="metric-label">蛋白质</text>
              <text class="metric-main small">{{ displayNumber(recommendedGoal.proteinTarget, 'g') }}</text>
              <text class="metric-sub">{{ displayNumber(recommendedGoal.proteinRatio, '%') }}</text>
            </view>
            <view class="metric-panel">
              <text class="metric-label">碳水</text>
              <text class="metric-main small">{{ displayNumber(recommendedGoal.carbsTarget, 'g') }}</text>
              <text class="metric-sub">{{ displayNumber(recommendedGoal.carbsRatio, '%') }}</text>
            </view>
            <view class="metric-panel">
              <text class="metric-label">脂肪</text>
              <text class="metric-main small">{{ displayNumber(recommendedGoal.fatTarget, 'g') }}</text>
              <text class="metric-sub">{{ displayNumber(recommendedGoal.fatRatio, '%') }}</text>
            </view>
            <view class="metric-panel">
              <text class="metric-label">饮水</text>
              <text class="metric-main small">{{ displayNumber(recommendedGoal.waterTarget, 'ml') }}</text>
              <text class="metric-sub">{{ displaySignedValue(recommendationContext.dailyAdjustment, 'kcal/日') }}</text>
            </view>
          </view>

          <view class="recommend-note">{{ recommendationContext.advice || '选择目标后会显示推荐说明。' }}</view>
        </view>

        <button class="primary-button" :disabled="loading" @click="saveGoal">
          {{ loading ? '保存中...' : '保存并进入首页' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import dietGoalApi from '@/api/dietGoal'
import { useUserStore } from '@/store/user'
import {
  computeDietGoalRecommendation,
  formatGoalDate,
  formatGoalTime
} from '@/utils/dietGoalRecommendation'
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

const userStore = useUserStore()
const loading = ref(false)
const goalOptions = [
  { value: 'fat_loss', label: '减肥减脂', tip: '降低热量缺口，稳步减重' },
  { value: 'muscle_toning', label: '增肌塑形', tip: '提升蛋白摄入，兼顾训练恢复' },
  { value: 'weight_maintenance', label: '维持体重', tip: '保持稳定饮食结构' },
  { value: 'healthy_weight_gain', label: '健康增重', tip: '温和增加热量与营养' },
  { value: 'blood_sugar_control', label: '控糖饮食', tip: '控制碳水波动，优先稳糖' },
  { value: 'lipid_control', label: '控脂降脂', tip: '优化脂肪结构与总热量' },
  { value: 'low_sodium', label: '控压低盐', tip: '减少钠摄入，清淡饮食' },
  { value: 'pregnancy_nutrition', label: '孕妇营养', tip: '兼顾孕期补充需求' },
  { value: 'child_growth', label: '儿童成长', tip: '平衡成长所需营养' },
  { value: 'senior_wellness', label: '老年养生', tip: '控制负担，重视蛋白与补水' }
]

const form = reactive({
  goalType: '',
  targetWeight: '',
  targetCalories: 2000,
  proteinRatio: 30,
  carbsRatio: 45,
  fatRatio: 25,
  proteinTarget: '',
  carbsTarget: '',
  fatTarget: '',
  waterTarget: 2000,
  status: 1,
  startDate: '',
  endDate: '',
  reminderEnabled: 1,
  reminderTime: '09:00:00'
})

const recommendedGoal = reactive({
  targetCalories: null,
  proteinRatio: null,
  carbsRatio: null,
  fatRatio: null,
  proteinTarget: null,
  carbsTarget: null,
  fatTarget: null,
  waterTarget: null
})

const recommendationContext = reactive({
  targetWeight: null,
  targetWeightUsed: false,
  planDays: null,
  weightDelta: null,
  dailyAdjustment: null,
  estimatedTdee: null,
  advice: ''
})

const currentWeightText = computed(() => userStore.healthInfo?.weight ? `${userStore.healthInfo.weight} kg` : '--')

const displayReminderTime = computed(() => (form.reminderTime ? String(form.reminderTime).slice(0, 5) : ''))

const syncFormFromExisting = () => {
  const goal = userStore.dietGoal || {}
  const today = new Date()
  const defaultEnd = new Date(today.getTime() + 84 * 24 * 60 * 60 * 1000)

  form.goalType = goal.goalType || form.goalType || 'weight_maintenance'
  form.targetWeight = goal.targetWeight !== null && goal.targetWeight !== undefined ? String(goal.targetWeight) : ''
  form.targetCalories = goal.targetCalories || 2000
  form.proteinRatio = goal.proteinRatio || 30
  form.carbsRatio = goal.carbsRatio || 45
  form.fatRatio = goal.fatRatio || 25
  form.proteinTarget = goal.proteinTarget || ''
  form.carbsTarget = goal.carbsTarget || ''
  form.fatTarget = goal.fatTarget || ''
  form.waterTarget = goal.waterTarget || 2000
  form.status = goal.status || 1
  form.startDate = goal.startDate || formatGoalDate(today)
  form.endDate = goal.endDate || formatGoalDate(defaultEnd)
  form.reminderEnabled = goal.reminderEnabled === 0 ? 0 : 1
  form.reminderTime = goal.reminderTime || '09:00:00'
  generateRecommendation(true)
}

const displayNumber = (value, unit = '') => {
  if (value === null || value === undefined || value === '') return '--'
  return `${value}${unit ? ` ${unit}` : ''}`
}

const displaySignedValue = (value, unit = '') => {
  if (value === null || value === undefined || value === '') return '--'
  const number = Number(value)
  return `${number > 0 ? '+' : ''}${Number.isInteger(number) ? number : number.toFixed(1)}${unit ? ` ${unit}` : ''}`
}

const applyRecommendation = (result) => {
  Object.assign(recommendedGoal, result.recommendedGoal)
  Object.assign(recommendationContext, result.recommendationContext)
  form.targetCalories = result.recommendedGoal.targetCalories
  form.proteinRatio = result.recommendedGoal.proteinRatio
  form.carbsRatio = result.recommendedGoal.carbsRatio
  form.fatRatio = result.recommendedGoal.fatRatio
  form.proteinTarget = result.recommendedGoal.proteinTarget
  form.carbsTarget = result.recommendedGoal.carbsTarget
  form.fatTarget = result.recommendedGoal.fatTarget
  form.waterTarget = result.recommendedGoal.waterTarget
}

const generateRecommendation = (silent = false) => {
  const result = computeDietGoalRecommendation({
    healthInfo: userStore.healthInfo,
    goalForm: {
      ...form,
      targetWeight: form.targetWeight ? Number(form.targetWeight) : null
    }
  })

  if (!result) {
    if (!silent) {
      uni.showToast({ title: '请先完善健康信息', icon: 'none' })
    }
    return
  }

  applyRecommendation(result)
}

const selectGoal = (goalType) => {
  form.goalType = goalType
  generateRecommendation(true)
}

const setDate = (field, value) => {
  form[field] = value
  generateRecommendation(true)
}

const handleReminderSwitch = (event) => {
  form.reminderEnabled = event.detail.value ? 1 : 0
}

const handleTimeChange = (event) => {
  form.reminderTime = `${event.detail.value}:00`
}

const saveGoal = async () => {
  if (!form.goalType) {
    uni.showToast({ title: '请选择目标类型', icon: 'none' })
    return
  }
  if (!form.startDate) {
    uni.showToast({ title: '请选择开始日期', icon: 'none' })
    return
  }

  generateRecommendation(true)
  loading.value = true
  try {
    const payload = {
      ...form,
      targetWeight: form.targetWeight ? Number(form.targetWeight) : null,
      targetCalories: Number(form.targetCalories || 0),
      proteinRatio: Number(form.proteinRatio || 0),
      carbsRatio: Number(form.carbsRatio || 0),
      fatRatio: Number(form.fatRatio || 0),
      proteinTarget: form.proteinTarget ? Number(form.proteinTarget) : null,
      carbsTarget: form.carbsTarget ? Number(form.carbsTarget) : null,
      fatTarget: form.fatTarget ? Number(form.fatTarget) : null,
      waterTarget: Number(form.waterTarget || 0),
      startDate: formatGoalDate(form.startDate),
      endDate: formatGoalDate(form.endDate),
      reminderTime: form.reminderEnabled === 1 ? formatGoalTime(form.reminderTime) : null
    }

    const response = await (userStore.hasDietGoal ? dietGoalApi.updateDietGoal(payload) : dietGoalApi.saveDietGoal(payload))
    if (response.code !== 200) {
      throw new Error(response.message || '保存失败')
    }

    userStore.setDietGoal(response.data || payload)
    userStore.setDietGoalMeta({
      ...(response.meta || {}),
      recommendationContext: { ...recommendationContext },
      appliedWeight: userStore.healthInfo?.weight || null,
      updatedAt: new Date().toISOString()
    })

    uni.showToast({ title: '目标已保存', icon: 'success' })
    uni.switchTab({ url: '/pages/tabbar/home' })
  } catch (error) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

onShow(() => {
  syncFormFromExisting()
})
</script>

<style scoped lang="scss">
.goal-page {
  padding-top: 20rpx;
}

.hero-block {
  margin-bottom: 28rpx;
}

.hero-title {
  font-size: 42rpx;
  font-weight: 700;
}

.hero-desc {
  margin-top: 14rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: #5b6159;
}

.form-card {
  padding: 32rpx;
}

.form-item {
  margin-bottom: 24rpx;
}

.form-label {
  display: block;
  margin-bottom: 12rpx;
  font-size: 24rpx;
  color: #5b6159;
}

.goal-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.goal-card {
  padding: 24rpx 22rpx;
  border-radius: 28rpx;
  background: #f2f5ed;
}

.goal-card.active {
  background: #486646;
}

.goal-name {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #2e342d;
}

.goal-tip {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #5b6159;
}

.goal-card.active .goal-name,
.goal-card.active .goal-tip {
  color: #eff8eb;
}

.metric-card,
.metric-panel,
.switch-row,
.recommend-card {
  border-radius: 28rpx;
}

.metric-card {
  min-height: 96rpx;
  display: flex;
  align-items: center;
  padding: 0 28rpx;
}

.metric-value {
  font-size: 28rpx;
  color: #2e342d;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  padding: 24rpx 28rpx;
}

.switch-title {
  display: block;
  font-size: 28rpx;
  color: #2e342d;
}

.switch-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #5b6159;
}

.recommend-card {
  margin-bottom: 28rpx;
  padding: 28rpx;
}

.recommend-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.recommend-title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
}

.recommend-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #5b6159;
}

.recommend-action {
  color: #486646;
  font-size: 24rpx;
}

.metric-panel {
  margin-top: 20rpx;
  padding: 24rpx;
  background: #ffffff;
}

.metric-panel.highlight {
  background: rgba(72, 102, 70, 0.1);
}

.metric-label {
  display: block;
  font-size: 22rpx;
  color: #5b6159;
}

.metric-main {
  display: block;
  margin-top: 10rpx;
  font-size: 44rpx;
  font-weight: 700;
  color: #2e342d;
}

.metric-main.small {
  font-size: 34rpx;
}

.metric-sub {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #486646;
}

.compact-grid {
  margin-top: 0;
}

.recommend-note {
  margin-top: 20rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #5b6159;
}

.picker-card {
  justify-content: space-between;
}
</style>
