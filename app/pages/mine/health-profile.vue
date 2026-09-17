<template>
  <view class="page-shell safe-bottom">
    <view class="page-content health-page">
      <view class="health-dashboard">
        <view class="metric-card metric-card-main">
          <view class="metric-head">
            <text class="metric-label">BMI 指数</text>
            <text class="metric-badge">{{ bmiStatus || '待计算' }}</text>
          </view>
          <text class="metric-value main">{{ bmiValue || '--' }}</text>
          <text class="metric-note">由当前身高和体重实时计算</text>
        </view>

        <view class="metric-side-grid">
          <view class="metric-card">
            <text class="metric-label">基础代谢</text>
            <view class="metric-inline">
              <text class="metric-value">{{ displayBmr }}</text>
              <text class="metric-unit">kcal/日</text>
            </view>
            <text class="metric-note">用于估算每日热量</text>
          </view>
          <view class="metric-card">
            <text class="metric-label">活动水平</text>
            <text class="metric-value compact">{{ currentActivityLabel }}</text>
            <text class="metric-note">影响热量目标</text>
          </view>
        </view>
      </view>

      <view class="card form-card">
        <view class="section-title">
          <text class="section-title__text">基础信息</text>
        </view>

        <view class="grid-2">
          <view class="form-item">
            <text class="form-label">年龄</text>
            <view class="input-card">
              <input v-model="form.age" type="number" placeholder="请输入年龄" />
            </view>
          </view>
          <view class="form-item">
            <text class="form-label">性别</text>
            <view class="gender-row">
              <view class="pill" :class="{ 'pill--active': form.gender === '男' }" @click="form.gender = '男'">男</view>
              <view class="pill" :class="{ 'pill--active': form.gender === '女' }" @click="form.gender = '女'">女</view>
            </view>
          </view>
        </view>

        <view class="grid-2">
          <view class="form-item">
            <text class="form-label">身高 cm</text>
            <view class="input-card">
              <input v-model="form.height" type="digit" placeholder="请输入身高" />
            </view>
          </view>
          <view class="form-item">
            <text class="form-label">体重 kg</text>
            <view class="input-card">
              <input v-model="form.weight" type="digit" placeholder="请输入体重" />
            </view>
          </view>
        </view>

        <view class="section-title detail-title">
          <text class="section-title__text">详细健康信息</text>
        </view>

        <view class="form-item">
          <text class="form-label">活动水平</text>
          <picker :range="activityOptions" range-key="label" :value="activityIndex" @change="handleActivityChange">
            <view class="input-card picker-card">
              <text>{{ currentActivityLabel }}</text>
              <text class="picker-arrow">›</text>
            </view>
          </picker>
        </view>

        <view class="grid-2">
          <view class="form-item">
            <text class="form-label">血压</text>
            <view class="input-card">
              <input v-model.trim="form.bloodPressure" type="text" placeholder="例如 120/80" />
            </view>
          </view>
          <view class="form-item">
            <text class="form-label">血糖 mmol/L</text>
            <view class="input-card">
              <input v-model="form.bloodSugar" type="digit" placeholder="可选" />
            </view>
          </view>
        </view>

        <view class="form-item">
          <text class="form-label">每日运动时长 分钟</text>
          <view class="input-card">
            <input v-model="form.exerciseDuration" type="number" placeholder="例如 30" />
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
          <text class="form-label">慢性疾病 / 特殊情况</text>
          <view class="input-card textarea-card">
            <textarea v-model.trim="form.chronicDiseases" maxlength="200" placeholder="例如 高血压、糖尿病；如无可留空" />
          </view>
        </view>

        <button class="primary-button" :disabled="loading" @click="saveHealthProfile">
          {{ loading ? '保存中...' : '保存健康档案' }}
        </button>
      </view>

      <view class="section-block">
        <view class="section-title">
          <text class="section-title__text">最近健康记录</text>
          <text class="section-title__meta">{{ history.length }} 条</text>
        </view>
        <view v-if="history.length" class="history-list">
          <view v-for="item in history" :key="item.id || item.updateTime || item.createTime" class="card history-card">
            <view>
              <text class="history-title">{{ formatTime(item.updateTime || item.createTime) }}</text>
              <text class="history-desc">体重 {{ item.weight || '--' }} kg · BMI {{ item.bmi || '--' }}</text>
            </view>
            <text class="history-badge">{{ activityLabel(item.activityLevel) }}</text>
          </view>
        </view>
        <view v-else class="card empty-card">
          <text>{{ historyLoading ? '正在加载历史记录...' : '暂无历史记录' }}</text>
        </view>
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
const historyLoading = ref(false)
const history = ref([])

