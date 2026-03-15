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
                <el-form-item label="腰围 (cm)" prop="waistCircumference">
                  <el-input-number v-model="detailForm.waistCircumference" :min="40" :max="200" :precision="1" placeholder="请输入腰围" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="血型" prop="bloodType">
                  <el-select v-model="detailForm.bloodType" placeholder="请选择血型">
                    <el-option label="A型" value="A"></el-option>
                    <el-option label="B型" value="B"></el-option>
                    <el-option label="AB型" value="AB"></el-option>
                    <el-option label="O型" value="O"></el-option>
                    <el-option label="未知" value="未知"></el-option>
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="血压 (mmHg)" prop="bloodPressure">
                  <el-input v-model="detailForm.bloodPressure" placeholder="如: 120/80" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="血糖 (mmol/L)" prop="bloodSugar">
                  <el-input-number v-model="detailForm.bloodSugar" :min="0" :max="30" :precision="1" placeholder="请输入血糖" />
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
                  <el-input-number v-model="detailForm.exerciseDuration" :min="0" :max="480" :step="10" placeholder="请输入运动时长" />
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
              <el-input v-model="detailForm.allergies" type="textarea" :rows="2" placeholder="请输入过敏食物，多个用逗号分隔"></el-input>
            </el-form-item>
            
            <el-form-item label="慢性疾病" prop="chronicDiseases">
              <el-input v-model="detailForm.chronicDiseases" type="textarea" :rows="2" placeholder="请输入慢性疾病，如无则填写无"></el-input>
            </el-form-item>
            
            <el-form-item label="健康状况描述" prop="healthCondition">
              <el-input v-model="detailForm.healthCondition" type="textarea" :rows="2" placeholder="请描述您的健康状况"></el-input>
            </el-form-item>
          </div>
          
          <div class="form-actions">
            <el-button class="btn-secondary" @click="skipStep">跳过</el-button>
            <el-button class="btn-primary" @click="submitForm" :loading="loading">完成录入</el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useUserStore } from '../stores/user';
import healthInfoApi from '../api/healthInfo';

const router = useRouter();
const userStore = useUserStore();
const detailFormRef = ref(null);
const loading = ref(false);

const detailForm = reactive({
  userId: userStore.userId,
  waistCircumference: null,
  bloodType: '',
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
  activityLevel: [
    { required: true, message: '请选择活动水平', trigger: 'change' }
  ]
};

const submitForm = async () => {
  await detailFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        detailForm.exerciseType = detailForm.exerciseTypeArr.join(',');
        
        const formData = {
          ...detailForm,
          waistCircumference: detailForm.waistCircumference ? Number(detailForm.waistCircumference) : null,
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
        ElMessage.error('保存失败，请检查网络连接');
      } finally {
        loading.value = false;
      }
    }
  });
};

const skipStep = () => {
  router.push('/dashboard/health-info');
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
  color: #3D4A3E;
  margin: 0 0 8px 0;
  letter-spacing: 2px;
}

.health-subtitle {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #8A9A8C;
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
  font-size: 11px;
  color: #8A9A8C;
}

.step-item.active .step-label,
.step-item.completed .step-label {
  color: #3D4A3E;
}

.step-line {
  width: 50px;
  height: 2px;
  background-color: #E8F0EA;
  margin: 0 10px;
  margin-bottom: 22px;
  transition: background-color 0.3s ease;
}

.step-line.active {
  background-color: #7BA088;
}

.health-form {
  background: #FFF;
  padding: 32px 36px;
  border-radius: 4px;
  box-shadow: 
    8px 8px 24px rgba(61, 74, 62, 0.08),
    -2px -2px 8px rgba(255, 255, 255, 0.6);
}

.form-section {
  margin-bottom: 28px;
  padding-bottom: 24px;
  border-bottom: 1px solid #E8F0EA;
}

.form-section:last-of-type {
  border-bottom: none;
  margin-bottom: 0;
}

.section-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 15px;
  font-weight: 500;
  color: #3D4A3E;
  margin: 0 0 20px 0;
  padding-left: 12px;
  border-left: 3px solid #9BC1A8;
}

.health-form :deep(.el-form-item__label) {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #5A6B5C;
  padding-bottom: 6px;
}

.health-form :deep(.el-input-number),
.health-form :deep(.el-select) {
  width: 100%;
}

.health-form :deep(.el-input-number .el-input__wrapper) {
  background-color: #F7FAF8;
  border: 1px solid #D8E4DC;
  border-radius: 4px;
  box-shadow: none;
  padding: 0 12px;
  min-height: 40px;
}

.health-form :deep(.el-input__wrapper),
.health-form :deep(.el-textarea__inner) {
  background-color: #F7FAF8;
  border: 1px solid #D8E4DC;
  border-radius: 4px;
  box-shadow: none;
  padding: 8px 12px;
}

.health-form :deep(.el-input__wrapper:hover),
.health-form :deep(.el-textarea__inner:hover) {
  border-color: #B8C8B8;
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
  transition: background-color 0.3s ease;
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

.health-form :deep(.el-input-number .el-input__wrapper) {
  background-color: #FAFAF8;
  border: 1px solid #E0DCD6;
  border-radius: 4px;
  box-shadow: none;
  padding: 0 12px;
  min-height: 40px;
  display: flex;
  align-items: center;
}

.health-form :deep(.el-input-number .el-input) {
  height: 40px;
}

.health-form :deep(.el-input-number .el-input__inner) {
  height: 38px;
  line-height: 1;
}

.health-form :deep(.el-input__wrapper),
.health-form :deep(.el-textarea__inner) {
  background-color: #FAFAF8;
  border: 1px solid #E0DCD6;
  border-radius: 4px;
  box-shadow: none;
  padding: 8px 12px;
}

.health-form :deep(.el-input__wrapper:hover),
.health-form :deep(.el-textarea__inner:hover) {
  border-color: #C4B8AB;
}

.health-form :deep(.el-input.is-focus .el-input__wrapper),
.health-form :deep(.el-textarea:focus .el-textarea__inner) {
  border-color: #9BC1A8;
}

.health-form :deep(.el-input__inner),
.health-form :deep(.el-textarea__inner) {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #3D4A3E;
}

.exercise-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.exercise-group :deep(.el-checkbox__label) {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #5A6B5C;
}

.exercise-group :deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #7BA088;
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

.health-form :deep(.el-input__inner),
.health-form :deep(.el-textarea__inner) {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #4A4238;
}

.exercise-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.exercise-group :deep(.el-checkbox__label) {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #6B635A;
}

.exercise-group :deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #8B7355;
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
    font-size: 10px;
  }
  
  .step-line {
    width: 24px;
    margin: 0 6px;
  }
}
</style>
