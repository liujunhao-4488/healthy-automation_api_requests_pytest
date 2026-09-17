<template>
  <div class="admin-overview-page" v-loading="loading">
    <section class="hero-panel">
      <div class="hero-copy">
        <p class="hero-eyebrow">ADMIN OVERVIEW</p>
        <h1>管理员后台总览</h1>
        <p class="hero-date">{{ displayDate }}</p>
        <p class="hero-summary">{{ overview.meta.summaryText || '正在汇总最近 7 天的系统运行情况。' }}</p>
      </div>

      <div class="hero-actions">
        <el-button type="primary" @click="router.push('/admin/articles')">内容管理</el-button>
        <el-button plain @click="router.push('/admin/notifications')">通知中心</el-button>
      </div>
    </section>

    <section class="summary-grid">
      <article v-for="card in summaryCards" :key="card.key" class="summary-card">
        <div class="card-top">
          <span class="card-label">{{ card.label }}</span>
          <span class="card-chip" :class="card.trendClass">{{ card.deltaText }}</span>
        </div>
        <strong class="card-value">{{ card.value }}</strong>
        <p class="card-note">{{ card.note }}</p>
      </article>
    </section>

    <section class="content-grid">
      <el-card class="panel-card trend-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <div>
              <h3>最近 7 天用户活跃趋势</h3>
              <p>展示每日活跃用户与新增用户变化</p>
            </div>
          </div>
        </template>
        <div ref="userTrendRef" class="chart-panel"></div>
      </el-card>

      <el-card class="panel-card trend-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <div>
              <h3>最近 7 天饮食记录新增趋势</h3>
              <p>观察饮食记录变化，反映用户打卡活跃度</p>
            </div>
          </div>
        </template>
        <div ref="recordTrendRef" class="chart-panel"></div>
      </el-card>

      <el-card class="panel-card trend-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <div>
              <h3>最近 7 天文章阅读趋势</h3>
              <p>展示文章阅读次数与读完次数，体现内容消费行为</p>
            </div>
          </div>
        </template>
        <div ref="articleReadTrendRef" class="chart-panel"></div>
      </el-card>

      <el-card class="panel-card rank-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <div>
              <h3>热门食谱 Top 5</h3>
              <p>按收藏与浏览热度综合排序</p>
            </div>
            <el-button text @click="router.push('/admin/recipes')">查看全部</el-button>
          </div>
        </template>
        <div class="rank-list">
          <div v-for="(item, index) in overview.topRecipes" :key="item.id || index" class="rank-item">
            <div class="rank-index">{{ index + 1 }}</div>
            <div class="rank-main">
              <div class="rank-title-row">
                <strong>{{ item.name || '未命名食谱' }}</strong>
                <el-tag v-if="item.isCustom" size="small" type="success">自定义</el-tag>
              </div>
              <p>{{ item.goalType || '通用健康饮食' }}</p>
            </div>
            <div class="rank-metric">
              <strong>{{ item.heatScore || 0 }}</strong>
              <span>热度</span>
            </div>
          </div>
          <el-empty v-if="!overview.topRecipes.length" description="暂无热榜数据" :image-size="70" />
        </div>
      </el-card>

      <el-card class="panel-card rank-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <div>
              <h3>热门文章 Top 5</h3>
              <p>按真实阅读、读完与收藏等行为综合排序</p>
            </div>
            <el-button text @click="router.push('/admin/articles')">查看全部</el-button>
          </div>
        </template>
        <div class="rank-list">
          <div v-for="(item, index) in overview.topArticles" :key="item.id || index" class="rank-item">
            <div class="rank-index">{{ index + 1 }}</div>
            <div class="rank-main">
              <div class="rank-title-row">
                <strong>{{ item.title || '未命名文章' }}</strong>
                <el-tag size="small" effect="plain">{{ item.category || '健康科普' }}</el-tag>
              </div>
              <p>阅读 {{ item.readCount || 0 }} · 读完 {{ item.finishedReadCount || 0 }} · 收藏 {{ item.collectCount || 0 }}</p>
            </div>
            <div class="rank-metric">
              <strong>{{ item.heatScore || 0 }}</strong>
              <span>热度</span>
            </div>
          </div>
          <el-empty v-if="!overview.topArticles.length" description="暂无热榜数据" :image-size="70" />
        </div>
      </el-card>
    </section>

    <section class="task-section">
      <el-card class="panel-card task-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <div>
              <h3>待处理事项</h3>
              <p>快速查看管理员需要关注的内容与风险</p>
            </div>
          </div>
        </template>

        <div class="task-metrics">
          <article class="task-metric">
            <span>被禁用用户数</span>
            <strong>{{ overview.recentActivities.disabledUserCount || 0 }}</strong>
          </article>
          <article class="task-metric warning">
            <span>未读通知量</span>
            <strong>{{ overview.recentActivities.unreadNotificationCount || 0 }}</strong>
          </article>
          <article class="task-metric">
            <span>今日阅读人数</span>
            <strong>{{ overview.recentActivities.todayReadUserCount || 0 }}</strong>
          </article>
          <article class="task-metric warning">
            <span>今日读完次数</span>
            <strong>{{ overview.recentActivities.todayFinishedReadCount || 0 }}</strong>
          </article>
        </div>

        <div class="task-columns">
          <div class="task-column">
            <div class="task-column-head">
              <h4>最近新增文章</h4>
              <el-button text @click="router.push('/admin/articles')">前往文章库</el-button>
            </div>
            <div v-if="overview.recentActivities.recentArticles?.length" class="recent-list">
              <div v-for="item in overview.recentActivities.recentArticles" :key="item.id" class="recent-item">
                <div>
                  <strong>{{ item.title || '未命名文章' }}</strong>
                  <p>{{ item.category || '健康科普' }}</p>
                </div>
                <span>{{ formatDateTime(item.createTime) }}</span>
              </div>
            </div>
            <el-empty v-else description="暂无新增文章" :image-size="70" />
          </div>

          <div class="task-column">
            <div class="task-column-head">
              <h4>最近新增自定义食谱</h4>
              <el-button text @click="router.push('/admin/recipes')">前往食谱库</el-button>
            </div>
            <div v-if="overview.recentActivities.recentCustomRecipes?.length" class="recent-list">
              <div v-for="item in overview.recentActivities.recentCustomRecipes" :key="item.id" class="recent-item">
                <div>
                  <strong>{{ item.name || '未命名食谱' }}</strong>
                  <p>{{ item.goalType || '通用健康饮食' }}</p>
                </div>
                <span>{{ formatDateTime(item.createTime) }}</span>
              </div>
            </div>
            <el-empty v-else description="暂无新增自定义食谱" :image-size="70" />
          </div>
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus';
import adminApi from '../api/admin';