const activityOptions = [
  { label: '久坐不动', value: 'sedentary' },
  { label: '轻度活动', value: 'lightly_active' },
  { label: '中度活动', value: 'moderately_active' },
  { label: '高度活动', value: 'very_active' },
  { label: '极高活动', value: 'extra_active' }
]
const exerciseOptions = ['跑步', '游泳', '骑行', '健身', '瑜伽', '球类', '其他']

const form = reactive({
  age: '',
  gender: '',
  height: '',
  weight: '',
  bloodPressure: '',
  bloodSugar: '',
  activityLevel: '',
  exerciseDuration: '',
  exerciseTypeArr: [],
  chronicDiseases: ''
})

const bmiValue = computed(() => {
  const height = Number(form.height)
  const weight = Number(form.weight)
  if (!height || !weight) return ''
  return (weight / Math.pow(height / 100, 2)).toFixed(1)
})

const bmiStatus = computed(() => {
  const bmi = Number(bmiValue.value)
  if (!bmi) return ''
  if (bmi < 18.5) return '偏瘦'
  if (bmi < 24) return '正常'
  if (bmi < 28) return '偏胖'
  return '肥胖'
})

const displayBmr = computed(() => userStore.healthInfo?.bmr ? Math.round(userStore.healthInfo.bmr) : '--')

const activityIndex = computed(() => {
  const index = activityOptions.findIndex((item) => item.value === form.activityLevel)
  return index >= 0 ? index : 0
})

const activityLabel = (value) => activityOptions.find((item) => item.value === value)?.label || '未设置'
const currentActivityLabel = computed(() => activityLabel(form.activityLevel))

const fillForm = (info = {}) => {
  form.age = info.age ? String(info.age) : ''
  form.gender = info.gender || ''
  form.height = info.height ? String(info.height) : ''
  form.weight = info.weight ? String(info.weight) : ''
  form.bloodPressure = info.bloodPressure || ''
  form.bloodSugar = info.bloodSugar !== null && info.bloodSugar !== undefined ? String(info.bloodSugar) : ''
  form.activityLevel = info.activityLevel || ''
  form.exerciseDuration = info.exerciseDuration !== null && info.exerciseDuration !== undefined ? String(info.exerciseDuration) : ''
  form.exerciseTypeArr = info.exerciseType ? String(info.exerciseType).split(',').filter(Boolean) : []
  form.chronicDiseases = info.chronicDiseases || ''
}

const handleActivityChange = (event) => {
  const option = activityOptions[event.detail.value]
  form.activityLevel = option?.value || ''
}

const handleExerciseChange = (event) => {
  form.exerciseTypeArr = event.detail.value || []
}

const validateForm = () => {
  if (!form.age || Number(form.age) <= 0) return '请输入年龄'
  if (!form.gender) return '请选择性别'
  if (!form.height || Number(form.height) <= 0) return '请输入身高'
  if (!form.weight || Number(form.weight) <= 0) return '请输入体重'
  if (!form.activityLevel) return '请选择活动水平'
  return ''
}

