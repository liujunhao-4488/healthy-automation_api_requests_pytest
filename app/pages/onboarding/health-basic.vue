<template>
  <view class="page-shell safe-bottom">
    <view class="page-content onboarding-page">
      <view class="step-card soft-card">
        <view class="step-chip active">1 账号</view>
        <view class="step-line active" />
        <view class="step-chip active">2 基础健康</view>
        <view class="step-line" />
        <view class="step-chip">3 详细信息</view>
      </view>

      <view class="hero-block">
        <view class="hero-title">基础健康信息</view>
        <view class="hero-desc">请先补充年龄、性别、身高和体重，系统会据此建立基础健康档案。</view>
      </view>

      <view class="card form-card">
        <view class="form-item">
          <text class="form-label">年龄</text>
          <view class="input-card">
            <input v-model="form.age" placeholder="请输入年龄" type="number" />
          </view>
        </view>

        <view class="form-item">
          <text class="form-label">性别</text>
          <view class="gender-row">
            <view class="pill" :class="{ 'pill--active': form.gender === '男' }" @click="form.gender = '男'">男</view>
            <view class="pill" :class="{ 'pill--active': form.gender === '女' }" @click="form.gender = '女'">女</view>
          </view>
        </view>

        <view class="grid-2">
          <view class="form-item">
            <text class="form-label">身高(cm)</text>
            <view class="input-card">
              <input v-model="form.height" placeholder="请输入身高" type="digit" />
            </view>
          </view>
          <view class="form-item">
            <text class="form-label">体重(kg)</text>
            <view class="input-card">
              <input v-model="form.weight" placeholder="请输入体重" type="digit" />
            </view>
          </view>
        </view>

        <view v-if="bmiValue" class="bmi-card soft-card">
          <text class="bmi-label">当前 BMI</text>
          <text class="bmi-value">{{ bmiValue }}</text>
          <text class="bmi-status">{{ bmiStatus }}</text>
        </view>

        <button class="primary-button" :disabled="loading" @click="handleNext">
          {{ loading ? '保存中...' : '下一步' }}
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
const form = reactive({
  userId: userStore.userId,
  age: '',
  gender: '',
  height: '',
  weight: ''
})

const bmiValue = computed(() => {
  const height = Number(form.height)
  const weight = Number(form.weight)
  if (!height || !weight) return ''
  const value = weight / Math.pow(height / 100, 2)
  return value.toFixed(1)
})

const bmiStatus = computed(() => {
  const bmi = Number(bmiValue.value)
  if (!bmi) return ''
  if (bmi < 18.5) return '偏瘦'
  if (bmi < 24) return '正常'
  if (bmi < 28) return '偏胖'
  return '肥胖'
})

const fillFromStore = () => {
  if (!userStore.healthInfo) return
  form.age = userStore.healthInfo.age ? String(userStore.healthInfo.age) : ''
  form.gender = userStore.healthInfo.gender || ''
  form.height = userStore.healthInfo.height ? String(userStore.healthInfo.height) : ''
  form.weight = userStore.healthInfo.weight ? String(userStore.healthInfo.weight) : ''
}

const handleNext = async () => {
  if (!form.age || Number(form.age) <= 0) {
    uni.showToast({ title: '请输入年龄', icon: 'none' })
    return
  }
  if (!form.gender) {
    uni.showToast({ title: '请选择性别', icon: 'none' })
    return
  }
  if (!form.height || Number(form.height) <= 0) {
    uni.showToast({ title: '请输入身高', icon: 'none' })
    return
  }
  if (!form.weight || Number(form.weight) <= 0) {
    uni.showToast({ title: '请输入体重', icon: 'none' })
    return
  }

  loading.value = true
  try {
    const response = await healthInfoApi.saveHealthInfo({
      userId: userStore.userId,
      age: Number(form.age),
      gender: form.gender,
      height: Number(form.height),
      weight: Number(form.weight)
    })

    if (response.code !== 200) {
      throw new Error(response.message || '保存失败')
    }

    userStore.setHealthInfo(response.data || {
      userId: userStore.userId,
      age: Number(form.age),
      gender: form.gender,
      height: Number(form.height),
      weight: Number(form.weight)
    })
    userStore.setHealthAnalysis(response.analysis || null)
    uni.navigateTo({ url: '/pages/onboarding/health-detail' })
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
  background: #dfe4da;
  color: #7a8178;
  font-size: 22rpx;
}

.step-chip.active {
  background: #486646;
  color: #fff;
}

.step-line {
  flex: 1;
  height: 2rpx;
  margin: 0 12rpx;
  background: #dfe4da;
}

.step-line.active {
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

.gender-row {
  display: flex;
  gap: 20rpx;
}

.bmi-card {
  margin: 12rpx 0 28rpx;
  padding: 26rpx 28rpx;
}

.bmi-label {
  display: block;
  color: #5b6159;
  font-size: 22rpx;
}

.bmi-value {
  display: block;
  margin-top: 10rpx;
  font-size: 52rpx;
  font-weight: 700;
  color: #486646;
}

.bmi-status {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #2e342d;
}
</style>
