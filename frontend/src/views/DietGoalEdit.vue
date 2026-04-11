<template>
  <div class="diet-goal-editor">
    <div class="page-header">
      <div>
        <p class="eyebrow">Edit Goal</p>
        <h2>修改饮食目标</h2>
        <p>
          系统会结合你当前体重、目标体重和计划周期生成推荐值。推荐仅作参考，你仍然可以按自己的情况微调后保存。
        </p>
      </div>
      <el-button class="ghost-button" @click="goBack">返回目标页</el-button>
    </div>

    <el-card class="editor-card" shadow="never">
      <el-form :model="dietGoalForm" :rules="rules" ref="dietGoalFormRef" label-width="120px">
        <el-card class="inner-card" shadow="never">
          <template #header>
            <span>目标设置</span>
          </template>

          <el-form-item label="目标类型" prop="goalType">
            <el-radio-group v-model="dietGoalForm.goalType" class="goal-radio-group">
              <el-radio v-for="option in goalOptions" :key="option.value" :label="option.value">
                {{ option.label }}
              </el-radio>
            </el-radio-group>
          </el-form-item>

          <el-row :gutter="20">
            <el-col :md="12" :xs="24">
              <el-form-item label="目标体重(kg)" prop="targetWeight">
                <el-input-number v-model="dietGoalForm.targetWeight" :min="20" :max="300" :precision="1" />
              </el-form-item>
            </el-col>
            <el-col :md="12" :xs="24">
              <el-form-item label="当前体重">
                <el-input :model-value="displayValue(currentWeight, 'kg')" disabled />
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <el-card class="inner-card" shadow="never">
          <template #header>
            <span>计划时间</span>
          </template>

          <el-row :gutter="20">
            <el-col :md="12" :xs="24">
              <el-form-item label="开始日期" prop="startDate">
                <el-date-picker
                  v-model="dietGoalForm.startDate"
                  type="date"
                  placeholder="选择开始日期"
                  style="width: 100%;"
                />
              </el-form-item>
            </el-col>
            <el-col :md="12" :xs="24">
              <el-form-item label="结束日期" prop="endDate">
                <el-date-picker
                  v-model="dietGoalForm.endDate"
                  type="date"
                  placeholder="选择结束日期"
                  style="width: 100%;"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <el-card class="inner-card" shadow="never">
          <template #header>
            <div class="card-head">
              <span>系统推荐</span>
              <el-button class="soft-button" @click="applyRecommendation">应用推荐</el-button>
            </div>
          </template>

          <div class="system-tip">
            <span class="tip-label">推荐依据</span>
            <span>
              当前体重 {{ displayValue(currentWeight, 'kg') }}，目标体重
              {{ displayValue(recommendationContext.targetWeight, 'kg') }}，计划
              {{ recommendationContext.planDays || '--' }} 天。
            </span>
          </div>

          <div class="recommend-summary-grid">
            <div class="recommend-metric compact">
              <span>预计体重变化</span>
              <strong>{{ displaySignedValue(recommendationContext.weightDelta, 'kg') }}</strong>
            </div>
            <div class="recommend-metric compact">
              <span>每日热量调整</span>
              <strong>{{ displaySignedValue(recommendationContext.dailyAdjustment, 'kcal') }}</strong>
            </div>
            <div class="recommend-metric compact">
              <span>估算日常消耗</span>
              <strong>{{ displayValue(recommendationContext.estimatedTdee, 'kcal') }}</strong>
            </div>
            <div class="recommend-metric compact highlight">
              <span>推荐热量</span>
              <strong>{{ displayValue(recommendedGoal.targetCalories, 'kcal') }}</strong>
            </div>
            <div class="recommend-metric compact highlight">
              <span>推荐饮水</span>
              <strong>{{ displayValue(recommendedGoal.waterTarget, 'ml') }}</strong>
            </div>
          </div>

          <div class="recommend-macro-grid">
            <div class="macro-card protein">
              <span>蛋白质</span>
              <strong>{{ displayValue(recommendedGoal.proteinTarget, 'g') }}</strong>
              <small>{{ displayValue(recommendedGoal.proteinRatio, '%') }}</small>
            </div>
            <div class="macro-card carbs">
              <span>碳水</span>
              <strong>{{ displayValue(recommendedGoal.carbsTarget, 'g') }}</strong>
              <small>{{ displayValue(recommendedGoal.carbsRatio, '%') }}</small>
            </div>
            <div class="macro-card fat">
              <span>脂肪</span>
              <strong>{{ displayValue(recommendedGoal.fatTarget, 'g') }}</strong>
              <small>{{ displayValue(recommendedGoal.fatRatio, '%') }}</small>
            </div>
          </div>

          <div v-if="recommendationContext.advice" class="recommend-note">
            {{ recommendationContext.advice }}
          </div>
        </el-card>

        <el-card class="inner-card" shadow="never">
          <template #header>
            <span>保存值</span>
          </template>

          <el-row :gutter="20">
            <el-col :md="12" :xs="24">
              <el-form-item label="每日热量(kcal)" prop="targetCalories">
                <el-input-number v-model="dietGoalForm.targetCalories" :min="800" :max="5000" :step="50" />
              </el-form-item>
            </el-col>
            <el-col :md="12" :xs="24">
              <el-form-item label="每日饮水(ml)" prop="waterTarget">
                <el-input-number v-model="dietGoalForm.waterTarget" :min="500" :max="5000" :step="100" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :md="8" :xs="24">
              <div class="manual-macro protein-lite">
                <div class="manual-title">蛋白质</div>
                <el-form-item label="克数(g)" prop="proteinTarget" class="compact-item">
                  <el-input-number v-model="dietGoalForm.proteinTarget" :min="0" :max="300" :step="5" />
                </el-form-item>
                <el-form-item label="占比(%)" prop="proteinRatio" class="compact-item">
                  <el-input-number v-model="dietGoalForm.proteinRatio" :min="10" :max="50" :step="1" />
                </el-form-item>
              </div>
            </el-col>
            <el-col :md="8" :xs="24">
              <div class="manual-macro carbs-lite">
                <div class="manual-title">碳水</div>
                <el-form-item label="克数(g)" prop="carbsTarget" class="compact-item">
                  <el-input-number v-model="dietGoalForm.carbsTarget" :min="0" :max="500" :step="10" />
                </el-form-item>
                <el-form-item label="占比(%)" prop="carbsRatio" class="compact-item">
                  <el-input-number v-model="dietGoalForm.carbsRatio" :min="20" :max="70" :step="1" />
                </el-form-item>
              </div>
            </el-col>
            <el-col :md="8" :xs="24">
              <div class="manual-macro fat-lite">
                <div class="manual-title">脂肪</div>
                <el-form-item label="克数(g)" prop="fatTarget" class="compact-item">
                  <el-input-number v-model="dietGoalForm.fatTarget" :min="0" :max="200" :step="5" />
                </el-form-item>
                <el-form-item label="占比(%)" prop="fatRatio" class="compact-item">
                  <el-input-number v-model="dietGoalForm.fatRatio" :min="10" :max="50" :step="1" />
                </el-form-item>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <el-card class="inner-card" shadow="never">
          <template #header>
            <span>提醒设置</span>
          </template>

          <el-form-item label="开启提醒" prop="reminderEnabled">
            <el-switch v-model="dietGoalForm.reminderEnabled" :active-value="1" :inactive-value="0" />
          </el-form-item>
          <el-form-item label="提醒时间" prop="reminderTime" v-if="dietGoalForm.reminderEnabled === 1">
            <el-time-picker
              v-model="dietGoalForm.reminderTime"
              placeholder="选择提醒时间"
              format="HH:mm"
              value-format="HH:mm:ss"
              style="width: 100%;"
            />
          </el-form-item>
        </el-card>

        <div class="actions">
          <el-button class="ghost-button" @click="goBack">取消</el-button>
          <el-button class="soft-button" @click="generateRecommendation">重新生成推荐</el-button>
          <el-button class="save-button" type="primary" @click="saveDietGoal" :loading="loading">
            保存修改
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useUserStore } from '../stores/user';
import dietGoalApi from '../api/dietGoal';
import { computeDietGoalRecommendation, formatGoalDate, formatGoalTime } from '../utils/dietGoalRecommendation';

