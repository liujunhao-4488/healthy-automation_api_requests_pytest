<template>
  <div class="knowledge-page">
    <section class="knowledge-shell">
      <section class="page-head">
        <div>
          <p class="page-eyebrow">HEALTH KNOWLEDGE</p>
          <h1>健康知识库</h1>
          <p class="page-desc">
            汇集饮食营养、慢病管理与科学科普内容，帮助你更快找到适合自己的健康建议。
          </p>
        </div>
        <div class="page-summary">
          <strong>{{ total }}</strong>
          <span>篇内容</span>
          <em>当前：{{ activeTabLabel }}</em>
        </div>
      </section>

      <div class="search-wrap">
        <el-input
          v-model="keyword"
          class="search-input"
          placeholder="搜索感兴趣的内容"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-button class="publish-btn" type="primary" @click="openPublishDialog">
          发布文章
        </el-button>
      </div>

      <div class="tabs-wrap" :class="{ expanded: showAllTags }">
        <button
          v-for="tab in displayTabs"
          :key="tab.value"
          type="button"
          class="tab-item"
          :class="{ active: activeTab === tab.value }"
          @click="changeTab(tab.value)"
        >
          {{ tab.label }}
        </button>
        <button
          v-if="tagTabs.length > 8"
          type="button"
          class="tab-item more-toggle"
          @click="toggleTagExpansion"
        >
          {{ showAllTags ? '收起' : '更多' }}
        </button>
      </div>

      <div
        ref="articleScrollRef"
        v-loading="loading"
        class="article-scroll"
        @scroll="handleArticleScroll"
      >
        <div class="article-list" :class="{ 'is-empty': !articleList.length }">
          <article
            v-for="article in articleList"
            :key="article.id"
            class="article-card"
            @click="viewDetails(article.id)"
          >
            <div class="article-cover" :class="article.coverShapeClass" :style="article.coverStyle">
              <span class="cover-category">{{ article.coverCategory }}</span>
              <div class="cover-copy">
                <strong>{{ article.coverHint }}</strong>
              </div>
            </div>

            <h3 class="article-title">{{ article.title }}</h3>

            <p class="article-content">{{ article.summaryText }}</p>

            <div class="article-footer">
              <div class="author-row">
                <div
                  class="author-avatar"
                  :class="{ 'has-image': Boolean(article.authorAvatar) }"
                  :style="article.authorAvatar ? undefined : { background: article.avatarColor }"
                >
                  <img
                    v-if="article.authorAvatar"
                    :src="article.authorAvatar"
                    :alt="`${article.authorName}头像`"
                    class="author-avatar-image"
                  />
                  <template v-else>
                    {{ article.avatarText }}
                  </template>
                </div>
                <div class="author-info">
                  <strong>{{ article.authorName }}</strong>
                  <p class="author-meta">{{ article.publishText }}</p>
                </div>
              </div>

              <div class="metric-row">
                <button
                  type="button"
                  class="metric-item action-btn"
                  :class="{ liked: article.liked }"
                  :disabled="article.actionLoading"
                  @click.stop="toggleLike(article)"
                >
                  <span class="metric-icon">♥</span>
                  <span>{{ article.likeCount }}</span>
                </button>
                <button
                  type="button"
                  class="metric-item action-btn comment-btn"
                  @click.stop="openComments(article)"
                >
                  <span class="metric-icon">💬</span>
                  <span>{{ article.commentCount }}</span>
                </button>
                <button
                  type="button"
                  class="metric-item action-btn"
                  :class="{ collected: article.collected }"
                  :disabled="article.actionLoading"
                  @click.stop="toggleCollect(article)"
                >
                  <span class="metric-icon">★</span>
                  <span>{{ article.collectCount }}</span>
                </button>
              </div>
            </div>
          </article>

          <el-empty
            v-if="!loading && !articleList.length"
            description="当前没有匹配的文章内容"
            class="empty-block"
          />
        </div>

        <div v-if="loadingMore" class="load-more-state">正在加载更多内容...</div>
        <div v-else-if="articleList.length && !hasMore" class="load-more-state done">已经到底了</div>
      </div>
    </section>

    <el-dialog
      v-model="publishDialogVisible"
      title="发布文章"
      width="720px"
      destroy-on-close
    >
      <el-form ref="publishFormRef" :model="publishForm" :rules="publishRules" label-position="top">
        <el-form-item label="文章标题" prop="title">
          <el-input v-model="publishForm.title" maxlength="100" placeholder="请输入文章标题" />
        </el-form-item>

        <div class="publish-grid">
          <el-form-item label="文章分类" prop="category">
            <el-select
              v-model="publishForm.category"
              placeholder="请选择或输入分类"
              filterable
              allow-create
              default-first-option
            >
              <el-option
                v-for="option in categoryOptions"
                :key="option"
                :label="option"
                :value="option"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="适用目标">
            <el-select v-model="publishForm.goalType" clearable placeholder="可选">
              <el-option label="减肥减脂" value="减肥减脂" />
              <el-option label="增肌塑形" value="增肌塑形" />
              <el-option label="维持体重" value="维持体重" />
              <el-option label="健康增重" value="健康增重" />
              <el-option label="控糖饮食" value="控糖饮食" />
              <el-option label="控脂降脂" value="控脂降脂" />
              <el-option label="控压低盐" value="控压低盐" />
              <el-option label="孕妇营养" value="孕妇营养" />
              <el-option label="儿童成长" value="儿童成长" />
              <el-option label="老年养生" value="老年养生" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="文章标签">
          <el-input
            v-model="publishForm.tags"
            placeholder="多个标签用中文逗号分隔，例如：控糖饮食，营养科普"
          />
        </el-form-item>

        <el-form-item label="正文内容" prop="content">
          <el-input
            v-model="publishForm.content"
            type="textarea"
            :rows="10"
            maxlength="5000"
            show-word-limit
            placeholder="请输入正文内容"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="publishDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="publishing" @click="submitPublish">
            立即发布
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import healthKnowledgeApi from '../api/healthKnowledge';

