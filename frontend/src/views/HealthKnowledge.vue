<template>
  <div class="knowledge-page">
    <section class="knowledge-shell">
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

      <div v-loading="loading" class="article-list">
        <article
          v-for="article in articleList"
          :key="article.id"
          class="article-card"
          @click="viewDetails(article.id)"
        >
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
            </div>
          </div>

          <h3 class="article-title">{{ article.title }}</h3>

          <div v-if="article.tags.length" class="article-tags">
            <span v-for="tag in article.tags" :key="tag" class="tag-chip">
              {{ tag }}
            </span>
          </div>

          <p class="article-content">{{ article.summaryText }}</p>

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
            <span class="metric-item">阅读 {{ article.readCount }}</span>
          </div>
        </article>

        <el-empty
          v-if="!loading && !articleList.length"
          description="当前没有匹配的文章内容"
          class="empty-block"
        />
      </div>

      <div v-if="total > pageSize" class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          layout="prev, pager, next"
          :total="total"
        />
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
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import healthKnowledgeApi from '../api/healthKnowledge';

const router = useRouter();
const articleList = ref([]);
const tagTabs = ref([]);
const activeTab = ref('recommend');
const keyword = ref('');
const currentPage = ref(1);
const pageSize = 8;
const total = ref(0);
const loading = ref(false);
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

const palette = ['#2f80ed', '#27ae60', '#f2994a', '#eb5757', '#56ccf2', '#6c5ce7', '#219653'];