const router = useRouter();
const userStore = useUserStore();
const dietGoalFormRef = ref(null);
const loading = ref(false);
const currentWeight = ref(null);

const dietGoalForm = reactive({
  goalType: '',
  targetWeight: null,
  targetCalories: 2000,
  proteinRatio: 30,
  carbsRatio: 45,
  fatRatio: 25,
  proteinTarget: null,
  carbsTarget: null,
  fatTarget: null,
  waterTarget: 2000,
  status: 1,
  startDate: '',
  endDate: '',
  reminderEnabled: 1,
  reminderTime: ''
});

const recommendedGoal = reactive({
  targetCalories: null,
  proteinRatio: null,
  carbsRatio: null,
  fatRatio: null,
  proteinTarget: null,
  carbsTarget: null,
  fatTarget: null,
  waterTarget: null
});

const recommendationContext = reactive({
  targetWeight: null,
  planDays: null,
  weightDelta: null,
  dailyAdjustment: null,
  estimatedTdee: null,
  advice: ''
});

const goalOptions = [
  { value: 'fat_loss', label: '减肥减脂' },
  { value: 'muscle_toning', label: '增肌塑形' },
  { value: 'weight_maintenance', label: '维持体重' },
  { value: 'healthy_weight_gain', label: '健康增重' },
  { value: 'blood_sugar_control', label: '控糖饮食' },
  { value: 'lipid_control', label: '控脂降脂' },
  { value: 'low_sodium', label: '控压低盐' },
  { value: 'pregnancy_nutrition', label: '孕妇营养' },
  { value: 'child_growth', label: '儿童成长' },
  { value: 'senior_wellness', label: '老年养生' }
];