const router = useRouter();
const articleList = ref([]);
const articleScrollRef = ref(null);
const tagTabs = ref([]);
const activeTab = ref('recommend');
const keyword = ref('');
const currentPage = ref(1);
const pageSize = 8;
const total = ref(0);
const loading = ref(false);
const loadingMore = ref(false);
const publishDialogVisible = ref(false);
const publishing = ref(false);
const publishFormRef = ref(null);
const showAllTags = ref(false);
const publishForm = ref({
  title: '',
  category: '',
  goalType: '',
  tags: '',
  content: ''
});

const publishRules = {
  title: [{ required: true, message: '请输入文章标题', trigger: 'blur' }],
  category: [{ required: true, message: '请选择文章分类', trigger: 'change' }],
  content: [{ required: true, message: '请输入正文内容', trigger: 'blur' }]
};

const categoryOptions = [
  '健康知识',
  '饮食指南',
  '控糖饮食',
  '低脂饮食',
  '减脂建议',
  '营养科普'
];

const coverPalette = [
  'linear-gradient(135deg, #f6d4ba 0%, #f3b487 100%)',
  'linear-gradient(135deg, #bfdcc3 0%, #7db78a 100%)',
  'linear-gradient(135deg, #cfd8f3 0%, #8da6de 100%)',
  'linear-gradient(135deg, #efd2e7 0%, #c38db7 100%)',
  'linear-gradient(135deg, #f1dfb8 0%, #d8b06f 100%)',
  'linear-gradient(135deg, #c7e2dd 0%, #7db6ae 100%)'
];
const coverShapeClasses = ['shape-sunrise', 'shape-wave', 'shape-orbit', 'shape-blob'];
const baseTabLabelMap = {
  recommend: '推荐',
  latest: '最新',
  hot: '热门'
};

const buildCoverSnippet = (text, maxLength = 34) => {
  const normalized = String(text || '')
    .replace(/\s+/g, ' ')
    .trim();

  if (!normalized) {
    return '科学饮食 · 健康生活';
  }

  return normalized.length > maxLength ? `${normalized.slice(0, maxLength)}...` : normalized;
};

const buildCoverHint = (article) => {
  if (article.goalType) return article.goalType;
  if (article.category) return article.category;
  return '健康知识';
};

const buildCoverCategory = (article) => article.category || '健康知识';

const summarizeContent = (content, summary) => {
  const source = summary && String(summary).trim() ? String(summary).trim() : String(content || '').trim();
  if (!source) return '暂无摘要';
  const normalized = source.replace(/\s+/g, ' ');
  return normalized.length > 88 ? `${normalized.slice(0, 88)}...` : normalized;
};

