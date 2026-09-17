<template>
  <view class="page-shell safe-bottom">
    <view class="page-content record-page">
      <view class="hero-card card">
        <view>
          <view class="hero-title">饮食记录</view>
          <view class="hero-desc">快速添加一条记录，并查看最近饮食与建议。</view>
        </view>
        <text class="hero-action" @click="loadAll">刷新</text>
      </view>

      <view class="summary-grid">
        <view class="summary-card soft-card">
          <text class="summary-label">热量目标</text>
          <text class="summary-value">{{ targetCalories }}</text>
        </view>
        <view class="summary-card soft-card">
          <text class="summary-label">最近记录</text>
          <text class="summary-value">{{ records.length }}</text>
        </view>
        <view class="summary-card soft-card">
          <text class="summary-label">饮食建议</text>
          <text class="summary-value">{{ suggestions.length }}</text>
        </view>
      </view>

      <view class="card form-card">
        <view class="section-title">
          <text class="section-title__text">快速录入</text>
        </view>

        <view class="form-item">
          <text class="form-label">日期</text>
          <picker mode="date" :value="form.date" @change="(e) => (form.date = e.detail.value)">
            <view class="input-card picker-card">
              <text>{{ form.date || '请选择日期' }}</text>
            </view>
          </picker>
        </view>

        <view class="form-item">
          <text class="form-label">餐次</text>
          <view class="meal-row">
            <view
              v-for="item in mealOptions"
              :key="item.value"
              class="meal-pill"
              :class="{ active: form.mealType === item.value }"
              @click="form.mealType = item.value"
            >
              {{ item.label }}
            </view>
          </view>
        </view>

        <view class="form-item">
          <text class="form-label">本餐名称</text>
          <view class="input-card">
            <input v-model.trim="form.foodName" placeholder="例如 鸡胸肉沙拉" type="text" />
          </view>
        </view>

        <view class="grid-2">
          <view class="form-item">
            <text class="form-label">分量</text>
            <view class="input-card">
              <input v-model="form.amount" placeholder="例如 200" type="digit" />
            </view>
          </view>
          <view class="form-item">
            <text class="form-label">单位</text>
            <view class="input-card">
              <input v-model.trim="form.unit" placeholder="g / ml / 份" type="text" />
            </view>
          </view>
        </view>

        <view class="grid-2">
          <view class="form-item">
            <text class="form-label">热量(kcal)</text>
            <view class="input-card">
              <input v-model="form.calories" placeholder="可选填写" type="digit" />
            </view>
          </view>
          <view class="form-item">
            <text class="form-label">蛋白质(g)</text>
            <view class="input-card">
              <input v-model="form.protein" placeholder="可选填写" type="digit" />
            </view>
          </view>
        </view>

        <view class="grid-2">
          <view class="form-item">
            <text class="form-label">碳水(g)</text>
            <view class="input-card">
              <input v-model="form.carbs" placeholder="可选填写" type="digit" />
            </view>
          </view>
          <view class="form-item">
            <text class="form-label">脂肪(g)</text>
            <view class="input-card">
              <input v-model="form.fat" placeholder="可选填写" type="digit" />
            </view>
          </view>
        </view>

        <view class="form-item">
          <text class="form-label">备注</text>
          <view class="input-card textarea-card">
            <textarea v-model.trim="form.notes" maxlength="200" placeholder="可选填写备注" />
          </view>
        </view>

        <button class="primary-button" :disabled="loading" @click="submitRecord">
          {{ loading ? '保存中...' : '保存记录' }}
        </button>
      </view>

      <view class="section-block">
        <view class="section-title">
          <text class="section-title__text">最近记录</text>
        </view>
        <view v-if="records.length" class="list-stack">
          <view v-for="item in records" :key="item.id" class="card record-card">
            <view class="record-head">
              <view>
                <text class="record-title">{{ item.mealTypeLabel }} · {{ item.foodName }}</text>
                <text class="record-desc">{{ item.date }}</text>
              </view>
              <text class="record-delete" @click="removeRecord(item)">删除</text>
            </view>
            <view class="record-metrics">
              <text>{{ item.calories }} kcal</text>
              <text>蛋白 {{ item.protein }} g</text>
              <text>碳水 {{ item.carbs }} g</text>
              <text>脂肪 {{ item.fat }} g</text>
            </view>
            <text v-if="item.notes" class="record-note">{{ item.notes }}</text>
          </view>
        </view>
        <view v-else class="card empty-card">
          <text>{{ listLoading ? '正在加载记录...' : '最近还没有饮食记录' }}</text>
        </view>
      </view>

      <view class="section-block">
        <view class="section-title">
          <text class="section-title__text">饮食建议</text>
        </view>
        <view v-if="suggestions.length" class="list-stack">
          <view v-for="(item, index) in suggestions" :key="index" class="soft-card suggestion-card">
            <text>{{ item }}</text>
          </view>
        </view>
        <view v-else class="card empty-card">
          <text>{{ listLoading ? '正在加载建议...' : '当前没有新的饮食建议' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import dietRecordApi from '@/api/dietRecord'
import { useUserStore } from '@/store/user'
import { reactive, ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'

const userStore = useUserStore()
const loading = ref(false)
const listLoading = ref(false)
const records = ref([])
const suggestions = ref([])

const mealOptions = [
  { label: '早餐', value: 'breakfast' },
  { label: '午餐', value: 'lunch' },
  { label: '晚餐', value: 'dinner' },
  { label: '加餐', value: 'snack' }
]

const mealTypeMap = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐'
}

const today = new Date().toISOString().slice(0, 10)

const form = reactive({
  date: today,
  mealType: 'breakfast',
  foodName: '',
  amount: '1',
  unit: '份',
  calories: '',
  protein: '',
  carbs: '',
  fat: '',
  notes: ''
})

const targetCalories = computed(() => userStore.dietGoal?.targetCalories ? `${userStore.dietGoal.targetCalories} kcal` : '--')

const toNumber = (value) => {
  if (value === '' || value === null || value === undefined) return 0
  const number = Number(value)
  return Number.isFinite(number) ? number : 0
}

const formatMetric = (value, digits = 1) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return '--'
  return number.toFixed(digits)
}

const normalizeRecords = (data) => {
  const list = Array.isArray(data) ? data : []
  return list.map((item) => {
    const details = Array.isArray(item.details) ? item.details : []
    const first = details[0] || {}
    return {
      ...item,
      mealTypeLabel: mealTypeMap[item.mealType] || '记录',
      foodName: item.foodName || first.foodName || item.mealName || '未命名记录',
      calories: formatMetric(item.calories ?? first.calories ?? 0, 0),
      protein: formatMetric(item.protein ?? first.protein ?? 0),
      carbs: formatMetric(item.carbs ?? first.carbs ?? 0),
      fat: formatMetric(item.fat ?? first.fat ?? 0)
    }
  })
}

const resetForm = () => {
  form.date = today
  form.mealType = 'breakfast'
  form.foodName = ''
  form.amount = '1'
  form.unit = '份'
  form.calories = ''
  form.protein = ''
  form.carbs = ''
  form.fat = ''
  form.notes = ''
}

const loadAll = async () => {
  listLoading.value = true
  try {
    const endDate = new Date().toISOString().slice(0, 10)
    const startDate = new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
    const [recordResponse, suggestionResponse] = await Promise.all([
      dietRecordApi.getDietRecords(startDate, endDate),
      dietRecordApi.getDietSuggestions()
    ])

    records.value = recordResponse.code === 200 ? normalizeRecords(recordResponse.data) : []
    suggestions.value = suggestionResponse.code === 200 && Array.isArray(suggestionResponse.data)
      ? suggestionResponse.data
      : []
  } catch (error) {
    records.value = []
    suggestions.value = []
  } finally {
    listLoading.value = false
  }
}

const submitRecord = async () => {
  if (!form.date) {
    uni.showToast({ title: '请选择日期', icon: 'none' })
    return
  }
  if (!form.mealType) {
    uni.showToast({ title: '请选择餐次', icon: 'none' })
    return
  }
  if (!form.foodName) {
    uni.showToast({ title: '请输入本餐名称', icon: 'none' })
    return
  }

  loading.value = true
  try {
    const payload = {
      date: form.date,
      mealType: form.mealType,
      notes: form.notes,
      details: [
        {
          foodName: form.foodName,
          amount: toNumber(form.amount) || 1,
          unit: form.unit || '份',
          calories: toNumber(form.calories),
          protein: toNumber(form.protein),
          carbs: toNumber(form.carbs),
          fat: toNumber(form.fat)
        }
      ]
    }

    const response = await dietRecordApi.submitRecord(payload)
    if (response.code !== 200) {
      throw new Error(response.message || '保存失败')
    }

    uni.showToast({ title: '记录已保存', icon: 'success' })
    resetForm()
    loadAll()
  } catch (error) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const removeRecord = async (item) => {
  if (!item?.id) return
  try {
    const response = await dietRecordApi.deleteRecord(item.id)
    if (response.code !== 200) {
      throw new Error(response.message || '删除失败')
    }
    uni.showToast({ title: '已删除', icon: 'none' })
    loadAll()
  } catch (error) {
    uni.showToast({ title: error.message || '删除失败', icon: 'none' })
  }
}

onShow(() => {
  loadAll()
})
</script>

<style scoped lang="scss">
.record-page {
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

.hero-action,
.record-delete {
  color: #486646;
  font-size: 24rpx;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18rpx;
  margin-top: 22rpx;
}

.summary-card {
  padding: 24rpx;
}

.summary-label,
.form-label {
  display: block;
  font-size: 22rpx;
  color: #5b6159;
}

.summary-value {
  display: block;
  margin-top: 10rpx;
  font-size: 32rpx;
  font-weight: 700;
  color: #2e342d;
}

.form-card {
  margin-top: 24rpx;
  padding: 32rpx;
}

.form-item {
  margin-bottom: 22rpx;
}

.meal-row {
  display: flex;
  gap: 14rpx;
  flex-wrap: wrap;
}

.meal-pill {
  min-width: 120rpx;
  height: 72rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: #edf3e8;
  color: #5b6159;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
}

.meal-pill.active {
  background: #486646;
  color: #eff8eb;
}

.picker-card {
  justify-content: space-between;
}

.textarea-card {
  align-items: flex-start;
  padding: 24rpx 28rpx;
}

.textarea-card textarea {
  min-height: 140rpx;
}

.section-block {
  margin-top: 28rpx;
}

.list-stack {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.record-card {
  padding: 28rpx;
}

.record-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.record-title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #2e342d;
}

.record-desc,
.record-note {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: #5b6159;
}

.record-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx 24rpx;
  margin-top: 18rpx;
  font-size: 22rpx;
  color: #6f776c;
}

.suggestion-card {
  padding: 24rpx 28rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #2e342d;
}

.empty-card {
  padding: 36rpx 28rpx;
  text-align: center;
  color: #7c8578;
  font-size: 24rpx;
}
</style>
