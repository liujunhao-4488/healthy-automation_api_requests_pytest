<template>
  <div class="admin-overview">
    <section class="stats-grid">
      <article class="stat-card">
        <span class="stat-label">食材总数</span>
        <strong>{{ stats.ingredientCount }}</strong>
        <p>为饮食分析、营养计算和替代建议提供基础营养数据。</p>
      </article>
      <article class="stat-card">
        <span class="stat-label">食谱总数</span>
        <strong>{{ stats.recipeCount }}</strong>
        <p>作为个性化推荐和用户饮食记录的一线候选内容。</p>
      </article>
      <article class="stat-card">
        <span class="stat-label">文章总数</span>
        <strong>{{ stats.articleCount }}</strong>
        <p>用于健康知识推荐、饮食误区提醒和科普展示。</p>
      </article>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import ingredientApi from '../api/ingredient';
import recipeApi from '../api/recipe';
import healthKnowledgeApi from '../api/healthKnowledge';

const stats = ref({
  ingredientCount: 0,
  recipeCount: 0,
  articleCount: 0
});

const normalizeArray = (payload) => {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.list)) return payload.list;
  return [];
};

const loadOverview = async () => {
  try {
    const [ingredientResponse, recipeResponse, articleResponse] = await Promise.all([
      ingredientApi.getAllIngredients(),
      recipeApi.getAllRecipes(),
      healthKnowledgeApi.getKnowledgeList(1, 100)
    ]);

    const ingredients = normalizeArray(ingredientResponse.data);
    const recipes = normalizeArray(recipeResponse.data);
    const articles = normalizeArray(articleResponse.data);

    stats.value = {
      ingredientCount: ingredients.length,
      recipeCount: recipes.length,
      articleCount: articles.length
    };
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '加载后台总览数据失败');
  }
};

onMounted(() => {
  loadOverview();
});
</script>

<style scoped>
.admin-overview {
  display: flex;
  flex-direction: column;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.stat-card {
  padding: 24px 22px;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 16px 36px rgba(32, 56, 44, 0.08);
}

.stat-label {
  display: inline-block;
  margin-bottom: 12px;
  color: #6f8575;
  font-size: 14px;
}

.stat-card strong {
  display: block;
  font-size: 34px;
  color: #1f3428;
}

.stat-card p {
  margin: 10px 0 0;
  line-height: 1.6;
  color: #7a8d7f;
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
