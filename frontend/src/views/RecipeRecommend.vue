<template>
  <div class="recipe-recommend-container">
    <h2>食谱推荐</h2>
    <el-button type="primary" @click="getRecommendations" :loading="loading">生成食谱推荐</el-button>
    <div class="recipe-list" v-if="recipes.length > 0">
      <el-card v-for="(recipe, index) in recipes" :key="index" class="recipe-card">
        <template #header>
          <div class="recipe-header">
            <h3>{{ recipe.name }}</h3>
            <el-tag>{{ recipe.type }}</el-tag>
          </div>
        </template>
        <div class="recipe-content">
          <div class="recipe-info">
            <p><strong>热量:</strong> {{ recipe.calories }} kcal</p>
            <p><strong>蛋白质:</strong> {{ recipe.protein }} g</p>
            <p><strong>碳水化合物:</strong> {{ recipe.carbs }} g</p>
            <p><strong>脂肪:</strong> {{ recipe.fat }} g</p>
          </div>
          <div class="recipe-ingredients">
            <h4>食材:</h4>
            <ul>
              <li v-for="(ingredient, idx) in recipe.ingredients" :key="idx">{{ ingredient }}</li>
            </ul>
          </div>
          <div class="recipe-steps">
            <h4>步骤:</h4>
            <ol>
              <li v-for="(step, idx) in recipe.steps" :key="idx">{{ step }}</li>
            </ol>
          </div>
        </div>
      </el-card>
    </div>
    <el-empty v-else description="暂无推荐食谱" style="margin-top: 40px;"></el-empty>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useUserStore } from '../stores/user';
import { ElMessage } from 'element-plus';
import recipeApi from '../api/recipe';

const userStore = useUserStore();
const recipes = ref([]);
const loading = ref(false);

const getRecommendations = async () => {
  if (!userStore.userId) {
    ElMessage.error('用户未登录');
    return;
  }
  if (!userStore.hasHealthInfo) {
    ElMessage.error('请先填写健康信息');
    return;
  }
  if (!userStore.hasDietGoal) {
    ElMessage.error('请先设置饮食目标');
    return;
  }
  loading.value = true;
  try {
    const response = await recipeApi.getRecommendations(userStore.userId);
    if (response.code === 200) {
      recipes.value = response.data;
      ElMessage.success('获取推荐食谱成功');
    } else {
      ElMessage.error(response.message || '获取推荐食谱失败');
    }
  } catch (error) {
    ElMessage.error('获取推荐食谱失败，请检查网络连接');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  // 页面加载时自动获取推荐食谱
  // getRecommendations();
});
</script>

<style scoped>
.recipe-recommend-container {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

h2 {
  margin-bottom: 20px;
  color: #303133;
}

.recipe-list {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.recipe-card {
  margin-bottom: 20px;
}

.recipe-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recipe-header h3 {
  margin: 0;
}

.recipe-content {
  margin-top: 10px;
}

.recipe-info {
  margin-bottom: 15px;
}

.recipe-ingredients {
  margin-bottom: 15px;
}

.recipe-ingredients ul {
  padding-left: 20px;
  margin: 10px 0;
}

.recipe-steps ol {
  padding-left: 20px;
  margin: 10px 0;
}
</style>