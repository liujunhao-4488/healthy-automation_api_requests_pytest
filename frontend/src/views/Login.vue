<template>
  <div class="auth-wrapper">
    <div class="auth-main">
      <div class="auth-header">
        <h1>健康饮食推荐</h1>
        <p class="auth-subtitle">科学搭配 · 健康生活</p>
      </div>
      
      <div class="auth-form">
        <h2>登录账号</h2>
        <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-position="top">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="loginForm.email" placeholder="请输入邮箱地址" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" />
          </el-form-item>
          <el-form-item>
            <el-button class="btn-primary" @click="login" :loading="loading">登录</el-button>
          </el-form-item>
          <div class="form-footer">
            <el-button text @click="resetForm" class="btn-text">重置</el-button>
          </div>
        </el-form>
        
        <div class="auth-footer">
          <span>还没有账号？</span>
          <el-link class="link-text" @click="goToRegister">立即注册</el-link>
        </div>
      </div>
    </div>
    
    <div class="auth-decor">
      <div class="decor-line"></div>
      <div class="decor-circle"></div>
      <div class="decor-dot"></div>
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
          if (response.code === 200) {
            userStore.setUser({
              userId: response.data.userId,
              username: response.data.username,
              token: response.data.token
            });
            ElMessage.success('登录成功');
            if (userStore.hasHealthInfo) {
              router.push('/dashboard/health-info');
            } else {
              router.push('/health-info-basic');
            }
          } else {
            ElMessage.error(response.message || '登录失败');
          }
        })
        .catch(error => {
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
.auth-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F7FAF8;
  padding: 40px 20px;
  position: relative;
  overflow: hidden;
}

.auth-main {
  width: 100%;
  max-width: 360px;
  position: relative;
  z-index: 2;
  animation: fadeInUp 0.6s ease-out;
}

.auth-header {
  margin-bottom: 40px;
  text-align: left;
}

.auth-header h1 {
  font-family: 'Noto Serif SC', 'Source Han Serif SC', serif;
  font-size: 30px;
  font-weight: 600;
  color: #3D4A3E;
  letter-spacing: 2px;
  margin: 0 0 6px 0;
}

.auth-subtitle {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #8A9A8C;
  letter-spacing: 1px;
}

.auth-form {
  background: #FFF;
  padding: 36px 32px;
  border-radius: 4px;
  box-shadow: 
    8px 8px 24px rgba(61, 74, 62, 0.08),
    -2px -2px 8px rgba(255, 255, 255, 0.6);
  animation: scaleIn 0.5s ease-out 0.1s both;
}

.auth-form h2 {
  font-family: 'Noto Serif SC', 'Source Han Serif SC', serif;
  font-size: 20px;
  font-weight: 500;
  color: #3D4A3E;
  margin: 0 0 28px 0;
  padding-bottom: 14px;
  border-bottom: 1px solid #E8F0EA;
}

.auth-form :deep(.el-form-item__label) {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #5A6B5C;
  padding-bottom: 6px;
}

.auth-form :deep(.el-input__wrapper) {
  background-color: #F7FAF8;
  border: 1px solid #D8E4DC;
  border-radius: 4px;
  box-shadow: none;
  padding: 8px 12px;
  min-height: 40px;
  transition: all 0.3s ease;
}

.auth-form :deep(.el-input__wrapper:hover) {
  border-color: #B8C8B8;
}

.auth-form :deep(.el-input__wrapper.is-focus) {
  border-color: #9BC1A8;
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.04);
}

.auth-form :deep(.el-input__inner) {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #3D4A3E;
}

.auth-form :deep(.el-input__inner::placeholder) {
  color: #A8B8A8;
}

.btn-primary {
  width: 100%;
  height: 44px;
  background-color: #7BA088;
  border: none;
  border-radius: 4px;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: #FFF;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  margin-top: 8px;
}

.btn-primary:hover {
  background-color: #6A9177;
  transform: scale(1.02);
  box-shadow: 4px 4px 12px rgba(123, 160, 136, 0.25);
}

.btn-primary:active {
  transform: scale(0.98);
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.btn-text {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #8A9A8C;
}

.btn-text:hover {
  color: #5A6B5C;
}

.auth-footer {
  margin-top: 24px;
  text-align: center;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  color: #8A9A8C;
}

.link-text {
  color: #7BA088;
  font-weight: 500;
  margin-left: 4px;
}

.link-text:hover {
  color: #6A9177;
}

.auth-decor {
  position: absolute;
  top: 0;
  right: 0;
  width: 45%;
  height: 100%;
  pointer-events: none;
}

.decor-line {
  position: absolute;
  top: 12%;
  right: 18%;
  width: 100px;
  height: 1px;
  background: linear-gradient(90deg, transparent, #C8D8CC, transparent);
}

.decor-line:nth-child(2) {
  top: 22%;
  right: 24%;
  width: 70px;
}

.decor-circle {
  position: absolute;
  bottom: 12%;
  right: 8%;
  width: 180px;
  height: 180px;
  border: 1px solid #E8F0EA;
  border-radius: 50%;
  opacity: 0.5;
}

.decor-dot {
  position: absolute;
  top: 40%;
  right: 30%;
  width: 6px;
  height: 6px;
  background-color: #B8C8B8;
  border-radius: 50%;
}

@media (max-width: 480px) {
  .auth-wrapper {
    padding: 24px 16px;
  }
  
  .auth-header h1 {
    font-size: 24px;
  }
  
  .auth-form {
    padding: 28px 20px;
  }
  
  .auth-decor {
    display: none;
  }
}
</style>
