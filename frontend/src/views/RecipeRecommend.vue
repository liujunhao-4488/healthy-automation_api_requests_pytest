<template>
  <div class="recipe-recommend-container">
    <section class="hero-card">
      <div>
        <p class="eyebrow">AI 智能配餐</p>
        <h2>个性化食谱推荐</h2>
        <p class="hero-text">
          系统会结合健康信息、饮食目标和当前偏好，为你生成每日、7 天或 30 天的食谱方案。
        </p>
      </div>

      <div class="hero-actions">
        <el-segmented
          v-model="planMode"
          :options="planOptions"
          class="mode-switch"
        />
        <el-button type="primary" :loading="loading" @click="getRecommendations">
          生成推荐
        </el-button>
        <el-button @click="rotateRecommendations" :disabled="!canRotateRecommendations">
          换一批
        </el-button>
        <el-dropdown trigger="click" @command="handleExportCommand" :disabled="allRecipesCount === 0">
          <el-button>
            导出
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="pdf">导出 PDF</el-dropdown-item>
              <el-dropdown-item command="word">导出 Word</el-dropdown-item>
              <el-dropdown-item command="excel">导出 Excel</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </section>

    <section class="summary-grid">
      <el-card class="summary-card" shadow="never">
        <p class="summary-label">当前目标</p>
        <strong>{{ currentGoalLabel }}</strong>
        <span>按当前目标调整热量与营养分配</span>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <p class="summary-label">每日热量目标</p>
        <strong>{{ targetCaloriesText }}</strong>
        <span>{{ planModeLabel }}方案会自动按三餐比例拆分</span>
      </el-card>
      <el-card class="summary-card" shadow="never">
        <p class="summary-label">推荐状态</p>
        <strong>{{ recommendationMode }}</strong>
        <span>{{ allRecipesCount }} 道候选食谱可用于生成计划</span>
      </el-card>
    </section>

    <section v-if="mealPlanDays.length" class="plan-section">
      <div class="section-head">
        <div>
          <h3>{{ planModeLabel }}食谱计划</h3>
          <p>系统会复用当前候选食谱并按天排列，方便直接查看 7 天或 30 天的饮食安排。</p>
        </div>
      </div>

      <div class="plan-grid">
        <el-card v-for="day in mealPlanDays" :key="day.index" class="plan-card" shadow="never">
          <template #header>
            <div class="plan-card-head">
              <strong>{{ day.label }}</strong>
              <span>{{ currentGoalLabel }}</span>
            </div>
          </template>

          <div class="plan-day-summary">
            <span>当日总热量</span>
            <strong>{{ calculateDayCalories(day) }}</strong>
          </div>

          <div class="plan-meals">
            <div class="plan-meal">
              <label>早餐</label>
              <strong>{{ day.breakfast?.name || day.breakfast?.recipeName || '--' }}</strong>
            </div>
            <div class="plan-meal">
              <label>午餐</label>
              <strong>{{ day.lunch?.name || day.lunch?.recipeName || '--' }}</strong>
            </div>
            <div class="plan-meal">
              <label>晚餐</label>
              <strong>{{ day.dinner?.name || day.dinner?.recipeName || '--' }}</strong>
            </div>
          </div>

          <div class="plan-card-actions">
            <el-button size="small" type="primary" plain @click="openPlanDayDetail(day)">
              查看当日详情
            </el-button>
          </div>
        </el-card>
      </div>
    </section>

    <div v-if="planMode === 'daily' && recipeGroups.length > 0">
      <section v-for="group in recipeGroups" :key="group.key" class="meal-section">
        <div class="meal-header">
          <div>
            <h3>{{ group.label }}</h3>
            <p>{{ mealDescriptions[group.key] }}</p>
          </div>
          <el-tag type="success" effect="plain">
            建议热量 {{ mealTargetCalories(group.key) }} kcal
          </el-tag>
        </div>

        <div class="recipe-list">
          <el-card
            v-for="(recipe, index) in group.recipes"
            :key="`${group.key}-${recipe.id || index}`"
            class="recipe-card"
            shadow="never"
          >
            <template #header>
              <div class="recipe-header">
                <div>
                  <h4>{{ recipe.name || recipe.recipeName || '未命名食谱' }}</h4>
                  <p>{{ recipe.description || '根据当前目标自动筛选出的推荐结果。' }}</p>
                </div>
                <div class="score-badge">
                  <span>匹配度</span>
                  <strong>{{ formatScore(recipe.matchScore) }}</strong>
                </div>
              </div>
            </template>

            <div class="nutrition-grid">
              <div class="nutrition-item">
                <span>热量</span>
                <strong>{{ formatNumber(recipe.calories ?? recipe.totalCalories, 0) }}</strong>
                <small>kcal</small>
              </div>
              <div class="nutrition-item">
                <span>蛋白质</span>
                <strong>{{ formatNumber(recipe.protein, 1) }}</strong>
                <small>g</small>
              </div>
              <div class="nutrition-item">
                <span>碳水</span>
                <strong>{{ formatNumber(recipe.carbs, 1) }}</strong>
                <small>g</small>
              </div>
              <div class="nutrition-item">
                <span>脂肪</span>
                <strong>{{ formatNumber(recipe.fat, 1) }}</strong>
                <small>g</small>
              </div>
            </div>

            <div class="nutrition-grid nutrition-grid-secondary">
              <div
                v-for="metric in buildHealthMetrics(recipe)"
                :key="`health-${metric.key}`"
                class="nutrition-item nutrition-item-secondary"
              >
                <span>{{ metric.label }}</span>
                <strong>{{ formatNumber(metric.value, metric.digits ?? 1) }}</strong>
                <small>{{ metric.unit }}</small>
              </div>
            </div>

            <div class="tag-row" v-if="normalizeTags(recipe.tags).length">
              <el-tag
                v-for="tag in normalizeTags(recipe.tags)"
                :key="tag"
                size="small"
                effect="plain"
                round
              >
                {{ tag }}
              </el-tag>
            </div>

            <el-alert
              class="reason-box"
              :title="recipe.recommendationReason || buildReason(recipe, group.key)"
              type="success"
              :closable="false"
              show-icon
            />

            <div class="recipe-meta">
              <span>烹饪时间：{{ recipe.cookingTime || '--' }} 分钟</span>
              <span>难度：{{ recipe.difficulty || '家常' }}</span>
            </div>

            <div class="recipe-actions">
              <el-button
                :type="isCollected(recipe) ? 'warning' : 'default'"
                plain
                :loading="collectingRecipeId === Number(recipe.id)"
                @click="toggleCollectRecipe(recipe)"
              >
                {{ isCollected(recipe) ? '已收藏' : '收藏食谱' }}
              </el-button>
              <el-button
                :type="isAlreadyAdded(recipe, group.key) ? 'success' : 'primary'"
                :plain="!isAlreadyAdded(recipe, group.key)"
                :loading="savingRecordKey === `${group.key}-${recipe.id || index}`"
                :disabled="isAlreadyAdded(recipe, group.key)"
                @click="addToDietRecord(recipe, group.key, index)"
              >
                {{ isAlreadyAdded(recipe, group.key) ? '已加入今日记录' : '一键加入饮食记录' }}
              </el-button>
            </div>

            <div class="recipe-section" v-if="normalizeIngredients(recipe.ingredients, recipe).length">
              <h5>食材（左：标准数量；右：推荐数量）</h5>
              <ul class="ingredient-list">
                <li
                  v-for="(ingredient, idx) in normalizeIngredients(recipe.ingredients, recipe)"
                  :key="idx"
                  class="ingredient-item"
                >
                  <span class="ingredient-name">{{ ingredient.name }}</span>
                  <span class="ingredient-standard">{{ ingredient.standardQuantityText || '--' }}</span>
                  <span class="ingredient-arrow">→</span>
                  <span class="ingredient-recommended">{{ ingredient.recommendedQuantityText || '--' }}</span>
                </li>
              </ul>
            </div>

            <div class="recipe-section" v-if="normalizeSteps(recipe.steps).length">
              <h5>制作步骤</h5>
              <ol>
                <li v-for="(step, idx) in normalizeSteps(recipe.steps)" :key="idx">
                  {{ step }}
                </li>
              </ol>
            </div>
          </el-card>
        </div>
      </section>
    </div>

    <el-empty
      v-if="(planMode === 'daily' && recipeGroups.length === 0) || (planMode !== 'daily' && mealPlanDays.length === 0)"
      description="暂无推荐食谱，点击上方按钮生成推荐"
      class="empty-state"
    />

    <el-drawer
      v-model="planDetailVisible"
      :title="selectedPlanDay ? `${selectedPlanDay.label} 详细食谱` : '当日详细食谱'"
      size="70%"
    >
      <div class="plan-detail-content" v-if="planDetailRecipeGroups.length">
        <section v-for="group in planDetailRecipeGroups" :key="`detail-${group.key}`" class="meal-section plan-detail-section">
          <div class="meal-header">
            <div>
              <h3>{{ group.label }}</h3>
              <p>{{ mealDescriptions[group.key] }}</p>
            </div>
            <el-tag type="success" effect="plain">
              建议热量 {{ mealTargetCalories(group.key) }} kcal
            </el-tag>
          </div>

          <div class="recipe-list plan-detail-list">
            <el-card
              v-for="(recipe, index) in group.recipes"
              :key="`detail-${group.key}-${recipe.id || index}`"
              class="recipe-card"
              shadow="never"
            >
              <template #header>
                <div class="recipe-header">
                  <div>
                    <h4>{{ recipe.name || recipe.recipeName || '未命名食谱' }}</h4>
                    <p>{{ recipe.description || '根据当前目标自动筛选出的推荐结果。' }}</p>
                  </div>
                  <div class="score-badge">
                    <span>匹配度</span>
                    <strong>{{ formatScore(recipe.matchScore) }}</strong>
                  </div>
                </div>
              </template>

              <div class="nutrition-grid">
                <div class="nutrition-item">
                  <span>热量</span>
                  <strong>{{ formatNumber(recipe.calories ?? recipe.totalCalories, 0) }}</strong>
                  <small>kcal</small>
                </div>
                <div class="nutrition-item">
                  <span>蛋白质</span>
                  <strong>{{ formatNumber(recipe.protein, 1) }}</strong>
                  <small>g</small>
                </div>
                <div class="nutrition-item">
                  <span>碳水</span>
                  <strong>{{ formatNumber(recipe.carbs, 1) }}</strong>
                  <small>g</small>
                </div>
                <div class="nutrition-item">
                  <span>脂肪</span>
                  <strong>{{ formatNumber(recipe.fat, 1) }}</strong>
                  <small>g</small>
                </div>
              </div>

              <div class="nutrition-grid nutrition-grid-secondary">
                <div
                  v-for="metric in buildHealthMetrics(recipe)"
                  :key="`plan-health-${metric.key}`"
                  class="nutrition-item nutrition-item-secondary"
                >
                  <span>{{ metric.label }}</span>
                  <strong>{{ formatNumber(metric.value, metric.digits ?? 1) }}</strong>
                  <small>{{ metric.unit }}</small>
                </div>
              </div>

              <div class="tag-row" v-if="normalizeTags(recipe.tags).length">
                <el-tag
                  v-for="tag in normalizeTags(recipe.tags)"
                  :key="tag"
                  size="small"
                  effect="plain"
                  round
                >
                  {{ tag }}
                </el-tag>
              </div>

              <el-alert
                class="reason-box"
                :title="recipe.recommendationReason || buildReason(recipe, group.key)"
                type="success"
                :closable="false"
                show-icon
              />

              <div class="recipe-meta">
                <span>烹饪时间：{{ recipe.cookingTime || '--' }} 分钟</span>
                <span>难度：{{ recipe.difficulty || '家常' }}</span>
              </div>

              <div class="recipe-actions">
                <el-button
                  :type="isCollected(recipe) ? 'warning' : 'default'"
                  plain
                  :loading="collectingRecipeId === Number(recipe.id)"
                  @click="toggleCollectRecipe(recipe)"
                >
                  {{ isCollected(recipe) ? '已收藏' : '收藏食谱' }}
                </el-button>
                <el-button
                  :type="isAlreadyAdded(recipe, group.key) ? 'success' : 'primary'"
                  :plain="!isAlreadyAdded(recipe, group.key)"
                  :loading="savingRecordKey === `${group.key}-${recipe.id || index}`"
                  :disabled="isAlreadyAdded(recipe, group.key)"
                  @click="addToDietRecord(recipe, group.key, index)"
                >
                  {{ isAlreadyAdded(recipe, group.key) ? '已加入今日记录' : '一键加入饮食记录' }}
                </el-button>
              </div>

              <div class="recipe-section" v-if="normalizeIngredients(recipe.ingredients, recipe).length">
                <h5>食材（左：标准数量；右：推荐数量）</h5>
                <ul class="ingredient-list">
                  <li
                    v-for="(ingredient, idx) in normalizeIngredients(recipe.ingredients, recipe)"
                    :key="idx"
                    class="ingredient-item"
                  >
                    <span class="ingredient-name">{{ ingredient.name }}</span>
                    <span class="ingredient-standard">{{ ingredient.standardQuantityText || '--' }}</span>
                    <span class="ingredient-arrow">→</span>
                    <span class="ingredient-recommended">{{ ingredient.recommendedQuantityText || '--' }}</span>
                  </li>
                </ul>
              </div>

              <div class="recipe-section" v-if="normalizeSteps(recipe.steps).length">
                <h5>制作步骤</h5>
                <ol>
                  <li v-for="(step, idx) in normalizeSteps(recipe.steps)" :key="idx">
                    {{ step }}
                  </li>
                </ol>
              </div>
            </el-card>
          </div>
        </section>
      </div>

      <el-empty v-else description="当前日期暂无食谱详情" />
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { ArrowDown } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import recipeApi from '../api/recipe';
import dietRecordApi from '../api/dietRecord';
import { useUserStore } from '../stores/user';
import {
  exportPlanToExcel,
  exportPlanToPdf,
  exportPlanToWord,
  exportRecipesToExcel,
  exportRecipesToPdf,
  exportRecipesToWord
} from '../utils/recipeExport';

