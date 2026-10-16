<template>
  <div class="forum-page">
    <section class="forum-shell">
      <section class="page-head">
        <div>
          <p class="page-eyebrow">HEALTH COMMUNITY</p>
          <h1>健康交流论坛</h1>
          <p class="page-desc">
            分享饮食心得、交流健康经验，和大家一起科学管理饮食与生活。
          </p>
        </div>
        <div class="page-stats">
          <div class="stat-item">
            <strong>{{ total }}</strong>
            <span>主题</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <strong>{{ activeTabLabel }}</strong>
            <span>当前板块</span>
          </div>
        </div>
      </section>

      <div class="toolbar">
        <el-input
          v-model="keyword"
          class="search-input"
          placeholder="搜索帖子标题或内容"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-button class="post-btn" type="primary" @click="openPublishDialog">
          <el-icon><EditPen /></el-icon>
          <span>发布新帖</span>
        </el-button>
      </div>

      <div class="tabs-wrap">
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
          @click="openTagDialog"
        >
          更多板块
        </button>
      </div>

      <el-dialog
        v-model="tagDialogVisible"
        title="选择帖子板块"
        width="680px"
        class="tag-dialog"
      >
        <el-input
          v-model="tagSearchKeyword"
          class="tag-search"
          placeholder="搜索板块"
          clearable
        />
        <div v-if="filteredDialogTags.length" class="dialog-tag-list">
          <button
            v-for="tag in filteredDialogTags"
            :key="tag"
            type="button"
            class="dialog-tag-item"
            :class="{ active: activeTab === `tag:${tag}` }"
            @click="selectDialogTag(tag)"
          >
            {{ tag }}
          </button>
        </div>
        <el-empty v-else description="没有匹配的板块" />
      </el-dialog>

      <div
        ref="articleScrollRef"
        v-loading="loading"
        class="thread-scroll"
        @scroll="handleArticleScroll"
      >
        <div class="thread-list" :class="{ 'is-empty': !articleList.length }">
          <article
            v-for="article in articleList"
            :key="article.id"
            class="thread-card"
            @click="viewDetails(article.id)"
          >
            <div class="thread-main">
              <div class="thread-tag-row">
                <span class="thread-category">{{ article.coverCategory || '交流讨论' }}</span>
                <span v-if="article.recommendReason" class="thread-recommend">精选</span>
              </div>

              <h3 class="thread-title">{{ article.title }}</h3>

              <p class="thread-summary">{{ article.summaryText }}</p>

              <div class="thread-meta">
                <div class="author-row">
                  <div
                    class="author-avatar"
                    :class="{ 'has-image': Boolean(article.authorAvatar) }"
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
                    <span class="author-time">{{ article.publishText }}</span>
                  </div>
                </div>

                <div class="thread-stats">
                  <button
                    type="button"
                    class="stat-action"
                    :class="{ liked: article.liked }"
                    :disabled="article.actionLoading"
                    @click.stop="toggleLike(article)"
                  >
                    <span>♥</span>
                    <span>{{ article.likeCount }}</span>
                  </button>
                  <button
                    type="button"
                    class="stat-action"
                    @click.stop="openComments(article)"
                  >
                    <span>💬</span>
                    <span>{{ article.commentCount }}</span>
                  </button>
                  <button
                    type="button"
                    class="stat-action"
                    :class="{ collected: article.collected }"
                    :disabled="article.actionLoading"
                    @click.stop="toggleCollect(article)"
                  >
                    <span>★</span>
                    <span>{{ article.collectCount }}</span>
                  </button>
                </div>
              </div>
            </div>
          </article>

          <el-empty
            v-if="!loading && !articleList.length"
            description="当前板块还没有帖子，来发第一帖吧"
            class="empty-block"
          />
        </div>

        <div v-if="loadingMore" class="load-more-state">正在加载更多...</div>
        <div v-else-if="articleList.length && !hasMore" class="load-more-state done">已经到底了</div>
      </div>
    </section>

    <el-dialog
      v-model="publishDialogVisible"
      width="680px"
      destroy-on-close
      class="publish-dialog"
    >
      <template #header>
        <div class="dialog-header">
          <h3>发布新帖</h3>
          <p>分享你的饮食心得，和大家一起交流健康经验</p>
        </div>
      </template>

      <el-form ref="publishFormRef" :model="publishForm" :rules="publishRules" label-position="top" class="publish-form">
        <el-form-item prop="title">
          <el-input
            v-model="publishForm.title"
            class="title-input"
            maxlength="100"
            placeholder="请输入帖子标题..."
          />
        </el-form-item>

        <el-form-item label="选择板块" prop="category" class="form-label-block">
          <div class="option-chips">
            <button
              v-for="option in categoryOptions"
              :key="option"
              type="button"
              class="chip"
              :class="{ active: publishForm.category === option }"
              @click="publishForm.category = option"
            >
              {{ option }}
            </button>
          </div>
        </el-form-item>

        <el-form-item label="适用目标（用于个性化推荐）" class="form-label-block">
          <div class="option-chips">
            <button
              v-for="goal in goalOptions"
              :key="goal"
              type="button"
              class="chip"
              :class="{ active: publishForm.goalType === goal }"
              @click="publishForm.goalType = publishForm.goalType === goal ? '' : goal"
            >
              {{ goal }}
            </button>
          </div>
        </el-form-item>

        <el-form-item label="帖子标签" class="form-label-block">
          <el-input
            v-model="publishForm.tags"
            placeholder="多个标签用中文逗号分隔，例如：减脂，饮食分享"
          />
        </el-form-item>

        <el-form-item label="帖子内容" prop="content" class="form-label-block">
          <el-input
            v-model="publishForm.content"
            type="textarea"
            :rows="8"
            maxlength="5000"
            show-word-limit
            placeholder="分享你的饮食心得、提问或者经验吧..."
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="publishDialogVisible = false">取消</el-button>
          <el-button type="primary" class="publish-submit" :loading="publishing" @click="submitPublish">
            发布帖子
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
import { EditPen } from '@element-plus/icons-vue';
import healthKnowledgeApi from '../api/healthKnowledge';