const rules = {
  goalType: [{ required: true, message: '请选择目标类型', trigger: 'change' }],
  targetCalories: [{ required: true, message: '请输入每日热量目标', trigger: 'blur' }],
  startDate: [{ required: true, message: '请选择开始日期', trigger: 'change' }]
};

const displayValue = (value, unit = '') => {
  if (value === null || value === undefined || value === '') {
    return '--';
  }

  const normalizedValue =
    typeof value === 'number'
      ? Number.isInteger(value)
        ? value
        : value.toFixed(1)
      : value;

  return `${normalizedValue}${unit ? ` ${unit}` : ''}`;
};

const displaySignedValue = (value, unit = '') => {
  if (value === null || value === undefined || value === '') {
    return '--';
  }

  const normalizedValue = Number.isInteger(value) ? value : Number(value).toFixed(1);
  const prefix = Number(value) > 0 ? '+' : '';
  return `${prefix}${normalizedValue}${unit ? ` ${unit}` : ''}`;
};

const computeRecommendation = () => {
  const recommendation = computeDietGoalRecommendation({
    healthInfo: userStore.healthInfo,
    goalForm: dietGoalForm
  });

  if (!recommendation) {
    return null;
  }

  currentWeight.value = recommendation.currentWeight;
  return recommendation;
};

const generateRecommendation = (silent = false) => {
  const recommendation = computeRecommendation();

  if (!recommendation) {
    if (!silent) {
      ElMessage.warning('请先完善健康信息并选择目标类型');
    }
    return;
  }

  Object.assign(recommendedGoal, recommendation.recommendedGoal);
  Object.assign(recommendationContext, recommendation.recommendationContext);

  if (!silent) {
    ElMessage.success('系统推荐已更新');
  }
};

