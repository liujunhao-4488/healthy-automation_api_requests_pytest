<template>
  <div class="ingredient-library-container">
    <div class="page-header">
      <div>
        <h2>食材库管理</h2>
        <p>维护食材基础营养数据，支持分类筛选、搜索与新增编辑。</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">新增食材</el-button>
    </div>

    <el-card class="filter-card">
      <div class="filter-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索食材名称"
          clearable
          @keyup.enter="searchIngredients"
        />
        <el-select v-model="selectedCategory" placeholder="全部分类" clearable @change="filterByCategory">
          <el-option v-for="category in categories" :key="category" :label="category" :value="category" />
        </el-select>
        <el-button @click="resetFilters">重置</el-button>
        <el-button type="primary" @click="searchIngredients">查询</el-button>
      </div>
    </el-card>

    <el-table :data="pagedIngredients" class="ingredient-table">
      <el-table-column prop="name" label="食材名称" min-width="160" />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column prop="caloriesPer100g" label="热量/100g" width="120" />
      <el-table-column prop="proteinPer100g" label="蛋白质" width="110" />
      <el-table-column prop="carbsPer100g" label="碳水" width="110" />
      <el-table-column prop="fatPer100g" label="脂肪" width="110" />
      <el-table-column prop="giValue" label="GI" width="90" />
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button size="small" @click="viewIngredient(row)">详情</el-button>
          <el-button size="small" type="primary" plain @click="editIngredient(row)">编辑</el-button>
          <el-popconfirm title="确认删除该食材吗？" @confirm="removeIngredient(row.id)">
            <template #reference>
              <el-button size="small" type="danger" plain>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="ingredients.length > pageSize" class="pagination-wrap">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        layout="prev, pager, next"
        :total="ingredients.length"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增食材' : '编辑食材'" width="720px">
      <el-form ref="ingredientFormRef" :model="ingredientForm" :rules="rules" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="食材名称" prop="name">
              <el-input v-model="ingredientForm.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-input v-model="ingredientForm.category" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="热量/100g" prop="caloriesPer100g">
              <el-input-number v-model="ingredientForm.caloriesPer100g" :min="0" :precision="1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="蛋白质" prop="proteinPer100g">
              <el-input-number v-model="ingredientForm.proteinPer100g" :min="0" :precision="1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="碳水" prop="carbsPer100g">
              <el-input-number v-model="ingredientForm.carbsPer100g" :min="0" :precision="1" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="脂肪" prop="fatPer100g">
              <el-input-number v-model="ingredientForm.fatPer100g" :min="0" :precision="1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="膳食纤维" prop="fiberPer100g">
              <el-input-number v-model="ingredientForm.fiberPer100g" :min="0" :precision="1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="GI" prop="giValue">
              <el-input-number v-model="ingredientForm.giValue" :min="0" :max="200" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述" prop="description">
          <el-input v-model="ingredientForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitIngredient" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="食材详情" width="640px">
      <div v-if="currentIngredient" class="detail-grid">
        <div class="detail-item"><span>名称</span><strong>{{ currentIngredient.name }}</strong></div>
        <div class="detail-item"><span>分类</span><strong>{{ currentIngredient.category || '--' }}</strong></div>
        <div class="detail-item"><span>热量/100g</span><strong>{{ currentIngredient.caloriesPer100g ?? '--' }}</strong></div>
        <div class="detail-item"><span>蛋白质</span><strong>{{ currentIngredient.proteinPer100g ?? '--' }}</strong></div>
        <div class="detail-item"><span>碳水</span><strong>{{ currentIngredient.carbsPer100g ?? '--' }}</strong></div>
        <div class="detail-item"><span>脂肪</span><strong>{{ currentIngredient.fatPer100g ?? '--' }}</strong></div>
        <div class="detail-item"><span>膳食纤维</span><strong>{{ currentIngredient.fiberPer100g ?? '--' }}</strong></div>
        <div class="detail-item"><span>GI</span><strong>{{ currentIngredient.giValue ?? '--' }}</strong></div>
      </div>
      <p class="detail-description">{{ currentIngredient?.description || '暂无描述' }}</p>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import ingredientApi from '../api/ingredient';

const ingredients = ref([]);
const keyword = ref('');
const selectedCategory = ref('');
const dialogVisible = ref(false);
const detailVisible = ref(false);
const dialogMode = ref('create');
const submitting = ref(false);
const currentIngredient = ref(null);
const ingredientFormRef = ref(null);
const currentPage = ref(1);
const pageSize = 10;

const createEmptyIngredient = () => ({
  id: null,
  name: '',
  category: '',
  caloriesPer100g: 0,
  proteinPer100g: 0,
  carbsPer100g: 0,
  fatPer100g: 0,
  fiberPer100g: 0,
  giValue: null,
  description: '',
  status: 1
});

