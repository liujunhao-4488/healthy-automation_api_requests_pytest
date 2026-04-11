<template>
  <div class="health-wrapper">
    <div class="health-main">
      <div class="health-header">
        <h1>详细健康信息</h1>
        <p class="health-subtitle">完善您的健康档案，获得更精准的饮食推荐</p>
      </div>

      <div class="step-indicator">
        <div class="step-item completed">
          <span class="step-num">1</span>
          <span class="step-label">账号信息</span>
        </div>
        <div class="step-line active"></div>
        <div class="step-item completed">
          <span class="step-num">2</span>
          <span class="step-label">基础健康</span>
        </div>
        <div class="step-line active"></div>
        <div class="step-item active">
          <span class="step-num">3</span>
          <span class="step-label">详细信息</span>
        </div>
      </div>

      <div class="health-form">
        <el-form :model="detailForm" :rules="rules" ref="detailFormRef" label-position="top">
          <div class="form-section">
            <h3 class="section-title">身体指标</h3>
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="血压" prop="bloodPressure">
                  <el-input v-model="detailForm.bloodPressure" placeholder="例如 120/80" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="血糖 (mmol/L)" prop="bloodSugar">
                  <el-input-number v-model="detailForm.bloodSugar" :min="0" :max="30" :precision="1" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <div class="form-section">
            <h3 class="section-title">运动习惯</h3>
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="活动水平" prop="activityLevel">
                  <el-select v-model="detailForm.activityLevel" placeholder="请选择活动水平">
                    <el-option label="久坐不动" value="sedentary"></el-option>
                    <el-option label="轻度活动" value="lightly_active"></el-option>
                    <el-option label="中度活动" value="moderately_active"></el-option>
                    <el-option label="高度活动" value="very_active"></el-option>
                    <el-option label="极高活动" value="extra_active"></el-option>
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="每日运动时长 (分钟)" prop="exerciseDuration">
                  <el-input-number v-model="detailForm.exerciseDuration" :min="0" :max="480" :step="10" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="运动类型" prop="exerciseTypeArr">
              <el-checkbox-group v-model="detailForm.exerciseTypeArr" class="exercise-group">
                <el-checkbox value="跑步">跑步</el-checkbox>
                <el-checkbox value="游泳">游泳</el-checkbox>
                <el-checkbox value="骑行">骑行</el-checkbox>
                <el-checkbox value="健身">健身</el-checkbox>
                <el-checkbox value="瑜伽">瑜伽</el-checkbox>
                <el-checkbox value="球类">球类</el-checkbox>
                <el-checkbox value="其他">其他</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </div>

          <div class="form-section">
            <h3 class="section-title">健康状况</h3>
            <el-form-item label="过敏食物" prop="allergies">
              <el-input v-model="detailForm.allergies" type="textarea" :rows="2" placeholder="多个请用逗号分隔" />
            </el-form-item>

            <el-form-item label="慢性疾病" prop="chronicDiseases">
              <el-input v-model="detailForm.chronicDiseases" type="textarea" :rows="2" placeholder="如无可填写无" />
            </el-form-item>

            <el-form-item label="健康状况描述" prop="healthCondition">
              <el-input v-model="detailForm.healthCondition" type="textarea" :rows="2" placeholder="请输入当前健康状况描述" />
            </el-form-item>
          </div>

          <div class="form-actions single-action">
            <el-button class="btn-primary" @click="submitForm" :loading="loading">完成录入</el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useUserStore } from '../stores/user';
import healthInfoApi from '../api/healthInfo';

const router = useRouter();
const userStore = useUserStore();
const detailFormRef = ref(null);
const loading = ref(false);
const basicHealthInfo = computed(() => userStore.healthInfo || {});

const detailForm = reactive({
  userId: userStore.userId,
  bloodPressure: '',
  bloodSugar: null,
  activityLevel: '',
  exerciseDuration: null,
  exerciseTypeArr: [],
  exerciseType: '',
  allergies: '',
  chronicDiseases: '',
  healthCondition: ''
});

const rules = {
  activityLevel: [{ required: true, message: '请选择活动水平', trigger: 'change' }]
};

