<template>
  <div class="knowledge-page collected-page">
    <section class="knowledge-shell">
      <div class="page-top">
        <div>
          <p class="eyebrow">MY COLLECTIONS</p>
          <h2>我的收藏文章</h2>
          <span>统一查看已收藏的健康知识文章</span>
        </div>
        <el-button @click="router.push('/dashboard/profile')">返回个人中心</el-button>
      </div>

      <div v-loading="loading" class="article-list">
        <article
          v-for="article in articles"
          :key="article.id"
          class="article-card"
          @click="router.push(`/dashboard/health-knowledge/${article.id}`)"
        >
          <div class="author-row">
            <div class="author-avatar" :style="{ background: article.avatarColor }">
              {{ article.avatarText }}
            </div>
            <div class="author-info">
              <strong>{{ article.authorName }}</strong>
              <span>{{ article.authorDesc }}</span>
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
            <span class="metric-item">点赞 {{ article.likeCount }}</span>
            <span class="metric-item">评论 {{ article.commentCount }}</span>
            <span class="metric-item">收藏 {{ article.collectCount }}</span>
            <span class="metric-item">阅读 {{ article.readCount }}</span>
          </div>
        </article>

        <el-empty v-if="!loading && !articles.length" description="还没有收藏文章" class="empty-block" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import healthKnowledgeApi from '../api/healthKnowledge';

const router = useRouter();
const loading = ref(false);
const articles = ref([]);
const palette = ['#2f80ed', '#27ae60', '#f2994a', '#eb5757', '#56ccf2', '#6c5ce7', '#219653'];

const parseTags = (tags) => {
  if (!tags) return [];
  if (Array.isArray(tags)) return tags.filter(Boolean).map((item) => String(item).trim());

  return String(tags)
    .replace(/[\[\]"]/g, '')
    .split(/[，,、|/]/)
    .map((item) => item.trim())
    .filter(Boolean);
};

const summarizeContent = (content, summary) => {
  const source = summary && String(summary).trim() ? String(summary).trim() : String(content || '').trim();
  if (!source) return '暂无摘要';
  const normalized = source.replace(/\s+/g, ' ');
  return normalized.length > 88 ? `${normalized.slice(0, 88)}...` : normalized;
};

const normalizeArticle = (article, index) => {
  const authorName = article.author || '健康营养师';
  return {
    ...article,
    authorName,
    authorDesc: `${article.category || '健康知识'}专栏作者`,
    avatarText: String(authorName).trim().charAt(0) || '营',
    avatarColor: palette[index % palette.length],
    tags: parseTags(article.tags),
    summaryText: summarizeContent(article.content, article.summary),
    likeCount: Number(article.likeCount || 0),
    commentCount: Number(article.commentCount || 0),
    collectCount: Number(article.collectCount || 0),
    readCount: Number(article.readCount || 0)
  };
};

const loadCollectedArticles = async () => {
  loading.value = true;
  try {
    const response = await healthKnowledgeApi.getCollectedArticles();
    articles.value =
      response.code === 200 && Array.isArray(response.data)
        ? response.data.map(normalizeArticle)
        : [];
  } finally {
    loading.value = false;
  }
};

onMounted(loadCollectedArticles);
</script>

<style scoped>
.collected-page {
  padding: 8px 0;
}

.knowledge-shell {
  background: #fff;
  border-radius: 24px;
  border: 1px solid #ebeff4;
  overflow: hidden;
  box-shadow: 0 12px 28px rgba(22, 45, 77, 0.05);
}

.page-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 22px 18px 18px;
  border-bottom: 1px solid #edf1f5;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.16em;
  color: #6f8f72;
}

.page-top h2 {
  margin: 0;
  color: #314337;
  font-size: 28px;
  font-family: 'Noto Serif SC', serif;
}

.page-top span {
  color: #718073;
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
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.author-info strong {
  color: #182538;
  font-size: 24px;
}

.author-info span {
  color: #7a889a;
  font-size: 15px;
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

.empty-block {
  padding: 42px 0 36px;
}

@media (max-width: 768px) {
  .page-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .article-list {
    padding: 14px;
  }

  .article-card {
    padding: 16px;
  }

  .author-info strong {
    font-size: 20px;
  }

  .article-title {
    font-size: 18px;
  }
}
</style>
