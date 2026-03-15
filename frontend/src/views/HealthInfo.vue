<template>
  <div class="health-info-container">
    <h2>健康信息管理</h2>
    <el-form :model="healthInfoForm" :rules="rules" ref="healthInfoFormRef" label-width="140px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="年龄" prop="age">
            <el-input-number v-model="healthInfoForm.age" :min="1" :max="150" placeholder="请输入年龄"></el-input-number>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="性别" prop="gender">
            <el-radio-group v-model="healthInfoForm.gender">
              <el-radio label="男">男</el-radio>
              <el-radio label="女">女</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="身高(cm)" prop="height">
            <el-input-number v-model="healthInfoForm.height" :min="50" :max="250" :precision="1" placeholder="请输入身高"></el-input-number>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="体重(kg)" prop="weight">
            <el-input-number v-model="healthInfoForm.weight" :min="20" :max="300" :precision="1" placeholder="请输入体重"></el-input-number>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="腰围(cm)" prop="waistCircumference">
            <el-input-number v-model="healthInfoForm.waistCircumference" :min="40" :max="200" :precision="1" placeholder="请输入腰围"></el-input-number>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="血型" prop="bloodType">
            <el-select v-model="healthInfoForm.bloodType" placeholder="请选择血型">
              <el-option label="A型" value="A"></el-option>
              <el-option label="B型" value="B"></el-option>
              <el-option label="AB型" value="AB"></el-option>
              <el-option label="O型" value="O"></el-option>
              <el-option label="未知" value="未知"></el-option>
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="血压(mmHg)" prop="bloodPressure">
            <el-input v-model="healthInfoForm.bloodPressure" placeholder="如: 120/80"></el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="血糖(mmol/L)" prop="bloodSugar">
            <el-input-number v-model="healthInfoForm.bloodSugar" :min="0" :max="30" :precision="1" placeholder="请输入血糖"></el-input-number>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="BMI" prop="bmi">
            <el-input v-model="healthInfoForm.bmi" placeholder="自动计算" disabled></el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="基础代谢率(kcal)" prop="bmr">
            <el-input v-model="healthInfoForm.bmr" placeholder="自动计算" disabled></el-input>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="活动水平" prop="activityLevel">
            <el-select v-model="healthInfoForm.activityLevel" placeholder="请选择活动水平">
              <el-option label="久坐不动 (办公室工作，几乎无运动)" value="sedentary"></el-option>
              <el-option label="轻度活动 (每周1-3天运动)" value="lightly_active"></el-option>
              <el-option label="中度活动 (每周3-5天运动)" value="moderately_active"></el-option>
              <el-option label="高度活动 (每周6-7天运动)" value="very_active"></el-option>
              <el-option label="极高活动 (体力劳动或高强度训练)" value="extra_active"></el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="每日运动时长(分钟)" prop="exerciseDuration">
            <el-input-number v-model="healthInfoForm.exerciseDuration" :min="0" :max="480" :step="10" placeholder="请输入运动时长"></el-input-number>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-form-item label="运动类型" prop="exerciseType">
        <el-checkbox-group v-model="healthInfoForm.exerciseTypeArr">
          <el-checkbox label="跑步">跑步</el-checkbox>
          <el-checkbox label="游泳">游泳</el-checkbox>
          <el-checkbox label="骑行">骑行</el-checkbox>
          <el-checkbox label="健身">健身</el-checkbox>
          <el-checkbox label="瑜伽">瑜伽</el-checkbox>
          <el-checkbox label="球类">球类</el-checkbox>
          <el-checkbox label="其他">其他</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
      
      <el-form-item label="过敏食物" prop="allergies">
        <el-input v-model="healthInfoForm.allergies" type="textarea" :rows="2" placeholder="请输入过敏食物，多个用逗号分隔"></el-input>
      </el-form-item>
      
      <el-form-item label="慢性疾病" prop="chronicDiseases">
        <el-input v-model="healthInfoForm.chronicDiseases" type="textarea" :rows="2" placeholder="请输入慢性疾病，如无则填写无"></el-input>
      </el-form-item>
      
      <el-form-item label="健康状况" prop="healthCondition">
        <el-input v-model="healthInfoForm.healthCondition" type="textarea" :rows="2" placeholder="请描述您的健康状况"></el-input>
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="saveHealthInfo" :loading="loading">保存</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { useUserStore } from '../stores/user';
import { ElMessage } from 'element-plus';
import healthInfoApi from '../api/healthInfo';

const userStore = useUserStore();
const healthInfoFormRef = ref(null);
const loading = ref(false);

const healthInfoForm = reactive({
  userId: userStore.userId,
  age: null,
  gender: '',
  height: null,
  weight: null,
  waistCircumference: null,
  bmi: '',
  bmr: '',
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
  ],
  activityLevel: [
    { required: true, message: '请选择活动水平', trigger: 'change' }
  ]
};