onMounted(() => {
  if (userStore.hasCompletedHealthProfile) {
    router.replace('/dashboard/health-info');
    return;
  }

  if (basicHealthInfo.value) {
    detailForm.bloodPressure = basicHealthInfo.value.bloodPressure || '';
    detailForm.bloodSugar = basicHealthInfo.value.bloodSugar ?? null;
    detailForm.activityLevel = basicHealthInfo.value.activityLevel || '';
    detailForm.exerciseDuration = basicHealthInfo.value.exerciseDuration ?? null;
    detailForm.allergies = basicHealthInfo.value.allergies || '';
    detailForm.chronicDiseases = basicHealthInfo.value.chronicDiseases || '';
    detailForm.healthCondition = basicHealthInfo.value.healthCondition || '';
    if (basicHealthInfo.value.exerciseType) {
      detailForm.exerciseTypeArr = basicHealthInfo.value.exerciseType.split(',');
    }
  }
});

const submitForm = async () => {
  await detailFormRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      if (!basicHealthInfo.value.age || !basicHealthInfo.value.gender || !basicHealthInfo.value.height || !basicHealthInfo.value.weight) {
        ElMessage.warning('请先完成基础健康信息录入');
        router.push('/health-info-basic');
        return;
      }

      detailForm.exerciseType = detailForm.exerciseTypeArr.join(',');

      const formData = {
        ...basicHealthInfo.value,
        ...detailForm,
        age: Number(basicHealthInfo.value.age),
        height: Number(basicHealthInfo.value.height),
        weight: Number(basicHealthInfo.value.weight),
        bloodPressure: detailForm.bloodPressure || '',
        bloodSugar: detailForm.bloodSugar ? Number(detailForm.bloodSugar) : null,
        exerciseDuration: detailForm.exerciseDuration ? Number(detailForm.exerciseDuration) : null
      };

      const response = await healthInfoApi.updateHealthInfo(formData);
      if (response.code === 200) {
        ElMessage.success('健康信息已完善');
        userStore.setHealthInfo(formData);
        router.push('/dashboard/health-info');
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

</script>

<style scoped>
.health-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F7FAF8;
  padding: 40px 20px;
}

.health-main {
  width: 100%;
  max-width: 600px;
}

.health-header {
  text-align: center;
  margin-bottom: 36px;
}

.health-header h1 {
  font-family: 'Noto Serif SC', 'Source Han Serif SC', serif;
  font-size: 26px;
  font-weight: 600;
  color: #4A4238;
  margin: 0 0 8px 0;
  letter-spacing: 2px;
}

.health-subtitle {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #8B8175;
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 36px;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.step-num {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  font-weight: 500;
  background-color: #E8E4DF;
  color: #8B8175;
  transition: all 0.3s ease;
}

.step-item.active .step-num,
.step-item.completed .step-num {
  background-color: #8B7355;
  color: #FFF;
}

.step-label {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 11px;
  color: #8B8175;
}

.step-item.active .step-label,
.step-item.completed .step-label {
  color: #4A4238;
}

.step-line {
  width: 50px;
  height: 2px;
  background-color: #E8E4DF;
  margin: 0 10px;
  margin-bottom: 22px;
}

.step-line.active {
  background-color: #8B7355;
}

.health-form {
  background: #FFF;
  padding: 32px 36px;
  border-radius: 4px;
  box-shadow:
    8px 8px 24px rgba(74, 66, 56, 0.08),
    -2px -2px 8px rgba(255, 255, 255, 0.6);
}

.form-section {
  margin-bottom: 28px;
  padding-bottom: 24px;
  border-bottom: 1px solid #F0ECE7;
}

.form-section:last-of-type {
  border-bottom: none;
  margin-bottom: 0;
}

.section-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 15px;
  font-weight: 500;
  color: #4A4238;
  margin: 0 0 20px 0;
  padding-left: 12px;
  border-left: 3px solid #A69277;
}

.health-form :deep(.el-form-item__label) {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #6B635A;
  padding-bottom: 6px;
}

.health-form :deep(.el-input-number),
.health-form :deep(.el-select) {
  width: 100%;
}

.health-form :deep(.el-input-number .el-input__wrapper),
.health-form :deep(.el-input__wrapper),
.health-form :deep(.el-textarea__inner) {
  background-color: #FAFAF8;
  border: 1px solid #E0DCD6;
  border-radius: 4px;
  box-shadow: none;
}

.exercise-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.form-actions {
  display: flex;
  gap: 16px;
  margin-top: 32px;
}

.single-action {
  justify-content: flex-end;
}

.btn-secondary,
.btn-primary {
  flex: 1;
  height: 44px;
  border-radius: 4px;
}

.btn-secondary {
  background-color: transparent;
  border: 1px solid #C4B8AB;
  color: #6B635A;
}

.btn-primary {
  background-color: #8B7355;
  border: none;
  color: #FFF;
}

@media (max-width: 480px) {
  .health-form {
    padding: 24px 20px;
  }
}
</style>
