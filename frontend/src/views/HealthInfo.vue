<template>
  <div class="health-overview">
    <section class="hero-card">
      <div>
        <p class="eyebrow">HEALTH PROFILE</p>
        <h2>健康信息档案</h2>
        <p class="hero-copy">
          集中查看基础体征、运动习惯和健康状态，趋势图支持按日与按周查看长期体重和 BMI 变化。
        </p>
      </div>
      <div class="hero-actions">
        <el-button class="edit-button" type="primary" @click="goToEdit">
          <el-icon><EditPen /></el-icon>
          <span>修改信息</span>
        </el-button>
      </div>
    </section>

    <el-row :gutter="20" class="summary-grid">
      <el-col :xs="24" :sm="8">
        <div class="summary-card accent-sand">
          <div class="summary-meta">
            <el-icon class="summary-icon"><User /></el-icon>
            <span>当前体重</span>
          </div>
          <strong>{{ displayValue(healthInfo.weight, 'kg') }}</strong>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8">
        <div class="summary-card accent-green">
          <div class="summary-meta">
            <el-icon class="summary-icon"><TrendCharts /></el-icon>
            <span>BMI 指数</span>
          </div>
          <strong>{{ displayValue(healthInfo.bmi) }}</strong>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8">
        <div class="summary-card accent-cream">
          <div class="summary-meta">
            <el-icon class="summary-icon"><Timer /></el-icon>
            <span>基础代谢</span>
          </div>
          <strong>{{ displayValue(healthInfo.bmr, 'kcal') }}</strong>
        </div>
      </el-col>
    </el-row>

    <el-card class="chart-card" shadow="never">
      <template #header>
        <div class="section-head">
          <div class="section-title">
            <el-icon><TrendCharts /></el-icon>
            <span>体重 / BMI 历史趋势</span>
            <small>累计 {{ healthHistory.length || 0 }} 条历史记录</small>
          </div>
          <el-radio-group v-model="trendView" size="small" class="trend-toggle">
            <el-radio-button label="daily">按日</el-radio-button>
            <el-radio-button label="weekly">按周</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="trendChartRef" class="trend-chart"></div>
    </el-card>

    <div class="info-grid">
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="section-title">
            <el-icon><Memo /></el-icon>
            <span>基础信息</span>
          </div>
        </template>
        <div class="info-list">
          <div class="info-item">
            <label>年龄</label>
            <span>{{ displayValue(healthInfo.age, '岁') }}</span>
          </div>
          <div class="info-item">
            <label>性别</label>
            <span>{{ displayValue(healthInfo.gender) }}</span>
          </div>
          <div class="info-item">
            <label>身高</label>
            <span>{{ displayValue(healthInfo.height, 'cm') }}</span>
          </div>
          <div class="info-item">
            <label>体重</label>
            <span>{{ displayValue(healthInfo.weight, 'kg') }}</span>
          </div>
          <div class="info-item">
            <label>血压</label>
            <span>{{ displayValue(healthInfo.bloodPressure) }}</span>
          </div>
          <div class="info-item">
            <label>血糖</label>
            <span>{{ displayValue(healthInfo.bloodSugar, 'mmol/L') }}</span>
          </div>
        </div>
      </el-card>

      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="section-title">
            <el-icon><DataAnalysis /></el-icon>
            <span>运动与习惯</span>
          </div>
        </template>
        <div class="info-list">
          <div class="info-item">
            <label>活动水平</label>
            <span>{{ activityLevelLabel }}</span>
          </div>
          <div class="info-item">
            <label>每日运动时长</label>
            <span>{{ displayValue(healthInfo.exerciseDuration, '分钟') }}</span>
          </div>
          <div class="info-item wide">
            <label>运动类型</label>
            <span>{{ exerciseTypesLabel }}</span>
          </div>
          <div class="info-item wide">
            <label>慢性疾病</label>
            <span>{{ displayValue(healthInfo.chronicDiseases) }}</span>
          </div>
        </div>
      </el-card>
    </div>

    <el-card v-if="healthAnalysis" class="analysis-card" shadow="never">
      <template #header>
        <div class="section-title">
          <el-icon><DataAnalysis /></el-icon>
          <span>系统分析</span>
        </div>
      </template>
      <div class="analysis-overview">
        <div class="analysis-badge">
          <span>综合状态</span>
          <strong>{{ healthAnalysis.overallLevel || '--' }}</strong>
        </div>
        <p>{{ healthAnalysis.summary || '暂无分析结果' }}</p>
      </div>
      <div v-if="healthAnalysis.tags?.length" class="analysis-tags">
        <el-tag
          v-for="tag in healthAnalysis.tags"
          :key="tag"
          effect="plain"
          round
          type="success"
        >
          {{ tag }}
        </el-tag>
      </div>
      <div class="analysis-grid">
        <div class="analysis-item">
          <label>BMI评价</label>
          <strong>{{ healthAnalysis.bmiCategory || '--' }}</strong>
          <p>{{ healthAnalysis.bmiAdvice || '--' }}</p>
        </div>
        <div class="analysis-item">
          <label>血压评价</label>
          <strong>{{ healthAnalysis.bloodPressureStatus || '--' }}</strong>
          <p>{{ healthAnalysis.bloodPressureAdvice || '--' }}</p>
        </div>
        <div class="analysis-item">
          <label>血糖评价</label>
          <strong>{{ healthAnalysis.bloodSugarStatus || '--' }}</strong>
          <p>{{ healthAnalysis.bloodSugarAdvice || '--' }}</p>
        </div>
        <div class="analysis-item">
          <label>运动评价</label>
          <strong>{{ healthAnalysis.activityStatus || '--' }}</strong>
          <p>{{ healthAnalysis.activityAdvice || '--' }}</p>
        </div>
      </div>
      <div v-if="healthAnalysis.goalInsight || healthAnalysis.recommendations?.length" class="analysis-recommendations">
        <h3>建议摘要</h3>
        <p v-if="healthAnalysis.goalInsight">{{ healthAnalysis.goalInsight }}</p>
        <ul v-if="healthAnalysis.recommendations?.length">
          <li v-for="item in healthAnalysis.recommendations" :key="item">{{ item }}</li>
        </ul>
      </div>
    </el-card>
  </div>
