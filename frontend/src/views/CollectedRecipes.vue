<template>
  <div class="recipe-page collected-page">
    <section class="recipe-shell">
      <div class="page-top">
        <div>
          <p class="eyebrow">MY RECIPE COLLECTIONS</p>
          <h2>我的收藏食谱</h2>
          <span>统一查看已收藏的推荐食谱和自定义食谱</span>
        </div>
        <el-button @click="router.push('/dashboard/profile')">返回个人中心</el-button>
      </div>

      <div v-loading="loading" class="recipe-list">
        <article
          v-for="recipe in recipes"
          :key="recipe.id"
          class="recipe-card"
          @click="openRecipeDetail(recipe)"
        >
          <div class="recipe-card-top">
            <div>
              <h3>{{ recipe.name }}</h3>
              <p>{{ recipe.description || '已加入收藏，方便后续随时查看。' }}</p>
            </div>
            <el-tag :type="recipe.isCustom ? 'warning' : 'success'" effect="plain">
              {{ recipe.isCustom ? '自定义食谱' : '系统食谱' }}
            </el-tag>
          </div>

          <div class="metric-grid">
            <div class="metric-item">
              <span>热量</span>
              <strong>{{ formatNumber(recipe.totalCalories, 0) }}</strong>
              <small>kcal</small>
            </div>
            <div class="metric-item">
              <span>蛋白质</span>
              <strong>{{ formatNumber(recipe.protein, 1) }}</strong>
              <small>g</small>
            </div>
            <div class="metric-item">
              <span>碳水</span>
              <strong>{{ formatNumber(recipe.carbs, 1) }}</strong>
              <small>g</small>
            </div>
            <div class="metric-item">
              <span>脂肪</span>
              <strong>{{ formatNumber(recipe.fat, 1) }}</strong>
              <small>g</small>
            </div>
          </div>

          <div class="recipe-meta">
            <span>烹饪时间 {{ recipe.cookingTime || '--' }} 分钟</span>
            <span>难度 {{ recipe.difficulty || '家常' }}</span>
            <span>评分 {{ formatNumber(recipe.score, 1) }}</span>
          </div>
        </article>

        <el-empty v-if="!loading && !recipes.length" description="还没有收藏食谱" class="empty-block" />
      </div>
    </section>

    <el-dialog v-model="detailVisible" title="食谱详情" width="760px">
      <template v-if="selectedRecipe">
        <div class="detail-head">
          <div>
            <h3>{{ selectedRecipe.name }}</h3>
            <p>{{ selectedRecipe.description || '暂无描述' }}</p>
          </div>
          <el-tag :type="selectedRecipe.isCustom ? 'warning' : 'success'" effect="plain">
            {{ selectedRecipe.isCustom ? '自定义食谱' : '系统食谱' }}
          </el-tag>
        </div>

        <div class="detail-metrics">
          <div class="detail-metric">
            <span>热量</span>
            <strong>{{ formatNumber(selectedRecipe.totalCalories, 0) }} kcal</strong>
          </div>
          <div class="detail-metric">
            <span>蛋白质</span>
            <strong>{{ formatNumber(selectedRecipe.protein, 1) }} g</strong>
          </div>
          <div class="detail-metric">
            <span>碳水</span>
            <strong>{{ formatNumber(selectedRecipe.carbs, 1) }} g</strong>
          </div>
          <div class="detail-metric">
            <span>脂肪</span>
            <strong>{{ formatNumber(selectedRecipe.fat, 1) }} g</strong>
          </div>
        </div>

        <div v-if="selectedRecipe.ingredients.length" class="detail-section">
          <h4>食材</h4>
          <ul>
            <li v-for="(ingredient, index) in selectedRecipe.ingredients" :key="index">
              {{ ingredient }}
            </li>
          </ul>
        </div>

        <div v-if="selectedRecipe.steps.length" class="detail-section">
          <h4>制作步骤</h4>
          <ol>
            <li v-for="(step, index) in selectedRecipe.steps" :key="index">
              {{ step }}
            </li>
          </ol>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import recipeApi from '../api/recipe';

const router = useRouter();
const loading = ref(false);
const recipes = ref([]);
const detailVisible = ref(false);
const selectedRecipe = ref(null);

const formatNumber = (value, digits = 1) => {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : '--';
};

const splitLines = (text) =>
  String(text || '')
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);

