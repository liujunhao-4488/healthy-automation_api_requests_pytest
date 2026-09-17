<template>
  <view class="page-shell safe-bottom">
    <view class="page-content onboarding-page">
      <view class="step-card soft-card">
        <view class="step-chip active">1 账号</view>
        <view class="step-line active" />
        <view class="step-chip active">2 基础健康</view>
        <view class="step-line active" />
        <view class="step-chip active">3 详细信息</view>
      </view>

      <view class="hero-block">
        <view class="hero-title">详细健康信息</view>
        <view class="hero-desc">补充运动习惯和身体指标后，系统才能更准确地生成饮食目标与推荐。</view>
      </view>

      <view class="card form-card">
        <view class="form-item">
          <text class="form-label">血压</text>
          <view class="input-card">
            <input v-model.trim="form.bloodPressure" placeholder="例如 120/80" type="text" />
          </view>
        </view>

        <view class="form-item">
          <text class="form-label">血糖(mmol/L)</text>
          <view class="input-card">
            <input v-model="form.bloodSugar" placeholder="可选填写" type="digit" />
          </view>
        </view>

        <view class="form-item">
          <text class="form-label">活动水平</text>
          <picker :range="activityOptions" range-key="label" :value="activityIndex" @change="handleActivityChange">
            <view class="input-card picker-card">
              <text>{{ currentActivityLabel }}</text>
            </view>
          </picker>
        </view>

        <view class="form-item">
          <text class="form-label">每日运动时长(分钟)</text>
          <view class="input-card">
            <input v-model="form.exerciseDuration" placeholder="例如 30" type="number" />
          </view>
        </view>

        <view class="form-item">
          <text class="form-label">运动类型</text>
          <checkbox-group @change="handleExerciseChange">
            <view class="option-grid">
              <label v-for="item in exerciseOptions" :key="item" class="check-card">
                <checkbox :value="item" :checked="form.exerciseTypeArr.includes(item)" color="#486646" />
                <text>{{ item }}</text>
              </label>
            </view>
          </checkbox-group>
        </view>

        <view class="form-item">
          <text class="form-label">慢性疾病</text>
          <view class="input-card textarea-card">
            <textarea v-model.trim="form.chronicDiseases" maxlength="200" placeholder="如无可留空或填写无" />
          </view>
        </view>

        <button class="primary-button" :disabled="loading" @click="handleSubmit">
          {{ loading ? '保存中...' : '完成并进入目标设置' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import healthInfoApi from '@/api/healthInfo'
import { useUserStore } from '@/store/user'
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

const userStore = useUserStore()
const loading = ref(false)
const activityOptions = [
  { label: '久坐不动', value: 'sedentary' },
  { label: '轻度活动', value: 'lightly_active' },
  { label: '中度活动', value: 'moderately_active' },
  { label: '高度活动', value: 'very_active' },
  { label: '极高活动', value: 'extra_active' }
]
const exerciseOptions = ['跑步', '游泳', '骑行', '健身', '瑜伽', '球类', '其他']

const form = reactive({
  userId: userStore.userId,
  bloodPressure: '',
  bloodSugar: '',
  activityLevel: '',
  exerciseDuration: '',
  exerciseTypeArr: [],
  chronicDiseases: ''
})

const activityIndex = computed(() => {
  const index = activityOptions.findIndex((item) => item.value === form.activityLevel)
  return index >= 0 ? index : 0
})

const currentActivityLabel = computed(() => {
  const matched = activityOptions.find((item) => item.value === form.activityLevel)
  return matched?.label || '请选择活动水平'
})

const fillFromStore = () => {
  const info = userStore.healthInfo || {}
  form.bloodPressure = info.bloodPressure || ''
  form.bloodSugar = info.bloodSugar !== null && info.bloodSugar !== undefined ? String(info.bloodSugar) : ''
  form.activityLevel = info.activityLevel || ''
  form.exerciseDuration = info.exerciseDuration !== null && info.exerciseDuration !== undefined ? String(info.exerciseDuration) : ''
  form.chronicDiseases = info.chronicDiseases || ''
  form.exerciseTypeArr = info.exerciseType ? String(info.exerciseType).split(',').filter(Boolean) : []
}

const handleActivityChange = (event) => {
  const option = activityOptions[event.detail.value]
  form.activityLevel = option?.value || ''
}

const handleExerciseChange = (event) => {
  form.exerciseTypeArr = event.detail.value || []
}

const handleSubmit = async () => {
  const basicInfo = userStore.healthInfo || {}
  if (!basicInfo.age || !basicInfo.gender || !basicInfo.height || !basicInfo.weight) {
    uni.showToast({ title: '请先完成基础健康信息', icon: 'none' })
    uni.redirectTo({ url: '/pages/onboarding/health-basic' })
    return
  }
  if (!form.activityLevel) {
    uni.showToast({ title: '请选择活动水平', icon: 'none' })
    return
  }

  loading.value = true
  try {
    const payload = {
      ...basicInfo,
      userId: userStore.userId,
      bloodPressure: form.bloodPressure || '',
      bloodSugar: form.bloodSugar ? Number(form.bloodSugar) : null,
      activityLevel: form.activityLevel,
      exerciseDuration: form.exerciseDuration ? Number(form.exerciseDuration) : null,
      exerciseType: form.exerciseTypeArr.join(','),
      chronicDiseases: form.chronicDiseases || ''
    }
    const response = await healthInfoApi.updateHealthInfo(payload)
    if (response.code !== 200) {
      throw new Error(response.message || '保存失败')
    }

    userStore.setHealthInfo(response.data || payload)
    userStore.setHealthAnalysis(response.analysis || null)
    uni.navigateTo({ url: '/pages/onboarding/diet-goal' })
  } catch (error) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

onShow(() => {
  fillFromStore()
})
</script>

<style scoped lang="scss">
.onboarding-page {
  padding-top: 20rpx;
}

.step-card {
  display: flex;
  align-items: center;
  padding: 20rpx 24rpx;
  margin-bottom: 28rpx;
}

.step-chip {
  padding: 12rpx 20rpx;
  border-radius: 999rpx;
  background: #486646;
  color: #fff;
  font-size: 22rpx;
}

.step-line {
  flex: 1;
  height: 2rpx;
  margin: 0 12rpx;
  background: #486646;
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

.picker-card {
  justify-content: space-between;
}

.option-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.check-card {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-height: 88rpx;
  padding: 0 24rpx;
  border-radius: 24rpx;
  background: #f2f5ed;
  font-size: 24rpx;
  color: #2e342d;
}

.textarea-card {
  align-items: flex-start;
  padding: 24rpx 28rpx;
}

.textarea-card textarea {
  min-height: 180rpx;
}
</style>