const ingredientForm = reactive(createEmptyIngredient());

const rules = {
  name: [{ required: true, message: '请输入食材名称', trigger: 'blur' }],
  category: [{ required: true, message: '请输入分类', trigger: 'blur' }],
  caloriesPer100g: [{ required: true, message: '请输入热量', trigger: 'change' }]
};

const categories = computed(() =>
  [...new Set(ingredients.value.map((item) => item.category).filter(Boolean))]
);
const pagedIngredients = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return ingredients.value.slice(start, start + pageSize);
});

const loadIngredients = async () => {
  try {
    const response = await ingredientApi.getAllIngredients();
    if (response.code === 200) {
      ingredients.value = Array.isArray(response.data) ? response.data : [];
      currentPage.value = 1;
    } else {
      ElMessage.error(response.message || '获取食材列表失败');
    }
  } catch (error) {
    ElMessage.error(error.message || '获取食材列表失败');
  }
};

const resetForm = () => {
  Object.assign(ingredientForm, createEmptyIngredient());
};

const openCreateDialog = () => {
  dialogMode.value = 'create';
  resetForm();
  dialogVisible.value = true;
};

const editIngredient = (ingredient) => {
  dialogMode.value = 'edit';
  Object.assign(ingredientForm, {
    ...createEmptyIngredient(),
    ...ingredient
  });
  dialogVisible.value = true;
};

const viewIngredient = async (ingredient) => {
  try {
    const response = await ingredientApi.getIngredientDetail(ingredient.id);
    currentIngredient.value = response.code === 200 ? response.data : ingredient;
    detailVisible.value = true;
  } catch (error) {
    currentIngredient.value = ingredient;
    detailVisible.value = true;
  }
};

const submitIngredient = async () => {
  await ingredientFormRef.value.validate(async (valid) => {
    if (!valid) {
      return;
    }

    submitting.value = true;
    try {
      const payload = { ...ingredientForm };
      const response =
        dialogMode.value === 'create'
          ? await ingredientApi.saveIngredient(payload)
          : await ingredientApi.updateIngredient(payload);

      if (response.code === 200) {
        ElMessage.success(dialogMode.value === 'create' ? '新增食材成功' : '更新食材成功');
        dialogVisible.value = false;
        await loadIngredients();
      } else {
        ElMessage.error(response.message || '保存食材失败');
      }
    } catch (error) {
      ElMessage.error(error.message || '保存食材失败');
    } finally {
      submitting.value = false;
    }
  });
};

const removeIngredient = async (id) => {
  try {
    const response = await ingredientApi.deleteIngredient(id);
    if (response.code === 200) {
      ElMessage.success('删除食材成功');
      await loadIngredients();
    } else {
      ElMessage.error(response.message || '删除食材失败');
    }
  } catch (error) {
    ElMessage.error(error.message || '删除食材失败');
  }
};

const searchIngredients = async () => {
  try {
    const trimmed = keyword.value.trim();
    const response = trimmed
      ? await ingredientApi.searchIngredients(trimmed)
      : selectedCategory.value
        ? await ingredientApi.getIngredientsByCategory(selectedCategory.value)
        : await ingredientApi.getAllIngredients();

    if (response.code === 200) {
      ingredients.value = Array.isArray(response.data) ? response.data : [];
      currentPage.value = 1;
    } else {
      ElMessage.error(response.message || '查询食材失败');
    }
  } catch (error) {
    ElMessage.error(error.message || '查询食材失败');
  }
};

const filterByCategory = async () => {
  keyword.value = '';
  if (!selectedCategory.value) {
    await loadIngredients();
    return;
  }

  try {
    const response = await ingredientApi.getIngredientsByCategory(selectedCategory.value);
    if (response.code === 200) {
      ingredients.value = Array.isArray(response.data) ? response.data : [];
      currentPage.value = 1;
    } else {
      ElMessage.error(response.message || '按分类查询失败');
    }
  } catch (error) {
    ElMessage.error(error.message || '按分类查询失败');
  }
};

const resetFilters = async () => {
  keyword.value = '';
  selectedCategory.value = '';
  await loadIngredients();
};

onMounted(() => {
  loadIngredients();
});
</script>

<style scoped>
.ingredient-library-container {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #909399;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-bar {
  display: grid;
  grid-template-columns: 2fr 1fr auto auto;
  gap: 12px;
}

.ingredient-table {
  margin-top: 8px;
}

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.detail-item {
  padding: 12px;
  border-radius: 8px;
  background: #f7faf8;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.detail-item span {
  color: #909399;
}

.detail-description {
  margin: 0;
  color: #606266;
  line-height: 1.7;
}

@media (max-width: 768px) {
  .filter-bar {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