const saveHealthProfile = async () => {
  const error = validateForm()
  if (error) {
    uni.showToast({ title: error, icon: 'none' })
    return
  }

  loading.value = true
  try {
    const payload = {
      ...(userStore.healthInfo || {}),
      userId: userStore.userId,
      age: Number(form.age),
      gender: form.gender,
      height: Number(form.height),
      weight: Number(form.weight),
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
    fillForm(response.data || payload)
    uni.showToast({ title: '已保存', icon: 'none' })
    loadHistory()
  } catch (error) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const loadHealthInfo = async () => {
  try {
    const response = await healthInfoApi.getHealthInfo()
    if (response.code === 200 && response.data) {
      userStore.setHealthInfo(response.data)
      userStore.setHealthAnalysis(response.analysis || null)
      fillForm(response.data)
      return
    }
  } catch (error) {
  }
  fillForm(userStore.healthInfo || {})
}

const loadHistory = async () => {
  historyLoading.value = true
  try {
    const response = await healthInfoApi.getHealthHistory()
    const data = response.code === 200 ? response.data : []
    history.value = Array.isArray(data) ? data.slice(0, 5) : []
  } catch (error) {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

const loadAll = () => {
  loadHealthInfo()
  loadHistory()
}

const formatTime = (value) => {
  if (!value) return '暂无时间'
  const text = String(value).replace('T', ' ')
  return text.length > 16 ? text.slice(0, 16) : text
}

onShow(() => {
  loadAll()
})
</script>

<style scoped lang="scss">
.health-page {
  padding-top: 20rpx;
}

.health-dashboard {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 18rpx;
  margin: 0 0 28rpx;
  position: relative;
  z-index: 2;
}

.metric-side-grid {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.metric-card {
  min-height: 132rpx;
  padding: 24rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 18rpx 44rpx rgba(65, 83, 62, 0.12);
  border: 1rpx solid rgba(111, 149, 128, 0.12);
}

.metric-card-main {
  min-height: 284rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.metric-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.metric-label {
  display: block;
  color: #66705f;
  font-size: 23rpx;
  font-weight: 800;
}

.metric-badge {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: #eef4e9;
  color: #486646;
  font-size: 21rpx;
  font-weight: 900;
}

.metric-value {
  display: block;
  margin-top: 10rpx;
  color: #243323;
  font-size: 38rpx;
  font-weight: 950;
  line-height: 1.15;
}

.metric-value.main {
  margin-top: 24rpx;
  font-size: 78rpx;
  letter-spacing: -2rpx;
}

.metric-value.compact {
  font-size: 30rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metric-inline {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.metric-unit {
  color: #7a8376;
  font-size: 21rpx;
  font-weight: 800;
}

.metric-note {
  display: block;
  margin-top: 12rpx;
  color: #8a9285;
  font-size: 21rpx;
  line-height: 1.35;
}

.form-card {
  padding: 30rpx;
}

.detail-title {
  margin-top: 18rpx;
}

.form-item {
  margin-bottom: 24rpx;
}

.form-label {
  display: block;
  margin-bottom: 12rpx;
  color: #5b6159;
  font-size: 24rpx;
}

.gender-row {
  display: flex;
  gap: 16rpx;
}

.gender-row .pill {
  flex: 1;
  text-align: center;
}

.picker-card {
  justify-content: space-between;
}

.picker-arrow {
  color: #8a9285;
  font-size: 34rpx;
}

.option-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.check-card {
  display: flex;
  align-items: center;
  gap: 10rpx;
  min-height: 84rpx;
  padding: 0 20rpx;
  border-radius: 22rpx;
  background: #f2f5ed;
  color: #2e342d;
  font-size: 24rpx;
}

.textarea-card {
  align-items: flex-start;
  padding: 22rpx 24rpx;
}

.textarea-card textarea {
  width: 100%;
  min-height: 160rpx;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.history-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.history-title {
  display: block;
  color: #263326;
  font-size: 27rpx;
  font-weight: 800;
}

.history-desc {
  display: block;
  margin-top: 8rpx;
  color: #687064;
  font-size: 23rpx;
}

.history-badge {
  flex: 0 0 auto;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: #eef4e9;
  color: #486646;
  font-size: 22rpx;
  font-weight: 800;
}
</style>