const parseTags = (tags) => {
  if (!tags) return [];
  if (Array.isArray(tags)) return tags.filter(Boolean).map((item) => String(item).trim());

  return String(tags)
    .replace(/[\[\]"]/g, '')
    .split(/[，、/]/)
    .map((item) => item.trim())
    .filter(Boolean);
};

const summarizeContent = (content, summary) => {
  const source = summary && String(summary).trim() ? String(summary).trim() : String(content || '').trim();
  if (!source) return '暂无摘要';
  const normalized = source.replace(/\s+/g, ' ');
  return normalized.length > 88 ? `${normalized.slice(0, 88)}...` : normalized;
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

const normalizeArticle = (article, index) => {
  const authorName = buildAuthorName(article);
  return {
    ...article,
    authorName,
    avatarText: buildAvatarText(authorName),
    avatarColor: palette[index % palette.length],
    authorAvatar: article.authorAvatar || '',
    tags: parseTags(article.tags),
    summaryText: summarizeContent(article.content, article.summary),
    likeCount: Number(article.likeCount || 0),
    commentCount: Number(article.commentCount || 0),
    collectCount: Number(article.collectCount || 0),
    readCount: Number(article.readCount || 0),
    liked: Boolean(article.liked),
    collected: Boolean(article.collected),
    actionLoading: false
  };
};

const normalizeListResponse = (data) => {
  const list = Array.isArray(data) ? data : data?.list || [];
  articleList.value = list.map(normalizeArticle);
  total.value = Array.isArray(data) ? list.length : Number(data?.total || list.length);
  if (!Array.isArray(data) && Array.isArray(data?.tags) && data.tags.length) {
    tagTabs.value = data.tags;
  }
};

const buildListParams = () => {
  const params = {
    page: currentPage.value,
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

const loadKnowledgeList = async () => {
  loading.value = true;
  try {
    const hasKeyword = Boolean(keyword.value.trim());
    const response =
      !hasKeyword && activeTab.value === 'recommend'
        ? await healthKnowledgeApi.getRecommendedArticles(100)
        : await healthKnowledgeApi.getKnowledgeList(buildListParams());

    if (response.code === 200) {
      normalizeListResponse(response.data);
      return;
    }

    ElMessage.error(response.message || '获取文章列表失败');
  } catch (error) {
    ElMessage.error(error.message || '获取文章列表失败，请检查网络连接');
  } finally {
    loading.value = false;
  }
};

const changeTab = (tab) => {
  activeTab.value = tab;
  currentPage.value = 1;
  loadKnowledgeList();
};

const toggleTagExpansion = () => {
  showAllTags.value = !showAllTags.value;
};

const handleSearch = () => {
  currentPage.value = 1;
  loadKnowledgeList();
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
      currentPage.value = 1;
      keyword.value = '';
      await loadKnowledgeList();
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

watch(currentPage, () => {
  loadKnowledgeList();
});

onMounted(async () => {
  await loadTagTabs();
  await loadKnowledgeList();
});
</script>

<style scoped>
.knowledge-page {
  padding: 8px 0;
}

.knowledge-shell {
  background: #fff;
  border-radius: 24px;
  border: 1px solid #ebeff4;
  overflow: hidden;
  box-shadow: 0 12px 28px rgba(22, 45, 77, 0.05);
}

.search-wrap {
  padding: 16px 18px 14px;
  border-bottom: 1px solid #edf1f5;
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  flex: 1;
}

.search-input :deep(.el-input__wrapper) {
  min-height: 48px;
  border-radius: 999px;
  background: #f5f6f8;
  box-shadow: none;
}

.publish-btn {
  min-width: 112px;
  height: 46px;
  border-radius: 999px;
}

.tabs-wrap {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 18px;
  border-bottom: 1px solid #edf1f5;
  overflow-x: auto;
}

.tabs-wrap.expanded {
  flex-wrap: wrap;
  align-items: flex-start;
  row-gap: 0;
  overflow-x: visible;
  padding-top: 8px;
}

.tab-item {
  position: relative;
  padding: 16px 0 15px;
  border: none;
  background: transparent;
  color: #4f5d73;
  font-size: 17px;
  cursor: pointer;
  white-space: nowrap;
}

.tab-item.active {
  color: #2f80ed;
  font-weight: 600;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 3px;
  border-radius: 999px;
  background: #2f80ed;
}

.more-toggle {
  color: #7d8ca1;
}

.tabs-wrap.expanded .tab-item {
  padding-top: 10px;
}

.article-list {
  min-height: 260px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.article-card {
  padding: 20px;
  border-radius: 22px;
  border: 1px solid #eef2f7;
  background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.article-card:hover {
  transform: translateY(-2px);
  border-color: #d5e4f7;
  box-shadow: 0 14px 28px rgba(31, 53, 84, 0.08);
}

.author-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.author-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  flex-shrink: 0;
  overflow: hidden;
}

.author-avatar.has-image {
  background: #f1f5f9;
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
}

.author-info strong {
  color: #182538;
  font-size: 24px;
}

.article-title {
  margin: 16px 0 12px;
  color: #16263c;
  font-size: 21px;
  line-height: 1.45;
}

.article-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.tag-chip {
  padding: 7px 12px;
  border-radius: 10px;
  background: #edf5ff;
  color: #2f80ed;
  font-size: 14px;
}

.article-content {
  margin: 0;
  color: #4a586a;
  font-size: 17px;
  line-height: 1.8;
}

.metric-row {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid #eef2f7;
}

.metric-item {
  color: #7b8798;
  font-size: 15px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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
  font-size: 16px;
  line-height: 1;
}

.action-btn.liked {
  color: #eb5757;
}

.comment-btn {
  color: #6b7280;
}

.action-btn.collected {
  color: #f2b94b;
}

.pagination-wrap {
  padding: 0 18px 22px;
  display: flex;
  justify-content: center;
}

.empty-block {
  padding: 42px 0 36px;
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

@media (max-width: 768px) {
  .article-list {
    padding: 14px;
  }

  .article-card {
    padding: 16px;
  }

  .search-wrap {
    flex-direction: column;
    align-items: stretch;
  }

  .publish-btn {
    width: 100%;
  }

  .tabs-wrap {
    gap: 18px;
  }

  .author-info strong {
    font-size: 20px;
  }

  .article-title {
    font-size: 18px;
  }

  .publish-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