const userStore = useUserStore();
const loading = ref(false);
const savingRecordKey = ref('');
const collectingRecipeId = ref(null);
const existingRecordKeys = ref(new Set());
const collectedRecipeIds = ref(new Set());
const batchIndex = ref(0);
const batchSize = 2;
const dailyCandidateCount = 6;
const planMode = ref('daily');
const planDetailVisible = ref(false);
const selectedPlanDay = ref(null);
const createEmptyRecipeGroups = () => ({
  breakfast: [],
  lunch: [],
  dinner: []
});

const modeRecommendationCache = ref({
  daily: {
    groups: createEmptyRecipeGroups(),
    batchIndex: 0
  },
  weekly: {
    groups: createEmptyRecipeGroups(),
    batchIndex: 0
  },
  monthly: {
    groups: createEmptyRecipeGroups(),
    batchIndex: 0
  }
});

const allRecipes = ref(createEmptyRecipeGroups());
const visibleRecipes = ref(createEmptyRecipeGroups());

const planOptions = [
  { label: '每日', value: 'daily' },
  { label: '7 天', value: 'weekly' },
  { label: '30 天', value: 'monthly' }
];

const mealLabels = {
  breakfast: '早餐推荐',
  lunch: '午餐推荐',
  dinner: '晚餐推荐'
};

