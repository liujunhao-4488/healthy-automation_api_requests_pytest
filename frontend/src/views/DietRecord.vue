<template>
  <div class="diet-record-container">
    <h2>饮食记录</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="添加记录" name="add">
        <el-form :model="dietRecordForm" :rules="rules" ref="dietRecordFormRef" label-width="120px">
          <el-form-item label="日期" prop="date">
            <el-date-picker v-model="dietRecordForm.date" type="date" placeholder="选择日期"></el-date-picker>
          </el-form-item>
          <el-form-item label="餐次" prop="mealType">
            <el-select v-model="dietRecordForm.mealType" placeholder="请选择餐次">
              <el-option label="早餐" value="breakfast"></el-option>
              <el-option label="午餐" value="lunch"></el-option>
              <el-option label="晚餐" value="dinner"></el-option>
              <el-option label="加餐" value="snack"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="食物名称" prop="foodName">
            <el-input v-model="dietRecordForm.foodName" placeholder="请输入食物名称"></el-input>
          </el-form-item>
          <el-form-item label="热量(kcal)" prop="calories">
            <el-input v-model="dietRecordForm.calories" placeholder="请输入热量"></el-input>
          </el-form-item>
          <el-form-item label="蛋白质(g)" prop="protein">
            <el-input v-model="dietRecordForm.protein" placeholder="请输入蛋白质"></el-input>
          </el-form-item>
          <el-form-item label="碳水化合物(g)" prop="carbs">
            <el-input v-model="dietRecordForm.carbs" placeholder="请输入碳水化合物"></el-input>
          </el-form-item>
          <el-form-item label="脂肪(g)" prop="fat">
            <el-input v-model="dietRecordForm.fat" placeholder="请输入脂肪"></el-input>
          </el-form-item>
          <el-form-item label="备注" prop="notes">
            <el-input v-model="dietRecordForm.notes" type="textarea" placeholder="请输入备注"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveDietRecord" :loading="loading">保存</el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="记录列表" name="list">
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" @change="loadDietRecords"></el-date-picker>
        <el-button type="primary" @click="loadDietRecords" style="margin-left: 10px;">查询</el-button>
        <el-table :data="dietRecords" style="margin-top: 20px;">
          <el-table-column prop="date" label="日期" width="180"></el-table-column>
          <el-table-column prop="mealType" label="餐次" width="120"></el-table-column>
          <el-table-column prop="foodName" label="食物名称"></el-table-column>
          <el-table-column prop="calories" label="热量(kcal)" width="120"></el-table-column>
          <el-table-column prop="protein" label="蛋白质(g)" width="120"></el-table-column>
          <el-table-column prop="carbs" label="碳水化合物(g)" width="150"></el-table-column>
          <el-table-column prop="fat" label="脂肪(g)" width="120"></el-table-column>
          <el-table-column prop="notes" label="备注"></el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="分析图表" name="analysis">
        <div class="analysis-charts">
          <div class="chart-item">
            <h3>每日热量摄入趋势</h3>
            <div ref="calorieChart" style="width: 100%; height: 400px;"></div>
          </div>
          <div class="chart-item">
            <h3>营养成分分布</h3>
            <div ref="nutritionChart" style="width: 100%; height: 400px;"></div>
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="饮食建议" name="suggestions">
        <el-card class="suggestion-card">
          <template #header>
            <div class="card-header">
              <span>饮食建议与误区提醒</span>
              <el-button type="primary" @click="loadDietSuggestions" :loading="suggestionLoading">刷新建议</el-button>
            </div>
          </template>
          <el-alert
            v-for="(suggestion, index) in dietSuggestions"
            :key="index"
            :title="suggestion"
            :type="suggestion.startsWith('⚠️') ? 'warning' : suggestion.startsWith('✓') ? 'success' : 'info'"
            :closable="false"
            style="margin-bottom: 10px;"
          />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { useUserStore } from '../stores/user';
import { ElMessage } from 'element-plus';
import dietRecordApi from '../api/dietRecord';
import * as echarts from 'echarts';

const userStore = useUserStore();
const activeTab = ref('add');
const dietRecordFormRef = ref(null);
const dietRecordForm = reactive({
  userId: userStore.userId,
  date: '',
  mealType: '',
  foodName: '',
  calories: '',
  protein: '',
  carbs: '',
  fat: '',
  notes: ''
});

