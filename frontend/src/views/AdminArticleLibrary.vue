<template>
  <div class="admin-page">
    <div class="page-top">
      <div>
        <h2>健康文章管理</h2>
        <p>查看当前文章库内容，并支持删除不合适的文章。</p>
      </div>
    </div>

    <el-card class="toolbar-card">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索标题或关键词" clearable @keyup.enter="loadArticles" />
        <el-button @click="loadArticles">查询</el-button>
      </div>
    </el-card>

    <el-card class="table-card">
      <el-table :data="articles" v-loading="loading">
        <el-table-column prop="title" label="标题" min-width="220" />
        <el-table-column prop="category" label="分类" width="140" />
        <el-table-column prop="author" label="作者" width="140" />
        <el-table-column prop="publishDateText" label="发布时间" width="180" />
        <el-table-column prop="readCount" label="阅读量" width="100" />
        <el-table-column prop="collectCount" label="收藏量" width="100" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button text @click="viewArticle(row)">查看</el-button>
            <el-button text type="danger" @click="deleteArticle(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="total > pageSize" class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          layout="prev, pager, next"
          :total="total"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" title="文章详情" width="920px">
      <div v-if="currentArticle" class="admin-article-detail-view">
        <div class="admin-author-row">
          <div
            class="admin-author-avatar"
            :class="{ 'has-image': Boolean(currentArticle.authorAvatar) }"
            :style="currentArticle.authorAvatar ? undefined : { background: getAuthorAvatarColor(currentArticle.id) }"
          >
            <img
              v-if="currentArticle.authorAvatar"
              :src="currentArticle.authorAvatar"
              :alt="`${currentArticle.author || '作者'}头像`"
              class="admin-author-avatar-image"
            >
            <template v-else>
              {{ getAuthorAvatarText(currentArticle.author) }}
            </template>
          </div>
          <div class="admin-author-meta">
            <strong>{{ currentArticle.author || '未知作者' }}</strong>
          </div>
        </div>

        <div class="admin-article-meta">
          <el-tag>{{ currentArticle.category || '健康科普' }}</el-tag>
          <span>{{ currentArticle.publishDateText || '--' }}</span>
          <span>阅读 {{ currentArticle.readCount || 0 }}</span>
          <span>点赞 {{ currentArticle.likeCount || 0 }}</span>
          <span>评论 {{ currentArticle.commentCount || 0 }}</span>
          <span>收藏 {{ currentArticle.collectCount || 0 }}</span>
        </div>

        <h1 class="admin-detail-title">{{ currentArticle.title }}</h1>

        <div class="admin-detail-tags" v-if="currentArticle.tags">
          <el-tag
            v-for="tag in parseTags(currentArticle.tags)"
            :key="tag"
            round
            effect="plain"
          >
            {{ tag }}
          </el-tag>
        </div>

        <div class="admin-detail-content">
          <p v-for="(paragraph, index) in buildParagraphs(currentArticle.content)" :key="index">
            {{ paragraph }}
          </p>
        </div>

        <section class="admin-comment-section">
          <div class="admin-comment-header">
            <h3>评论区</h3>
            <span>{{ totalCommentCount }} 条评论</span>
          </div>

          <div v-if="comments.length" class="admin-comment-list">
            <article v-for="comment in comments" :key="comment.id" class="admin-comment-item">
              <div class="admin-comment-avatar">{{ getCommentAvatarText(comment) }}</div>
              <div class="admin-comment-body">
                <div class="admin-comment-meta">
                  <strong>{{ comment.username }}</strong>
                  <span>{{ formatDateTimeValue(comment.createTime) }}</span>
                </div>
                <p>{{ comment.content }}</p>

                <div v-if="comment.replies?.length" class="admin-reply-list">
                  <article v-for="reply in comment.replies" :key="reply.id" class="admin-reply-item">
                    <div class="admin-reply-avatar">{{ getCommentAvatarText(reply) }}</div>
                    <div class="admin-reply-body">
                      <div class="admin-comment-meta">
                        <strong>{{ reply.username }}</strong>
                        <span v-if="reply.replyToUsername" class="admin-reply-to">回复 {{ reply.replyToUsername }}</span>
                        <span>{{ formatDateTimeValue(reply.createTime) }}</span>
                      </div>
                      <p>{{ reply.content }}</p>
                    </div>
                  </article>
                </div>
              </div>
            </article>
          </div>

          <el-empty v-else description="暂无评论" />
        </section>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import healthKnowledgeApi from '../api/healthKnowledge';

const loading = ref(false);
const detailVisible = ref(false);
const articles = ref([]);
const currentArticle = ref(null);
const keyword = ref('');
const comments = ref([]);
const currentPage = ref(1);
const pageSize = 10;
const total = ref(0);
const authorPalette = ['#2f80ed', '#27ae60', '#f2994a', '#eb5757', '#56ccf2', '#6c5ce7', '#219653'];

const parseTags = (tags) =>
  String(tags || '')
    .replace(/[\[\]\"]/g, '')
    .split(/[，,、/]/)
    .map((item) => item.trim())
    .filter(Boolean);

const buildParagraphs = (content) =>
  String(content || '')
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);

const getAuthorAvatarText = (author) => String(author || '作').trim().charAt(0) || '作';
const getAuthorAvatarColor = (id) => authorPalette[(Number(id || 0) || 0) % authorPalette.length];
const getCommentAvatarText = (comment) => String(comment?.username || '评').trim().charAt(0) || '评';

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
    second: '2-digit',
    hour12: false
  });
};

