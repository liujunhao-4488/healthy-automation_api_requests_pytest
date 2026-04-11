<template>
  <div class="health-wrapper">
    <div class="health-main">
      <div class="health-header">
        <h1>健康信息录入</h1>
        <p class="health-subtitle">请提供您的基本健康数据</p>
      </div>
      
      <div class="step-indicator">
        <div class="step-item completed">
          <span class="step-num">1</span>
          <span class="step-label">账号信息</span>
        </div>
        <div class="step-line active"></div>
        <div class="step-item active">
          <span class="step-num">2</span>
          <span class="step-label">基础健康</span>
        </div>
        <div class="step-line"></div>
        <div class="step-item">
          <span class="step-num">3</span>
          <span class="step-label">详细信息</span>
        </div>
      </div>
      
      <div class="health-form">
        <el-form :model="healthForm" :rules="rules" ref="healthFormRef" label-position="top">
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="年龄" prop="age">
                <el-input-number v-model="healthForm.age" :min="1" :max="150" placeholder="请输入年龄" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="性别" prop="gender">
                <el-radio-group v-model="healthForm.gender" class="gender-group">
                  <el-radio value="男">男</el-radio>
                  <el-radio value="女">女</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="身高 (cm)" prop="height">
                <el-input-number v-model="healthForm.height" :min="50" :max="250" :precision="1" placeholder="请输入身高" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="体重 (kg)" prop="weight">
                <el-input-number v-model="healthForm.weight" :min="20" :max="300" :precision="1" placeholder="请输入体重" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <div class="bmi-result" v-if="bmiValue">
            <span class="bmi-label">您的BMI指数</span>
            <span class="bmi-value">{{ bmiValue }}</span>
            <span class="bmi-status">{{ bmiStatus }}</span>
          </div>
          
          <div class="form-actions single-action">
            <el-button class="btn-primary" @click="nextStep" :loading="loading">下一步</el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useUserStore } from '../stores/user';
import healthInfoApi from '../api/healthInfo';

const router = useRouter();
const userStore = useUserStore();
const healthFormRef = ref(null);
const loading = ref(false);

const healthForm = reactive({
  userId: userStore.userId,
  age: null,
  gender: '',
  height: null,
  weight: null
});

const rules = {
  age: [
    { required: true, message: '请输入年龄', trigger: 'blur' }
  ],
  gender: [
    { required: true, message: '请选择性别', trigger: 'change' }
  ],
  height: [
    { required: true, message: '请输入身高', trigger: 'blur' }
  ],
  weight: [
    { required: true, message: '请输入体重', trigger: 'blur' }
  ]
};

const bmiValue = computed(() => {
  if (healthForm.height && healthForm.weight) {
    const heightInMeters = Number(healthForm.height) / 100;
    const weight = Number(healthForm.weight);
    return (weight / (heightInMeters * heightInMeters)).toFixed(1);
  }
  return null;
});

const bmiStatus = computed(() => {
  if (!bmiValue.value) return '';
  const bmi = Number(bmiValue.value);
  if (bmi < 18.5) return '偏瘦';
  if (bmi < 24) return '正常';
  if (bmi < 28) return '偏胖';
  return '肥胖';
});

onMounted(() => {
  if (userStore.hasCompletedHealthProfile) {
    router.replace('/dashboard/health-info');
  }
});

const nextStep = async () => {
  await healthFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const response = await healthInfoApi.saveHealthInfo({
          ...healthForm,
          age: Number(healthForm.age),
          height: Number(healthForm.height),
          weight: Number(healthForm.weight)
        });
        if (response.code === 200) {
          ElMessage.success('信息已保存');
          userStore.setHealthInfo(response.data || healthForm);
          userStore.setHealthAnalysis(response.analysis || null);
          router.push('/health-info-detail');
        } else {
          ElMessage.error(response.message || '保存失败');
        }
      } catch (error) {
        ElMessage.error('保存失败，请检查网络连接');
      } finally {
        loading.value = false;
      }
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
  max-width: 520px;
}

.health-header {
  text-align: center;
  margin-bottom: 40px;
}

.health-header h1 {
  font-family: 'Noto Serif SC', 'Source Han Serif SC', serif;
  font-size: 28px;
  font-weight: 600;
  color: #3D4A3E;
  margin: 0 0 8px 0;
  letter-spacing: 2px;
}