</template>
<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { DataAnalysis, EditPen, Memo, Timer, TrendCharts, User } from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import { useUserStore } from '../stores/user';
import healthInfoApi from '../api/healthInfo';

const router = useRouter();
const userStore = useUserStore();
const trendChartRef = ref(null);
const chartInstance = ref(null);
const healthHistory = ref([]);
const trendView = ref('daily');

const activityLevelMap = {
  sedentary: '久坐少动',
  lightly_active: '轻度活动',
  moderately_active: '中度活动',
  very_active: '高度活动',
  extra_active: '高强度活动'
};

const healthInfo = computed(() => userStore.healthInfo || {});
const healthAnalysis = computed(() => userStore.healthAnalysis || null);

const parseHistoryDate = (value) => {
  if (!value) {
    return null;
  }

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value;
  }

  if (Array.isArray(value)) {
    const [year, month, day, hour = 0, minute = 0, second = 0] = value;
    const parsed = new Date(year, (month || 1) - 1, day || 1, hour, minute, second);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  const parsed = new Date(typeof value === 'string' ? value.replace(/-/g, '/') : value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
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

const exerciseTypesLabel = computed(() => {
  if (!healthInfo.value.exerciseType) {
    return '--';
  }

  return healthInfo.value.exerciseType
    .split(',')
    .filter(Boolean)
    .join('、');
});

const activityLevelLabel = computed(() => activityLevelMap[healthInfo.value.activityLevel] || '--');

const normalizedHistory = computed(() =>
  [...healthHistory.value]
    .map((item) => {
      const parsedDate = parseHistoryDate(item.createTime || item.recordDate);
      return {
        ...item,
        parsedDate,
        weight: Number(item.weight ?? 0),
        bmi: Number(item.bmi ?? 0)
      };
    })
    .filter((item) => item.parsedDate)
    .sort((a, b) => a.parsedDate - b.parsedDate)
);

const formatDailyAxis = (date) =>
  date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });

const getWeekKey = (date) => {
  const current = new Date(date);
  current.setHours(0, 0, 0, 0);
  const day = current.getDay() || 7;
  current.setDate(current.getDate() + 4 - day);
  const yearStart = new Date(current.getFullYear(), 0, 1);
  const weekNo = Math.ceil((((current - yearStart) / 86400000) + 1) / 7);
  return `${current.getFullYear()}-W${String(weekNo).padStart(2, '0')}`;
};