const mealDescriptions = {
  breakfast: '早餐更关注轻负担、晨间饱腹感和上午能量补充。',
  lunch: '午餐更强调能量稳定、蛋白质补充和整体营养均衡。',
  dinner: '晚餐更重视清淡、热量控制和夜间消化体验。'
};

const goalLabels = {
  fat_loss: '减肥减脂',
  muscle_toning: '增肌塑形',
  weight_maintenance: '维持体重',
  healthy_weight_gain: '健康增重',
  blood_sugar_control: '控糖饮食',
  lipid_control: '控脂降脂',
  low_sodium: '控压低盐',
  pregnancy_nutrition: '孕妇营养',
  child_growth: '儿童成长',
  senior_wellness: '老年养生'
};

const allRecipesCount = computed(
  () =>
    (allRecipes.value.breakfast?.length || 0) +
    (allRecipes.value.lunch?.length || 0) +
    (allRecipes.value.dinner?.length || 0)
);

const canRotateRecommendations = computed(() => {
  if (planMode.value !== 'daily') {
    return false;
  }

  return Object.values(allRecipes.value).some((items) => Array.isArray(items) && items.length > batchSize);
});

const recipeGroups = computed(() =>
  Object.entries(visibleRecipes.value)
    .map(([key, items]) => ({
      key,
      label: mealLabels[key] || key,
      recipes: Array.isArray(items) ? items : []
    }))
    .filter((group) => group.recipes.length > 0)
);

const currentGoalLabel = computed(() => goalLabels[userStore.dietGoal?.goalType] || '均衡饮食');

const targetCaloriesText = computed(() => {
  const value = Number(userStore.dietGoal?.targetCalories || 0);
  return value > 0 ? `${Math.round(value)} kcal` : '未设置';
});

const recommendationMode = computed(() =>
  allRecipesCount.value > 0 ? '已生成个性化结果' : '等待生成'
);

