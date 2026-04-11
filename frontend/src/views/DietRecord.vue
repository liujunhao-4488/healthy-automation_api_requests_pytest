<template>
  <div class="diet-record-page">
    <section class="page-hero">
      <div>
        <p class="eyebrow">Diet Record</p>
        <h2>饮食记录</h2>
        <p>先查看最近饮食记录和摄入状态，再根据需要新增记录。</p>
      </div>
      <el-button type="primary" class="add-button" @click="openAddDialog">添加记录</el-button>
    </section>

    <section class="summary-grid">
      <el-card class="summary-card" shadow="never">
        <span>目标热量</span>
        <strong>{{ goalSummary.targetCalories }} kcal</strong>
        <small>来自当前饮食目标</small>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <span>平均摄入</span>
        <strong>{{ goalSummary.averageCalories }} kcal</strong>
        <small>按当前筛选范围统计</small>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <span>达标率</span>
        <strong>{{ goalSummary.completionRate }}%</strong>
        <small>越接近目标越高</small>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <span>营养评价</span>
        <strong>{{ goalSummary.statusText }}</strong>
        <small>{{ dietRecords.length }} 条记录</small>
      </el-card>
    </section>

    <section class="content-stack">
      <el-card class="record-card" shadow="never">
        <template #header>
          <div class="section-head">
            <div>
              <span>记录列表</span>
              <p>按时间查看已保存的饮食记录</p>
            </div>
            <div class="filter-tools">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                @change="handleDateChange"
              />
              <el-button plain @click="loadDietRecords">查询</el-button>
            </div>
          </div>
        </template>

        <el-table v-loading="loading" :data="dietRecords" stripe class="record-table">
          <el-table-column type="expand" width="56">
            <template #default="{ row }">
              <div class="detail-panel">
                <div class="detail-head">
                  <strong>饮食明细</strong>
                  <span>{{ row.detailCount }} 项食物</span>
                </div>
                <el-table
                  v-if="row.details.length"
                  :data="row.details"
                  size="small"
                  class="detail-table"
                  border
                >
                  <el-table-column prop="foodName" label="食物名称" min-width="160" />
                  <el-table-column prop="quantityText" label="分量(单位)" width="120" />
                  <el-table-column prop="calories" label="热量(kcal)" width="110" />
                  <el-table-column prop="protein" label="蛋白质(g)" width="110" />
                  <el-table-column prop="carbs" label="碳水(g)" width="100" />
                  <el-table-column prop="fat" label="脂肪(g)" width="100" />
                </el-table>
                <el-empty v-else description="暂无详细食物明细" :image-size="70" />
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="mealTypeLabel" label="餐次" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="mealTagType(row.mealType)">{{ row.mealTypeLabel }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="mealName" label="本餐名称" min-width="220" show-overflow-tooltip />
          <el-table-column prop="detailCount" label="明细数" width="90" />
          <el-table-column prop="calories" label="热量(kcal)" width="110" />
          <el-table-column prop="protein" label="蛋白质(g)" width="110" />
          <el-table-column prop="carbs" label="碳水(g)" width="100" />
          <el-table-column prop="fat" label="脂肪(g)" width="100" />
          <el-table-column prop="notes" label="备注" min-width="180" show-overflow-tooltip />
          <el-table-column label="操作" width="88" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" link @click="deleteDietRecord(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card class="chart-card" shadow="never">
        <template #header>
          <div class="section-head compact">
            <div>
              <span>趋势分析</span>
              <p>切换查看热量趋势或营养分布</p>
            </div>
            <el-radio-group v-model="activeChart" size="small">
              <el-radio-button label="calorie">热量</el-radio-button>
              <el-radio-button label="nutrition">营养</el-radio-button>
            </el-radio-group>
          </div>
        </template>
        <div ref="chartCanvas" class="chart-canvas"></div>
      </el-card>
    </section>

    <el-card class="suggestion-card" shadow="never">
      <template #header>
        <div class="section-head compact">
          <div>
            <span>饮食建议</span>
            <p>根据最近记录自动生成提醒</p>
          </div>
          <el-button plain size="small" @click="loadDietSuggestions" :loading="suggestionLoading">
            刷新
          </el-button>
        </div>
      </template>

      <div v-if="dietSuggestions.length" class="suggestion-list">
        <el-alert
          v-for="(suggestion, index) in dietSuggestions"
          :key="index"
          :title="suggestion"
          :type="getSuggestionType(suggestion)"
          :closable="false"
          show-icon
        />
      </div>
      <el-empty v-else description="当前没有新的饮食建议" />
    </el-card>

    <el-dialog v-model="dialogVisible" title="添加饮食记录" width="920px" @closed="resetForm">
      <el-form ref="dietRecordFormRef" :model="dietRecordForm" :rules="rules" label-width="100px">
        <el-form-item label="日期" prop="date">
          <el-date-picker
            v-model="dietRecordForm.date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="餐次" prop="mealType">
          <el-select v-model="dietRecordForm.mealType" placeholder="请选择餐次" style="width: 100%;">
            <el-option label="早餐" value="breakfast" />
            <el-option label="午餐" value="lunch" />
            <el-option label="晚餐" value="dinner" />
            <el-option label="加餐" value="snack" />
          </el-select>
        </el-form-item>
        <el-form-item label="菜品名称" prop="foodName">
          <el-input v-model="dietRecordForm.foodName" placeholder="请输入这餐菜品名称，例如：三文鱼藜麦沙拉" />
        </el-form-item>

        <el-form-item label="食材明细">
          <div class="ingredient-editor">
            <div v-for="(ingredient, index) in dietRecordForm.ingredients" :key="index" class="ingredient-row">
              <el-input
                v-model="ingredient.foodName"
                class="ingredient-name"
                placeholder="食材名称"
              />
              <el-input-number
                v-model="ingredient.amount"
                class="ingredient-amount"
                :min="0"
                :step="10"
                :precision="1"
              />
              <el-select v-model="ingredient.unit" class="ingredient-unit" placeholder="单位">
                <el-option label="g" value="g" />
                <el-option label="ml" value="ml" />
                <el-option label="份" value="份" />
                <el-option label="个" value="个" />
                <el-option label="碗" value="碗" />
              </el-select>
              <el-input v-model="ingredient.calories" class="ingredient-metric" placeholder="热量(kcal)" />
              <el-input v-model="ingredient.protein" class="ingredient-metric" placeholder="蛋白质(g)" />
              <el-input v-model="ingredient.carbs" class="ingredient-metric" placeholder="碳水(g)" />
              <el-input v-model="ingredient.fat" class="ingredient-metric" placeholder="脂肪(g)" />
              <el-button
                type="danger"
                link
                :disabled="dietRecordForm.ingredients.length === 1"
                @click="removeIngredient(index)"
              >
                删除
              </el-button>
            </div>

            <el-button plain class="add-ingredient-btn" @click="addIngredient">
              添加食材
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="备注" prop="notes">
          <el-input v-model="dietRecordForm.notes" type="textarea" :rows="3" placeholder="可选填写备注" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="saveDietRecord">保存记录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';
import { ChatDotRound, Document, Histogram, Plus, TrendCharts } from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useUserStore } from '../stores/user';
import dietRecordApi from '../api/dietRecord';

const userStore = useUserStore();
const dialogVisible = ref(false);
const dietRecordFormRef = ref(null);
const dietRecords = ref([]);
const dateRange = ref([]);
const loading = ref(false);
const chartCanvas = ref(null);
const chartInstance = ref(null);
const dietSuggestions = ref([]);
const suggestionLoading = ref(false);
const activeChart = ref('calorie');
const analysisSummary = ref({
  totalCalories: 0,
  totalProtein: 0,
  totalCarbs: 0,
  totalFat: 0,
  dailyStats: {}
});

const mealTypeMap = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐'
};

