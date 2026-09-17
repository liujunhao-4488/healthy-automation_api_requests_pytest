<template>
  <view class="page-shell safe-bottom">
    <view class="page-content knowledge-page">
      <view class="hero-card card">
        <view>
          <view class="hero-title">健康知识</view>
          <view class="hero-desc">查看推荐文章、最新内容，并按关键词快速搜索。</view>
        </view>
        <text class="hero-action" @click="refreshArticles">刷新</text>
      </view>

      <view class="search-card soft-card">
        <view class="search-box input-card">
          <input
            v-model.trim="keyword"
            confirm-type="search"
            placeholder="搜索营养、控糖、减脂等内容"
            type="text"
            @confirm="handleSearch"
          />
        </view>
        <button class="secondary-button search-btn" @click="handleSearch">搜索</button>
      </view>

      <view class="tab-row soft-card">
        <view
          v-for="item in tabs"
          :key="item.value"
          class="tab-pill"
          :class="{ active: activeTab === item.value }"
          @click="changeTab(item.value)"
        >
          {{ item.label }}
        </view>
      </view>

      <view v-if="tagList.length" class="tag-row">
        <view
          v-for="tag in tagList"
          :key="tag"
          class="tag-pill"
          :class="{ active: activeTag === tag }"
          @click="toggleTag(tag)"
        >
          {{ tag }}
        </view>
      </view>

      <view v-if="loading && !articles.length" class="card empty-card">
        <text>正在加载文章...</text>
      </view>

      <view v-if="articles.length" class="list-stack">
        <view v-for="item in articles" :key="item.id" class="card article-card" @click="openArticle(item)">
          <view class="author-row">
            <view class="author-avatar" :style="{ background: item.avatarColor }">
              <image v-if="item.authorAvatar" :src="item.authorAvatar" mode="aspectFill" class="author-avatar-img" />
              <text v-else>{{ item.avatarText }}</text>
            </view>
            <view class="author-info">
              <text class="author-name">{{ item.author }}</text>
              <text class="publish-time">{{ item.publishText || '刚刚更新' }}</text>
            </view>
            <text class="article-tag">{{ item.category || activeTag || '推荐' }}</text>
          </view>

          <view class="article-body">
            <text class="article-title">{{ item.title }}</text>
            <text class="article-desc clamp-3">{{ item.summary }}</text>
          </view>

          <view class="article-meta">
            <text>阅读 {{ item.readCount }}</text>
            <text>点赞 {{ item.likeCount }}</text>
            <text>评论 {{ item.commentCount }}</text>
          </view>
        </view>

        <view class="load-more-state">
          <text v-if="loadingMore">正在加载更多...</text>
          <text v-else-if="!hasMore">已经到底了</text>
          <text v-else>上拉加载更多</text>
        </view>
      </view>

      <view v-else-if="!loading" class="card empty-card">
        <text>{{ emptyText }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import healthKnowledgeApi from '@/api/healthKnowledge'
import { computed, ref } from 'vue'
import { onReachBottom, onShow } from '@dcloudio/uni-app'

const tabs = [
  { label: '推荐', value: 'recommend' },
  { label: '最新', value: 'latest' },
  { label: '热门', value: 'hot' }
]

const loading = ref(false)
const loadingMore = ref(false)
const activeTab = ref('recommend')
const activeTag = ref('')
const keyword = ref('')
const articles = ref([])
const tagList = ref([])
const currentPage = ref(1)
const total = ref(0)
const hasMore = ref(true)
const pageSize = 10
const avatarColors = ['#6f9580', '#8fae91', '#d4a373', '#7b9acc', '#c58b8b', '#93a875']

const buildAvatarText = (name) => String(name || '营').trim().charAt(0) || '营'

const normalizeArticle = (item) => {
  const author = item.author || item.publisher || '健康管理编辑部'
  return {
    ...item,
    title: item.title || '未命名文章',
    summary: String(item.summary || item.content || '暂无摘要').replace(/\s+/g, ' ').slice(0, 90),
    category: item.category || item.tagName || '',
    author,
    authorAvatar: item.authorAvatar || item.avatar || '',
    avatarText: buildAvatarText(author),
    avatarColor: avatarColors[Math.abs(Number(item.id || 0)) % avatarColors.length],
    publishText: item.publishTime || item.createdAt || item.createTime || item.publishDate || '',
    readCount: Number(item.readCount || 0),
    likeCount: Number(item.likeCount || 0),
    commentCount: Number(item.commentCount || 0)
  }
}

const extractArticleList = (data) => {
  if (Array.isArray(data?.records)) {
    return data.records
  }
  if (Array.isArray(data?.list)) {
    return data.list
  }
  return Array.isArray(data) ? data : []
}

const extractTotal = (data, fallback) => {
  if (Number.isFinite(Number(data?.total))) {
    return Number(data.total)
  }
  if (Number.isFinite(Number(data?.count))) {
    return Number(data.count)
  }
  return fallback
}

const emptyText = computed(() => {
  if (keyword.value) {
    return `没有找到与“${keyword.value}”相关的内容`
  }
  return '当前暂无相关文章'
})

const loadTags = async () => {
  try {
    const response = await healthKnowledgeApi.getArticleTags()
    tagList.value = response.code === 200 && Array.isArray(response.data)
      ? response.data.map((item) => (typeof item === 'string' ? item : item.name || item.tagName)).filter(Boolean).slice(0, 8)
      : []
  } catch (error) {
    tagList.value = []
  }
}

const buildArticleRequest = (page) => {
  if (keyword.value) {
    return healthKnowledgeApi.searchArticles(keyword.value, page, pageSize)
  }

  if (activeTab.value === 'recommend') {
    return healthKnowledgeApi.getRecommendedArticles({
      page,
      pageSize,
      tag: activeTag.value || undefined
    })
  }

  return healthKnowledgeApi.getKnowledgeList({
    page,
    pageSize,
    sort: activeTab.value === 'hot' ? 'hot' : 'latest',
    tag: activeTag.value || undefined
  })
}

const loadRecommendedArticleResponse = async (page) => {
  const recommendResponse = await healthKnowledgeApi.getRecommendedArticles({
    page,
    pageSize,
    tag: activeTag.value || undefined
  })
  const recommendList = recommendResponse.code === 200 ? extractArticleList(recommendResponse.data) : []

  if (recommendList.length || keyword.value || activeTab.value !== 'recommend') {
    return recommendResponse
  }

  return healthKnowledgeApi.getKnowledgeList({
    page,
    pageSize,
    sort: 'latest',
    tag: activeTag.value || undefined
  })
}

const loadArticles = async ({ reset = false, force = false } = {}) => {
  if ((loading.value || loadingMore.value) && !force) return
  if (!reset && !hasMore.value) return

  const targetPage = reset ? 1 : currentPage.value + 1

  if (reset) {
    loading.value = true
    articles.value = []
    currentPage.value = 1
    total.value = 0
    hasMore.value = true
  } else {
    loadingMore.value = true
  }

  try {
    const response = activeTab.value === 'recommend' && !keyword.value
      ? await loadRecommendedArticleResponse(targetPage)
      : await buildArticleRequest(targetPage)
    const list = response.code === 200 ? extractArticleList(response.data) : []
    const normalizedList = list.map(normalizeArticle)
    const nextArticles = reset ? normalizedList : [...articles.value, ...normalizedList]

    articles.value = nextArticles
    currentPage.value = targetPage
    total.value = extractTotal(response.data, nextArticles.length)
    hasMore.value = nextArticles.length < total.value && normalizedList.length > 0
  } catch (error) {
    if (reset) {
      articles.value = []
      total.value = 0
      hasMore.value = false
    }
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const refreshArticles = () => {
  loadArticles({ reset: true, force: true })
}

const changeTab = (value) => {
  if (activeTab.value === value) return
  activeTab.value = value
  keyword.value = ''
  loadArticles({ reset: true, force: true })
}

const toggleTag = (tag) => {
  activeTag.value = activeTag.value === tag ? '' : tag
  loadArticles({ reset: true, force: true })
}

const handleSearch = () => {
  activeTag.value = ''
  loadArticles({ reset: true, force: true })
}

const openArticle = (item) => {
  if (!item?.id) return
  uni.navigateTo({ url: `/pages/detail/article?id=${item.id}` })
}

onShow(() => {
  loadTags()
  loadArticles({ reset: true, force: true })
})

onReachBottom(() => {
  loadArticles()
})
</script>

<style scoped lang="scss">
.knowledge-page {
  padding-top: 20rpx;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  padding: 32rpx;
  align-items: flex-start;
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

.search-card {
  display: flex;
  gap: 16rpx;
  padding: 18rpx;
  margin-top: 22rpx;
}

.search-box {
  flex: 1;
}

.search-btn {
  width: 156rpx;
  height: 82rpx;
  font-size: 26rpx;
}

.tab-row {
  display: flex;
  gap: 14rpx;
  padding: 12rpx;
  margin-top: 22rpx;
}

.tab-pill {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 72rpx;
  border-radius: 999rpx;
  color: #5b6159;
  font-size: 24rpx;
}

.tab-pill.active,
.tag-pill.active {
  background: #486646;
  color: #eff8eb;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 22rpx;
}

.tag-pill {
  padding: 12rpx 22rpx;
  border-radius: 999rpx;
  background: #edf3e8;
  color: #5b6159;
  font-size: 22rpx;
}

.list-stack {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 22rpx;
}

.article-card {
  padding: 26rpx;
  border: 1rpx solid rgba(72, 102, 70, 0.08);
}

.author-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.author-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24rpx;
  font-weight: 700;
  overflow: hidden;
  flex-shrink: 0;
}

.author-avatar-img {
  width: 100%;
  height: 100%;
  display: block;
}

.author-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.author-name {
  color: #2e342d;
  font-size: 24rpx;
  font-weight: 600;
}

.publish-time {
  color: #8a9486;
  font-size: 20rpx;
}

.article-body {
  margin-top: 18rpx;
}

.article-title {
  display: block;
  font-size: 32rpx;
  line-height: 1.45;
  font-weight: 700;
  color: #20291f;
}

.article-desc {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #5b6159;
}

.article-tag {
  flex-shrink: 0;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: #edf3e8;
  color: #486646;
  font-size: 22rpx;
}

.article-meta {
  display: flex;
  align-items: center;
  gap: 22rpx;
  margin-top: 20rpx;
  padding-top: 18rpx;
  border-top: 1rpx solid #eef3ea;
  font-size: 21rpx;
  color: #7c8578;
}

.empty-card {
  margin-top: 22rpx;
  padding: 36rpx 28rpx;
  text-align: center;
  color: #7c8578;
  font-size: 24rpx;
}

.load-more-state {
  padding: 12rpx 0 26rpx;
  text-align: center;
  color: #7c8578;
  font-size: 22rpx;
}

.clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