const router = useRouter();
const loading = ref(false);
const userTrendRef = ref(null);
const recordTrendRef = ref(null);
const articleReadTrendRef = ref(null);
let userTrendChart = null;
let recordTrendChart = null;
let articleReadTrendChart = null;

const overview = reactive({
  summary: {
    changes: {}
  },
  trends: {
    dates: [],
    activeUsers: [],
    newUsers: [],
    dietRecords: [],
    articleReads: [],
    finishedReads: []
  },
  topRecipes: [],
  topArticles: [],
  recentActivities: {
    disabledUserCount: 0,
    unreadNotificationCount: 0,
    todayReadUserCount: 0,
    todayFinishedReadCount: 0,
    recentArticles: [],
    recentCustomRecipes: []
  },
  meta: {}
});

const toNumber = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
};

const getChange = (key) => overview.summary?.changes?.[key] || {};

const buildTrendClass = (key) => {
  const trend = getChange(key).trend;
  if (trend === 'down') return 'is-down';
  if (trend === 'up') return 'is-up';
  return '';
};

const summaryCards = computed(() => [
  {
    key: 'userCount',
    label: '用户总数',
    value: toNumber(overview.summary.userCount),
    note: `系统当前累计用户规模 ${toNumber(overview.summary.userCount)} 人`,
    deltaText: getChange('userCount').deltaText || '+0',
    trendClass: buildTrendClass('userCount')
  },
  {
    key: 'todayActiveUserCount',
    label: '今日活跃用户',
    value: toNumber(overview.summary.todayActiveUserCount),
    note: '按今日有饮食记录的用户去重统计',
    deltaText: getChange('todayActiveUserCount').deltaText || '+0',
    trendClass: buildTrendClass('todayActiveUserCount')
  },
  {
    key: 'recipeCount',
    label: '食谱总数',
    value: toNumber(overview.summary.recipeCount),
    note: `其中自定义食谱 ${toNumber(overview.summary.customRecipeCount)} 个`,
    deltaText: `${toNumber(overview.summary.customRecipeCount)}`,
    trendClass: ''
  },
  {
    key: 'todayDietRecordCount',
    label: '今日新增饮食记录',
    value: toNumber(overview.summary.todayDietRecordCount),
    note: '按今日新增记录统计',
    deltaText: getChange('todayDietRecordCount').deltaText || '+0',
    trendClass: buildTrendClass('todayDietRecordCount')
  },
  {
    key: 'articleCount',
    label: '文章总数',
    value: toNumber(overview.summary.articleCount),
    note: `今日文章阅读 ${toNumber(overview.summary.todayArticleReadCount)} 次`,
    deltaText: getChange('todayArticleReadCount').deltaText || '+0',
    trendClass: buildTrendClass('todayArticleReadCount')
  },
  {
    key: 'todayNotificationCount',
    label: '今日通知发送数',
    value: toNumber(overview.summary.todayNotificationCount),
    note: `今日读完文章 ${toNumber(overview.summary.todayFinishedReadCount)} 次`,
    deltaText: getChange('todayNotificationCount').deltaText || '+0',
    trendClass: buildTrendClass('todayNotificationCount')
  }
]);