const rules = {
  date: [
    { required: true, message: '请选择日期', trigger: 'blur' }
  ],
  mealType: [
    { required: true, message: '请选择餐次', trigger: 'blur' }
  ],
  foodName: [
    { required: true, message: '请输入食物名称', trigger: 'blur' }
  ],
  calories: [
    { required: true, message: '请输入热量', trigger: 'blur' },
    { type: 'number', message: '请输入有效的热量值', trigger: 'blur' }
  ],
  protein: [
    { required: true, message: '请输入蛋白质', trigger: 'blur' },
    { type: 'number', message: '请输入有效的蛋白质值', trigger: 'blur' }
  ],
  carbs: [
    { required: true, message: '请输入碳水化合物', trigger: 'blur' },
    { type: 'number', message: '请输入有效的碳水化合物值', trigger: 'blur' }
  ],
  fat: [
    { required: true, message: '请输入脂肪', trigger: 'blur' },
    { type: 'number', message: '请输入有效的脂肪值', trigger: 'blur' }
  ]
};

const dietRecords = ref([]);
const dateRange = ref([]);
const loading = ref(false);

const calorieChart = ref(null);
const nutritionChart = ref(null);
const dietSuggestions = ref([]);
const suggestionLoading = ref(false);

const saveDietRecord = async () => {
  await dietRecordFormRef.value.validate(async (valid) => {
    if (valid) {
      dietRecordForm.userId = userStore.userId;
      loading.value = true;
      try {
        const response = await dietRecordApi.submitRecord(dietRecordForm);
        if (response.code === 200) {
          ElMessage.success('保存成功');
          resetForm();
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

const loadDietSuggestions = async () => {
  suggestionLoading.value = true;
  try {
    const response = await dietRecordApi.getDietSuggestions();
    if (response.code === 200) {
      dietSuggestions.value = response.data;
    } else {
      ElMessage.error(response.message || '获取建议失败');
    }
  } catch (error) {
    ElMessage.error('获取建议失败，请检查网络连接');
  } finally {
    suggestionLoading.value = false;
  }
};

const resetForm = () => {
  dietRecordFormRef.value.resetFields();
};

const loadDietRecords = async () => {
  if (!userStore.userId) {
    ElMessage.error('用户未登录');
    return;
  }
  loading.value = true;
  try {
    const startDate = dateRange.value[0] ? dateRange.value[0] : '';
    const endDate = dateRange.value[1] ? dateRange.value[1] : '';
    const response = await dietRecordApi.getDietRecords(startDate, endDate);
    if (response.code === 200) {
      dietRecords.value = response.data;
    } else {
      ElMessage.error(response.message || '获取记录失败');
    }
  } catch (error) {
    ElMessage.error('获取记录失败，请检查网络连接');
  } finally {
    loading.value = false;
  }
};

const loadDietAnalysis = async () => {
  if (!userStore.userId) {
    return;
  }
  try {
    const startDate = dateRange.value[0] ? dateRange.value[0] : '';
    const endDate = dateRange.value[1] ? dateRange.value[1] : '';
    const response = await dietRecordApi.getDietAnalysis(startDate, endDate);
    if (response.code === 200) {
      renderCharts(response.data);
    }
  } catch (error) {
    console.error('获取分析数据失败:', error);
  }
};

const renderCharts = (analysisData) => {
  // 渲染热量摄入趋势图
  if (calorieChart.value) {
    const chart = echarts.init(calorieChart.value);
    const dailyStats = analysisData.dailyStats || {};
    const dates = Object.keys(dailyStats).sort();
    const calories = dates.map(date => dailyStats[date].calories || 0);
    const option = {
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: dates
      },
      yAxis: {
        type: 'value',
        name: '热量(kcal)'
      },
      series: [{
        data: calories,
        type: 'line',
        smooth: true,
        areaStyle: {
          opacity: 0.3
        }
      }]
    };
    chart.setOption(option);
  }

  // 渲染营养成分分布图
  if (nutritionChart.value) {
    const chart = echarts.init(nutritionChart.value);
    const option = {
      tooltip: {
        trigger: 'item'
      },
      legend: {
        top: '5%',
        left: 'center'
      },
      series: [{
        name: '营养成分',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { value: analysisData.totalProtein || 0, name: '蛋白质' },
          { value: analysisData.totalCarbs || 0, name: '碳水化合物' },
          { value: analysisData.totalFat || 0, name: '脂肪' }
        ]
      }]
    };
    chart.setOption(option);
  }
};

// 监听标签页变化，当切换到分析标签页时加载分析数据
watch(activeTab, (newTab) => {
  if (newTab === 'analysis') {
    setTimeout(() => {
      loadDietAnalysis();
    }, 100);
  }
  if (newTab === 'suggestions') {
    setTimeout(() => {
      loadDietSuggestions();
    }, 100);
  }
});

onMounted(() => {
  // 设置默认日期为今天
  dietRecordForm.date = new Date();
  // 初始化日期范围为最近7天
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 6);
  dateRange.value = [start, end];
});
</script>

<style scoped>
.diet-record-container {
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
  margin-bottom: 20px;
}

.analysis-charts {
  margin-top: 20px;
}

.chart-item {
  margin-bottom: 30px;
}

.chart-item h3 {
  margin-bottom: 10px;
  color: #303133;
}

.suggestion-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>