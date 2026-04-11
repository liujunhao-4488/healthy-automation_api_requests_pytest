<template>
  <div class="auth-wrapper">
    <div class="auth-main">
      <div class="auth-header">
        <h1>健康饮食推荐</h1>
        <p class="auth-subtitle">开启您的健康生活</p>
      </div>

      <div class="auth-form">
        <h2>创建账号</h2>
        <el-form :model="registerForm" :rules="rules" ref="registerFormRef" label-position="top">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="registerForm.username" placeholder="请输入用户名" />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input v-model="registerForm.email" placeholder="请输入邮箱" />
          </el-form-item>

          <el-form-item label="手机号" prop="phone">
            <el-input v-model="registerForm.phone" placeholder="请输入手机号" />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
            />
          </el-form-item>

          <el-form-item>
            <el-button class="btn-primary" @click="register" :loading="loading">下一步</el-button>
          </el-form-item>
        </el-form>

        <div class="auth-footer">
          <span>已有账号？</span>
          <el-link class="link-text" @click="goToLogin">立即登录</el-link>
        </div>
      </div>
    </div>

    <div class="auth-decor">
      <div class="decor-line"></div>
      <div class="decor-circle"></div>
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
const registerFormRef = ref(null);
const loading = ref(false);

const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  phone: ''
});

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        const phoneRegex = /^1[3-9]\d{9}$/;
        if (!phoneRegex.test(value)) {
          callback(new Error('请输入有效的手机号'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
};

const register = async () => {
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) {
      return;
    }

    loading.value = true;
    const registerPayload = {
      username: registerForm.username,
      password: registerForm.password,
      email: registerForm.email,
      phone: registerForm.phone
    };

    try {
      const response = await authApi.register(registerPayload);
      if (response.code !== 200) {
        ElMessage.error(response.message || '注册失败');
        return;
      }

      let authData = response.data;
      if (!authData?.token) {
        const loginResponse = await authApi.login({
          email: registerPayload.email,
          password: registerPayload.password
        });

        if (loginResponse.code !== 200) {
          throw new Error(loginResponse.message || '自动登录失败');
        }

        authData = loginResponse.data;
      }

      userStore.setUser({
        userId: authData.userId,
        username: authData.username,
        email: authData.email,
        phone: authData.phone,
        avatar: authData.avatar,
        role: authData.role,
        token: authData.token
      });

      ElMessage.success('注册成功，请继续完善健康信息');
      router.push('/health-info-basic');
    } catch (error) {
      ElMessage.error(error.message || '注册失败，请检查网络连接');
    } finally {
      loading.value = false;
    }
  });
};

const goToLogin = () => {
  router.push('/login');
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
  max-width: 380px;
  position: relative;
  z-index: 2;
}

.auth-header {
  margin-bottom: 48px;
  text-align: left;
}

.auth-header h1 {
  font-family: 'Noto Serif SC', 'Source Han Serif SC', serif;
  font-size: 32px;
  font-weight: 600;
  color: #3D4A3E;
  letter-spacing: 2px;
  margin: 0 0 8px 0;
}

.auth-subtitle {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #8A9A8C;
  letter-spacing: 1px;
}

.auth-form {
  background: #FFF;
  padding: 40px 36px;
  border-radius: 4px;
  box-shadow:
    8px 8px 24px rgba(61, 74, 62, 0.08),
    -2px -2px 8px rgba(255, 255, 255, 0.6);
}

.auth-form h2 {
  font-family: 'Noto Serif SC', 'Source Han Serif SC', serif;
  font-size: 22px;
  font-weight: 500;
  color: #3D4A3E;
  margin: 0 0 32px 0;
  padding-bottom: 16px;
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
  top: 15%;
  right: 20%;
  width: 120px;
  height: 1px;
  background: linear-gradient(90deg, transparent, #C8D8CC, transparent);
}

.decor-line:nth-child(2) {
  top: 25%;
  right: 25%;
  width: 80px;
}

.decor-circle {
  position: absolute;
  bottom: 15%;
  right: 10%;
  width: 200px;
  height: 200px;
  border: 1px solid #E8F0EA;
  border-radius: 50%;
  opacity: 0.5;
}

@media (max-width: 480px) {
  .auth-wrapper {
    padding: 24px 16px;
  }

  .auth-header h1 {
    font-size: 26px;
  }

  .auth-form {
    padding: 28px 20px;
  }
}
</style>
