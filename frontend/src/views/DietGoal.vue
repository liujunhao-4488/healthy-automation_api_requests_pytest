<template>
  <div class="diet-goal-container">
    <h2>饮食目标设置</h2>
    <el-form :model="dietGoalForm" :rules="rules" ref="dietGoalFormRef" label-width="160px">
      <el-card class="goal-type-card">
        <template #header>
          <span>目标类型</span>
        </template>
        <el-form-item label="目标类型" prop="goalType">
          <el-radio-group v-model="dietGoalForm.goalType">
            <el-radio label="weight_loss">减肥</el-radio>
            <el-radio label="muscle_gain">增肌</el-radio>
            <el-radio label="blood_sugar_control">控糖</el-radio>
            <el-radio label="maintain">维持健康</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="目标体重(kg)" prop="targetWeight">
          <el-input-number v-model="dietGoalForm.targetWeight" :min="20" :max="300" :precision="1"></el-input-number>
        </el-form-item>
      </el-card>
      
      <el-card class="nutrition-card" style="margin-top: 20px;">
        <template #header>
          <span>营养目标</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="每日热量(kcal)" prop="targetCalories">
              <el-input-number v-model="dietGoalForm.targetCalories" :min="800" :max="5000" :step="50"></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="每日饮水(ml)" prop="waterTarget">
              <el-input-number v-model="dietGoalForm.waterTarget" :min="500" :max="5000" :step="100"></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider>宏量营养素比例</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="蛋白质(g)" prop="proteinTarget">
              <el-input-number v-model="dietGoalForm.proteinTarget" :min="0" :max="300" :step="5"></el-input-number>
            </el-form-item>
            <el-form-item label="蛋白质占比(%)" prop="proteinRatio">
              <el-slider v-model="dietGoalForm.proteinRatio" :min="10" :max="50" show-input></el-slider>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="碳水化合物(g)" prop="carbsTarget">
              <el-input-number v-model="dietGoalForm.carbsTarget" :min="0" :max="500" :step="10"></el-input-number>
            </el-form-item>
            <el-form-item label="碳水占比(%)" prop="carbsRatio">
              <el-slider v-model="dietGoalForm.carbsRatio" :min="20" :max="70" show-input></el-slider>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="脂肪(g)" prop="fatTarget">
              <el-input-number v-model="dietGoalForm.fatTarget" :min="0" :max="200" :step="5"></el-input-number>
            </el-form-item>
            <el-form-item label="脂肪占比(%)" prop="fatRatio">
              <el-slider v-model="dietGoalForm.fatRatio" :min="10" :max="50" show-input></el-slider>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>
      
      <el-card class="schedule-card" style="margin-top: 20px;">
        <template #header>
          <span>计划时间</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期" prop="startDate">
              <el-date-picker v-model="dietGoalForm.startDate" type="date" placeholder="选择开始日期" style="width: 100%;"></el-date-picker>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期" prop="endDate">
              <el-date-picker v-model="dietGoalForm.endDate" type="date" placeholder="选择结束日期" style="width: 100%;"></el-date-picker>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>
      
      <el-card class="reminder-card" style="margin-top: 20px;">
        <template #header>
          <span>提醒设置</span>
        </template>
        <el-form-item label="开启提醒" prop="reminderEnabled">
          <el-switch v-model="dietGoalForm.reminderEnabled" :active-value="1" :inactive-value="0"></el-switch>
        </el-form-item>
        <el-form-item label="提醒时间" prop="reminderTime" v-if="dietGoalForm.reminderEnabled === 1">
          <el-time-picker v-model="dietGoalForm.reminderTime" placeholder="选择提醒时间" style="width: 100%;"></el-time-picker>
        </el-form-item>
      </el-card>
      
      <el-form-item style="margin-top: 20px;">
        <el-button type="primary" @click="saveDietGoal" :loading="loading">保存目标</el-button>
        <el-button @click="resetForm">重置</el-button>
        <el-button type="success" @click="autoCalculate">自动计算</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useUserStore } from '../stores/user';
import { ElMessage } from 'element-plus';
import dietGoalApi from '../api/dietGoal';

const userStore = useUserStore();
const dietGoalFormRef = ref(null);
const loading = ref(false);

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