const dietRecordForm = reactive({
  date: '',
  mealType: '',
  foodName: '',
  ingredients: [],
  notes: ''
});

const numberValidator = (message) => ({
  validator: (rule, value, callback) => {
    if (value === '' || value === null || value === undefined) {
      callback(new Error(message));
      return;
    }
    if (Number.isNaN(Number(value))) {
      callback(new Error('请输入有效数字'));
      return;
    }
    callback();
  },
  trigger: 'blur'
});

const rules = {
  date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  mealType: [{ required: true, message: '请选择餐次', trigger: 'change' }],
  foodName: [{ required: true, message: '请输入菜品名称', trigger: 'blur' }]
};

const goalSummary = computed(() => {
  const targetCalories = Number(userStore.dietGoal?.targetCalories || 0);
  const dailyStats = analysisSummary.value.dailyStats || {};
  const dayCount = Object.keys(dailyStats).length || 0;
  const averageCalories = dayCount ? Math.round((analysisSummary.value.totalCalories || 0) / dayCount) : 0;

  let completionRate = 0;
  if (targetCalories > 0 && averageCalories > 0) {
    const diff = Math.abs(averageCalories - targetCalories);
    completionRate = Math.max(0, Math.round((1 - diff / targetCalories) * 100));
  }

  let statusText = '待记录';
  if (completionRate >= 90) {
    statusText = '控制优秀';
  } else if (completionRate >= 75) {
    statusText = '基本达标';
  } else if (averageCalories > 0) {
    statusText = averageCalories > targetCalories ? '摄入偏高' : '摄入偏低';
  }

  return {
    targetCalories,
    averageCalories,
    completionRate,
    statusText
  };
});