.health-subtitle {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #8A9A8C;
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40px;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.step-num {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  font-weight: 500;
  background-color: #E8F0EA;
  color: #8A9A8C;
  transition: all 0.3s ease;
}

.step-item.active .step-num,
.step-item.completed .step-num {
  background-color: #7BA088;
  color: #FFF;
}

.step-label {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 12px;
  color: #8A9A8C;
}

.step-item.active .step-label,
.step-item.completed .step-label {
  color: #3D4A3E;
}

.step-line {
  width: 60px;
  height: 2px;
  background-color: #E8F0EA;
  margin: 0 12px;
  margin-bottom: 24px;
  transition: background-color 0.3s ease;
}

.step-line.active {
  background-color: #7BA088;
}

.health-form {
  background: #FFF;
  padding: 36px 40px;
  border-radius: 4px;
  box-shadow: 
    8px 8px 24px rgba(61, 74, 62, 0.08),
    -2px -2px 8px rgba(255, 255, 255, 0.6);
}

.health-form :deep(.el-form-item__label) {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #5A6B5C;
  padding-bottom: 6px;
}

.health-form :deep(.el-input-number) {
  width: 100%;
}

.health-form :deep(.el-input-number .el-input__wrapper) {
  background-color: #F7FAF8;
  border: 1px solid #D8E4DC;
  border-radius: 4px;
  box-shadow: none;
  padding: 0 12px;
}

.health-form :deep(.el-input-number .el-input__inner) {
  text-align: center;
}

.health-form :deep(.el-input-number .el-input__wrapper:hover) {
  border-color: #B8C8B8;
}

.health-form :deep(.el-input__inner) {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #3D4A3E;
  text-align: left;
}

.gender-group :deep(.el-radio .el-radio__label) {
  padding: 0 24px;
  height: 40px;
  line-height: 40px;
  border: 1px solid #D8E4DC;
  border-radius: 4px;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #5A6B5C;
  cursor: pointer;
  transition: all 0.25s ease;
}

.gender-group :deep(.el-radio.is-checked .el-radio__label) {
  background-color: #7BA088;
  border-color: #7BA088;
  color: #FFF;
}

.bmi-result {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background-color: #F7FAF8;
  border-radius: 4px;
  margin: 24px 0;
}

.bmi-label {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #8A9A8C;
}

.bmi-value {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 600;
  color: #7BA088;
}

.bmi-status {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #5A6B5C;
  padding: 4px 12px;
  background-color: #E8F0EA;
  border-radius: 4px;
}

.form-actions {
  display: flex;
  gap: 16px;
  margin-top: 32px;
}

.single-action {
  justify-content: flex-end;
}

.btn-secondary {
  flex: 1;
  height: 44px;
  background-color: transparent;
  border: 1px solid #B8C8B8;
  border-radius: 4px;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #5A6B5C;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  border-color: #7BA088;
  color: #7BA088;
}

.btn-primary {
  flex: 1;
  height: 44px;
  background-color: #7BA088;
  border: none;
  border-radius: 4px;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: #FFF;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-primary:hover {
  background-color: #6A9177;
  transform: scale(1.02);
  box-shadow: 4px 4px 12px rgba(123, 160, 136, 0.25);
}

.health-form :deep(.el-input-number.is-focus .el-input__wrapper) {
  border-color: #A69277;
}

.health-form :deep(.el-input__inner) {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #4A4238;
  text-align: left;
}

.gender-group {
  display: flex;
  gap: 12px;
}

.gender-group :deep(.el-radio) {
  margin-right: 0;
}

.gender-group :deep(.el-radio .el-radio__inner) {
  display: none;
}

.gender-group :deep(.el-radio .el-radio__label) {
  padding: 0 24px;
  height: 40px;
  line-height: 40px;
  border: 1px solid #E0DCD6;
  border-radius: 4px;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #6B635A;
  cursor: pointer;
  transition: all 0.25s ease;
}

.gender-group :deep(.el-radio.is-checked .el-radio__label) {
  background-color: #8B7355;
  border-color: #8B7355;
  color: #FFF;
}

.bmi-result {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background-color: #FAFAF8;
  border-radius: 4px;
  margin: 24px 0;
}

.bmi-label {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #8B8175;
}

.bmi-value {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 600;
  color: #8B7355;
}

.bmi-status {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #6B635A;
  padding: 4px 12px;
  background-color: #E8E4DF;
  border-radius: 4px;
}

.form-actions {
  display: flex;
  gap: 16px;
  margin-top: 32px;
}

.btn-secondary {
  flex: 1;
  height: 44px;
  background-color: transparent;
  border: 1px solid #C4B8AB;
  border-radius: 4px;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #6B635A;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  border-color: #8B7355;
  color: #8B7355;
}

.btn-primary {
  flex: 1;
  height: 44px;
  background-color: #8B7355;
  border: none;
  border-radius: 4px;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: #FFF;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-primary:hover {
  background-color: #7A6548;
  transform: scale(1.02);
  box-shadow: 4px 4px 12px rgba(139, 115, 85, 0.25);
}

@media (max-width: 480px) {
  .health-form {
    padding: 24px 20px;
  }
  
  .step-label {
    font-size: 11px;
  }
  
  .step-line {
    width: 30px;
    margin: 0 8px;
  }
}
</style>