const displayDate = computed(() => {
  const raw = overview.meta.currentDate;
  if (!raw) return '';
  const date = new Date(`${raw}T00:00:00`);
  if (Number.isNaN(date.getTime())) return raw;
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  });
});

const formatDateTime = (value) => {
  if (!value) return '--';
  const text = String(value).trim();
  const normalized = text.includes('T') ? text.replace('T', ' ') : text;
  const date = new Date(normalized.replace(/-/g, '/'));
  if (Number.isNaN(date.getTime())) return text;
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

const ensureCharts = () => {
  if (userTrendRef.value && !userTrendChart) userTrendChart = echarts.init(userTrendRef.value);
  if (recordTrendRef.value && !recordTrendChart) recordTrendChart = echarts.init(recordTrendRef.value);
  if (articleReadTrendRef.value && !articleReadTrendChart) articleReadTrendChart = echarts.init(articleReadTrendRef.value);
};

const renderUserTrendChart = () => {
  if (!userTrendChart) return;
  userTrendChart.setOption({
    color: ['#2f6b52', '#c97b2c'],
    tooltip: { trigger: 'axis' },
    legend: { top: 0, textStyle: { color: '#54645a' } },
    grid: { left: 36, right: 18, top: 48, bottom: 24 },
    xAxis: {
      type: 'category',
      data: overview.trends.dates || [],
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#d8e1da' } }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#eef2ec' } }
    },
    series: [
      {
        name: '活跃用户',
        type: 'line',
        smooth: true,
        data: overview.trends.activeUsers || [],
        symbolSize: 8,
        lineStyle: { width: 3 },
        areaStyle: { color: 'rgba(47, 107, 82, 0.12)' }
      },
      {
        name: '新增用户',
        type: 'line',
        smooth: true,
        data: overview.trends.newUsers || [],
        symbolSize: 7,
        lineStyle: { width: 2 }
      }
    ]
  });
};

const renderRecordTrendChart = () => {
  if (!recordTrendChart) return;
  recordTrendChart.setOption({
    color: ['#6aa66a'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 18, top: 28, bottom: 24 },
    xAxis: {
      type: 'category',
      data: overview.trends.dates || [],
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#d8e1da' } }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#eef2ec' } }
    },
    series: [
      {
        name: '饮食记录',
        type: 'line',
        smooth: true,
        data: overview.trends.dietRecords || [],
        symbolSize: 8,
        lineStyle: { width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(106, 166, 106, 0.28)' },
              { offset: 1, color: 'rgba(106, 166, 106, 0.02)' }
            ]
          }
        }
      }
    ]
  });
};

