<template>
  <div class="ingredient-substitute-container">
    <h2>食材替代建议</h2>
    <el-form :model="substituteForm" :rules="rules" ref="substituteFormRef" label-width="120px" inline>
      <el-form-item label="食材名称" prop="ingredient">
        <el-input v-model="substituteForm.ingredient" placeholder="请输入食材名称"></el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="getSubstitutes" :loading="loading">查询替代食材</el-button>
      </el-form-item>
    </el-form>
    <div class="substitute-result" v-if="substitutes.length > 0">
      <h3>替代建议:</h3>
      <el-card v-for="(substitute, index) in substitutes" :key="index" class="substitute-card">
        <div class="substitute-content">
          <div class="substitute-info">
            <h4>{{ substitute.name }}</h4>
            <p><strong>相似度:</strong> {{ substitute.similarity }}</p>
            <p><strong>营养差异:</strong> {{ substitute.nutrition_difference }}</p>
            <p><strong>使用建议:</strong> {{ substitute.usage_suggestion }}</p>
          </div>
        </div>
      </el-card>
    </div>
    <el-empty v-else-if="hasSearched" description="暂无替代建议" style="margin-top: 40px;"></el-empty>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import recipeApi from '../api/recipe';

const substituteFormRef = ref(null);
const substituteForm = reactive({
  ingredient: ''
});

const rules = {
  ingredient: [
    { required: true, message: '请输入食材名称', trigger: 'blur' }
  ]
};

const substitutes = ref([]);
const loading = ref(false);
const hasSearched = ref(false);

const getSubstitutes = async () => {
  await substituteFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      hasSearched.value = true;
      try {
        const response = await recipeApi.getSubstitutes(substituteForm.ingredient);
        if (response.code === 200) {
          substitutes.value = response.data;
          if (substitutes.value.length === 0) {
            ElMessage.info('暂无替代建议');
          }
        } else {
          ElMessage.error(response.message || '查询失败');
        }
      } catch (error) {
        ElMessage.error('查询失败，请检查网络连接');
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style scoped>
.ingredient-substitute-container {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

h2 {
  margin-bottom: 20px;
  color: #303133;
}

.substitute-result {
  margin-top: 20px;
}

.substitute-result h3 {
  margin-bottom: 15px;
  color: #303133;
}

.substitute-card {
  margin-bottom: 15px;
}

.substitute-content {
  padding: 10px 0;
}

.substitute-info h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #409EFF;
}

.substitute-info p {
  margin: 5px 0;
}
</style>