const applyRecommendation = () => {
  generateRecommendation(true);
  Object.assign(dietGoalForm, {
    ...dietGoalForm,
    targetWeight: recommendationContext.targetWeight ?? dietGoalForm.targetWeight,
    targetCalories: recommendedGoal.targetCalories,
    proteinRatio: recommendedGoal.proteinRatio,
    carbsRatio: recommendedGoal.carbsRatio,
    fatRatio: recommendedGoal.fatRatio,
    proteinTarget: recommendedGoal.proteinTarget,
    carbsTarget: recommendedGoal.carbsTarget,
    fatTarget: recommendedGoal.fatTarget,
    waterTarget: recommendedGoal.waterTarget
  });
  ElMessage.success('已应用系统推荐');
};

watch(
  [() => dietGoalForm.goalType, () => dietGoalForm.targetWeight, () => dietGoalForm.startDate, () => dietGoalForm.endDate],
  () => {
    if (!dietGoalForm.goalType) {
      return;
    }
    generateRecommendation(true);
  }
);

const applyDietGoal = (goal) => {
  Object.assign(dietGoalForm, {
    ...dietGoalForm,
    ...goal
  });
};

const loadDietGoal = async () => {
  try {
    const response = await dietGoalApi.getDietGoal();
    if (response.code === 200 && response.data) {
      applyDietGoal(response.data);
      userStore.setDietGoal(response.data);
      generateRecommendation(true);
      return;
    }
  } catch (error) {
    console.error('获取饮食目标失败:', error);
  }

  if (userStore.dietGoal) {
    applyDietGoal(userStore.dietGoal);
  }

  generateRecommendation(true);
};

const saveDietGoal = async () => {
  await dietGoalFormRef.value.validate(async (valid) => {
    if (!valid) {
      return;
    }

    loading.value = true;
    try {
      const formData = {
        ...dietGoalForm,
        startDate: formatGoalDate(dietGoalForm.startDate),
        endDate: formatGoalDate(dietGoalForm.endDate),
        reminderTime: formatGoalTime(dietGoalForm.reminderTime)
      };

      const response = userStore.hasDietGoal
        ? await dietGoalApi.updateDietGoal(formData)
        : await dietGoalApi.saveDietGoal(formData);

      if (response.code === 200) {
        userStore.setDietGoal(response.data || formData);
        if (Number.isFinite(Number(userStore.healthInfo?.weight))) {
          userStore.setDietGoalMeta({
            appliedWeight: Number(userStore.healthInfo.weight),
            appliedAt: new Date().toISOString()
          });
        }
        ElMessage.success('饮食目标已更新');
        router.push('/dashboard/diet-goal');
      } else {
        ElMessage.error(response.message || '保存失败');
      }
    } catch (error) {
      ElMessage.error(error.message || '保存失败，请检查网络连接');
    } finally {
      loading.value = false;
    }
  });
};

const goBack = () => {
  router.push('/dashboard/diet-goal');
};

onMounted(() => {
  currentWeight.value = Number(userStore.healthInfo?.weight || 0) || null;
  loadDietGoal();
});
</script>

<style scoped>
.diet-goal-editor {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #6f8f72;
}

.page-header h2 {
  margin: 0;
  font-family: 'Noto Serif SC', serif;
  font-size: 30px;
  color: #334235;
}

.page-header p {
  margin: 10px 0 0;
  color: #6b786d;
  line-height: 1.7;
}

.editor-card,
.inner-card {
  border: 1px solid #e4ecdf;
  border-radius: 24px;
}