// 计算BMI
const calculateBMI = () => {
  if (healthInfoForm.height && healthInfoForm.weight) {
    const heightInMeters = Number(healthInfoForm.height) / 100;
    const weight = Number(healthInfoForm.weight);
    const bmi = (weight / (heightInMeters * heightInMeters)).toFixed(2);
    healthInfoForm.bmi = bmi;
    calculateBMR();
  }
};

// 计算BMR (基础代谢率)
const calculateBMR = () => {
  if (healthInfoForm.height && healthInfoForm.weight && healthInfoForm.age && healthInfoForm.gender) {
    let bmr = 0;
    if (healthInfoForm.gender === '男') {
      bmr = 88.362 + (13.397 * healthInfoForm.weight) + (4.799 * healthInfoForm.height) - (5.677 * healthInfoForm.age);
    } else {
      bmr = 447.593 + (9.247 * healthInfoForm.weight) + (3.098 * healthInfoForm.height) - (4.330 * healthInfoForm.age);
    }
    healthInfoForm.bmr = Math.round(bmr);
  }
};

// 监听身高和体重变化，自动计算BMI和BMR
watch(
  [() => healthInfoForm.height, () => healthInfoForm.weight, () => healthInfoForm.age, () => healthInfoForm.gender],
  () => {
    calculateBMI();
  }
);

const saveHealthInfo = async () => {
  healthInfoFormRef.value.validate(async (valid) => {
    if (valid) {
      calculateBMI();
      healthInfoForm.exerciseType = healthInfoForm.exerciseTypeArr.join(',');
      
      const formData = {
        ...healthInfoForm,
        age: Number(healthInfoForm.age),
        height: Number(healthInfoForm.height),
        weight: Number(healthInfoForm.weight),
        waistCircumference: healthInfoForm.waistCircumference ? Number(healthInfoForm.waistCircumference) : null,
        bloodSugar: healthInfoForm.bloodSugar ? Number(healthInfoForm.bloodSugar) : null,
        exerciseDuration: healthInfoForm.exerciseDuration ? Number(healthInfoForm.exerciseDuration) : null
      };
      
      loading.value = true;
      try {
        let response;
        if (userStore.hasHealthInfo) {
          response = await healthInfoApi.updateHealthInfo(formData);
        } else {
          response = await healthInfoApi.saveHealthInfo(formData);
        }
        if (response.code === 200) {
          userStore.setHealthInfo(formData);
          ElMessage.success('保存成功');
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

const resetForm = () => {
  healthInfoFormRef.value.resetFields();
  healthInfoForm.exerciseTypeArr = [];
};

const loadHealthInfo = async () => {
  if (userStore.userId) {
    try {
      const response = await healthInfoApi.getHealthInfo();
      if (response.code === 200 && response.data) {
        Object.assign(healthInfoForm, response.data);
        if (response.data.exerciseType) {
          healthInfoForm.exerciseTypeArr = response.data.exerciseType.split(',');
        }
        userStore.setHealthInfo(response.data);
      }
    } catch (error) {
      console.error('获取健康信息失败:', error);
    }
  }
};

onMounted(() => {
  loadHealthInfo();
});
</script>

<style scoped>
.health-info-container {
  background-color: #FFF;
  padding: 32px;
  border-radius: 4px;
  box-shadow: 8px 8px 24px rgba(61, 74, 62, 0.08);
}

.health-info-container :deep(.el-form-item__label) {
  font-family: 'Noto Sans SC', sans-serif;
  color: #5A6B5C;
  font-size: 13px;
}

.health-info-container :deep(.el-input-number) {
  width: 100%;
}

.health-info-container :deep(.el-input-number .el-input__wrapper) {
  background-color: #F7FAF8;
  border: 1px solid #D8E4DC;
  border-radius: 4px;
  padding: 0 12px;
  min-height: 40px;
}

.health-info-container :deep(.el-input-number .el-input__inner) {
  text-align: center;
}

.health-info-container :deep(.el-input__wrapper) {
  background-color: #F7FAF8;
  border: 1px solid #D8E4DC;
  border-radius: 4px;
  padding: 8px 12px;
  min-height: 40px;
}

.health-info-container :deep(.el-select) {
  width: 100%;
}

.health-info-container :deep(.el-checkbox-group),
.health-info-container :deep(.el-radio-group) {
  font-family: 'Noto Sans SC', sans-serif;
}

h2 {
  margin-bottom: 24px;
  color: #3D4A3E;
  font-family: 'Noto Serif SC', serif;
  font-weight: 500;
  font-size: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #E8F0EA;
}

.el-form-item {
  margin-bottom: 20px;
}

.el-form-item:last-child {
  margin-top: 32px;
}

.el-form-item:last-child :deep(.el-button--primary) {
  background-color: #7BA088;
  border-color: #7BA088;
  font-family: 'Noto Sans SC', sans-serif;
}

.el-form-item:last-child :deep(.el-button--primary:hover) {
  background-color: #6A9177;
  border-color: #6A9177;
}
</style>