const totalCommentCount = computed(() =>
  comments.value.reduce((sum, item) => sum + 1 + (Array.isArray(item.replies) ? item.replies.length : 0), 0)
);

const normalizeArticle = (article) => ({
  ...article,
  publishDate: article.publishDate || article.publish_date || '',
  publishDateText: formatDateTimeValue(article.createTime || article.create_time || article.updateTime || article.update_time),
  collectCount: article.collectCount || 0
});

const normalizeArticleList = (payload) => {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.list)) return payload.list;
  if (Array.isArray(payload?.data?.list)) return payload.data.list;
  return [];
};

const normalizeTotal = (payload, fallback) => {
  if (typeof payload?.total === 'number') return payload.total;
  if (typeof payload?.data?.total === 'number') return payload.data.total;
  return fallback;
};

const loadArticles = async () => {
  loading.value = true;
  try {
    const [response, statsResponse] = await Promise.all([
      keyword.value.trim()
        ? healthKnowledgeApi.searchArticles(keyword.value.trim(), currentPage.value, pageSize)
        : healthKnowledgeApi.getKnowledgeList({ page: currentPage.value, pageSize, sort: 'latest' }),
      healthKnowledgeApi.getArticleCollectStats()
    ]);

    const list = response.code === 200 ? normalizeArticleList(response.data) : [];
    total.value = response.code === 200 ? normalizeTotal(response.data, list.length) : 0;
    const statMap = new Map(
      statsResponse.code === 200 && Array.isArray(statsResponse.data)
        ? statsResponse.data.map((item) => [String(item.id), item.collectCount || 0])
        : []
    );

    articles.value = list.map((article) =>
      normalizeArticle({
        ...article,
        collectCount: statMap.get(String(article.id)) || 0
      })
    );
  } catch (error) {
    ElMessage.error(error.message || '加载文章失败');
  } finally {
    loading.value = false;
  }
};

const viewArticle = async (article) => {
  try {
    const [detailResponse, commentResponse] = await Promise.all([
      healthKnowledgeApi.getArticleDetail(article.id),
      healthKnowledgeApi.getArticleComments(article.id)
    ]);
    currentArticle.value =
      detailResponse.code === 200 ? normalizeArticle(detailResponse.data) : normalizeArticle(article);
    comments.value = commentResponse.code === 200 && Array.isArray(commentResponse.data) ? commentResponse.data : [];
    detailVisible.value = true;
  } catch (error) {
    currentArticle.value = normalizeArticle(article);
    comments.value = [];
    detailVisible.value = true;
  }
};

const deleteArticle = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除这篇文章吗？', '删除确认', { type: 'warning' });
    const response = await healthKnowledgeApi.deleteArticle(id);
    if (response.code === 200) {
      ElMessage.success('删除成功');
      await loadArticles();
    } else {
      ElMessage.error(response.message || '删除失败');
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败');
    }
  }
};

watch(currentPage, () => {
  loadArticles();
});

onMounted(loadArticles);
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.page-top h2 {
  margin: 0 0 8px;
}

.page-top p {
  margin: 0;
  color: #73887b;
}

.toolbar-card,
.table-card {
  border-radius: 22px;
}

.toolbar {
  display: flex;
  gap: 12px;
}

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.admin-article-detail-view {
  padding: 4px 4px 12px;
}

.admin-author-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}

.admin-author-avatar {
  width: 52px;
  height: 52px;
  min-width: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  overflow: hidden;
  flex-shrink: 0;
}

.admin-author-avatar.has-image {
  background: #f1f5f9;
}

.admin-author-avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.admin-author-meta {
  display: flex;
  flex-direction: column;
}

.admin-author-meta strong {
  color: #233449;
  font-size: 20px;
}

.admin-article-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  color: #62796b;
  margin-bottom: 16px;
}

.admin-detail-title {
  margin: 0 0 20px;
  color: #303133;
  line-height: 1.4;
}

.admin-detail-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.admin-detail-content {
  line-height: 1.8;
  color: #2d4336;
  font-size: 15px;
}

.admin-detail-content p {
  margin: 0;
}

.admin-detail-content p + p {
  margin-top: 14px;
}

.admin-comment-section {
  margin-top: 30px;
  padding-top: 24px;
  border-top: 1px solid #eef2f7;
}

.admin-comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.admin-comment-header h3 {
  margin: 0;
  font-size: 20px;
  color: #233449;
}

.admin-comment-header span {
  color: #7b8796;
  font-size: 14px;
}

.admin-comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.admin-comment-item {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-top: 1px solid #f0f3f7;
}

.admin-comment-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: #2f80ed;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}

.admin-comment-body {
  flex: 1;
}

.admin-comment-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
}

.admin-comment-meta strong {
  color: #24364c;
}

.admin-comment-meta span {
  color: #8b97a8;
  font-size: 13px;
}

.admin-comment-body p {
  margin: 0;
  color: #4a586a;
  line-height: 1.7;
}

.admin-reply-list {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.admin-reply-item {
  display: flex;
  gap: 10px;
}

.admin-reply-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #6c5ce7;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  flex-shrink: 0;
}

.admin-reply-body {
  flex: 1;
}

.admin-reply-body p {
  margin: 0;
  color: #4a586a;
  line-height: 1.7;
}

.admin-reply-to {
  color: #2f80ed !important;
}

@media (max-width: 900px) {
  .page-top,
  .toolbar {
    flex-direction: column;
  }
}
</style>