const formatQuantityText = (quantity, unit) => {
  if (quantity === null || quantity === undefined || quantity === '') {
    return '';
  }

  const unitText = String(unit || '').trim();
  const rawText = String(quantity).trim();
  const normalizedRaw = rawText.toLowerCase();
  const normalizedUnit = unitText.toLowerCase();
  if (normalizedUnit && normalizedRaw.endsWith(normalizedUnit)) {
    return rawText;
  }

  const value = Number(quantity);
  if (!Number.isFinite(value)) {
    return `${rawText}${unitText}`.trim();
  }

  const quantityText = Number.isInteger(value) ? String(value) : value.toFixed(1);
  return `${quantityText}${unitText}`.trim();
};

const normalizeIngredients = (ingredients) => {
  if (!Array.isArray(ingredients)) return [];
  return ingredients.map((item) => {
    if (typeof item === 'string') return item;
    const name = item.name || item.ingredientName || '食材';
    const quantityText = formatQuantityText(
      item.quantityValue ?? item.quantity,
      item.unit
    );
    return quantityText ? `${name} ${quantityText}` : name;
  });
};

const normalizeRecipe = (recipe) => ({
  ...recipe,
  isCustom: Number(recipe.isCustom || 0) === 1,
  ingredients: normalizeIngredients(recipe.ingredients),
  steps: Array.isArray(recipe.steps) ? recipe.steps : splitLines(recipe.instructions)
});

const loadCollectedRecipes = async () => {
  loading.value = true;
  try {
    const response = await recipeApi.getCollectedRecipes();
    recipes.value =
      response.code === 200 && Array.isArray(response.data)
        ? response.data.map(normalizeRecipe)
        : [];
  } finally {
    loading.value = false;
  }
};

const openRecipeDetail = async (recipe) => {
  selectedRecipe.value = normalizeRecipe(recipe);
  detailVisible.value = true;

  try {
    const response = await recipeApi.getRecipeDetail(recipe.id);
    if (response.code === 200 && response.data?.recipe) {
      selectedRecipe.value = normalizeRecipe({
        ...response.data.recipe,
        ingredients: response.data.ingredients
      });
    }
  } catch (error) {
    // keep list data as fallback
  }
};

onMounted(loadCollectedRecipes);
</script>

<style scoped>
.collected-page {
  padding: 8px 0;
}

.recipe-shell {
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

.recipe-list {
  min-height: 260px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recipe-card {
  padding: 20px;
  border-radius: 22px;
  border: 1px solid #eef2f7;
  background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.recipe-card:hover {
  transform: translateY(-2px);
  border-color: #d8e7dc;
  box-shadow: 0 14px 28px rgba(31, 53, 84, 0.08);
}

.recipe-card-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.recipe-card-top h3 {
  margin: 0 0 8px;
  color: #1d3025;
  font-size: 22px;
}

.recipe-card-top p {
  margin: 0;
  color: #738075;
  line-height: 1.7;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 18px 0 14px;
}

.metric-item {
  padding: 14px 12px;
  border-radius: 16px;
  background: #f7fbf8;
  text-align: center;
}

.metric-item span,
.metric-item small {
  display: block;
  color: #7f9186;
}

.metric-item strong {
  display: block;
  margin: 6px 0 2px;
  color: #22382c;
  font-size: 20px;
}

.recipe-meta {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  color: #76867b;
  font-size: 14px;
}

.empty-block {
  padding: 42px 0 36px;
}

.detail-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.detail-head h3 {
  margin: 0 0 10px;
  color: #1d3025;
  font-size: 26px;
}

.detail-head p {
  margin: 0;
  color: #6f8073;
  line-height: 1.7;
}

.detail-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.detail-metric {
  padding: 14px 16px;
  border-radius: 16px;
  background: #f7fbf8;
}

.detail-metric span {
  display: block;
  margin-bottom: 6px;
  color: #75867a;
  font-size: 13px;
}

.detail-metric strong {
  color: #203526;
  font-size: 18px;
}

.detail-section + .detail-section {
  margin-top: 18px;
}

.detail-section h4 {
  margin: 0 0 10px;
  color: #22352a;
}

.detail-section ul,
.detail-section ol {
  margin: 0;
  padding-left: 20px;
  color: #5b6f61;
  line-height: 1.8;
}

@media (max-width: 768px) {
  .page-top,
  .recipe-card-top,
  .detail-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .metric-grid,
  .detail-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