const planModeLabel = computed(() => {
  if (planMode.value === 'weekly') return '7 天';
  if (planMode.value === 'monthly') return '30 天';
  return '每日';
});

const planDayCount = computed(() => {
  if (planMode.value === 'weekly') return 7;
  if (planMode.value === 'monthly') return 30;
  return 1;
});

const mealPlanDays = computed(() => {
  if (planMode.value === 'daily') {
    return [];
  }

  const result = [];
  const breakfasts = allRecipes.value.breakfast || [];
  const lunches = allRecipes.value.lunch || [];
  const dinners = allRecipes.value.dinner || [];

  for (let index = 0; index < planDayCount.value; index += 1) {
    result.push({
      index: index + 1,
      label: `第 ${index + 1} 天`,
      breakfast: breakfasts.length ? breakfasts[index % breakfasts.length] : null,
      lunch: lunches.length ? lunches[index % lunches.length] : null,
      dinner: dinners.length ? dinners[index % dinners.length] : null
    });
  }

  return result;
});

const calculateRecipeCalories = (recipe) => {
  const value = Number(recipe?.calories ?? recipe?.totalCalories ?? 0);
  return Number.isFinite(value) ? value : 0;
};

const calculateDayCalories = (day) => {
  const total =
    calculateRecipeCalories(day?.breakfast) +
    calculateRecipeCalories(day?.lunch) +
    calculateRecipeCalories(day?.dinner);

  if (total <= 0) return '--';
  return `${Math.round(total)} kcal`;
};

const openPlanDayDetail = (day) => {
  selectedPlanDay.value = day || null;
  planDetailVisible.value = true;
};

const planDetailRecipeGroups = computed(() => {
  const day = selectedPlanDay.value;
  if (!day) return [];

  return [
    { key: 'breakfast', recipe: day.breakfast },
    { key: 'lunch', recipe: day.lunch },
    { key: 'dinner', recipe: day.dinner }
  ]
    .filter((item) => item.recipe)
    .map((item) => ({
      key: item.key,
      label: mealLabels[item.key] || item.key,
      recipes: [item.recipe]
    }));
});
const visibleFlattenedRecipes = computed(() =>
  ['breakfast', 'lunch', 'dinner'].flatMap((mealType) =>
    (visibleRecipes.value[mealType] || []).map((recipe) => ({
      ...recipe,
      mealType
    }))
  )
);

const flattenedRecipes = computed(() =>
  ['breakfast', 'lunch', 'dinner'].flatMap((mealType) =>
    (allRecipes.value[mealType] || []).map((recipe) => ({
      ...recipe,
      mealType
    }))
  )
);

const formatNumber = (value, digits = 1) => {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : '--';
};