const formatDateTimeValue = (value) => {
  if (!value) return '';
  const text = String(value).trim();
  if (!text) return '';
  const normalized = text.includes('T') ? text.replace('T', ' ') : text;
  const date = new Date(normalized.replace(/-/g, '/'));
  if (Number.isNaN(date.getTime())) {
    return normalized;
  }
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

const buildPublishText = (article) => {
  const publishTime =
    article.createTime || article.create_time || article.publishDate || article.publish_date || article.updateTime || article.update_time;
  const formatted = formatDateTimeValue(publishTime);
  return formatted ? `发布于 ${formatted}` : '健康知识专栏';
};

const buildAuthorName = (article) => article.author || '健康营养师';
const buildAvatarText = (name) => String(name || '营').trim().charAt(0) || '营';

const displayTabs = computed(() => [
  { label: '推荐', value: 'recommend' },
  { label: '最新', value: 'latest' },
  { label: '热门', value: 'hot' },
  ...(showAllTags.value ? tagTabs.value : tagTabs.value.slice(0, 8)).map((tag) => ({
    label: tag,
    value: `tag:${tag}`
  }))
]);

const activeTabLabel = computed(() => {
  if (activeTab.value.startsWith('tag:')) {
    return activeTab.value.slice(4) || '标签';
  }
  return baseTabLabelMap[activeTab.value] || '推荐';
});

const hasMore = computed(() => articleList.value.length < total.value);

const normalizeArticle = (article, index) => {
  const authorName = buildAuthorName(article);
  return {
    ...article,
    authorName,
    avatarText: buildAvatarText(authorName),
    avatarColor: coverPalette[(index + 2) % coverPalette.length],
    authorAvatar: article.authorAvatar || '',
    summaryText: summarizeContent(article.content, article.summary),
    publishText: buildPublishText(article),
    coverStyle: {
      background: coverPalette[index % coverPalette.length]
    },
    coverShapeClass: coverShapeClasses[index % coverShapeClasses.length],
    coverHint: buildCoverHint(article),
    coverCategory: buildCoverCategory(article),
    likeCount: Number(article.likeCount || 0),
    commentCount: Number(article.commentCount || 0),
    collectCount: Number(article.collectCount || 0),
    readCount: Number(article.readCount || 0),
    liked: Boolean(article.liked),
    collected: Boolean(article.collected),
    actionLoading: false
  };
};

const normalizeListResponse = (data, append = false) => {
  const list = Array.isArray(data) ? data : data?.list || [];
  const startIndex = append ? articleList.value.length : 0;
  const normalizedList = list.map((item, index) => normalizeArticle(item, startIndex + index));
  articleList.value = append ? [...articleList.value, ...normalizedList] : normalizedList;
  total.value = Array.isArray(data) ? list.length : Number(data?.total || list.length);
  if (!Array.isArray(data) && Array.isArray(data?.tags) && data.tags.length) {
    tagTabs.value = data.tags;
  }
};

const buildListParams = (page = currentPage.value) => {
  const params = {
    page,
    pageSize
  };

  if (keyword.value.trim()) {
    params.keyword = keyword.value.trim();
  }

  if (activeTab.value === 'latest' || activeTab.value === 'recommend') {
    params.sort = 'latest';
  } else if (activeTab.value === 'hot') {
    params.sort = 'hot';
  } else if (activeTab.value.startsWith('tag:')) {
    params.tag = activeTab.value.slice(4);
    params.sort = 'latest';
  }

  return params;
};

const loadTagTabs = async () => {
  try {
    const response = await healthKnowledgeApi.getArticleTags();
    if (response.code === 200 && Array.isArray(response.data)) {
      tagTabs.value = response.data;
    }
  } catch (error) {
    console.error('获取文章标签失败:', error);
  }
};

const loadKnowledgeList = async ({ page = currentPage.value, append = false } = {}) => {
  if (append) {
    if (loading.value || loadingMore.value || !hasMore.value) {
      return false;
    }
    loadingMore.value = true;
  } else {
    loading.value = true;
  }

  try {
    const hasKeyword = Boolean(keyword.value.trim());
    const response =
      !hasKeyword && activeTab.value === 'recommend'
        ? await healthKnowledgeApi.getRecommendedArticles({ page, pageSize })
        : await healthKnowledgeApi.getKnowledgeList(buildListParams(page));

    if (response.code === 200) {
      normalizeListResponse(response.data, append);
      return true;
    }

    ElMessage.error(response.message || '获取文章列表失败');
    return false;
  } catch (error) {
    ElMessage.error(error.message || '获取文章列表失败，请检查网络连接');
    return false;
  } finally {
    if (append) {
      loadingMore.value = false;
    } else {
      loading.value = false;
    }
  }
};

const scrollArticleListToTop = async () => {
  await nextTick();
  articleScrollRef.value?.scrollTo({ top: 0, behavior: 'auto' });
};

const reloadKnowledgeList = async () => {
  currentPage.value = 1;
  await scrollArticleListToTop();
  await loadKnowledgeList({ page: 1 });
};

const loadMoreKnowledgeList = async () => {
  if (!hasMore.value || loading.value || loadingMore.value) {
    return;
  }

  const nextPage = currentPage.value + 1;
  const loaded = await loadKnowledgeList({ page: nextPage, append: true });
  if (loaded) {
    currentPage.value = nextPage;
  }
};

const handleArticleScroll = () => {
  const container = articleScrollRef.value;
  if (!container || loading.value || loadingMore.value || !hasMore.value) {
    return;
  }

  const remainingDistance = container.scrollHeight - container.scrollTop - container.clientHeight;
  if (remainingDistance <= 120) {
    loadMoreKnowledgeList();
  }
};

const changeTab = async (tab) => {
  activeTab.value = tab;
  await reloadKnowledgeList();
};

const toggleTagExpansion = () => {
  showAllTags.value = !showAllTags.value;
};

const handleSearch = async () => {
  await reloadKnowledgeList();
};

const viewDetails = (id) => {
  router.push(`/dashboard/health-knowledge/${id}`);
};

const openComments = (article) => {
  router.push({
    path: `/dashboard/health-knowledge/${article.id}`,
    query: { focus: 'comments' }
  });
};

const toggleLike = async (article) => {
  article.actionLoading = true;
  try {
    const response = article.liked
      ? await healthKnowledgeApi.cancelLikeArticle(article.id)
      : await healthKnowledgeApi.likeArticle(article.id);

    if (response.code === 200) {
      article.liked = Boolean(response.data?.liked);
      article.likeCount = Number(response.data?.likeCount || 0);
      return;
    }

    ElMessage.error(response.message || '操作失败');
  } catch (error) {
    ElMessage.error(error.message || '操作失败');
  } finally {
    article.actionLoading = false;
  }
};

const toggleCollect = async (article) => {
  article.actionLoading = true;
  try {
    const response = article.collected
      ? await healthKnowledgeApi.cancelCollectArticle(article.id)
      : await healthKnowledgeApi.collectArticle(article.id);

    if (response.code === 200) {
      article.collected = Boolean(response.data?.collected);
      article.collectCount = Number(response.data?.collectCount || 0);
      return;
    }

    ElMessage.error(response.message || '操作失败');
  } catch (error) {
    ElMessage.error(error.message || '操作失败');
  } finally {
    article.actionLoading = false;
  }
};

const resetPublishForm = () => {
  publishForm.value = {
    title: '',
    category: '',
    goalType: '',
    tags: '',
    content: ''
  };
  publishFormRef.value?.clearValidate?.();
};

const openPublishDialog = () => {
  resetPublishForm();
  publishDialogVisible.value = true;
};

const submitPublish = async () => {
  if (!publishFormRef.value) return;

  try {
    await publishFormRef.value.validate();
  } catch {
    return;
  }

  publishing.value = true;
  try {
    const payload = {
      title: publishForm.value.title.trim(),
      category: publishForm.value.category,
      goalType: publishForm.value.goalType || null,
      tags: publishForm.value.tags.trim(),
      content: publishForm.value.content.trim()
    };

    const response = await healthKnowledgeApi.publishArticle(payload);
    if (response.code === 200) {
      ElMessage.success('文章发布成功');
      publishDialogVisible.value = false;
      activeTab.value = 'latest';
      keyword.value = '';
      await reloadKnowledgeList();
      if (response.data?.id) {
        router.push(`/dashboard/health-knowledge/${response.data.id}`);
      }
      return;
    }

    ElMessage.error(response.message || '文章发布失败');
  } catch (error) {
    ElMessage.error(error.message || '文章发布失败');
  } finally {
    publishing.value = false;
  }
};

onMounted(async () => {
  await loadTagTabs();
  await loadKnowledgeList({ page: 1 });
});
</script>

<style scoped>
.knowledge-page {
  height: calc(100vh - 118px);
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

.knowledge-shell {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #fffdfa 0%, #ffffff 18%, #fcfaf7 100%);
  border-radius: 30px;
  border: 1px solid #ece4da;
  overflow: hidden;
  box-shadow: 0 20px 42px rgba(72, 55, 38, 0.06);
}

.page-head {
  display: none;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  padding: 28px 28px 20px;
  background:
    radial-gradient(circle at right top, rgba(210, 195, 172, 0.18), transparent 38%),
    linear-gradient(135deg, #fff9f1 0%, #f8f2ea 100%);
  border-bottom: 1px solid #efe6dc;
}

.page-eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #9a7e64;
}

.page-head h1 {
  margin: 0;
  color: #3f3126;
  font-size: 32px;
  font-weight: 700;
}

.page-desc {
  max-width: 660px;
  margin: 12px 0 0;
  color: #75685d;
  font-size: 15px;
  line-height: 1.85;
}

.page-summary {
  min-width: 156px;
  padding: 18px 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(225, 214, 201, 0.9);
  box-shadow: 0 10px 24px rgba(95, 72, 49, 0.06);
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.page-summary strong {
  color: #4b3a2d;
  font-size: 30px;
  line-height: 1;
}

.page-summary span,
.page-summary em {
  color: #877667;
  font-style: normal;
  font-size: 13px;
}

.search-wrap {
  position: relative;
  z-index: 3;
  flex-shrink: 0;
  padding: 18px 22px 16px;
  border-bottom: 1px solid #f0e9e0;
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 252, 248, 0.96);
}

.search-input {
  flex: 1;
}

.search-input :deep(.el-input__wrapper) {
  min-height: 48px;
  border-radius: 999px;
  background: #f8f4ef;
  box-shadow: none;
}

.publish-btn {
  min-width: 112px;
  height: 46px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #8b7355 0%, #6f8f72 100%);
}

.tabs-wrap {
  position: relative;
  z-index: 3;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 22px 0;
  border-bottom: 1px solid #f0e9e0;
  overflow-x: auto;
  scrollbar-width: none;
  background: rgba(255, 252, 248, 0.98);
}

.tabs-wrap::-webkit-scrollbar {
  display: none;
}

.tabs-wrap.expanded {
  flex-wrap: wrap;
  align-items: flex-start;
  row-gap: 8px;
  overflow-x: visible;
  padding-bottom: 12px;
}

.tab-item {
  position: relative;
  padding: 10px 16px;
  margin-bottom: 12px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  color: #6f6256;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.18s ease;
}

.tab-item:hover {
  color: #5d4c3d;
  background: #faf4ec;
}

.tab-item.active {
  color: #5f4c3b;
  font-weight: 600;
  background: #f5ede3;
  border-color: #eadbc9;
  box-shadow: inset 0 0 0 1px rgba(244, 233, 220, 0.55);
}

.tab-item.active::after {
  display: none;
}

.more-toggle {
  color: #877667;
}

.tabs-wrap.expanded .tab-item {
  margin-bottom: 0;
}

.article-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 18px 16px 20px;
  overscroll-behavior: contain;
}

.article-list {
  min-height: 260px;
  column-count: 3;
  column-gap: 14px;
}

.article-list.is-empty {
  display: grid;
  column-count: auto;
}

.article-card {
  display: inline-block;
  width: 100%;
  margin: 0 0 14px;
  break-inside: avoid;
  -webkit-column-break-inside: avoid;
  padding: 0;
  border-radius: 18px;
  border: 1px solid #efe7de;
  background: #ffffff;
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.article-card:hover {
  transform: translateY(-3px);
  border-color: #dccab5;
  box-shadow: 0 16px 30px rgba(70, 50, 33, 0.08);
}

.article-cover {
  position: relative;
  min-height: 164px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
}

.article-cover::before,
.article-cover::after {
  content: '';
  position: absolute;
  pointer-events: none;
}

.article-cover.shape-sunrise::before {
  width: 122px;
  height: 122px;
  right: -26px;
  top: -34px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.24);
}

.article-cover.shape-sunrise::after {
  width: 76px;
  height: 76px;
  left: -18px;
  bottom: -20px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
}

.article-cover.shape-wave::before {
  width: 145px;
  height: 72px;
  left: -16px;
  bottom: 18px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  transform: rotate(-12deg);
}

.article-cover.shape-wave::after {
  width: 118px;
  height: 118px;
  right: -34px;
  top: -24px;
  border-radius: 38px;
  background: rgba(255, 255, 255, 0.12);
  transform: rotate(22deg);
}

.article-cover.shape-orbit::before {
  width: 138px;
  height: 138px;
  right: -34px;
  top: -28px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.24);
}