const chartSource = computed(() => {
  if (trendView.value === 'daily') {
    return normalizedHistory.value.map((item) => ({
      label: formatDailyAxis(item.parsedDate),
      weight: Number(item.weight.toFixed(1)),
      bmi: Number(item.bmi.toFixed(1))
    }));
  }

  const grouped = normalizedHistory.value.reduce((result, item) => {
    const key = getWeekKey(item.parsedDate);
    if (!result[key]) {
      result[key] = {
        label: key,
        weightTotal: 0,
        bmiTotal: 0,
        count: 0
      };
    }

    result[key].weightTotal += item.weight;
    result[key].bmiTotal += item.bmi;
    result[key].count += 1;
    return result;
  }, {});

  return Object.values(grouped).map((item) => ({
    label: item.label,
    weight: Number((item.weightTotal / item.count).toFixed(1)),
    bmi: Number((item.bmiTotal / item.count).toFixed(1))
  }));
});

const goToEdit = () => {
  router.push('/dashboard/health-info/edit');
};

const renderTrendChart = async () => {
  await nextTick();

  if (!trendChartRef.value) {
    return;
  }

  if (!chartInstance.value) {
    chartInstance.value = echarts.init(trendChartRef.value);
  }

  const chart = chartInstance.value;
  const source = chartSource.value;

  if (!source.length) {
    chart.clear();
    chart.setOption({
      title: {
        text: '暂无历史记录',
        left: 'center',
        top: 'middle',
        textStyle: {
          color: '#8b8175',
          fontSize: 14,
          fontWeight: 'normal'
        }
      }
    });
    return;
  }

  chart.clear();
  chart.setOption({
    color: ['#8b7355', '#6f8f72'],
    tooltip: {
      show: true,
      trigger: 'item',
      triggerOn: 'mousemove|click',
      renderMode: 'html',
      appendToBody: true,
      confine: false,
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e7ddd0',
      borderWidth: 1,
      extraCssText:
        'z-index:9999;box-shadow:0 8px 24px rgba(60,45,34,0.12);border-radius:12px;padding:10px 12px;',
      textStyle: {
        color: '#4c4034'
      },
      formatter: (param) => {
        const unit = param.seriesName === '体重趋势' ? ' kg' : '';
        const value = typeof param.value === 'number' ? param.value.toFixed(1) : param.value;
        return `
          <div style="font-weight:600;margin-bottom:6px;">${param.name}</div>
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${param.color};"></span>
            <span>${param.seriesName}: ${value}${unit}</span>
          </div>
        `;
      }
    },
    grid: { left: 48, right: 40, top: 36, bottom: 48 },
    legend: {
      data: ['体重趋势', 'BMI'],
      top: 8,
      textStyle: {
        color: '#6f6255'
      }
    },
    xAxis: {
      type: 'category',
      axisLine: { lineStyle: { color: '#d8d0c6' } },
      axisLabel: {
        color: '#7f7060',
        formatter: (value) => value.replace(' ', '\n')
      },
      data: source.map((item) => item.label)
    },
    yAxis: [
      {
        type: 'value',
        name: '体重',
        splitLine: { lineStyle: { color: '#f1ece5' } }
      },
      {
        type: 'value',
        name: 'BMI',
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '体重趋势',
        type: 'line',
        smooth: true,
        showSymbol: true,
        showAllSymbol: true,
        symbol: 'circle',
        symbolSize: 10,
        emphasis: {
          focus: 'series',
          scale: true,
          itemStyle: {
            borderWidth: 3,
            borderColor: '#fff'
          }
        },
        label: { show: false },
        data: source.map((item) => item.weight)
      },
      {
        name: 'BMI',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        showSymbol: true,
        showAllSymbol: true,
        symbol: 'circle',
        symbolSize: 10,
        emphasis: {
          focus: 'series',
          scale: true,
          itemStyle: {
            borderWidth: 3,
            borderColor: '#fff'
          }
        },
        label: { show: false },
        data: source.map((item) => item.bmi)
      }
    ]
  }, true);
};

const loadHealthInfo = async () => {
  try {
    const response = await healthInfoApi.getHealthInfo();
    if (response.code === 200 && response.data) {
      userStore.setHealthInfo(response.data);
      userStore.setHealthAnalysis(response.analysis || null);
    }
  } catch (error) {
    console.error('获取健康信息失败:', error);
  }
};

const loadHealthHistory = async () => {
  try {
    const response = await healthInfoApi.getHealthHistory();
    if (response.code === 200 && Array.isArray(response.data)) {
      healthHistory.value = response.data;
    } else {
      healthHistory.value = [];
    }
  } catch (error) {
    console.error('获取健康历史失败:', error);
    healthHistory.value = [];
  } finally {
    renderTrendChart();
  }
};

