<template>
  <div class="edit-page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Edit Profile</p>
        <h2>修改健康信息</h2>
        <p>在这里更新你的基础信息、体征和运动习惯，保存后会返回健康档案页。</p>
      </div>
      <el-button class="ghost-button" @click="goBack">返回档案</el-button>
    </div>

    <el-card class="edit-card" shadow="never">
      <el-form :model="healthInfoForm" :rules="rules" ref="healthInfoFormRef" label-width="120px" class="info-form">
        <el-row :gutter="20">
          <el-col :md="12" :xs="24">
            <el-form-item label="年龄" prop="age">
              <el-input-number v-model="healthInfoForm.age" :min="1" :max="150" />
            </el-form-item>
          </el-col>
          <el-col :md="12" :xs="24">
            <el-form-item label="性别" prop="gender">
              <el-radio-group v-model="healthInfoForm.gender">
                <el-radio label="男">男</el-radio>
                <el-radio label="女">女</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :md="12" :xs="24">
            <el-form-item label="身高(cm)" prop="height">
              <el-input-number v-model="healthInfoForm.height" :min="50" :max="250" :precision="1" />
            </el-form-item>
          </el-col>
          <el-col :md="12" :xs="24">
            <el-form-item label="体重(kg)" prop="weight">
              <el-input-number v-model="healthInfoForm.weight" :min="20" :max="300" :precision="1" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :md="12" :xs="24">
            <el-form-item label="血压" prop="bloodPressure">
              <el-input v-model="healthInfoForm.bloodPressure" placeholder="例如 120/80" />
            </el-form-item>
          </el-col>
          <el-col :md="12" :xs="24">
            <el-form-item label="血糖(mmol/L)" prop="bloodSugar">
              <el-input-number v-model="healthInfoForm.bloodSugar" :min="0" :max="30" :precision="1" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :md="12" :xs="24">
            <el-form-item label="BMI">
              <el-input :model-value="healthInfoForm.bmi" disabled />
            </el-form-item>
          </el-col>
          <el-col :md="12" :xs="24">
            <el-form-item label="基础代谢">
              <el-input :model-value="healthInfoForm.bmr" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :md="12" :xs="24">
            <el-form-item label="活动水平" prop="activityLevel">
              <el-select v-model="healthInfoForm.activityLevel" placeholder="请选择活动水平">
                <el-option label="久坐少动" value="sedentary" />
                <el-option label="轻度活动" value="lightly_active" />
                <el-option label="中度活动" value="moderately_active" />
                <el-option label="高度活动" value="very_active" />
                <el-option label="高强度活动" value="extra_active" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :md="12" :xs="24">
            <el-form-item label="运动时长(分钟)" prop="exerciseDuration">
              <el-input-number v-model="healthInfoForm.exerciseDuration" :min="0" :max="480" :step="10" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="运动类型">
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

        <el-form-item label="慢性疾病">
          <el-input v-model="healthInfoForm.chronicDiseases" type="textarea" :rows="2" placeholder="如无可填写无" />
        </el-form-item>

        <div class="actions">
          <el-button class="ghost-button" @click="goBack">取消</el-button>
          <el-button class="save-button" type="primary" @click="saveHealthInfo" :loading="loading">保存修改</el-button>
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
import healthInfoApi from '../api/healthInfo';

const router = useRouter();
const userStore = useUserStore();
const healthInfoFormRef = ref(null);
const loading = ref(false);

const healthInfoForm = reactive({
  userId: userStore.userId,
  age: null,
  gender: '',
  height: null,
  weight: null,
  bmi: '',
  bmr: '',
  bloodPressure: '',
  bloodSugar: null,
  activityLevel: '',
  exerciseDuration: null,
  exerciseTypeArr: [],
  exerciseType: '',
  chronicDiseases: ''
});