const renderArticleReadTrendChart = () => {
  if (!articleReadTrendChart) return;
  articleReadTrendChart.setOption({
    color: ['#b97932', '#567c5c'],
    tooltip: { trigger: 'axis' },
    legend: { top: 0, textStyle: { color: '#54645a' } },
    grid: { left: 36, right: 18, top: 48, bottom: 24 },
    xAxis: {
      type: 'category',
      data: overview.trends.dates || [],
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#d8e1da' } }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#eef2ec' } }
    },
    series: [
      {
        name: '文章阅读',
        type: 'line',
        smooth: true,
        data: overview.trends.articleReads || [],
        symbolSize: 8,
        lineStyle: { width: 3 }
      },
      {
        name: '读完次数',
        type: 'line',
        smooth: true,
        data: overview.trends.finishedReads || [],
        symbolSize: 7,
        lineStyle: { width: 2 }
      }
    ]
  });
};

const renderCharts = async () => {
  await nextTick();
  ensureCharts();
  renderUserTrendChart();
  renderRecordTrendChart();
  renderArticleReadTrendChart();
};

const handleResize = () => {
  userTrendChart?.resize();
  recordTrendChart?.resize();
  articleReadTrendChart?.resize();
};

const loadOverview = async () => {
  loading.value = true;
  try {
    const response = await adminApi.getOverview();
    if (response.code !== 200) {
      throw new Error(response.message || '加载后台总览失败');
    }

    const data = response.data || {};
    overview.summary = { changes: {}, ...(data.summary || {}) };
    overview.trends = {
      dates: [],
      activeUsers: [],
      newUsers: [],
      dietRecords: [],
      articleReads: [],
      finishedReads: [],
      ...(data.trends || {})
    };
    overview.topRecipes = Array.isArray(data.topRecipes) ? data.topRecipes : [];
    overview.topArticles = Array.isArray(data.topArticles) ? data.topArticles : [];
    overview.recentActivities = {
      disabledUserCount: 0,
      unreadNotificationCount: 0,
      todayReadUserCount: 0,
      todayFinishedReadCount: 0,
      recentArticles: [],
      recentCustomRecipes: [],
      ...(data.recentActivities || {})
    };
    overview.meta = data.meta || {};
    await renderCharts();
  } catch (error) {
    ElMessage.error(error.message || '加载后台总览失败');
  } finally {
    loading.value = false;
  }
};

watch(
  () => [
    overview.trends.dates,
    overview.trends.activeUsers,
    overview.trends.newUsers,
    overview.trends.dietRecords,
    overview.trends.articleReads,
    overview.trends.finishedReads
  ],
  () => {
    renderCharts();
  },
  { deep: true }
);

onMounted(async () => {
  window.addEventListener('resize', handleResize);
  await loadOverview();
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  userTrendChart?.dispose();
  recordTrendChart?.dispose();
  articleReadTrendChart?.dispose();
  userTrendChart = null;
  recordTrendChart = null;
  articleReadTrendChart = null;
});
</script>

<style scoped>
.admin-overview-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  color: #243127;
}

.hero-panel {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 32px;
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(237, 198, 120, 0.2), transparent 28%),
    linear-gradient(135deg, #193d2d 0%, #2f6b52 45%, #93b071 100%);
  color: #f8fbf7;
  box-shadow: 0 20px 40px rgba(28, 60, 46, 0.18);
}

.hero-copy h1 {
  margin: 6px 0 10px;
  font-size: 34px;
  line-height: 1.2;
}

.hero-eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.18em;
  opacity: 0.72;
}

.hero-date {
  margin: 0 0 8px;
  font-size: 15px;
  opacity: 0.88;
}

.hero-summary {
  margin: 0;
  max-width: 680px;
  font-size: 15px;
  line-height: 1.7;
  opacity: 0.92;
}

