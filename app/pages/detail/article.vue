<template>
  <view class="page-shell safe-bottom">
    <view class="page-content detail-page">
      <view class="hero-card card">
        <view>
          <view class="hero-title">文章详情</view>
          <view class="hero-desc">查看文章正文、摘要与互动状态。</view>
        </view>
        <text class="hero-action" @click="loadDetail">刷新</text>
      </view>

      <view v-if="loading" class="card empty-card">
        <text>正在加载文章...</text>
      </view>

      <view v-else-if="article" class="list-stack">
        <view class="card article-card">
          <text class="article-title">{{ article.title }}</text>
          <view class="meta-row">
            <text>{{ article.category || '推荐' }}</text>
            <text>{{ article.publishTime || article.createdAt || '刚刚更新' }}</text>
          </view>
          <text class="article-summary">{{ article.summary }}</text>
        </view>

        <view class="card article-card">
          <view class="section-title">
            <text class="section-title__text">正文内容</text>
          </view>
          <text class="article-content">{{ article.content }}</text>
        </view>
      </view>

      <view v-else class="card empty-card">
        <text>未找到对应文章</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import healthKnowledgeApi from '@/api/healthKnowledge'
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const loading = ref(false)
const articleId = ref('')
const article = ref(null)

const normalizeArticle = (item) => ({
  ...item,
  title: item.title || '未命名文章',
  summary: String(item.summary || item.content || '暂无摘要').replace(/\s+/g, ' ').slice(0, 120),
  content: item.content || item.summary || '暂无正文内容',
  category: item.category || item.tagName || ''
})

const loadDetail = async () => {
  if (!articleId.value) return
  loading.value = true
  try {
    const response = await healthKnowledgeApi.getArticleDetail(articleId.value)
    article.value = response.code === 200 && response.data ? normalizeArticle(response.data) : null
  } catch (error) {
    article.value = null
  } finally {
    loading.value = false
  }
}

onLoad((query) => {
  articleId.value = query?.id || ''
  loadDetail()
})
</script>

<style scoped lang="scss">
.detail-page {
  padding-top: 20rpx;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  padding: 32rpx;
}

.hero-title {
  font-size: 40rpx;
  font-weight: 700;
}

.hero-desc {
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #5b6159;
}

.hero-action {
  color: #486646;
  font-size: 24rpx;
}

.list-stack {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 22rpx;
}

.article-card {
  padding: 28rpx;
}

.article-title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: #2e342d;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  margin-top: 18rpx;
  font-size: 22rpx;
  color: #7c8578;
}

.article-summary {
  display: block;
  margin-top: 18rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #5b6159;
}

.article-content {
  display: block;
  margin-top: 20rpx;
  font-size: 26rpx;
  line-height: 1.9;
  color: #2e342d;
  white-space: pre-wrap;
}

.empty-card {
  margin-top: 22rpx;
  padding: 36rpx 28rpx;
  text-align: center;
  color: #7c8578;
  font-size: 24rpx;
}
</style>