const router = useRouter();
const articleList = ref([]);
const readHistory = ref([]);
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
const tagDialogVisible = ref(false);
const tagSearchKeyword = ref('');
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

const goalOptions = [
  '减肥减脂',
  '增肌塑形',
  '维持体重',
  '健康增重',
  '控糖饮食',
  '控脂降脂',
  '控压低盐',
  '孕妇营养',
  '儿童成长',
  '老年养生'
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

const normalizeTagTabs = (tags) => {
  const result = [];
  const seen = new Set();
  (Array.isArray(tags) ? tags : []).forEach((tag) => {
    String(tag || '')
      .replace(/[\[\]"]/g, '')
      .split(/[,，、;；/|\s]+/)
      .map((item) => item.trim())
      .filter(Boolean)
      .forEach((item) => {
        if (!seen.has(item)) {
          seen.add(item);
          result.push(item);
        }
      });
  });
  return result;
};

const currentSelectedTag = computed(() => (activeTab.value.startsWith('tag:') ? activeTab.value.slice(4) : ''));

const visibleTopTags = computed(() => {
  const topTags = tagTabs.value.slice(0, 8);
  const selectedTag = currentSelectedTag.value;
  if (selectedTag && !topTags.includes(selectedTag)) {
    return [selectedTag, ...topTags.slice(0, 7)];
  }
  return topTags;
});

const filteredDialogTags = computed(() => {
  const keywordText = tagSearchKeyword.value.trim().toLowerCase();
  if (!keywordText) {
    return tagTabs.value;
  }
  return tagTabs.value.filter((tag) => tag.toLowerCase().includes(keywordText));
});

const displayTabs = computed(() => [
  { label: '推荐', value: 'recommend' },
  { label: '最新', value: 'latest' },
  { label: '热门', value: 'hot' },
  ...visibleTopTags.value.map((tag) => ({
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
    recommendReason: article.recommendReason || '',
    liked: Boolean(article.liked),
    collected: Boolean(article.collected),
    actionLoading: false
  };
};

const normalizeReadHistoryItem = (article) => ({
  id: article.id,
  title: article.title || '未命名文章',
  finished: Boolean(article.finished),
  scrollPercent: Number(article.scrollPercent || 0)
});

const normalizeListResponse = (data, append = false) => {
  const list = Array.isArray(data) ? data : data?.list || [];
  const startIndex = append ? articleList.value.length : 0;
  const normalizedList = list.map((item, index) => normalizeArticle(item, startIndex + index));
  articleList.value = append ? [...articleList.value, ...normalizedList] : normalizedList;
  total.value = Array.isArray(data) ? list.length : Number(data?.total || list.length);
  if (!Array.isArray(data) && Array.isArray(data?.tags) && data.tags.length) {
    tagTabs.value = normalizeTagTabs(data.tags);
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
      tagTabs.value = normalizeTagTabs(response.data);
    }
  } catch (error) {
    console.error('获取文章标签失败:', error);
  }
};

const loadReadHistory = async () => {
  try {
    const response = await healthKnowledgeApi.getReadHistory(4);
    if (response.code === 200 && Array.isArray(response.data)) {
      readHistory.value = response.data.map(normalizeReadHistoryItem);
    }
  } catch (error) {
    console.error('获取阅读历史失败:', error);
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

const openTagDialog = () => {
  tagSearchKeyword.value = '';
  tagDialogVisible.value = true;
};

const selectDialogTag = async (tag) => {
  tagDialogVisible.value = false;
  tagSearchKeyword.value = '';
  await changeTab(`tag:${tag}`);
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
  await loadReadHistory();
  await loadTagTabs();
  await loadKnowledgeList({ page: 1 });
});
</script>

<style scoped>
.forum-page {
  height: calc(100vh - 118px);
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

.forum-shell {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 16px;
  border: 1px solid #e8ede9;
  overflow: hidden;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  padding: 24px 28px 18px;
  border-bottom: 1px solid #f0f4f1;
}

.page-eyebrow {
  margin: 0 0 8px;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #7ba088;
  font-weight: 500;
}

.page-head h1 {
  margin: 0;
  color: #2d3a30;
  font-size: 24px;
  font-weight: 600;
}

.page-desc {
  max-width: 520px;
  margin: 8px 0 0;
  color: #6b7c70;
  font-size: 14px;
  line-height: 1.7;
}

.page-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 18px;
  background: #f7faf8;
  border-radius: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-item strong {
  color: #2d3a30;
  font-size: 20px;
  font-weight: 600;
  line-height: 1;
}

.stat-item span {
  color: #8a988d;
  font-size: 12px;
}

.stat-divider {
  width: 1px;
  height: 28px;
  background: #e0e8e2;
}

.toolbar {
  flex-shrink: 0;
  padding: 16px 28px;
  border-bottom: 1px solid #f0f4f1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  flex: 1;
  max-width: 420px;
}

.search-input :deep(.el-input__wrapper) {
  height: 40px;
  border-radius: 8px;
  background: #f7faf8;
  box-shadow: none;
}

.post-btn {
  height: 40px;
  padding: 0 20px;
  border-radius: 8px;
  background: #5a8a68;
  border: none;
}

.tabs-wrap {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 28px 12px;
  border-bottom: 1px solid #f0f4f1;
  overflow-x: auto;
  scrollbar-width: none;
}

.tabs-wrap::-webkit-scrollbar {
  display: none;
}

.tab-item {
  padding: 7px 14px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #5f6f63;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.tab-item:hover {
  color: #3d4a3e;
  background: #f0f5f1;
}

.tab-item.active {
  color: #fff;
  font-weight: 500;
  background: #5a8a68;
}

.more-toggle {
  color: #8a988d;
}

.tag-search {
  margin-bottom: 16px;
}

.dialog-tag-list {
  max-height: 360px;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 4px 2px;
}

.dialog-tag-item {
  padding: 7px 14px;
  border-radius: 8px;
  border: 1px solid #d8e5db;
  background: #fafdfb;
  color: #4f7d5c;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.dialog-tag-item:hover,
.dialog-tag-item.active {
  color: #fff;
  border-color: #5a8a68;
  background: #5a8a68;
}

.thread-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px 20px;
  overscroll-behavior: contain;
}

.thread-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.thread-list.is-empty {
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.thread-card {
  padding: 18px 20px;
  border-radius: 12px;
  border: 1px solid #e8ede9;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.thread-card:hover {
  border-color: #c5d8cb;
  box-shadow: 0 4px 16px rgba(90, 138, 104, 0.06);
}

.thread-main {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.thread-tag-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.thread-category {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 6px;
  background: #eef5f0;
  color: #5a8a68;
  font-size: 12px;
  font-weight: 500;
}

.thread-recommend {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 6px;
  background: #fdf3e7;
  color: #c89b42;
  font-size: 11px;
  font-weight: 500;
}

.thread-title {
  margin: 0;
  color: #2d3a30;
  font-size: 16px;
  line-height: 1.4;
  font-weight: 600;
}

.thread-summary {
  margin: 0;
  color: #6b7c70;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.thread-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 4px;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.author-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #d8e5db;
  color: #5a8a68;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
  overflow: hidden;
}

.author-avatar.has-image {
  background: #f0f5f1;
}

.author-avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.author-info strong {
  color: #3d4a3e;
  font-size: 13px;
  font-weight: 500;
}

.author-time {
  color: #9aa89e;
  font-size: 12px;
}

.thread-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.stat-action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: transparent;
  padding: 0;
  color: #8a988d;
  font-size: 12px;
  cursor: pointer;
  transition: color 0.15s ease;
}

.stat-action:hover {
  color: #5a8a68;
}

.stat-action.liked {
  color: #d46c6c;
}

.stat-action.collected {
  color: #c89b42;
}

.load-more-state {
  padding: 16px 0 4px;
  text-align: center;
  color: #9aa89e;
  font-size: 13px;
}

.load-more-state.done {
  color: #b0bcb4;
}

.empty-block {
  padding: 48px 0 40px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.publish-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}

.publish-dialog :deep(.el-dialog__body) {
  padding: 20px 24px 8px;
}

.dialog-header {
  padding: 24px 24px 0;
}

.dialog-header h3 {
  margin: 0;
  color: #2d3a30;
  font-size: 20px;
  font-weight: 600;
}

.dialog-header p {
  margin: 6px 0 0;
  color: #8a988d;
  font-size: 13px;
}

.publish-form {
  margin-top: 16px;
}

.title-input :deep(.el-input__wrapper) {
  height: 48px;
  border-radius: 10px;
  background: #f7faf8;
  box-shadow: none;
  border: 1px solid #e8ede9;
}

.title-input :deep(.el-input__inner) {
  font-size: 16px;
  font-weight: 500;
}

.form-label-block :deep(.el-form-item__label) {
  padding-bottom: 8px;
  color: #5f6f63;
  font-size: 13px;
  font-weight: 500;
}

.option-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  padding: 6px 14px;
  border: 1px solid #d8e5db;
  border-radius: 8px;
  background: #fafdfb;
  color: #4f7d5c;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.chip:hover {
  border-color: #5a8a68;
  background: #f0f5f1;
}

.chip.active {
  background: #5a8a68;
  border-color: #5a8a68;
  color: #fff;
  font-weight: 500;
}

.publish-submit {
  background: #5a8a68;
  border: none;
  border-radius: 8px;
  padding: 0 24px;
}

@media (max-width: 768px) {
  .forum-page {
    height: calc(100vh - 96px);
    min-height: 0;
    padding: 4px 0;
  }

  .page-head {
    flex-direction: column;
    gap: 14px;
    padding: 20px 16px 16px;
  }

  .page-head h1 {
    font-size: 22px;
  }

  .page-stats {
    width: 100%;
    justify-content: center;
  }

  .toolbar {
    padding: 12px 16px;
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    max-width: 100%;
  }

  .tabs-wrap {
    padding: 0 16px 10px;
  }

  .thread-scroll {
    padding: 12px 12px 16px;
  }

  .thread-card {
    padding: 14px 16px;
  }

  .thread-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .publish-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
