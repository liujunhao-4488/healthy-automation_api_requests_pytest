<template>
  <div class="article-detail-container">
    <div class="page-actions">
      <el-button text @click="goBack" class="back-link">返回文章列表</el-button>
      <div v-if="article" class="page-action-group">
        <el-button plain :loading="likeLoading" :class="{ 'is-liked': liked }" @click="toggleLike">
          {{ liked ? '已点赞' : '点赞' }}
        </el-button>
        <el-button plain :loading="collectLoading" :class="{ 'is-collected': collected }" @click="toggleCollect">
          {{ collected ? '已收藏' : '收藏文章' }}
        </el-button>
      </div>
    </div>

    <el-card v-if="article" class="article-card">
      <div class="author-row">
        <div
          class="author-avatar"
          :class="{ 'has-image': Boolean(article.authorAvatar) }"
          :style="article.authorAvatar ? undefined : { background: avatarColor }"
        >
          <img
            v-if="article.authorAvatar"
            :src="article.authorAvatar"
            :alt="`${article.author || '作者'}头像`"
            class="author-avatar-image"
          />
          <template v-else>
            {{ avatarText }}
          </template>
        </div>
        <div class="author-meta">
          <strong>{{ article.author || '健康营养师' }}</strong>
        </div>
      </div>

      <div class="article-meta">
        <el-tag>{{ article.category || '健康科普' }}</el-tag>
        <span>{{ formatDate(article.publishDate || article.publish_date) }}</span>
        <span>阅读 {{ article.readCount || 0 }}</span>
        <span>点赞 {{ article.likeCount || 0 }}</span>
        <span>评论 {{ article.commentCount || 0 }}</span>
        <span>收藏 {{ article.collectCount || 0 }}</span>
      </div>

      <h1>{{ article.title }}</h1>

      <div class="tags" v-if="tagList.length > 0">
        <el-tag v-for="tag in tagList" :key="tag" type="success" effect="plain">{{ tag }}</el-tag>
      </div>

      <div class="article-content">
        <p v-for="(paragraph, index) in contentParagraphs" :key="index">{{ paragraph }}</p>
      </div>

      <section ref="commentSectionRef" class="comment-section">
        <div class="comment-header">
          <h3>评论区</h3>
          <span>{{ totalCommentCount }} 条评论</span>
        </div>

        <div class="comment-editor">
          <div v-if="replyTarget" class="reply-banner">
            <span>正在回复 {{ replyTarget.username }}</span>
            <el-button text @click="cancelReply">取消</el-button>
          </div>
          <el-input
            v-model="commentContent"
            type="textarea"
            :rows="4"
            maxlength="200"
            show-word-limit
            :placeholder="replyTarget ? `回复 ${replyTarget.username}...` : '写下你的看法...'"
          />
          <div class="comment-actions">
            <el-button type="primary" :loading="commentSubmitting" @click="submitComment">
              {{ replyTarget ? '发送回复' : '发表评论' }}
            </el-button>
          </div>
        </div>

        <div v-if="comments.length" class="comment-list">
          <article v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-avatar">{{ getCommentAvatarText(comment) }}</div>
            <div class="comment-body">
              <div class="comment-meta">
                <strong>{{ comment.username }}</strong>
                <span>{{ formatDateTime(comment.createTime) }}</span>
              </div>
              <p>{{ comment.content }}</p>
              <div class="comment-toolbar">
                <button type="button" class="reply-btn" @click="startReply(comment)">回复</button>
              </div>

              <div v-if="comment.replies?.length" class="reply-list">
                <article v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                  <div class="reply-avatar">{{ getCommentAvatarText(reply) }}</div>
                  <div class="reply-body">
                    <div class="comment-meta">
                      <strong>{{ reply.username }}</strong>
                      <span v-if="reply.replyToUsername" class="reply-to">回复 {{ reply.replyToUsername }}</span>
                      <span>{{ formatDateTime(reply.createTime) }}</span>
                    </div>
                    <p>{{ reply.content }}</p>
                    <div class="comment-toolbar">
                      <button type="button" class="reply-btn" @click="startReply(reply, comment)">回复</button>
                    </div>
                  </div>
                </article>
              </div>
            </div>
          </article>
        </div>
        <el-empty v-else description="还没有评论，来发表第一条吧" />
      </section>
    </el-card>

    <el-empty v-else description="未找到文章详情" />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import healthKnowledgeApi from '../api/healthKnowledge';