.article-cover.shape-orbit::after {
  width: 96px;
  height: 96px;
  left: -24px;
  bottom: -18px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.article-cover.shape-blob::before {
  width: 132px;
  height: 132px;
  right: -26px;
  top: -34px;
  border-radius: 44% 56% 52% 48%;
  background: rgba(255, 255, 255, 0.18);
}

.article-cover.shape-blob::after {
  width: 92px;
  height: 92px;
  left: -20px;
  bottom: -18px;
  border-radius: 60% 40% 58% 42%;
  background: rgba(255, 255, 255, 0.12);
}

.cover-category,
.cover-copy {
  position: relative;
  z-index: 1;
}

.cover-category {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
  color: #fffdf9;
  font-size: 12px;
  font-weight: 600;
  backdrop-filter: blur(8px);
}

.cover-copy {
  color: #fffdf9;
}

.cover-copy strong {
  display: block;
  font-size: 18px;
  line-height: 1.35;
}

.article-title {
  margin: 12px 14px 8px;
  color: #2f241b;
  font-size: 16px;
  line-height: 1.45;
  font-weight: 700;
}

.article-content {
  margin: 0 14px;
  color: #65584c;
  font-size: 13px;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin: 12px 14px 12px;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  min-width: 0;
  flex: 1;
}

.author-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.22);
}