.inner-card {
  margin-bottom: 18px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.goal-radio-group {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.goal-radio-group :deep(.el-radio) {
  margin-right: 0;
  display: flex;
}

.goal-radio-group :deep(.el-radio__label) {
  width: 100%;
  min-height: 44px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid #d9e5d8;
  background: #ffffff;
  color: #5f6d61;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  line-height: 1.4;
  transition: all 0.25s ease;
}

.goal-radio-group :deep(.el-radio__label:hover) {
  border-color: #9fbea4;
  color: #46614a;
}

.goal-radio-group :deep(.el-radio.is-checked .el-radio__label) {
  border-color: #6f8f72;
  background: #eef6ef;
  color: #35513a;
  font-weight: 500;
}

.editor-card :deep(.el-form-item__label) {
  color: #647166;
}

.editor-card :deep(.el-input-number),
.editor-card :deep(.el-select) {
  width: 100%;
}

.editor-card :deep(.el-input__wrapper),
.editor-card :deep(.el-input-number .el-input__wrapper),
.editor-card :deep(.el-textarea__inner) {
  background-color: #f7faf6;
  border: 1px solid #dde7db;
  box-shadow: none;
}

.system-tip {
  margin-bottom: 18px;
  padding: 14px 16px;
  border-radius: 16px;
  background: #f3f8f4;
  color: #607062;
  line-height: 1.7;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tip-label {
  font-weight: 600;
  color: #46614a;
}

.recommend-summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.recommend-metric {
  min-height: 96px;
  padding: 18px;
  border-radius: 18px;
  background: #f7faf6;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.recommend-metric.compact {
  min-height: 110px;
}

.recommend-metric.highlight {
  background: linear-gradient(180deg, #f8fbf8 0%, #e7f2e7 100%);
}

.recommend-metric span {
  color: #708072;
}

.recommend-metric strong {
  font-size: 24px;
  line-height: 1.2;
  color: #334235;
}

.recommend-macro-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.recommend-note {
  margin-top: 8px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #fffaf0;
  color: #766652;
  line-height: 1.7;
}

.manual-macro {
  height: 100%;
  padding: 18px 16px 8px;
  border-radius: 18px;
  border: 1px solid #e3ebdf;
}

.manual-title {
  margin-bottom: 14px;
  font-size: 14px;
  font-weight: 600;
  color: #334235;
}

.compact-item :deep(.el-form-item__label) {
  padding-bottom: 4px;
}

.compact-item {
  margin-bottom: 14px;
}

.protein-lite {
  background: #f6fbff;
}

.carbs-lite {
  background: #fffaf2;
}

.fat-lite {
  background: #faf7ff;
}

.macro-card {
  min-height: 122px;
  padding: 18px 18px 16px;
  border-radius: 22px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 8px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.55);
}

.macro-card span {
  color: #617165;
  font-size: 13px;
  letter-spacing: 0.04em;
}

.macro-card strong {
  font-size: 28px;
  color: #334235;
  line-height: 1.1;
}

.macro-card small {
  color: #7f8b81;
  font-size: 14px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  align-self: flex-start;
}

.protein {
  background: linear-gradient(180deg, #eef7ff 0%, #dbeaff 100%);
}

.carbs {
  background: linear-gradient(180deg, #fff8ee 0%, #ffe8c9 100%);
}

.fat {
  background: linear-gradient(180deg, #f7f3ff 0%, #e7dcff 100%);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 28px;
}

.ghost-button {
  border-color: #d4ddcf;
  color: #5f6d61;
}

.soft-button {
  border-color: #cfe0d2;
  color: #46614a;
  background-color: #f4fbf5;
}

.save-button {
  min-width: 120px;
  border: none;
  background: linear-gradient(135deg, #6f8f72 0%, #8b7355 100%);
}

@media (max-width: 768px) {
  .goal-radio-group {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .page-header {
    flex-direction: column;
  }

  .actions {
    flex-direction: column;
  }

  .recommend-summary-grid,
  .recommend-macro-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .goal-radio-group {
    grid-template-columns: 1fr;
  }
}
</style>