const formatScore = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number)} 分` : '--';
};

const normalizeTags = (tags) => (Array.isArray(tags) ? tags.filter(Boolean) : []);

const buildHealthMetrics = (recipe) => {
  const goalType = userStore.dietGoal?.goalType || '';
  const metrics = [];

  if (goalType === 'blood_sugar_control') {
    metrics.push(
      { key: 'sugar', label: '含糖量', value: recipe?.sugar, unit: 'g', digits: 1 },
      { key: 'gi', label: 'GI', value: recipe?.gi, unit: '', digits: 0 },
      { key: 'fiber', label: '膳食纤维', value: recipe?.fiber, unit: 'g', digits: 1 }
    );
  } else if (goalType === 'low_sodium') {
    metrics.push(
      { key: 'sodium', label: '钠', value: recipe?.sodium, unit: 'mg', digits: 0 },
      { key: 'fiber', label: '膳食纤维', value: recipe?.fiber, unit: 'g', digits: 1 },
      { key: 'sugar', label: '含糖量', value: recipe?.sugar, unit: 'g', digits: 1 }
    );
  } else {
    metrics.push(
      { key: 'fiber', label: '膳食纤维', value: recipe?.fiber, unit: 'g', digits: 1 },
      { key: 'sugar', label: '含糖量', value: recipe?.sugar, unit: 'g', digits: 1 },
      { key: 'sodium', label: '钠', value: recipe?.sodium, unit: 'mg', digits: 0 }
    );
    if (Number(recipe?.gi) > 0) {
      metrics.push({ key: 'gi', label: 'GI', value: recipe?.gi, unit: '', digits: 0 });
    }
  }

  return metrics.filter((metric) => Number.isFinite(Number(metric.value)) && Number(metric.value) > 0);
};

const formatIngredientAmount = (quantity, unit) => {
  if (quantity === null || quantity === undefined || quantity === '') return '';

  const unitText = String(unit || '').trim();
  const rawText = String(quantity).trim();
  const normalizedRaw = rawText.toLowerCase();
  const normalizedUnit = unitText.toLowerCase();

  if (normalizedUnit && normalizedRaw.endsWith(normalizedUnit)) {
    return rawText;
  }

  const number = Number(quantity);
  if (!Number.isFinite(number)) {
    return `${rawText}${unitText}`.trim();
  }

  const digits = Number.isInteger(number) ? 0 : 1;
  return `${number.toFixed(digits)}${unitText}`.trim();
};

const normalizeIngredients = (ingredients, recipe = {}) => {
  if (!Array.isArray(ingredients)) return [];
  const servingFactor = Number(recipe?.servingFactor ?? 1);
  const validServingFactor = Number.isFinite(servingFactor) && servingFactor > 0 ? servingFactor : 1;

  return ingredients.map((ingredient) => {
    if (typeof ingredient === 'string') {
      return {
        name: ingredient,
        standardQuantityText: '',
        recommendedQuantityText: ''
      };
    }

    const name = ingredient.name || ingredient.ingredientName || '未命名食材';
    const standardQuantitySource =
      ingredient.standardQuantity ?? ingredient.standardQuantityValue ?? ingredient.quantity;

    const hasRecommendedQuantity =
      ingredient.recommendedQuantity !== undefined &&
      ingredient.recommendedQuantity !== null &&
      ingredient.recommendedQuantity !== '';
    const hasRecommendedQuantityValue =
      ingredient.recommendedQuantityValue !== undefined &&
      ingredient.recommendedQuantityValue !== null &&
      ingredient.recommendedQuantityValue !== '';

    let recommendedQuantitySource;
    if (hasRecommendedQuantity) {
      recommendedQuantitySource = ingredient.recommendedQuantity;
    } else if (hasRecommendedQuantityValue) {
      recommendedQuantitySource = ingredient.recommendedQuantityValue;
    } else {
      const baseValue = Number(ingredient.standardQuantityValue ?? ingredient.quantityValue);
      if (Number.isFinite(baseValue) && baseValue > 0) {
        recommendedQuantitySource = Number((baseValue * validServingFactor).toFixed(1));
      } else {
        recommendedQuantitySource = ingredient.quantityValue ?? ingredient.quantity;
      }
    }

    const standardQuantityText = formatIngredientAmount(
      standardQuantitySource,
      ingredient.unit
    );
    const recommendedQuantityText = formatIngredientAmount(
      recommendedQuantitySource,
      ingredient.unit
    );

    return {
      name,
      standardQuantityText,
      recommendedQuantityText
    };
  });
};

const buildIngredientsSummary = (recipe) => {
  const ingredients = normalizeIngredients(recipe?.ingredients, recipe);
  if (!ingredients.length) return '--';

  return ingredients
    .slice(0, 6)
    .map((ingredient) => {
      const quantityText = ingredient.recommendedQuantityText || ingredient.standardQuantityText || '';
      return quantityText ? `${ingredient.name} ${quantityText}` : ingredient.name;
    })
    .join('、');
};

const normalizeSteps = (steps) => (Array.isArray(steps) ? steps : []);

const normalizeRecordName = (name) => String(name || '').trim().toLowerCase();

const createRecordKey = (mealType, foodName) => `${mealType}::${normalizeRecordName(foodName)}`;

const isAlreadyAdded = (recipe, mealType) =>
  existingRecordKeys.value.has(createRecordKey(mealType, recipe.name || recipe.recipeName));

const isCollected = (recipe) => collectedRecipeIds.value.has(Number(recipe.id));

const mealTargetCalories = (mealType) => {
  const totalCalories = Number(userStore.dietGoal?.targetCalories || 0);
  if (!totalCalories) return '--';
  const ratio = mealType === 'lunch' ? 0.4 : 0.3;
  return Math.round(totalCalories * ratio);
};

const normalizeRecipeGroups = (groups) => ({
  breakfast: Array.isArray(groups?.breakfast) ? groups.breakfast : [],
  lunch: Array.isArray(groups?.lunch) ? groups.lunch : [],
  dinner: Array.isArray(groups?.dinner) ? groups.dinner : []
});

const clearRecommendationsView = () => {
  allRecipes.value = createEmptyRecipeGroups();
  visibleRecipes.value = createEmptyRecipeGroups();
  batchIndex.value = 0;
};

const hasRecipeGroups = (groups) =>
  Object.values(normalizeRecipeGroups(groups)).some((items) => Array.isArray(items) && items.length > 0);

const normalizeRecommendationCache = (payload) => {
  const emptyCache = {
    daily: {
      groups: createEmptyRecipeGroups(),
      batchIndex: 0
    },
    weekly: {
      groups: createEmptyRecipeGroups(),
      batchIndex: 0
    },
    monthly: {
      groups: createEmptyRecipeGroups(),
      batchIndex: 0
    }
  };

  if (!payload) {
    return emptyCache;
  }

  if (payload.modes && typeof payload.modes === 'object') {
    for (const mode of ['daily', 'weekly', 'monthly']) {
      const source = payload.modes[mode];
      emptyCache[mode] = {
        groups: normalizeRecipeGroups(source?.groups),
        batchIndex: Number.isFinite(source?.batchIndex) ? source.batchIndex : 0
      };
    }
    return emptyCache;
  }

  if (payload.groups && payload.planMode) {
    emptyCache[payload.planMode] = {
      groups: normalizeRecipeGroups(payload.groups),
      batchIndex: Number.isFinite(payload.batchIndex) ? payload.batchIndex : 0
    };
  }

  return emptyCache;
};

const buildVisibleRecipes = () => {
  const nextVisible = {};
  for (const key of Object.keys(allRecipes.value)) {
    const list = Array.isArray(allRecipes.value[key]) ? allRecipes.value[key] : [];
    if (list.length <= batchSize) {
      nextVisible[key] = list;
      continue;
    }

    const start = (batchIndex.value * batchSize) % list.length;
    nextVisible[key] = [...list.slice(start, start + batchSize)];
    if (nextVisible[key].length < batchSize) {
      nextVisible[key].push(...list.slice(0, batchSize - nextVisible[key].length));
    }
  }
  visibleRecipes.value = nextVisible;
};

const applyRecommendations = (groups, index = 0) => {
  allRecipes.value = normalizeRecipeGroups(groups);
  batchIndex.value = Number.isFinite(index) ? index : 0;
  buildVisibleRecipes();
};

const loadRecommendationsForMode = (mode) => {
  const cached = modeRecommendationCache.value[mode];
  if (!cached || !hasRecipeGroups(cached.groups)) {
    clearRecommendationsView();
    return;
  }

  applyRecommendations(cached.groups, cached.batchIndex || 0);
};

const persistRecommendations = () => {
  userStore.setRecipeRecommendations({
    modes: {
      daily: {
        groups: normalizeRecipeGroups(modeRecommendationCache.value.daily?.groups),
        batchIndex: modeRecommendationCache.value.daily?.batchIndex || 0
      },
      weekly: {
        groups: normalizeRecipeGroups(modeRecommendationCache.value.weekly?.groups),
        batchIndex: modeRecommendationCache.value.weekly?.batchIndex || 0
      },
      monthly: {
        groups: normalizeRecipeGroups(modeRecommendationCache.value.monthly?.groups),
        batchIndex: modeRecommendationCache.value.monthly?.batchIndex || 0
      }
    },
    planMode: planMode.value,
    updatedAt: new Date().toISOString()
  });
};

const rotateRecommendations = () => {
  if (!canRotateRecommendations.value) {
    ElMessage.info('当前推荐数量不足，暂时没有更多可切换的方案');
    return;
  }

  batchIndex.value += 1;
  buildVisibleRecipes();
  if (allRecipesCount.value > 0) {
    modeRecommendationCache.value[planMode.value] = {
      groups: normalizeRecipeGroups(allRecipes.value),
      batchIndex: batchIndex.value
    };
    persistRecommendations();
  }
};

const buildReason = (recipe, mealType) => {
  const mealReasonMap = {
    breakfast: '早餐优先选择能量适中、蛋白质充足的食谱，帮助维持上午状态。',
    lunch: '午餐需要兼顾饱腹感和营养密度，适合作为一天中的主要能量来源。',
    dinner: '晚餐推荐相对清淡、易消化的搭配，避免夜间摄入过重。'
  };

  const calories = Number(recipe.calories ?? recipe.totalCalories ?? 0);
  const calorieReason = calories > 0
    ? ` 当前约 ${Math.round(calories)} kcal，便于控制每日总热量。`
    : ' 当前食谱已按你的饮食目标进行匹配。';
  return `${mealReasonMap[mealType] || '该食谱与当前饮食目标匹配。'}${calorieReason}`;
};

const buildRecordDetailsFromRecipe = (recipe) => {
  const ingredients = Array.isArray(recipe.ingredients) ? recipe.ingredients : [];
  const details = ingredients
    .filter((ingredient) => ingredient && typeof ingredient === 'object')
    .map((ingredient) => ({
      ingredientId: ingredient.ingredientId ?? ingredient.id ?? null,
      recipeId: recipe.id ?? null,
      foodName: ingredient.name || ingredient.ingredientName || '未命名食材',
      amount: Number(ingredient.quantityValue ?? ingredient.quantity ?? 1) || 1,
      unit: ingredient.unit || 'g',
      calories: Number(ingredient.calories ?? 0),
      protein: Number(ingredient.protein ?? 0),
      carbs: Number(ingredient.carbs ?? 0),
      fat: Number(ingredient.fat ?? 0),
      fiber: Number(ingredient.fiber ?? 0),
      sugar: Number(ingredient.sugar ?? 0),
      sodium: Number(ingredient.sodium ?? 0),
      gi: Number(ingredient.gi ?? 0)
    }));

  if (details.length) {
    return details;
  }

  return [
    {
      recipeId: recipe.id ?? null,
      foodName: recipe.name || recipe.recipeName || '未命名食谱',
      amount: 1,
      unit: '份',
      calories: Number(recipe.calories ?? recipe.totalCalories ?? 0),
      protein: Number(recipe.protein ?? 0),
      carbs: Number(recipe.carbs ?? 0),
      fat: Number(recipe.fat ?? 0),
      fiber: Number(recipe.fiber ?? 0),
      sugar: Number(recipe.sugar ?? 0),
      sodium: Number(recipe.sodium ?? 0),
      gi: Number(recipe.gi ?? 0)
    }
  ];
};
const hasMeaningfulNutrition = (details) =>
  Array.isArray(details) &&
  details.some((detail) =>
    Number(detail?.calories || 0) > 0 ||
    Number(detail?.protein || 0) > 0 ||
    Number(detail?.carbs || 0) > 0 ||
    Number(detail?.fat || 0) > 0
  );

const loadAccurateRecordDetails = async (recipe) => {
  const fallbackDetails = buildRecordDetailsFromRecipe(recipe);
  if (!recipe?.id || hasMeaningfulNutrition(fallbackDetails)) {
    return fallbackDetails;
  }

  try {
    const response = await recipeApi.getRecipeDetail(recipe.id);
    if (response.code === 200) {
      const detailData = response.data || {};
      const accurateRecipe = {
        ...recipe,
        ingredients: Array.isArray(detailData.ingredients) ? detailData.ingredients : recipe.ingredients
      };
      const accurateDetails = buildRecordDetailsFromRecipe(accurateRecipe);
      if (hasMeaningfulNutrition(accurateDetails)) {
        return accurateDetails;
      }
    }
  } catch (error) {
    console.error('加载数据失败', error);
  }

  return fallbackDetails;
};

const addToDietRecord = async (recipe, mealType, index) => {
  if (isAlreadyAdded(recipe, mealType)) {
    ElMessage.warning('今天已添加过这道食谱，请不要重复加入饮食记录');
    return;
  }

  const actionKey = `${mealType}-${recipe.id || index}`;
  savingRecordKey.value = actionKey;
  try {
    const details = await loadAccurateRecordDetails(recipe);
    const response = await dietRecordApi.submitRecord({
      date: new Date().toISOString().slice(0, 10),
      mealType,
      notes: `来自推荐食谱：${recipe.name || recipe.recipeName || '未命名食谱'}`,
      details
    });

    if (response.code === 200) {
      const nextKeys = new Set(existingRecordKeys.value);
      nextKeys.add(createRecordKey(mealType, recipe.name || recipe.recipeName));
      existingRecordKeys.value = nextKeys;
      ElMessage.success('已加入今日饮食记录');
      return;
    }

    ElMessage.error(response.message || '加入饮食记录失败');
  } catch (error) {
    ElMessage.error(error.message || '加入饮食记录失败，请稍后重试');
  } finally {
    savingRecordKey.value = '';
  }
};
const loadCollectedRecipes = async () => {
  try {
    const response = await recipeApi.getCollectedRecipes();
    if (response.code === 200 && Array.isArray(response.data)) {
      collectedRecipeIds.value = new Set(
        response.data.map((item) => Number(item.id)).filter((item) => Number.isFinite(item))
      );
    }
  } catch (error) {
    console.error('加载数据失败', error);
  }
};

const toggleCollectRecipe = async (recipe) => {
  const recipeId = Number(recipe.id);
  if (!Number.isFinite(recipeId)) {
    ElMessage.warning('当前食谱缺少有效编号，暂不支持收藏');
    return;
  }

  collectingRecipeId.value = recipeId;
  try {
    const response = isCollected(recipe)
      ? await recipeApi.cancelCollectRecipe(recipeId)
      : await recipeApi.collectRecipe(recipeId);

    if (response.code === 200) {
      const next = new Set(collectedRecipeIds.value);
      if (response.data?.collected) {
        next.add(recipeId);
      } else {
        next.delete(recipeId);
      }
      collectedRecipeIds.value = next;
      ElMessage.success(response.data?.collected ? '已收藏食谱' : '已取消收藏');
      return;
    }

    ElMessage.error(response.message || '收藏状态更新失败');
  } catch (error) {
    ElMessage.error(error.message || '收藏状态更新失败，请稍后重试');
  } finally {
    collectingRecipeId.value = null;
  }
};
const loadTodayRecordKeys = async () => {
  if (!userStore.userId) return;

  try {
    const today = new Date().toISOString().slice(0, 10);
    const response = await dietRecordApi.getDietRecords(today, today);
    if (response.code !== 200) return;

    const keys = new Set();
    const records = Array.isArray(response.data) ? response.data : [];
    records.forEach((record) => {
      const mealType = record.mealType || '';
      const details = Array.isArray(record.details) ? record.details : [];
      details.forEach((detail) => {
        keys.add(createRecordKey(mealType, detail.foodName));
      });
      if (!details.length && record.foodName) {
        keys.add(createRecordKey(mealType, record.foodName));
      }
    });
    existingRecordKeys.value = keys;
  } catch (error) {
    console.error('加载数据失败', error);
  }
};

const exportRows = () =>
  visibleFlattenedRecipes.value.map((recipe) => ({
    name: recipe.name || recipe.recipeName || '未命名食谱',
    category: mealLabels[recipe.mealType] || recipe.mealType,
    calories: formatNumber(recipe.calories ?? recipe.totalCalories, 0),
    protein: formatNumber(recipe.protein, 1),
    carbs: formatNumber(recipe.carbs, 1),
    fat: formatNumber(recipe.fat, 1),
    fiber: formatNumber(recipe.fiber, 1),
    sugar: formatNumber(recipe.sugar, 1),
    sodium: formatNumber(recipe.sodium, 0),
    gi: formatNumber(recipe.gi, 0),
    cookingTime: recipe.cookingTime || '--',
    difficulty: recipe.difficulty || '普通'
  }));

const exportDetailedRows = () =>
  visibleFlattenedRecipes.value.map((recipe) => ({
    name: recipe.name || recipe.recipeName || '未命名食谱',
    category: mealLabels[recipe.mealType] || recipe.mealType,
    mealLabel: mealLabels[recipe.mealType] || recipe.mealType,
    description: recipe.description || '',
    score: formatScore(recipe.matchScore),
    calories: formatNumber(recipe.calories ?? recipe.totalCalories, 0),
    protein: formatNumber(recipe.protein, 1),
    carbs: formatNumber(recipe.carbs, 1),
    fat: formatNumber(recipe.fat, 1),
    fiber: formatNumber(recipe.fiber, 1),
    sugar: formatNumber(recipe.sugar, 1),
    sodium: formatNumber(recipe.sodium, 0),
    gi: formatNumber(recipe.gi, 0),
    cookingTime: recipe.cookingTime || '--',
    difficulty: recipe.difficulty || '普通',
    reason: recipe.recommendationReason || buildReason(recipe, recipe.mealType),
    ingredientsSummary: buildIngredientsSummary(recipe)
  }));

const handleExportCommand = (command) => {
  if (planMode.value === 'daily') {
    const rows = exportDetailedRows();
    const title = `${currentGoalLabel.value}每日推荐食谱`;
    if (command === 'pdf') {
      exportRecipesToPdf(title, rows);
    } else if (command === 'word') {
      exportRecipesToWord(`${title}.doc`, title, rows);
    } else if (command === 'excel') {
      exportRecipesToExcel(`${title}.xls`, title, rows);
    }
    return;
  }

  const title = `${currentGoalLabel.value}${planModeLabel.value}推荐食谱计划`;
  if (command === 'pdf') {
    exportPlanToPdf(title, mealPlanDays.value);
  } else if (command === 'word') {
    exportPlanToWord(`${title}.doc`, title, mealPlanDays.value);
  } else if (command === 'excel') {
    exportPlanToExcel(`${title}.xls`, title, mealPlanDays.value);
  }
};
const getRecommendations = async () => {
  if (!userStore.userId) {
    ElMessage.error('请先登录后再获取推荐食谱');
    return;
  }
  if (!userStore.hasHealthInfo) {
    ElMessage.error('请先完善健康信息，再生成推荐食谱');
    return;
  }
  if (!userStore.hasDietGoal) {
    ElMessage.error('请先设置饮食目标，再生成推荐食谱');
    return;
  }

  loading.value = true;
  try {
    const count = planMode.value === 'monthly' ? 30 : planMode.value === 'weekly' ? 7 : dailyCandidateCount;
    const response = await recipeApi.getRecommendations({
      breakfastCount: count,
      lunchCount: count,
      dinnerCount: count
    });
    if (response.code !== 200) {
      ElMessage.error(response.message || '获取推荐食谱失败');
      return;
    }

    const data = response.data || {};
    modeRecommendationCache.value[planMode.value] = {
      groups: normalizeRecipeGroups(data),
      batchIndex: 0
    };
    applyRecommendations(data, 0);
    persistRecommendations();
    ElMessage.success('推荐食谱已更新');
  } catch (error) {
    ElMessage.error(error.message || '获取推荐食谱失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};
watch(planMode, (mode) => {
  loadRecommendationsForMode(mode);
  persistRecommendations();
});

onMounted(() => {
  if (userStore.recipeRecommendations) {
    modeRecommendationCache.value = normalizeRecommendationCache(userStore.recipeRecommendations);
    if (userStore.recipeRecommendations.planMode) {
      planMode.value = userStore.recipeRecommendations.planMode;
    }
    loadRecommendationsForMode(planMode.value);
  }
  loadTodayRecordKeys();
  loadCollectedRecipes();
});
</script>

<style scoped>
.recipe-recommend-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 28px;
  border-radius: 24px;
  background: linear-gradient(135deg, #f5fbf6 0%, #edf8f0 100%);
  border: 1px solid #d9eadf;
}

.eyebrow {
  margin: 0 0 10px;
  color: #4a8f63;
  font-size: 13px;
  letter-spacing: 0.08em;
}

.hero-card h2 {
  margin: 0 0 12px;
  color: #203428;
}

.hero-text {
  margin: 0;
  max-width: 720px;
  line-height: 1.7;
  color: #5c6e62;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-start;
  justify-content: flex-end;
}

.mode-switch {
  min-width: 210px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.summary-card {
  border-radius: 20px;
}

.summary-label {
  margin: 0 0 10px;
  color: #7d8f84;
  font-size: 13px;
}

.summary-card strong {
  display: block;
  margin-bottom: 8px;
  color: #21352b;
  font-size: 24px;
}

.summary-card span {
  color: #708277;
  font-size: 14px;
}

.plan-section,
.meal-section {
  padding: 24px;
  border-radius: 22px;
  background: #fff;
  box-shadow: 0 12px 36px rgba(28, 54, 37, 0.08);
}

.section-head,
.meal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.section-head h3,
.meal-header h3 {
  margin: 0 0 8px;
  color: #21352b;
}

.section-head p,
.meal-header p {
  margin: 0;
  color: #78907f;
}

.plan-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.plan-card {
  border-radius: 18px;
}

.plan-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #1c3528;
}

.plan-card-head span {
  color: #6f8575;
  font-size: 13px;
}

.plan-meals {
  display: grid;
  gap: 12px;
}

.plan-meal {
  padding: 12px 14px;
  border-radius: 14px;
  background: #f7fbf8;
}

.plan-meal label {
  display: block;
  margin-bottom: 6px;
  color: #7d8f84;
  font-size: 13px;
}

.plan-day-summary {
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 12px;
  background: #f2f8f4;
}

.plan-day-summary span {
  color: #6f8575;
  font-size: 13px;
}

.plan-day-summary strong {
  color: #245f40;
}

.plan-card-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.plan-detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.plan-detail-section {
  padding: 20px;
}

.plan-detail-list {
  margin-top: 16px;
}

.recipe-list {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  justify-content: center;
}

.recipe-card {
  border-radius: 20px;
}

.recipe-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.recipe-header h4 {
  margin: 0 0 8px;
  color: #21352b;
}

.recipe-header p {
  margin: 0;
  color: #7d8f84;
  line-height: 1.6;
}

.score-badge {
  min-width: 88px;
  padding: 10px 12px;
  border-radius: 16px;
  background: #eef8f0;
  text-align: center;
}

.score-badge span {
  display: block;
  color: #6f8575;
  font-size: 12px;
}

.score-badge strong {
  color: #2a7a49;
  font-size: 22px;
}

.nutrition-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin: 14px 0 10px;
}

.nutrition-grid-secondary {
  grid-template-columns: repeat(auto-fit, minmax(88px, 1fr));
  margin-top: -4px;
}

.nutrition-item {
  padding: 12px 8px;
  border-radius: 16px;
  background: #f7fbf8;
  text-align: center;
}

.nutrition-item-secondary {
  background: #eef6f0;
}

.nutrition-item span,
.nutrition-item small {
  display: block;
  color: #7f9186;
}

.nutrition-item strong {
  display: block;
  margin: 4px 0 2px;
  color: #22382c;
  font-size: 18px;
}

.serving-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  color: #5f7468;
  font-size: 14px;
}

.serving-recommended {
  color: #2a7a49;
  font-weight: 600;
}

.serving-note {
  margin: 0 0 12px;
  color: #6f8575;
  font-size: 13px;
  line-height: 1.5;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.recipe-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  color: #6f8575;
  font-size: 14px;
  margin-bottom: 14px;
}

.recipe-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.recipe-section h5 {
  margin: 0 0 10px;
  color: #2a4133;
}

.ingredient-list {
  list-style: none;
  padding-left: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ingredient-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto auto;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.ingredient-name {
  color: #2a4133;
}

.ingredient-standard {
  color: #5a6d61;
}

.ingredient-arrow {
  color: #8aa092;
}

.ingredient-recommended {
  color: #2a7a49;
  font-weight: 600;
}

.recipe-section ul,
.recipe-section ol {
  margin: 0;
  padding-left: 20px;
  color: #5a6d61;
  line-height: 1.8;
}

.empty-state {
  padding: 40px 0 20px;
  background: #fff;
  border-radius: 22px;
}

@media (max-width: 900px) {
  .hero-card,
  .section-head,
  .meal-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .plan-detail-section {
    padding: 16px;
  }
}

@media (max-width: 640px) {
  .nutrition-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-actions {
    width: 100%;
  }

  .ingredient-item {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .ingredient-arrow {
    display: none;
  }
}
</style>
