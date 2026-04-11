<template>
  <div class="admin-page">
    <div class="page-top">
      <div>
        <h2>食谱库管理</h2>
        <p>集中维护系统食谱，支持新增、编辑、查看营养信息和删除。</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">新增食谱</el-button>
    </div>

    <el-card class="toolbar-card">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索食谱名称" clearable @keyup.enter="loadRecipes" />
        <el-button @click="loadRecipes">查询</el-button>
      </div>
    </el-card>

    <el-card class="table-card">
      <el-table :data="pagedRecipes" v-loading="loading">
        <el-table-column prop="name" label="食谱名称" min-width="180" />
        <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
        <el-table-column prop="cookingTime" label="烹饪时长" width="110" />
        <el-table-column prop="difficulty" label="难度" width="110" />
        <el-table-column prop="totalCalories" label="热量(kcal)" width="120" />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button text @click="viewRecipe(row)">查看</el-button>
            <el-button text type="primary" @click="editRecipe(row)">编辑</el-button>
            <el-button text type="danger" @click="deleteRecipe(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="recipes.length > pageSize" class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          layout="prev, pager, next"
          :total="recipes.length"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑食谱' : '新增食谱'" width="760px">
      <el-form ref="recipeFormRef" :model="recipeForm" :rules="rules" label-width="110px">
        <el-form-item label="食谱名称" prop="name">
          <el-input v-model="recipeForm.name" />
        </el-form-item>
        <el-form-item label="食谱描述" prop="description">
          <el-input v-model="recipeForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <div class="grid-two">
          <el-form-item label="烹饪时长" prop="cookingTime">
            <el-input-number v-model="recipeForm.cookingTime" :min="1" :max="300" />
          </el-form-item>
          <el-form-item label="难度" prop="difficulty">
            <el-select v-model="recipeForm.difficulty">
              <el-option label="简单" value="简单" />
              <el-option label="中等" value="中等" />
              <el-option label="困难" value="困难" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="制作步骤" prop="instructions">
          <el-input v-model="recipeForm.instructions" type="textarea" :rows="6" />
        </el-form-item>
        <el-form-item label="图片地址">
          <el-input v-model="recipeForm.imageUrl" />
        </el-form-item>
        <el-form-item label="食材组成">
          <div class="ingredient-list">
            <div v-for="(ingredient, index) in recipeForm.ingredients" :key="index" class="ingredient-row">
              <el-select v-model="ingredient.ingredientId" filterable placeholder="选择食材" class="ingredient-select">
                <el-option
                  v-for="item in ingredientOptions"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
              <el-input-number v-model="ingredient.quantity" :min="0.1" :precision="1" class="ingredient-number" />
              <el-select v-model="ingredient.unit" class="ingredient-unit">
                <el-option label="g" value="g" />
                <el-option label="ml" value="ml" />
                <el-option label="份" value="份" />
              </el-select>
              <el-button text type="danger" @click="removeIngredient(index)">删除</el-button>
            </div>
            <el-button type="success" plain @click="addIngredient">添加食材</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitRecipe">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="食谱详情" width="720px">
      <div v-if="currentRecipe">
        <h3>{{ currentRecipe.recipe?.name || currentRecipe.name }}</h3>
        <p class="detail-desc">{{ currentRecipe.recipe?.description || currentRecipe.description || '暂无描述' }}</p>
        <div class="detail-meta">
          <span>时长：{{ currentRecipe.recipe?.cookingTime || currentRecipe.cookingTime || '--' }} 分钟</span>
          <span>难度：{{ currentRecipe.recipe?.difficulty || currentRecipe.difficulty || '--' }}</span>
        </div>
        <div class="detail-meta">
          <span>热量：{{ currentRecipe.recipe?.totalCalories || currentRecipe.totalCalories || '--' }} kcal</span>
          <span>蛋白质：{{ currentRecipe.recipe?.protein || currentRecipe.protein || '--' }} g</span>
          <span>碳水：{{ currentRecipe.recipe?.carbs || currentRecipe.carbs || '--' }} g</span>
          <span>脂肪：{{ currentRecipe.recipe?.fat || currentRecipe.fat || '--' }} g</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import ingredientApi from '../api/ingredient';
import recipeApi from '../api/recipe';

const loading = ref(false);
const submitting = ref(false);
const dialogVisible = ref(false);
const detailVisible = ref(false);
const isEditing = ref(false);
const recipeFormRef = ref(null);
const recipes = ref([]);
const ingredientOptions = ref([]);
const currentRecipe = ref(null);
const keyword = ref('');
const currentPage = ref(1);
const pageSize = 10;

const createEmptyRecipe = () => ({
  id: null,
  name: '',
  description: '',
  cookingTime: 15,
  difficulty: '简单',
  instructions: '',
  imageUrl: '',
  ingredients: [{ ingredientId: null, quantity: 100, unit: 'g' }]
});