.author-avatar.has-image {
  background: #f3eee7;
}

.author-avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.author-info strong {
  color: #3f3126;
  font-size: 13px;
  font-weight: 600;
}

.author-meta {
  margin: 0;
  color: #8a7a6a;
  font-size: 11px;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: nowrap;
  margin: 0;
  flex-shrink: 0;
}

.metric-item {
  color: #8b7d70;
  font-size: 12px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  transition: color 0.18s ease, transform 0.18s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.metric-icon {
  font-size: 13px;
  line-height: 1;
}

.action-btn.liked {
  color: #d46c6c;
}

.comment-btn {
  color: #74695f;
}

.action-btn.collected {
  color: #c89b42;
}

.metric-read {
  margin-left: auto;
  color: #9a8b7c;
}

.load-more-state {
  padding: 14px 0 4px;
  text-align: center;
  color: #8f8172;
  font-size: 13px;
}

.load-more-state.done {
  color: #a09284;
}

.empty-block {
  grid-column: 1 / -1;
  padding: 48px 0 40px;
}

.publish-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 1360px) {
  .article-list {
    column-count: 2;
  }
}

@media (max-width: 900px) {
  .article-list {
    column-count: 1;
  }
}

@media (max-width: 768px) {
  .knowledge-page {
    height: calc(100vh - 96px);
    min-height: 0;
    padding: 4px 0;
  }

  .page-head,
  .search-wrap {
    padding-left: 16px;
    padding-right: 16px;
  }

  .page-head {
    flex-direction: column;
    gap: 14px;
    padding-top: 22px;
    padding-bottom: 18px;
  }

  .page-head h1 {
    font-size: 26px;
  }

  .page-summary {
    width: 100%;
    align-items: flex-start;
  }

  .article-scroll {
    padding: 14px 10px 16px;
  }

  .article-list {
    column-count: 1;
    gap: 0;
  }

  .article-cover {
    min-height: 146px;
    padding: 10px;
  }

  .cover-copy strong {
    font-size: 16px;
  }

  .cover-copy p {
    font-size: 12px;
  }

  .article-card {
    margin-bottom: 12px;
    border-radius: 16px;
  }

  .article-title {
    font-size: 15px;
    margin: 10px 12px 8px;
  }


  .article-content {
    margin-left: 12px;
    margin-right: 12px;
  }

  .article-footer {
    margin: 10px 12px 12px;
    align-items: flex-start;
    flex-direction: column;
  }

  .author-row,
  .metric-row {
    margin-left: 0;
    margin-right: 0;
  }

  .metric-row {
    width: 100%;
    justify-content: flex-start;
  }


  .search-wrap {
    flex-direction: column;
    align-items: stretch;
  }

  .publish-btn {
    width: 100%;
  }

  .tabs-wrap {
    gap: 10px;
    padding-left: 16px;
    padding-right: 16px;
  }

  .publish-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
