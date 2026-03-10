<template>
  <div class="custom-recipe-container">
    <h2>自定义食谱</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="创建食谱" name="create">
        <el-form :model="recipeForm" :rules="rules" ref="recipeFormRef" label-width="120px">
          <el-form-item label="食谱名称" prop="name">
            <el-input v-model="recipeForm.name" placeholder="请输入食谱名称"></el-input>
          </el-form-item>
          <el-form-item label="食谱描述" prop="description">
            <el-input v-model="recipeForm.description" type="textarea" placeholder="请输入食谱描述"></el-input>
          </el-form-item>
          <el-form-item label="烹饪时间" prop="cookingTime">
            <el-input-number v-model="recipeForm.cookingTime" :min="1" :max="300"></el-input-number>
            <span style="margin-left: 10px;">分钟</span>
          </el-form-item>
          <el-form-item label="难度" prop="difficulty">
            <el-select v-model="recipeForm.difficulty" placeholder="请选择难度">
              <el-option label="简单" value="简单"></el-option>
              <el-option label="中等" value="中等"></el-option>
              <el-option label="困难" value="困难"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="烹饪步骤" prop="instructions">
            <el-input v-model="recipeForm.instructions" type="textarea" :rows="6" placeholder="请输入烹饪步骤"></el-input>
          </el-form-item>
          <el-form-item label="图片URL" prop="imageUrl">
            <el-input v-model="recipeForm.imageUrl" placeholder="请输入图片URL（可选）"></el-input>
          </el-form-item>
          <el-form-item label="食材">
            <div v-for="(ingredient, index) in recipeForm.ingredients" :key="index" class="ingredient-row">
              <el-select v-model="ingredient.ingredientId" placeholder="选择食材" filterable style="width: 200px;">
                <el-option
                  v-for="item in ingredientList"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id">
                </el-option>
              </el-select>
              <el-input-number v-model="ingredient.quantity" :min="0.1" :precision="1" style="width: 120px; margin-left: 10px;"></el-input-number>
              <el-select v-model="ingredient.unit" placeholder="单位" style="width: 100px; margin-left: 10px;">
                <el-option label="g" value="g"></el-option>
                <el-option label="ml" value="ml"></el-option>
                <el-option label="个" value="个"></el-option>
                <el-option label="勺" value="勺"></el-option>
                <el-option label="块" value="块"></el-option>
              </el-select>
              <el-button type="danger" @click="removeIngredient(index)" style="margin-left: 10px;">删除</el-button>
            </div>
            <el-button type="primary" @click="addIngredient" style="margin-top: 10px;">添加食材</el-button>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveRecipe" :loading="loading">保存食谱</el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="我的食谱" name="myRecipes">
        <el-table :data="myRecipes" style="width: 100%; margin-top: 20px;">
          <el-table-column prop="name" label="食谱名称" width="180"></el-table-column>
          <el-table-column prop="description" label="描述"></el-table-column>
          <el-table-column prop="cookingTime" label="烹饪时间(分钟)" width="120"></el-table-column>
          <el-table-column prop="difficulty" label="难度" width="80"></el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="scope">
              <el-button size="small" @click="viewRecipe(scope.row)">查看</el-button>
              <el-button size="small" type="danger" @click="deleteRecipe(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import recipeApi from '../api/recipe';

const activeTab = ref('create');
const recipeFormRef = ref(null);
const loading = ref(false);
const myRecipes = ref([]);
const ingredientList = ref([]);

const recipeForm = reactive({
  name: '',
  description: '',
  cookingTime: 30,
  difficulty: '简单',
  instructions: '',
  imageUrl: '',
  ingredients: [
    { ingredientId: null, quantity: 100, unit: 'g' }
  ]
});

const rules = {
  name: [
    { required: true, message: '请输入食谱名称', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入食谱描述', trigger: 'blur' }
  ],
  cookingTime: [
    { required: true, message: '请输入烹饪时间', trigger: 'blur' }
  ],
  difficulty: [
    { required: true, message: '请选择难度', trigger: 'change' }
  ],
  instructions: [
    { required: true, message: '请输入烹饪步骤', trigger: 'blur' }
  ]
};

const addIngredient = () => {
  recipeForm.ingredients.push({ ingredientId: null, quantity: 100, unit: 'g' });
};

const removeIngredient = (index) => {
  recipeForm.ingredients.splice(index, 1);
};

const saveRecipe = async () => {
  await recipeFormRef.value.validate(async (valid) => {
    if (valid) {
      const hasValidIngredient = recipeForm.ingredients.some(i => i.ingredientId !== null);
      if (!hasValidIngredient) {
        ElMessage.error('请至少添加一种食材');
        return;
      }
      loading.value = true;
      try {
        const response = await recipeApi.saveRecipe(recipeForm);
        if (response.code === 200) {
          ElMessage.success('保存成功');
          resetForm();
          loadMyRecipes();
        } else {
          ElMessage.error(response.message || '保存失败');
        }
      } catch (error) {
        ElMessage.error('保存失败，请检查网络连接');
      } finally {
        loading.value = false;
      }
    }
  });
};

const resetForm = () => {
  recipeFormRef.value.resetFields();
  recipeForm.ingredients = [{ ingredientId: null, quantity: 100, unit: 'g' }];
};

const loadMyRecipes = async () => {
  try {
    const response = await recipeApi.getCustomRecipes();
    if (response.code === 200) {
      myRecipes.value = response.data;
    }
  } catch (error) {
    console.error('获取自定义食谱失败:', error);
  }
};

const loadIngredients = async () => {
  try {
    const response = await axios.get('/api/ingredient/list');
    if (response.code === 200) {
      ingredientList.value = response.data;
    }
  } catch (error) {
    console.error('获取食材列表失败:', error);
  }
};

const viewRecipe = (recipe) => {
  ElMessage.info(`查看食谱: ${recipe.name}`);
};

const deleteRecipe = async (id) => {
  try {
    const response = await recipeApi.deleteRecipe(id);
    if (response.code === 200) {
      ElMessage.success('删除成功');
      loadMyRecipes();
    } else {
      ElMessage.error(response.message || '删除失败');
    }
  } catch (error) {
    ElMessage.error('删除失败');
  }
};

import axios from '../utils/axios';

onMounted(() => {
  loadMyRecipes();
  loadIngredients();
});
</script>

<style scoped>
.custom-recipe-container {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

h2 {
  margin-bottom: 20px;
  color: #303133;
}

.ingredient-row {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}
</style>