const route = useRoute();
const router = useRouter();
const article = ref(null);
const liked = ref(false);
const collected = ref(false);
const comments = ref([]);
const commentContent = ref('');
const commentSectionRef = ref(null);
const replyTarget = ref(null);
const likeLoading = ref(false);
const collectLoading = ref(false);
const commentSubmitting = ref(false);

const palette = ['#2f80ed', '#27ae60', '#f2994a', '#eb5757', '#56ccf2', '#6c5ce7', '#219653'];

const tagList = computed(() => {
  const tags = article.value?.tags;
  if (!tags) return [];
  if (Array.isArray(tags)) return tags;
  return String(tags)
    .replace(/[\[\]"]/g, '')
    .split(/[，,、|/]/)
    .map((item) => item.trim())
    .filter(Boolean);
});

const contentParagraphs = computed(() => {
  const content = article.value?.content || article.value?.summary || '';
  return String(content)
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);
});

const avatarText = computed(() => String(article.value?.author || '营').trim().charAt(0) || '营');
const avatarColor = computed(() => palette[(Number(route.params.id || 0) || 0) % palette.length]);
const totalCommentCount = computed(() =>
  comments.value.reduce((sum, item) => sum + 1 + (Array.isArray(item.replies) ? item.replies.length : 0), 0)
);

const formatDate = (value) => {
  if (!value) return '--';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString('zh-CN');
};

const formatDateTime = (value) => {
  if (!value) return '--';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString('zh-CN');
};

const getCommentAvatarText = (comment) => String(comment?.username || '评').trim().charAt(0) || '评';

const loadLikeStatus = async () => {
  try {
    const response = await healthKnowledgeApi.getArticleLikeStatus(route.params.id);
    if (response.code === 200) {
      liked.value = Boolean(response.data?.liked);
      if (article.value) {
        article.value.likeCount = Number(response.data?.likeCount || 0);
      }
    }
  } catch (error) {
    console.error('获取点赞状态失败:', error);
  }
};

const loadCollectStatus = async () => {
  try {
    const response = await healthKnowledgeApi.getArticleCollectStatus(route.params.id);
    if (response.code === 200) {
      collected.value = Boolean(response.data?.collected);
      if (article.value) {
        article.value.collectCount = Number(response.data?.collectCount || 0);
      }
    }
  } catch (error) {
    console.error('获取收藏状态失败:', error);
  }
};

const loadComments = async () => {
  try {
    const response = await healthKnowledgeApi.getArticleComments(route.params.id);
    if (response.code === 200 && Array.isArray(response.data)) {
      comments.value = response.data;
      if (article.value) {
        article.value.commentCount = totalCommentCount.value;
      }
    }
  } catch (error) {
    ElMessage.error(error.message || '获取评论失败');
  }
};

const loadArticle = async () => {
  try {
    const response = await healthKnowledgeApi.getArticleDetail(route.params.id);
    if (response.code === 200) {
      article.value = response.data;
      await Promise.all([loadLikeStatus(), loadCollectStatus(), loadComments()]);
      if (route.query.focus === 'comments') {
        await nextTick();
        commentSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      return;
    }
    ElMessage.error(response.message || '获取文章详情失败');
  } catch (error) {
    ElMessage.error(error.message || '获取文章详情失败');
  }
};

const toggleLike = async () => {
  likeLoading.value = true;
  try {
    const response = liked.value
      ? await healthKnowledgeApi.cancelLikeArticle(route.params.id)
      : await healthKnowledgeApi.likeArticle(route.params.id);

    if (response.code === 200) {
      liked.value = Boolean(response.data?.liked);
      if (article.value) {
        article.value.likeCount = Number(response.data?.likeCount || 0);
      }
      return;
    }
    ElMessage.error(response.message || '操作失败');
  } catch (error) {
    ElMessage.error(error.message || '操作失败');
  } finally {
    likeLoading.value = false;
  }
};

const toggleCollect = async () => {
  collectLoading.value = true;
  try {
    const response = collected.value
      ? await healthKnowledgeApi.cancelCollectArticle(route.params.id)
      : await healthKnowledgeApi.collectArticle(route.params.id);

    if (response.code === 200) {
      collected.value = Boolean(response.data?.collected);
      if (article.value) {
        article.value.collectCount = Number(response.data?.collectCount || 0);
      }
      ElMessage.success(collected.value ? '文章已加入收藏' : '已取消收藏');
      return;
    }
    ElMessage.error(response.message || '操作失败');
  } catch (error) {
    ElMessage.error(error.message || '操作失败');
  } finally {
    collectLoading.value = false;
  }
};

const submitComment = async () => {
  if (!commentContent.value.trim()) {
    ElMessage.warning('评论内容不能为空');
    return;
  }

  commentSubmitting.value = true;
  try {
    const response = await healthKnowledgeApi.addArticleComment(route.params.id, {
      content: commentContent.value.trim(),
      parentId: replyTarget.value?.parentId || replyTarget.value?.id || null,
      replyToUserId: replyTarget.value?.userId || null
    });

    if (response.code === 200) {
      commentContent.value = '';
      replyTarget.value = null;
      await loadComments();
      ElMessage.success('评论成功');
      return;
    }
    ElMessage.error(response.message || '评论失败');
  } catch (error) {
    ElMessage.error(error.message || '评论失败');
  } finally {
    commentSubmitting.value = false;
  }
};

const startReply = async (comment, rootComment = null) => {
  replyTarget.value = {
    id: comment.id,
    userId: comment.userId,
    username: comment.username,
    parentId: rootComment ? rootComment.id : comment.id
  };
  await nextTick();
  commentSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

const cancelReply = () => {
  replyTarget.value = null;
};

const goBack = () => {
  router.push('/dashboard/health-knowledge');
};

onMounted(() => {
  loadArticle();
});
</script>

<style scoped>
.article-detail-container {
  max-width: 920px;
  margin: 0 auto;
}

.page-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.page-action-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.article-card {
  border-radius: 18px;
}

.is-liked {
  color: #eb5757;
  border-color: rgba(235, 87, 87, 0.35);
}

.is-collected {
  color: #d4a017;
  border-color: rgba(212, 160, 23, 0.35);
}

.author-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
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

.author-meta {
  display: flex;
  flex-direction: column;
}

.author-meta strong {
  color: #233449;
  font-size: 20px;
}

.article-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  color: #909399;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

h1 {
  margin: 0 0 20px;
  color: #303133;
  line-height: 1.4;
}

.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.article-content {
  color: #4a4a4a;
  line-height: 1.9;
  font-size: 15px;
}

.article-content p + p {
  margin-top: 14px;
}

.comment-section {
  margin-top: 30px;
  padding-top: 24px;
  border-top: 1px solid #eef2f7;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.comment-header h3 {
  margin: 0;
  font-size: 20px;
  color: #233449;
}

.comment-header span {
  color: #7b8796;
  font-size: 14px;
}

.comment-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.reply-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  background: #f5f8ff;
  color: #45628b;
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-top: 1px solid #f0f3f7;
}

.comment-avatar {
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

.comment-body {
  flex: 1;
}

.comment-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
}

.comment-meta strong {
  color: #24364c;
}

.comment-meta span {
  color: #8b97a8;
  font-size: 13px;
}

.comment-body p {
  margin: 0;
  color: #4a586a;
  line-height: 1.7;
}

.comment-toolbar {
  margin-top: 8px;
}

.reply-btn {
  border: none;
  background: transparent;
  padding: 0;
  color: #2f80ed;
  cursor: pointer;
  font-size: 14px;
}

.reply-list {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reply-item {
  display: flex;
  gap: 10px;
}

.reply-avatar {
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

.reply-body {
  flex: 1;
}

.reply-to {
  color: #2f80ed;
}

@media (max-width: 640px) {
  .page-actions {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