const formatDate = (value) => {
  if (!value) return '';
  if (typeof value === 'string') return value.slice(0, 10);
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ''
    : `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};

const toNumber = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
};

const formatMetric = (value, digits = 2) => {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return 0;
  }
  return Number(number.toFixed(digits));
};

const mealTagType = (mealType) => {
  if (mealType === 'breakfast') return 'success';
  if (mealType === 'lunch') return 'warning';
  if (mealType === 'dinner') return 'danger';
  return 'info';
};

const getSuggestionType = (suggestion) => {
  if (suggestion.includes('偏高') || suggestion.includes('不足')) return 'warning';
  if (suggestion.includes('合理') || suggestion.includes('良好')) return 'success';
  return 'info';
};

const normalizeDetailItem = (detail) => ({
  foodName: detail?.foodName || '--',
  quantityText: `${detail?.quantity ?? detail?.amount ?? 1}${detail?.unit || '份'}`,
  calories: formatMetric(detail?.calories, 2),
  protein: formatMetric(detail?.protein, 2),
  carbs: formatMetric(detail?.carbs, 2),
  fat: formatMetric(detail?.fat, 2)
});

const resolveMealName = (record, details) => {
  if (record?.mealName && String(record.mealName).trim()) {
    return String(record.mealName).trim();
  }

  const noteText = String(record?.notes || '').trim();
  const recipePrefix = '由食谱推荐一键加入：';
  if (noteText.startsWith(recipePrefix)) {
    return noteText.slice(recipePrefix.length).trim() || '推荐食谱';
  }

  if (details.length === 1) {
    return details[0].foodName || '--';
  }

  if (details.length > 1) {
    return `${details[0].foodName}等${details.length}项食物`;
  }

  return record?.foodName || '--';
};

const normalizeDietRecords = (records) =>
  (Array.isArray(records) ? records : []).map((record) => {
    const details = Array.isArray(record.details) ? record.details.map(normalizeDetailItem) : [];
    const firstDetail = details[0] || null;

    return {
      id: record.id,
      mealType: record.mealType || '',
      date: formatDate(record.recordDate || record.date),
      mealTypeLabel: mealTypeMap[record.mealType] || record.mealType || '--',
      mealName: resolveMealName(record, details),
      detailCount: details.length || 1,
      calories: formatMetric(record.totalCalories ?? firstDetail?.calories ?? 0, 2),
      protein: formatMetric(record.totalProtein ?? firstDetail?.protein ?? 0, 2),
      carbs: formatMetric(record.totalCarbs ?? firstDetail?.carbs ?? 0, 2),
      fat: formatMetric(record.totalFat ?? firstDetail?.fat ?? 0, 2),
      notes: record.notes || '',
      details
    };
  });

const renderCharts = () => {
  if (!chartCanvas.value) return;

  if (!chartInstance.value) {
    chartInstance.value = echarts.init(chartCanvas.value);
  }

  const dailyStats = analysisSummary.value.dailyStats || {};
  const dates = Object.keys(dailyStats).sort();

  if (activeChart.value === 'nutrition') {
    chartInstance.value.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [
        {
          type: 'pie',
          radius: ['42%', '72%'],
          center: ['50%', '45%'],
          label: { formatter: '{b}\n{d}%' },
          data: [
            { value: analysisSummary.value.totalProtein || 0, name: '蛋白质' },
            { value: analysisSummary.value.totalCarbs || 0, name: '碳水' },
            { value: analysisSummary.value.totalFat || 0, name: '脂肪' }
          ]
        }
      ]
    });
    return;
  }

  chartInstance.value.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 24, bottom: 36 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#cdddcf' } }
    },
    yAxis: {
      type: 'value',
      name: 'kcal',
      splitLine: { lineStyle: { color: '#eef3ee' } }
    },
    series: [
      {
        data: dates.map((date) => dailyStats[date]?.calories || 0),
        type: 'line',
        smooth: true,
        showSymbol: true,
        symbolSize: 8,
        lineStyle: { color: '#67a97a', width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(103, 169, 122, 0.24)' },
              { offset: 1, color: 'rgba(103, 169, 122, 0.03)' }
            ]
          }
        }
      }
    ]
  });
};

const openAddDialog = () => {
  dialogVisible.value = true;
  if (!dietRecordForm.date) {
    dietRecordForm.date = formatDate(new Date());
  }
};

const createIngredientRow = () => ({
  foodName: '',
  amount: 100,
  unit: 'g',
  calories: '',
  protein: '',
  carbs: '',
  fat: ''
});

const addIngredient = () => {
  dietRecordForm.ingredients.push(createIngredientRow());
};

const removeIngredient = (index) => {
  if (dietRecordForm.ingredients.length === 1) return;
  dietRecordForm.ingredients.splice(index, 1);
};

const resetForm = () => {
  dietRecordFormRef.value?.resetFields();
  dietRecordForm.date = formatDate(new Date());
  dietRecordForm.ingredients = [createIngredientRow()];
};

const saveDietRecord = async () => {
  if (!dietRecordFormRef.value) return;

  await dietRecordFormRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      const validIngredients = dietRecordForm.ingredients
        .filter((item) => String(item.foodName || '').trim())
        .map((item) => ({
          foodName: item.foodName,
          amount: toNumber(item.amount),
          unit: item.unit || 'g',
          calories: toNumber(item.calories),
          protein: toNumber(item.protein),
          carbs: toNumber(item.carbs),
          fat: toNumber(item.fat)
        }));

      if (!validIngredients.length) {
        ElMessage.warning('请至少添加一项食材明细');
        loading.value = false;
        return;
      }

      const response = await dietRecordApi.submitRecord({
        date: dietRecordForm.date,
        mealType: dietRecordForm.mealType,
        notes: dietRecordForm.notes,
        details: validIngredients
      });

      if (response.code === 200) {
        ElMessage.success('保存成功');
        dialogVisible.value = false;
        resetForm();
        await loadDietRecords();
        await loadDietAnalysis();
        await loadDietSuggestions();
        return;
      }

      ElMessage.error(response.message || '保存失败');
    } catch (error) {
      ElMessage.error(error.message || '保存失败，请检查网络连接');
    } finally {
      loading.value = false;
    }
  });
};

const deleteDietRecord = async (row) => {
  if (!row?.id) return;

  try {
    await ElMessageBox.confirm(
      `确定删除 ${row.date} ${row.mealTypeLabel} 的这条饮食记录吗？`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    loading.value = true;
    const response = await dietRecordApi.deleteRecord(row.id);
    if (response.code === 200) {
      ElMessage.success('删除成功');
      await loadDietRecords();
      await loadDietAnalysis();
      await loadDietSuggestions();
      return;
    }

    ElMessage.error(response.message || '删除失败');
  } catch (error) {
    if (error === 'cancel' || error === 'close' || error?.message === 'cancel') {
      return;
    }
    ElMessage.error(error.message || '删除失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

const loadDietRecords = async () => {
  if (!userStore.userId) {
    ElMessage.error('用户未登录');
    return;
  }

  loading.value = true;
  try {
    const startDate = dateRange.value?.[0] || '';
    const endDate = dateRange.value?.[1] || '';
    const response = await dietRecordApi.getDietRecords(startDate, endDate);
    if (response.code === 200) {
      dietRecords.value = normalizeDietRecords(response.data);
    } else {
      ElMessage.error(response.message || '获取记录失败');
    }
  } catch (error) {
    ElMessage.error(error.message || '获取记录失败，请检查网络连接');
  } finally {
    loading.value = false;
  }
};

const loadDietAnalysis = async () => {
  const startDate = dateRange.value?.[0] || '';
  const endDate = dateRange.value?.[1] || '';
  if (!startDate || !endDate) return;

  try {
    const response = await dietRecordApi.getDietAnalysis(startDate, endDate);
    if (response.code === 200) {
      analysisSummary.value = response.data || {};
      await nextTick();
      renderCharts();
    }
  } catch (error) {
    console.error('获取饮食分析失败:', error);
  }
};

const loadDietSuggestions = async () => {
  suggestionLoading.value = true;
  try {
    const response = await dietRecordApi.getDietSuggestions();
    if (response.code === 200) {
      dietSuggestions.value = Array.isArray(response.data) ? response.data : [];
    } else {
      ElMessage.error(response.message || '获取建议失败');
    }
  } catch (error) {
    ElMessage.error(error.message || '获取建议失败，请检查网络连接');
  } finally {
    suggestionLoading.value = false;
  }
};

const handleDateChange = async () => {
  await loadDietRecords();
  await loadDietAnalysis();
};

watch(activeChart, async () => {
  await nextTick();
  renderCharts();
});

onMounted(async () => {
  const end = formatDate(new Date());
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - 6);
  dateRange.value = [formatDate(startDate), end];
  dietRecordForm.date = end;
  dietRecordForm.ingredients = [createIngredientRow()];

  await loadDietRecords();
  await loadDietAnalysis();
  await loadDietSuggestions();
});
</script>

<style scoped>
.diet-record-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 24px 28px;
  border: 1px solid #dfebdf;
  border-radius: 22px;
  background: linear-gradient(135deg, #f8fcf8 0%, #eef6ef 100%);
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #7b9280;
}

.page-hero h2 {
  margin: 0;
  color: #304136;
  font-size: 28px;
}

.page-hero p {
  margin: 8px 0 0;
  color: #708075;
}

.add-button {
  min-width: 116px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.summary-card {
  border-radius: 18px;
  border: 1px solid #e8efe7;
}

.summary-card span {
  display: block;
  margin-bottom: 10px;
  color: #7b8a7e;
}

.summary-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.summary-icon {
  font-size: 18px;
}

.summary-card strong {
  display: block;
  color: #2f4034;
  font-size: 24px;
}

.summary-card small {
  display: block;
  margin-top: 8px;
  color: #93a093;
}

.content-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.record-card,
.chart-card,
.suggestion-card {
  border-radius: 20px;
  border: 1px solid #e4ece4;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.section-head.compact {
  align-items: flex-start;
}

.section-head span {
  display: block;
  color: #334237;
  font-weight: 600;
}

.section-head p {
  margin: 6px 0 0;
  color: #7e8d82;
  font-size: 13px;
}

.filter-tools {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.section-title .el-icon {
  color: #6f8f72;
}

.record-table {
  margin-top: 4px;
}

.detail-panel {
  padding: 8px 12px 12px;
  background: #f8fbf8;
  border-radius: 14px;
}

.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  color: #5f7265;
}

.detail-head strong {
  color: #314037;
}

.detail-table {
  background: #fff;
}

.chart-canvas {
  width: 100%;
  height: 360px;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.ingredient-editor {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ingredient-row {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) 108px 82px repeat(4, minmax(0, 1fr)) 42px;
  gap: 8px;
  align-items: center;
}

.ingredient-name,
.ingredient-amount,
.ingredient-unit,
.ingredient-metric {
  width: 100%;
  min-width: 0;
}

.add-ingredient-btn {
  align-self: flex-start;
}

@media (max-width: 1120px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1100px) {
  .ingredient-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .page-hero,
  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }
  .filter-tools {
    width: 100%;
  }
}
</style>