const recipeForm = reactive(createEmptyRecipe());

const rules = {
  name: [{ required: true, message: '请输入食谱名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入食谱描述', trigger: 'blur' }],
  instructions: [{ required: true, message: '请输入制作步骤', trigger: 'blur' }]
};

const resetRecipeForm = () => {
  Object.assign(recipeForm, createEmptyRecipe());
};

const pagedRecipes = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return recipes.value.slice(start, start + pageSize);
});

const loadRecipes = async () => {
  loading.value = true;
  try {
    const response = keyword.value.trim()
      ? await recipeApi.searchRecipes(keyword.value.trim())
      : await recipeApi.getAllRecipes();
    recipes.value = response.code === 200 && Array.isArray(response.data) ? response.data : [];
    currentPage.value = 1;
  } catch (error) {
    ElMessage.error(error.message || '加载食谱失败');
  } finally {
    loading.value = false;
  }
};

const loadIngredients = async () => {
  try {
    const response = await ingredientApi.getAllIngredients();
    ingredientOptions.value = response.code === 200 && Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    ElMessage.error(error.message || '加载食材失败');
  }
};

const openCreateDialog = () => {
  isEditing.value = false;
  resetRecipeForm();
  dialogVisible.value = true;
};

const addIngredient = () => {
  recipeForm.ingredients.push({ ingredientId: null, quantity: 100, unit: 'g' });
};

const removeIngredient = (index) => {
  recipeForm.ingredients.splice(index, 1);
  if (!recipeForm.ingredients.length) {
    addIngredient();
  }
};

const editRecipe = async (recipe) => {
  isEditing.value = true;
  try {
    const response = await recipeApi.getRecipeDetail(recipe.id);
    const detail = response.code === 200 ? response.data : null;
    Object.assign(recipeForm, {
      id: recipe.id,
      name: detail?.recipe?.name || recipe.name,
      description: detail?.recipe?.description || recipe.description || '',
      cookingTime: detail?.recipe?.cookingTime || recipe.cookingTime || 15,
      difficulty: detail?.recipe?.difficulty || recipe.difficulty || '简单',
      instructions: detail?.recipe?.instructions || recipe.instructions || '',
      imageUrl: detail?.recipe?.imageUrl || recipe.imageUrl || '',
      ingredients: Array.isArray(detail?.ingredients) && detail.ingredients.length
        ? detail.ingredients.map((item) => ({
            ingredientId: item.ingredientId,
            quantity: item.quantity,
            unit: item.unit || 'g'
          }))
        : [{ ingredientId: null, quantity: 100, unit: 'g' }]
    });
    dialogVisible.value = true;
  } catch (error) {
    ElMessage.error(error.message || '加载食谱详情失败');
  }
};

const viewRecipe = async (recipe) => {
  try {
    const response = await recipeApi.getRecipeDetail(recipe.id);
    currentRecipe.value = response.code === 200 ? response.data : recipe;
    detailVisible.value = true;
  } catch (error) {
    currentRecipe.value = recipe;
    detailVisible.value = true;
  }
};

const submitRecipe = async () => {
  await recipeFormRef.value.validate(async (valid) => {
    if (!valid) return;
    submitting.value = true;
    try {
      const payload = {
        ...recipeForm,
        ingredients: recipeForm.ingredients.filter((item) => item.ingredientId)
      };
      if (!payload.ingredients.length) {
        ElMessage.warning('请至少选择一种食材');
        submitting.value = false;
        return;
      }
      const response = isEditing.value
        ? await recipeApi.updateRecipe(payload)
        : await recipeApi.saveRecipe(payload);
      if (response.code === 200) {
        ElMessage.success(isEditing.value ? '食谱更新成功' : '食谱新增成功');
        dialogVisible.value = false;
        await loadRecipes();
      } else {
        ElMessage.error(response.message || '保存食谱失败');
      }
    } catch (error) {
      ElMessage.error(error.message || '保存食谱失败');
    } finally {
      submitting.value = false;
    }
  });
};

const deleteRecipe = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除这条食谱吗？', '删除确认', { type: 'warning' });
    const response = await recipeApi.deleteRecipe(id);
    if (response.code === 200) {
      ElMessage.success('删除成功');
      await loadRecipes();
    } else {
      ElMessage.error(response.message || '删除失败');
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败');
    }
  }
};

onMounted(async () => {
  await Promise.all([loadRecipes(), loadIngredients()]);
});
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

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.ingredient-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ingredient-row {
  display: grid;
  grid-template-columns: 1.6fr 1fr 1fr auto;
  gap: 12px;
}

.detail-desc {
  color: #6e8374;
  line-height: 1.7;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  color: #486454;
  margin-top: 10px;
}

@media (max-width: 900px) {
  .page-top,
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .grid-two,
  .ingredient-row {
    grid-template-columns: 1fr;
  }
}
</style>
