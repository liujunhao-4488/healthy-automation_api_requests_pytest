<template>
  <div class="custom-recipe-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">我的食谱</h1>
        <p class="page-subtitle">管理自己创建的食谱，并支持按 PDF、Word、Excel 导出。</p>
      </div>
      <div class="header-actions">
        <el-dropdown trigger="click" @command="handleExportCommand" :disabled="!myRecipes.length">
          <el-button>导出我的食谱</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="pdf">导出 PDF</el-dropdown-item>
              <el-dropdown-item command="word">导出 Word</el-dropdown-item>
              <el-dropdown-item command="excel">导出 Excel</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" class="create-button" @click="openCreateDialog">创建食谱</el-button>
      </div>
    </div>

    <div class="recipe-panel">
      <div class="panel-header">
        <div>
          <h2>食谱列表</h2>
          <p>查看、分析和维护自己创建的食谱。</p>
        </div>
        <el-tag type="success" effect="plain">共 {{ myRecipes.length }} 个</el-tag>
      </div>

      <el-empty
        v-if="!myRecipes.length"
        description="你还没有创建食谱，点击右上角按钮开始创建吧"
      />

      <el-table
        v-else
        :data="myRecipes"
        style="width: 100%"
        class="recipe-table"
      >
        <el-table-column prop="name" label="食谱名称" min-width="180" />
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            {{ row.category || '自定义食谱' }}
          </template>
        </el-table-column>
        <el-table-column prop="cookingTime" label="烹饪时间" width="120">
          <template #default="{ row }">
            {{ row.cookingTime || '--' }} 分钟
          </template>
        </el-table-column>
        <el-table-column prop="difficulty" label="难度" width="110">
          <template #default="{ row }">
            {{ row.difficulty || '--' }}
          </template>
        </el-table-column>
        <el-table-column prop="totalCalories" label="热量" width="120">
          <template #default="{ row }">
            {{ formatValue(row.totalCalories, 'kcal') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="340" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button link type="primary" @click="viewRecipe(row.id)">查看</el-button>
              <el-button link type="success" @click="analyzeRecipe(row.id)">分析</el-button>
              <el-button
                link
                type="warning"
                :loading="savingRecordKey === row.id"
                :disabled="!!savingRecordKey && savingRecordKey !== row.id"
                @click="openMealTypeDialog(row)"
              >
                加入记录
              </el-button>
              <el-button link type="danger" @click="deleteRecipe(row.id)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="createDialogVisible"
      title="创建食谱"
      width="980px"
      destroy-on-close
      class="recipe-dialog"
    >
      <el-form
        ref="recipeFormRef"
        :model="recipeForm"
        :rules="rules"
        label-width="96px"
      >
        <el-form-item label="食谱名称" prop="name">
          <el-input v-model="recipeForm.name" placeholder="请输入食谱名称" />
        </el-form-item>

        <el-form-item label="食谱描述" prop="description">
          <el-input
            v-model="recipeForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入食谱描述"
          />
        </el-form-item>

        <div class="form-grid">
          <el-form-item label="烹饪时间" prop="cookingTime">
            <el-input-number
              v-model="recipeForm.cookingTime"
              :min="1"
              :max="300"
              controls-position="right"
            />
            <span class="inline-unit">分钟</span>
          </el-form-item>

          <el-form-item label="难度" prop="difficulty">
            <el-select v-model="recipeForm.difficulty" placeholder="请选择难度">
              <el-option label="简单" value="简单" />
              <el-option label="中等" value="中等" />
              <el-option label="困难" value="困难" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="烹饪步骤" prop="instructions">
          <el-input
            v-model="recipeForm.instructions"
            type="textarea"
            :rows="6"
            placeholder="请输入烹饪步骤"
          />
        </el-form-item>

        <el-form-item label="图片 URL">
          <el-input v-model="recipeForm.imageUrl" placeholder="请输入图片链接，可选" />
        </el-form-item>

        <el-form-item label="食材明细" prop="ingredients">
          <div class="ingredient-editor">
            <div
              v-for="(ingredient, index) in recipeForm.ingredients"
              :key="ingredient.key"
              class="ingredient-row"
            >
              <el-select
                v-model="ingredient.ingredientId"
                placeholder="选择食材"
                filterable
                class="ingredient-select"
              >
                <el-option
                  v-for="item in ingredients"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>

              <el-input-number
                v-model="ingredient.quantity"
                :min="1"
                :max="5000"
                controls-position="right"
                class="ingredient-quantity"
              />

              <el-select v-model="ingredient.unit" class="ingredient-unit">
                <el-option label="g" value="g" />
                <el-option label="ml" value="ml" />
                <el-option label="个" value="个" />
                <el-option label="份" value="份" />
              </el-select>

              <el-button
                v-if="recipeForm.ingredients.length > 1"
                link
                type="danger"
                @click="removeIngredient(index)"
              >
                删除
              </el-button>
            </div>

            <el-button plain type="primary" @click="addIngredient">添加食材</el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCreateDialogClose">取消</el-button>
          <el-button type="primary" @click="saveRecipe">保存食谱</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailDialogVisible"
      title="食谱详情"
      width="920px"
      class="recipe-detail-dialog"
    >
      <div v-if="selectedRecipe" class="recipe-detail">
        <div class="detail-header">
          <div>
            <h2>{{ selectedRecipe.name }}</h2>
            <p>{{ selectedRecipe.description || '暂无描述' }}</p>
          </div>
          <el-tag :type="selectedRecipe.isCustom ? 'warning' : 'success'">
            {{ selectedRecipe.isCustom ? '自定义食谱' : '系统食谱' }}
          </el-tag>
        </div>

        <div class="detail-grid">
          <div class="detail-stat">
            <span>热量</span>
            <strong>{{ formatValue(selectedRecipe.totalCalories, 'kcal') }}</strong>
          </div>
          <div class="detail-stat">
            <span>蛋白质</span>
            <strong>{{ formatValue(selectedRecipe.protein, 'g') }}</strong>
          </div>
          <div class="detail-stat">
            <span>碳水</span>
            <strong>{{ formatValue(selectedRecipe.carbs, 'g') }}</strong>
          </div>
          <div class="detail-stat">
            <span>脂肪</span>
            <strong>{{ formatValue(selectedRecipe.fat, 'g') }}</strong>
          </div>
        </div>

        <div class="detail-section">
          <h3>食材</h3>
          <ul class="ingredient-list">
            <li v-for="item in selectedRecipe.ingredients || []" :key="item.id || item.ingredientId">
              {{ item.name || item.ingredientName || '未知食材' }}
              {{ formatIngredientAmount(item.quantity, item.unit) }}
            </li>
          </ul>
        </div>

        <div class="detail-section">
          <h3>烹饪步骤</h3>
          <p class="multiline-text">{{ formatInstructions(selectedRecipe.instructions) }}</p>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="mealTypeDialogVisible"
      title="加入饮食记录"
      width="420px"
      class="meal-dialog"
    >
      <el-form :model="mealTypeForm" label-width="80px">
        <el-form-item label="选择餐次">
          <el-select v-model="mealTypeForm.mealType" style="width: 100%">
            <el-option label="早餐" value="breakfast" />
            <el-option label="午餐" value="lunch" />
            <el-option label="晚餐" value="dinner" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="mealTypeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="!!savingRecordKey" @click="confirmAddToRecord">
          确认添加
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="analysisDialogVisible"
      title="营养分析"
      width="700px"
      class="analysis-dialog"
    >
      <div v-if="analysisResult" class="analysis-content">
        <div class="analysis-score">
          <span>综合评分</span>
          <strong>{{ formatNumber(analysisResult.score, 1) }}</strong>
        </div>
        <p class="analysis-text multiline-text">
          {{ analysisResult.analysis || '暂无分析结果' }}
        </p>
        <div class="analysis-suggestion">
          <h3>建议</h3>
          <p class="multiline-text">{{ analysisResult.suggestion || '暂无建议' }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import recipeApi from '../api/recipe';
import ingredientApi from '../api/ingredient';
import dietRecordApi from '../api/dietRecord';
import {
  exportRecipesToExcel,
  exportRecipesToPdf,
  exportRecipesToWord
} from '../utils/recipeExport';

const recipeFormRef = ref(null);
const createDialogVisible = ref(false);
const detailDialogVisible = ref(false);
const analysisDialogVisible = ref(false);
const mealTypeDialogVisible = ref(false);
const mealTypeForm = reactive({ mealType: 'lunch' });
const pendingRecipe = ref(null);
const savingRecordKey = ref('');
const myRecipes = ref([]);
const ingredients = ref([]);
const selectedRecipe = ref(null);
const analysisResult = ref(null);

const createIngredientRow = () => ({
  key: `${Date.now()}-${Math.random()}`,
  ingredientId: undefined,
  quantity: 100,
  unit: 'g'
});

const recipeForm = reactive({
  name: '',
  description: '',
  cookingTime: 30,
  difficulty: '简单',
  instructions: '',
  imageUrl: '',
  ingredients: [createIngredientRow()]
});

const rules = {
  name: [{ required: true, message: '请输入食谱名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入食谱描述', trigger: 'blur' }],
  cookingTime: [{ required: true, message: '请输入烹饪时间', trigger: 'change' }],
  difficulty: [{ required: true, message: '请选择难度', trigger: 'change' }],
  instructions: [{ required: true, message: '请输入烹饪步骤', trigger: 'blur' }],
  ingredients: [{
    validator: (_, value, callback) => {
      const valid = Array.isArray(value) && value.some((item) => item.ingredientId);
      if (!valid) {
        callback(new Error('请至少添加一种食材'));
        return;
      }
      callback();
    },
    trigger: 'change'
  }]
};

const resetRecipeForm = () => {
  recipeForm.name = '';
  recipeForm.description = '';
  recipeForm.cookingTime = 30;
  recipeForm.difficulty = '简单';
  recipeForm.instructions = '';
  recipeForm.imageUrl = '';
  recipeForm.ingredients = [createIngredientRow()];
};

const openCreateDialog = () => {
  resetRecipeForm();
  createDialogVisible.value = true;
};

const handleCreateDialogClose = () => {
  createDialogVisible.value = false;
  recipeFormRef.value?.clearValidate?.();
  resetRecipeForm();
};

const addIngredient = () => {
  recipeForm.ingredients.push(createIngredientRow());
};

const removeIngredient = (index) => {
  recipeForm.ingredients.splice(index, 1);
};

const formatNumber = (value, digits = 0) => {
  if (value === null || value === undefined || value === '') return '--';
  const num = Number(value);
  if (Number.isNaN(num)) return '--';
  return num.toFixed(digits);
};

const formatValue = (value, unit) => {
  if (value === null || value === undefined || value === '') return `-- ${unit}`;
  const num = Number(value);
  if (Number.isNaN(num)) return `-- ${unit}`;
  const digits = Number.isInteger(num) ? 0 : 1;
  return `${num.toFixed(digits)} ${unit}`;
};

const formatIngredientAmount = (quantity, unit) => {
  if (quantity === null || quantity === undefined || quantity === '') return '';

  const unitText = String(unit || '').trim();
  const rawText = String(quantity).trim();
  const normalizedRaw = rawText.toLowerCase();
  const normalizedUnit = unitText.toLowerCase();
  if (normalizedUnit && normalizedRaw.endsWith(normalizedUnit)) return ` ${rawText}`;

  const num = Number(quantity);
  if (Number.isNaN(num)) return ` ${rawText}${unitText}`;
  const digits = Number.isInteger(num) ? 0 : 1;
  return ` ${num.toFixed(digits)}${unitText}`;
};

const formatInstructions = (instructions) => {
  if (!instructions) return '暂无步骤';
  if (Array.isArray(instructions)) {
    return instructions.map((item, index) => `${index + 1}. ${item}`).join('\n');
  }
  try {
    const parsed = JSON.parse(instructions);
    if (Array.isArray(parsed)) {
      return parsed.map((item, index) => `${index + 1}. ${item}`).join('\n');
    }
  } catch (_) {
    // noop
  }
  return String(instructions);
};

const buildRecipePayload = () => ({
  name: recipeForm.name.trim(),
  description: recipeForm.description.trim(),
  category: '自定义食谱',
  cookingTime: Number(recipeForm.cookingTime) || 30,
  difficulty: recipeForm.difficulty,
  instructions: recipeForm.instructions.trim(),
  imageUrl: recipeForm.imageUrl?.trim() || '',
  ingredients: recipeForm.ingredients
    .filter((item) => item.ingredientId)
    .map((item) => ({
      ingredientId: item.ingredientId,
      quantity: Number(item.quantity) || 0,
      unit: item.unit || 'g'
    }))
});

const exportRows = () =>
  myRecipes.value.map((recipe) => ({
    name: recipe.name || '未命名食谱',
    category: recipe.category || '自定义食谱',
    calories: recipe.totalCalories ?? '--',
    protein: recipe.protein ?? '--',
    carbs: recipe.carbs ?? '--',
    fat: recipe.fat ?? '--',
    cookingTime: recipe.cookingTime || '--',
    difficulty: recipe.difficulty || '--'
  }));

const handleExportCommand = (command) => {
  const title = '我的食谱';
  if (command === 'pdf') {
    exportRecipesToPdf(title, exportRows());
  } else if (command === 'word') {
    exportRecipesToWord(`${title}.doc`, title, exportRows());
  } else if (command === 'excel') {
    exportRecipesToExcel(`${title}.xls`, title, exportRows());
  }
};

const loadMyRecipes = async () => {
  try {
    const response = await recipeApi.getCustomRecipes();
    if (response.code === 200) {
      myRecipes.value = Array.isArray(response.data) ? response.data : [];
    } else {
      ElMessage.error(response.message || '加载我的食谱失败');
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '加载我的食谱失败');
  }
};

const loadIngredients = async () => {
  try {
    const response = await ingredientApi.getIngredientList?.() || await ingredientApi.getAllIngredients?.();
    if (response?.code === 200) {
      ingredients.value = Array.isArray(response.data) ? response.data : [];
    }
  } catch (error) {
    console.error('加载食材失败:', error);
  }
};

const saveRecipe = async () => {
  const valid = await recipeFormRef.value.validate().catch(() => false);
  if (!valid) return;

  try {
    const response = await recipeApi.saveRecipe(buildRecipePayload());
    if (response.code === 200) {
      ElMessage.success('食谱保存成功');
      handleCreateDialogClose();
      loadMyRecipes();
    } else {
      ElMessage.error(response.message || '保存食谱失败');
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '保存食谱失败');
  }
};

const viewRecipe = async (id) => {
  try {
    const response = await recipeApi.getRecipeDetail(id);
    if (response.code === 200) {
      const data = response.data || {};
      selectedRecipe.value = {
        ...(data.recipe || data),
        ingredients: Array.isArray(data.ingredients) ? data.ingredients : (data.recipe?.ingredients || [])
      };
      detailDialogVisible.value = true;
    } else {
      ElMessage.error(response.message || '加载食谱详情失败');
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '加载食谱详情失败');
  }
};

const analyzeRecipe = async (id) => {
  try {
    const response = await recipeApi.analyzeNutrition(id);
    if (response.code === 200) {
      analysisResult.value = response.data;
      analysisDialogVisible.value = true;
    } else {
      ElMessage.error(response.message || '加载营养分析失败');
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '加载营养分析失败');
  }
};

const deleteRecipe = async (id) => {
  try {
    await ElMessageBox.confirm('删除后不可恢复，确定删除这道食谱吗？', '删除确认', {
      type: 'warning'
    });
    const response = await recipeApi.deleteRecipe(id);
    if (response.code === 200) {
      ElMessage.success('删除成功');
      loadMyRecipes();
    } else {
      ElMessage.error(response.message || '删除失败');
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.message || '操作失败');
    }
  }
};

const openMealTypeDialog = (recipe) => {
  pendingRecipe.value = recipe;
  mealTypeForm.mealType = 'lunch';
  mealTypeDialogVisible.value = true;
};

const buildRecordDetailsFromRecipe = (recipe) => {
  if (!recipe) return [];
  const ingredients = Array.isArray(recipe.ingredients) ? recipe.ingredients : [];
  const details = ingredients.map((ingredient) => ({
    recipeId: recipe.id ?? null,
    foodName: ingredient.name || ingredient.ingredientName || recipe.name || '未命名',
    amount: Number(ingredient.quantity ?? 1),
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
  if (details.length) return details;
  return [{
    recipeId: recipe.id ?? null,
    foodName: recipe.name || '未命名食谱',
    amount: 1,
    unit: '份',
    calories: Number(recipe.totalCalories ?? 0),
    protein: Number(recipe.protein ?? 0),
    carbs: Number(recipe.carbs ?? 0),
    fat: Number(recipe.fat ?? 0),
    fiber: Number(recipe.fiber ?? 0),
    sugar: Number(recipe.sugar ?? 0),
    sodium: Number(recipe.sodium ?? 0),
    gi: Number(recipe.gi ?? 0)
  }];
};

const hasMeaningfulNutrition = (details) =>
  Array.isArray(details) &&
  details.some((d) => Number(d?.calories || 0) > 0 || Number(d?.protein || 0) > 0);

const loadAccurateRecordDetails = async (recipe) => {
  const fallbackDetails = buildRecordDetailsFromRecipe(recipe);
  if (!recipe?.id || hasMeaningfulNutrition(fallbackDetails)) return fallbackDetails;
  try {
    const response = await recipeApi.getRecipeDetail(recipe.id);
    if (response.code === 200) {
      const data = response.data || {};
      const enriched = { ...recipe, ingredients: Array.isArray(data.ingredients) ? data.ingredients : recipe.ingredients };
      const accurate = buildRecordDetailsFromRecipe(enriched);
      if (hasMeaningfulNutrition(accurate)) return accurate;
    }
  } catch (_) { /* fallback */ }
  return fallbackDetails;
};

const confirmAddToRecord = async () => {
  const recipe = pendingRecipe.value;
  if (!recipe) return;
  savingRecordKey.value = recipe.id;
  try {
    const details = await loadAccurateRecordDetails(recipe);
    const response = await dietRecordApi.submitRecord({
      date: new Date().toISOString().slice(0, 10),
      mealType: mealTypeForm.mealType,
      notes: `来自自定义食谱：${recipe.name || '未命名食谱'}`,
      details
    });
    if (response.code === 200) {
      ElMessage.success('已加入今日饮食记录');
      mealTypeDialogVisible.value = false;
    } else {
      ElMessage.error(response.message || '加入饮食记录失败');
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '加入饮食记录失败，请稍后重试');
  } finally {
    savingRecordKey.value = '';
  }
};

onMounted(async () => {
  await Promise.all([
    loadMyRecipes(),
    loadIngredients()
  ]);
});
</script>

<style scoped>
.custom-recipe-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header,
.panel-header,
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 34px;
  font-weight: 700;
  color: #193a2d;
}

.page-subtitle {
  margin: 8px 0 0;
  color: #6f8578;
  font-size: 15px;
}

.header-actions,
.dialog-footer,
.table-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.create-button {
  min-width: 120px;
  border-radius: 14px;
}

.recipe-panel {
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(186, 217, 200, 0.7);
  border-radius: 28px;
  padding: 28px;
  box-shadow: 0 18px 50px rgba(134, 171, 149, 0.12);
}

.panel-header {
  margin-bottom: 20px;
}

.panel-header h2 {
  margin: 0;
  font-size: 22px;
  color: #1d3b2f;
}

.panel-header p {
  margin: 8px 0 0;
  color: #71887b;
  font-size: 14px;
}

.recipe-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.inline-unit {
  margin-left: 10px;
  color: #6f8578;
}

.ingredient-editor {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ingredient-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) 150px 120px auto;
  gap: 12px;
  align-items: center;
}

.ingredient-select,
.ingredient-quantity,
.ingredient-unit {
  width: 100%;
}

.recipe-detail {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.detail-header h2 {
  margin: 0;
  font-size: 28px;
  color: #18392c;
}

.detail-header p {
  margin: 10px 0 0;
  color: #6e8578;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.detail-stat {
  padding: 18px 20px;
  border-radius: 20px;
  background: rgba(241, 247, 243, 0.92);
  border: 1px solid rgba(208, 225, 214, 0.75);
}

.detail-stat span {
  display: block;
  color: #6d8477;
  font-size: 14px;
  margin-bottom: 10px;
}

.detail-stat strong {
  font-size: 28px;
  color: #1d3b2f;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-section h3,
.analysis-suggestion h3 {
  margin: 0;
  font-size: 18px;
  color: #18392c;
}

.ingredient-list {
  margin: 0;
  padding-left: 18px;
  color: #294437;
  line-height: 1.9;
}

.multiline-text {
  white-space: pre-wrap;
  line-height: 1.9;
  color: #2b4438;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.analysis-score {
  padding: 20px 22px;
  border-radius: 22px;
  background: rgba(241, 247, 243, 0.92);
  border: 1px solid rgba(206, 224, 213, 0.75);
}

.analysis-score span {
  display: block;
  color: #6f8578;
  margin-bottom: 8px;
}

.analysis-score strong {
  font-size: 34px;
  color: #1a3a2d;
}

@media (max-width: 1024px) {
  .detail-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ingredient-row {
    grid-template-columns: minmax(0, 1fr) 130px 100px auto;
  }
}

@media (max-width: 768px) {
  .page-header,
  .panel-header,
  .detail-header {
    flex-direction: column;
    align-items: stretch;
  }

  .form-grid,
  .detail-grid,
  .ingredient-row {
    grid-template-columns: 1fr;
  }

  .header-actions,
  .dialog-footer {
    flex-wrap: wrap;
  }

  .recipe-panel {
    padding: 22px 18px;
  }
}
</style>