const rules = {
  goalType: [
    { required: true, message: '请选择目标类型', trigger: 'change' }
  ],
  targetCalories: [
    { required: true, message: '请输入每日热量目标', trigger: 'blur' }
  ],
  startDate: [
    { required: true, message: '请选择开始日期', trigger: 'change' }
  ]
};

// 根据目标类型自动计算营养目标
const autoCalculate = () => {
  if (!userStore.healthInfo) {
    ElMessage.warning('请先填写健康信息，系统将根据您的身体数据自动计算');
    return;
  }
  
  const healthInfo = userStore.healthInfo;
  const bmr = healthInfo.bmr || calculateBMR(healthInfo);
  let calories = bmr;
  
  // 根据活动水平调整
  const activityMultiplier = {
    'sedentary': 1.2,
    'lightly_active': 1.375,
    'moderately_active': 1.55,
    'very_active': 1.725,
    'extra_active': 1.9
  };
  
  const activityLevel = healthInfo.activityLevel || 'sedentary';
  calories = bmr * (activityMultiplier[activityLevel] || 1.2);
  
  // 根据目标类型调整
  switch (dietGoalForm.goalType) {
    case 'weight_loss':
      calories = calories * 0.8; // 减肥减少20%
      break;
    case 'muscle_gain':
      calories = calories * 1.1; // 增肌增加10%
      break;
    case 'blood_sugar_control':
      calories = calories * 0.9; // 控糖减少10%
      break;
    default:
      break;
  }
  
  dietGoalForm.targetCalories = Math.round(calories);
  
  // 计算宏量营养素
  const proteinCals = calories * (dietGoalForm.proteinRatio / 100);
  const carbsCals = calories * (dietGoalForm.carbsRatio / 100);
  const fatCals = calories * (dietGoalForm.fatRatio / 100);
  
  dietGoalForm.proteinTarget = Math.round(proteinCals / 4);
  dietGoalForm.carbsTarget = Math.round(carbsCals / 4);
  dietGoalForm.fatTarget = Math.round(fatCals / 9);
  
  ElMessage.success('已根据您的健康信息自动计算营养目标');
};

const calculateBMR = (healthInfo) => {
  if (!healthInfo.height || !healthInfo.weight || !healthInfo.age) {
    return 0;
  }
  let bmr = 0;
  if (healthInfo.gender === '男') {
    bmr = 88.362 + (13.397 * healthInfo.weight) + (4.799 * healthInfo.height) - (5.677 * healthInfo.age);
  } else {
    bmr = 447.593 + (9.247 * healthInfo.weight) + (3.098 * healthInfo.height) - (4.330 * healthInfo.age);
  }
  return Math.round(bmr);
};

const saveDietGoal = async () => {
  await dietGoalFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const formData = {
          ...dietGoalForm,
          startDate: dietGoalForm.startDate ? formatDate(dietGoalForm.startDate) : null,
          endDate: dietGoalForm.endDate ? formatDate(dietGoalForm.endDate) : null,
          reminderTime: dietGoalForm.reminderTime ? formatTime(dietGoalForm.reminderTime) : null
        };
        
        let response;
        if (userStore.hasDietGoal) {
          response = await dietGoalApi.updateDietGoal(formData);
        } else {
          response = await dietGoalApi.saveDietGoal(formData);
        }
        if (response.code === 200) {
          userStore.setDietGoal(formData);
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

const formatDate = (date) => {
  if (typeof date === 'string') return date;
  const d = new Date(date);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

const formatTime = (time) => {
  if (!time) return null;
  if (typeof time === 'string') return time;
  const t = new Date(time);
  return `${String(t.getHours()).padStart(2, '0')}:${String(t.getMinutes()).padStart(2, '0')}:00`;
};

const resetForm = () => {
  dietGoalFormRef.value.resetFields();
};

const loadDietGoal = async () => {
  try {
    const response = await dietGoalApi.getDietGoal();
    if (response.code === 200 && response.data) {
      Object.assign(dietGoalForm, response.data);
      userStore.setDietGoal(response.data);
    }
  } catch (error) {
    console.error('获取饮食目标失败:', error);
  }
};

onMounted(() => {
  loadDietGoal();
});
</script>

<style scoped>
.diet-goal-container {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

h2 {
  margin-bottom: 20px;
  color: #303133;
}

.el-form-item {
  margin-bottom: 18px;
}

.el-divider {
  margin: 20px 0;
}
</style>