.hero-actions {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.hero-actions :deep(.el-button) {
  border-radius: 999px;
  padding-inline: 18px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 16px;
}

.summary-card {
  padding: 20px 18px;
  border-radius: 22px;
  background: linear-gradient(180deg, #ffffff 0%, #f6f8f3 100%);
  border: 1px solid #e4ebdf;
  box-shadow: 0 12px 24px rgba(58, 76, 62, 0.08);
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.card-label {
  font-size: 13px;
  color: #5c6d62;
}

.card-chip {
  padding: 4px 10px;
  border-radius: 999px;
  background: #eef4eb;
  color: #45624e;
  font-size: 12px;
  line-height: 1;
}

.card-chip.is-up {
  background: rgba(76, 141, 91, 0.14);
  color: #2f6b3e;
}

.card-chip.is-down {
  background: rgba(191, 95, 67, 0.14);
  color: #ad5135;
}

.card-value {
  display: block;
  margin-bottom: 10px;
  font-size: 32px;
  line-height: 1.1;
  color: #243127;
}

.card-note {
  margin: 0;
  min-height: 42px;
  color: #6c7a70;
  font-size: 13px;
  line-height: 1.6;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.panel-card {
  border: none;
  border-radius: 26px;
  box-shadow: 0 14px 32px rgba(58, 76, 62, 0.08);
}

.panel-card :deep(.el-card__header) {
  padding: 22px 24px 12px;
  border-bottom: none;
}

.panel-card :deep(.el-card__body) {
  padding: 0 24px 24px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.panel-head h3 {
  margin: 0 0 6px;
  font-size: 20px;
}

.panel-head p {
  margin: 0;
  font-size: 13px;
  color: #708177;
}

.chart-panel {
  height: 320px;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.rank-item {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 14px 16px;
  border-radius: 18px;
  background: #f6f8f3;
}

.rank-index {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, #e9c97a 0%, #c97b2c 100%);
  color: #fff;
  font-size: 18px;
  font-weight: 700;
}

.rank-main {
  min-width: 0;
}

.rank-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.rank-title-row strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-main p {
  margin: 0;
  color: #6c7a70;
  font-size: 13px;
  line-height: 1.5;
}

.rank-metric {
  text-align: right;
}

.rank-metric strong {
  display: block;
  font-size: 24px;
}

.rank-metric span {
  font-size: 12px;
  color: #708177;
}

.task-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.task-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.task-metric {
  padding: 18px 20px;
  border-radius: 20px;
  background: #f4f8f0;
  border: 1px solid #e0ead9;
}

.task-metric.warning {
  background: #fff5ea;
  border-color: #f1ddc0;
}

.task-metric span {
  display: block;
  margin-bottom: 10px;
  color: #6c7a70;
  font-size: 13px;
}

.task-metric strong {
  font-size: 30px;
  color: #243127;
}

.task-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.task-column {
  padding: 18px;
  border-radius: 20px;
  background: #fafbf8;
  border: 1px solid #ecf0e8;
}

.task-column-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
}

.task-column-head h4 {
  margin: 0;
  font-size: 16px;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid #edf1eb;
}

.recent-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.recent-item strong {
  display: block;
  margin-bottom: 5px;
}

.recent-item p {
  margin: 0;
  color: #708177;
  font-size: 13px;
}

.recent-item span {
  flex-shrink: 0;
  font-size: 12px;
  color: #839287;
}

@media (max-width: 1440px) {
  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .hero-panel {
    flex-direction: column;
  }

  .content-grid,
  .task-columns {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .summary-grid,
  .task-metrics {
    grid-template-columns: 1fr;
  }

  .hero-panel {
    padding: 24px 20px;
  }

  .panel-card :deep(.el-card__header) {
    padding-inline: 18px;
  }

  .panel-card :deep(.el-card__body) {
    padding-inline: 18px;
  }

  .chart-panel {
    height: 280px;
  }

  .rank-item,
  .recent-item,
  .task-column-head,
  .panel-head {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .rank-metric {
    text-align: left;
  }
}
</style>