watch([healthHistory, trendView], () => renderTrendChart(), { deep: true });

onMounted(async () => {
  await loadHealthInfo();
  await loadHealthHistory();
  window.addEventListener('resize', renderTrendChart);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderTrendChart);
  if (chartInstance.value) {
    chartInstance.value.dispose();
    chartInstance.value = null;
  }
});
</script>

<style scoped>
.health-overview {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  padding: 28px 30px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, rgba(212, 198, 175, 0.35), transparent 42%),
    linear-gradient(135deg, #fffaf4 0%, #f5efe5 100%);
  border: 1px solid #eee4d7;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #8b7355;
}

.hero-card h2 {
  margin: 0;
  font-family: 'Noto Serif SC', serif;
  font-size: 30px;
  color: #43372b;
}

.hero-copy {
  max-width: 560px;
  margin: 12px 0 0;
  color: #736557;
  line-height: 1.7;
}

.edit-button {
  min-width: 124px;
  height: 44px;
  border: none;
  background: linear-gradient(135deg, #8b7355 0%, #6f8f72 100%);
}

.summary-grid {
  margin: 0;
}

.summary-card {
  min-height: 126px;
  padding: 22px;
  border-radius: 22px;
  color: #3f342a;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 12px 28px rgba(67, 55, 43, 0.06);
}

.summary-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.summary-card span {
  color: #7f7060;
}

.summary-icon {
  font-size: 18px;
}

.summary-card strong {
  font-size: 30px;
  font-weight: 600;
}

.accent-sand {
  background: linear-gradient(180deg, #fff8ef 0%, #f2e4d3 100%);
}

.accent-green {
  background: linear-gradient(180deg, #f4fbf5 0%, #deecdf 100%);
}

.accent-cream {
  background: linear-gradient(180deg, #fffdf8 0%, #efe8db 100%);
}

.chart-card,
.info-card,
.analysis-card {
  border: 1px solid #eee6da;
  border-radius: 22px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  font-weight: 600;
  color: #43372b;
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.section-title .el-icon {
  color: #8b7355;
}

.section-head small {
  display: block;
  margin-top: 4px;
  font-weight: 400;
  color: #8b8175;
}

.trend-toggle {
  flex-shrink: 0;
}

.trend-chart {
  width: 100%;
  height: 320px;
}

.analysis-overview {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, #f7fbf8 0%, #eef7ef 100%);
}

.analysis-badge {
  min-width: 132px;
  padding: 16px 18px;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 8px 18px rgba(80, 104, 84, 0.06);
}

.analysis-badge span {
  display: block;
  margin-bottom: 8px;
  color: #8b8175;
  font-size: 13px;
}

.analysis-badge strong {
  color: #43372b;
  font-size: 24px;
}

.analysis-overview p {
  margin: 0;
  color: #6f675f;
  line-height: 1.8;
}

.analysis-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.analysis-item {
  padding: 16px 18px;
  border-radius: 16px;
  background: #faf7f2;
}

.analysis-item label {
  display: block;
  margin-bottom: 8px;
  color: #8b8175;
  font-size: 13px;
}

.analysis-item strong {
  display: block;
  margin-bottom: 10px;
  color: #43372b;
  font-size: 18px;
}

.analysis-item p {
  margin: 0;
  color: #6f675f;
  line-height: 1.8;
}

.analysis-recommendations {
  margin-top: 18px;
  padding: 18px;
  border-radius: 18px;
  background: #fffaf4;
}

.analysis-recommendations h3 {
  margin: 0 0 10px;
  color: #43372b;
  font-size: 18px;
}

.analysis-recommendations p {
  margin: 0 0 10px;
  color: #6f675f;
  line-height: 1.8;
}

.analysis-recommendations ul {
  margin: 0;
  padding-left: 18px;
  color: #5f695f;
  line-height: 1.9;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 22px;
}

.info-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.info-item {
  padding: 16px 18px;
  border-radius: 16px;
  background: #faf7f2;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item.wide {
  grid-column: 1 / -1;
}

.info-item label {
  font-size: 13px;
  color: #8b8175;
}

.info-item span {
  color: #43372b;
  line-height: 1.7;
  word-break: break-word;
}

@media (max-width: 900px) {
  .info-grid {
    grid-template-columns: 1fr;
  }

  .analysis-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-card,
  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .info-list {
    grid-template-columns: 1fr;
  }

  .analysis-overview {
    flex-direction: column;
  }
}
</style>

