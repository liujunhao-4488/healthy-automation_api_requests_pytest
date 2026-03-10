<template>
  <div class="health-knowledge-container">
    <h2>健康知识推荐</h2>
    <div class="knowledge-list">
      <el-card v-for="(knowledge, index) in knowledgeList" :key="index" class="knowledge-card">
        <template #header>
          <div class="knowledge-header">
            <h3>{{ knowledge.title }}</h3>
            <el-tag>{{ knowledge.category }}</el-tag>
          </div>
        </template>
        <div class="knowledge-content">
          <p>{{ knowledge.summary }}</p>
          <div class="knowledge-footer">
            <span class="publish-date">{{ knowledge.publish_date }}</span>
            <el-button type="primary" size="small" @click="viewDetails(knowledge.id)">查看详情</el-button>
          </div>
        </div>
      </el-card>
    </div>
    <div class="pagination" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import healthKnowledgeApi from '../api/healthKnowledge';

const knowledgeList = ref([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

const loadKnowledgeList = async () => {
  try {
    const response = await healthKnowledgeApi.getKnowledgeList(currentPage.value, pageSize.value);
    if (response.code === 200) {
      knowledgeList.value = response.data.list;
      total.value = response.data.total;
    } else {
      ElMessage.error(response.message || '获取健康知识失败');
    }
  } catch (error) {
    ElMessage.error('获取健康知识失败，请检查网络连接');
  }
};

const handleSizeChange = (size) => {
  pageSize.value = size;
  loadKnowledgeList();
};

const handleCurrentChange = (current) => {
  currentPage.value = current;
  loadKnowledgeList();
};

const viewDetails = (id) => {
  // 这里可以实现查看详情的逻辑，比如跳转到详情页或弹出对话框
  ElMessage.info(`查看ID为${id}的健康知识详情`);
};

onMounted(() => {
  loadKnowledgeList();
});
</script>

<style scoped>
.health-knowledge-container {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

h2 {
  margin-bottom: 20px;
  color: #303133;
}

.knowledge-list {
  margin-bottom: 20px;
}

.knowledge-card {
  margin-bottom: 20px;
}

.knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.knowledge-header h3 {
  margin: 0;
  font-size: 18px;
}

.knowledge-content {
  margin-top: 10px;
}

.knowledge-content p {
  margin-bottom: 15px;
  line-height: 1.5;
}

.knowledge-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.publish-date {
  color: #909399;
  font-size: 14px;
}

.pagination {
  margin-top: 30px;
  display: flex;
  justify-content: center;
}
</style>