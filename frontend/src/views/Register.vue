<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="login-brand">
        <div class="brand-icon">
          <div class="brand-icon-inner">
            <span class="brand-monitor"></span>
          </div>
        </div>

        <div class="brand-copy">
          <h1>基于人工智能的个人饮食健康管理系统</h1>
          <p>建立账号后完善健康档案，系统将结合饮食目标、身体情况和营养数据生成个性化推荐。</p>
        </div>

        <ul class="brand-points">
          <li>个性化食谱推荐</li>
          <li>健康档案与目标管理</li>
          <li>饮食记录与智能分析</li>
        </ul>
      </section>

      <section class="login-panel register-panel">
        <div class="panel-head">
          <h2>创建账号</h2>
          <p>填写基础账号信息，下一步完善健康档案</p>
        </div>

        <div class="login-tabs">
          <button type="button" class="tab-item active">账号注册</button>
        </div>

        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="rules"
          label-position="top"
          class="login-form register-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="registerForm.username" placeholder="请输入用户名" class="login-input" />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input v-model="registerForm.email" placeholder="请输入邮箱地址" class="login-input" />
          </el-form-item>

          <el-form-item label="手机号" prop="phone">
            <el-input v-model="registerForm.phone" placeholder="请输入手机号" class="login-input" />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              show-password
              placeholder="请输入密码"
              class="login-input"
            />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              show-password
              placeholder="请再次输入密码"
              class="login-input"
            />
          </el-form-item>

          <el-form-item class="login-submit">
            <el-button class="submit-button" @click="register" :loading="loading">下一步</el-button>
          </el-form-item>
        </el-form>

        <div class="auth-footer">
          <span>已有账号？</span>
          <el-link class="register-link" @click="goToLogin">立即登录</el-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
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
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
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
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background:
    radial-gradient(circle at top left, rgba(123, 160, 136, 0.18), transparent 28%),
    linear-gradient(180deg, #f4f8f6 0%, #edf3ef 100%);
}

.login-shell {
  width: min(1180px, 100%);
  min-height: 720px;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  background: #ffffff;
  border-radius: 32px;
  overflow: hidden;
  box-shadow: 0 28px 80px rgba(77, 104, 88, 0.14);
  border: 1px solid rgba(221, 232, 227, 0.9);
}

.login-brand {
  position: relative;
  padding: 72px 60px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 28px;
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.12), transparent 16%),
    linear-gradient(180deg, #6f9580 0%, #86ab95 100%);
  color: #fff;
}

.brand-icon {
  display: flex;
  justify-content: center;
}

.brand-icon-inner {
  width: 132px;
  height: 132px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(4px);
}

.brand-monitor {
  width: 54px;
  height: 40px;
  border: 4px solid #fff;
  border-radius: 8px;
  position: relative;
  display: block;
}

.brand-monitor::before {
  content: '';
  position: absolute;
  bottom: -16px;
  left: 50%;
  width: 22px;
  height: 4px;
  background: #fff;
  transform: translateX(-50%);
  border-radius: 999px;
}

.brand-monitor::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  width: 4px;
  height: 12px;
  background: #fff;
  transform: translateX(-50%);
  border-radius: 999px;
}

.brand-copy {
  text-align: center;
}

.brand-copy h1 {
  margin: 0 0 14px;
  font-size: 44px;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 1px;
}

.brand-copy p {
  margin: 0;
  font-size: 18px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.88);
}

.brand-points {
  list-style: none;
  margin: 8px auto 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: fit-content;
  color: rgba(255, 255, 255, 0.92);
  font-size: 18px;
}

.brand-points li {
  position: relative;
  padding-left: 28px;
}

.brand-points li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.85);
}

.login-panel {
  padding: 64px 54px 46px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.panel-head h2 {
  margin: 0;
  font-size: 46px;
  line-height: 1.15;
  color: #1d3b2f;
  font-weight: 700;
}

.panel-head p {
  margin: 14px 0 0;
  color: #7d9082;
  font-size: 18px;
}

.login-tabs {
  display: flex;
  gap: 32px;
  margin-top: 32px;
  padding-bottom: 14px;
  border-bottom: 1px solid #dde5ef;
}

.tab-item {
  border: none;
  background: transparent;
  padding: 0 0 12px;
  font-size: 20px;
  color: #6b7f71;
  cursor: default;
}

.tab-item.active {
  color: #7ba088;
  font-weight: 600;
  border-bottom: 3px solid #7ba088;
}

.login-form {
  margin-top: 24px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.login-form :deep(.el-form-item__label) {
  font-size: 15px;
  color: #5d7163;
  padding-bottom: 8px;
}

.login-input :deep(.el-input__wrapper) {
  min-height: 52px;
  border-radius: 14px;
  box-shadow: none;
  background: #fff;
  border: 1px solid #d8e2ef;
  padding: 0 16px;
}

.login-input :deep(.el-input__wrapper:hover) {
  border-color: #bdd1c3;
}

.login-input :deep(.el-input__wrapper.is-focus) {
  border-color: #7ba088;
  box-shadow: 0 0 0 3px rgba(123, 160, 136, 0.14);
}

.login-input :deep(.el-input__inner) {
  font-size: 16px;
  color: #2d4335;
}

.login-submit {
  margin-top: 8px;
}

.submit-button {
  width: 100%;
  height: 54px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(180deg, #7ba088 0%, #6b9078 100%);
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.submit-button:hover {
  background: linear-gradient(180deg, #739982 0%, #62866f 100%);
}

.auth-footer {
  margin-top: 24px;
  text-align: center;
  color: #839587;
  font-size: 15px;
}

.register-link {
  margin-left: 6px;
  color: #7ba088;
  font-size: 15px;
  font-weight: 600;
}

@media (max-width: 980px) {
  .login-shell {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .login-brand {
    padding: 48px 30px;
  }

  .login-panel {
    padding: 44px 28px 36px;
  }

  .brand-copy h1 {
    font-size: 36px;
  }

  .panel-head h2 {
    font-size: 38px;
  }
}

@media (max-width: 640px) {
  .login-page {
    padding: 14px;
  }

  .login-shell {
    border-radius: 22px;
  }

  .login-brand {
    padding: 38px 22px;
  }

  .login-panel {
    padding: 34px 20px 28px;
  }

  .brand-copy h1 {
    font-size: 30px;
  }

  .brand-copy p,
  .brand-points {
    font-size: 15px;
  }

  .panel-head h2 {
    font-size: 32px;
  }

  .panel-head p {
    font-size: 15px;
  }

  .login-tabs {
    gap: 20px;
  }

  .tab-item {
    font-size: 17px;
  }
}
</style>