const rules = {
  age: [{ required: true, message: '请输入年龄', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  height: [{ required: true, message: '请输入身高', trigger: 'blur' }],
  weight: [{ required: true, message: '请输入体重', trigger: 'blur' }],
  activityLevel: [{ required: true, message: '请选择活动水平', trigger: 'change' }]
};

const calculateBMI = () => {
  if (healthInfoForm.height && healthInfoForm.weight) {
    const heightInMeters = Number(healthInfoForm.height) / 100;
    const weight = Number(healthInfoForm.weight);
    healthInfoForm.bmi = (weight / (heightInMeters * heightInMeters)).toFixed(1);
    calculateBMR();
  }
};

const calculateBMR = () => {
  if (healthInfoForm.height && healthInfoForm.weight && healthInfoForm.age && healthInfoForm.gender) {
    const isMale = healthInfoForm.gender === '男';
    const bmr = isMale
      ? 88.362 + (13.397 * healthInfoForm.weight) + (4.799 * healthInfoForm.height) - (5.677 * healthInfoForm.age)
      : 447.593 + (9.247 * healthInfoForm.weight) + (3.098 * healthInfoForm.height) - (4.33 * healthInfoForm.age);
    healthInfoForm.bmr = Math.round(bmr);
  }
};

watch(
  [() => healthInfoForm.height, () => healthInfoForm.weight, () => healthInfoForm.age, () => healthInfoForm.gender],
  () => calculateBMI()
);

const applyHealthInfo = (info) => {
  Object.assign(healthInfoForm, {
    ...healthInfoForm,
    ...info,
    exerciseTypeArr: info?.exerciseType ? info.exerciseType.split(',') : []
  });
};

const loadHealthInfo = async () => {
  try {
    const response = await healthInfoApi.getHealthInfo();
    if (response.code === 200 && response.data) {
      applyHealthInfo(response.data);
      userStore.setHealthInfo(response.data);
      userStore.setHealthAnalysis(response.analysis || null);
      return;
    }
  } catch (error) {
    console.error('获取健康信息失败:', error);
  }

  if (userStore.healthInfo) {
    applyHealthInfo(userStore.healthInfo);
  }
};

const saveHealthInfo = async () => {
  healthInfoFormRef.value.validate(async (valid) => {
    if (!valid) return;

    calculateBMI();
    healthInfoForm.exerciseType = healthInfoForm.exerciseTypeArr.join(',');

    const formData = {
      ...healthInfoForm,
      age: Number(healthInfoForm.age),
      height: Number(healthInfoForm.height),
      weight: Number(healthInfoForm.weight),
      bloodPressure: healthInfoForm.bloodPressure || '',
      bloodSugar: healthInfoForm.bloodSugar ? Number(healthInfoForm.bloodSugar) : null,
      exerciseDuration: healthInfoForm.exerciseDuration ? Number(healthInfoForm.exerciseDuration) : null
    };

    loading.value = true;
    try {
      const response = await healthInfoApi.updateHealthInfo(formData);
      if (response.code === 200) {
        userStore.setHealthInfo({
          ...formData,
          bmi: healthInfoForm.bmi,
          bmr: healthInfoForm.bmr
        });
        ElMessage.success('健康信息已更新');
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

const goBack = () => {
  router.push('/dashboard/health-info');
};

onMounted(() => {
  loadHealthInfo();
});
</script>

<style scoped>
.edit-page {
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
  color: #8b7355;
}

.page-header h2 {
  margin: 0;
  font-family: 'Noto Serif SC', serif;
  font-size: 30px;
  color: #43372b;
}

.page-header p {
  margin: 10px 0 0;
  color: #76695b;
  line-height: 1.7;
}

.edit-card {
  border: 1px solid #eee6da;
  border-radius: 24px;
}

.info-form :deep(.el-form-item__label) {
  color: #6b635a;
}

.info-form :deep(.el-input-number),
.info-form :deep(.el-select) {
  width: 100%;
}

.info-form :deep(.el-input__wrapper),
.info-form :deep(.el-input-number .el-input__wrapper),
.info-form :deep(.el-textarea__inner) {
  background-color: #faf7f2;
  border: 1px solid #e5dbce;
  box-shadow: none;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 28px;
}

.ghost-button {
  border-color: #d5c8b8;
  color: #6b5b49;
}

.save-button {
  min-width: 120px;
  border: none;
  background: linear-gradient(135deg, #8b7355 0%, #6f8f72 100%);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .actions {
    flex-direction: column;
  }
}
</style>
