<template>
  <div class="login-container">
    <div class="login-form">
      <h2>健康饮食推荐系统</h2>
      <h3>用户登录</h3>
      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-width="80px">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="loginForm.email" placeholder="请输入邮箱地址"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="login" :loading="loading">登录</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
        <el-form-item>
          <span>还没有账号？</span>
          <el-link type="primary" @click="goToRegister">立即注册</el-link>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import authApi from '../api/auth';
import { useUserStore } from '../stores/user';

const router = useRouter();
const userStore = useUserStore();
const loginFormRef = ref(null);
const loading = ref(false);

const loginForm = reactive({
  email: '2311697186@qq.com',
  password: '123456'
});

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
};

const login = () => {
  loginFormRef.value.validate((valid) => {
    if (valid) {
      loading.value = true;
      authApi.login({
        email: loginForm.email,
        password: loginForm.password
      })
        .then(response => {
          console.log('登录响应:', response);
          if (response.code === 200) {
            userStore.setUser({
              userId: response.data.userId,
              username: response.data.username,
              token: response.data.token
            });
            ElMessage.success('登录成功');
            console.log('执行路由跳转');
            router.push('/dashboard/health-info');
          } else {
            ElMessage.error(response.message || '登录失败');
          }
        })
        .catch(error => {
          console.error('登录错误:', error);
          ElMessage.error(error.message || '登录失败，请检查网络连接');
        })
        .finally(() => {
          loading.value = false;
        });
    }
  });
};

const resetForm = () => {
  loginFormRef.value.resetFields();
};

const goToRegister = () => {
  router.push('/register');
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f5f5;
}

.login-form {
  width: 400px;
  padding: 40px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.login-form h2 {
  text-align: center;
  color: #409EFF;
  margin-bottom: 10px;
}

.login-form h3 {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
}

.el-form-item {
  margin-bottom: 20px;
}

.el-form-item:last-child {
  margin-top: 30px;
  text-align: center;
}
</style>