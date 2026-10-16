<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- 左：品牌说明区（与登录页保持一致） -->
      <section class="auth-brand">
        <div class="auth-brand__badge">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M12 3c4.2 1.7 6.5 4.9 6.5 8.8 0 3.9-2.9 6.7-6.5 8.2-3.6-1.5-6.5-4.3-6.5-8.2C5.5 7.9 7.8 4.7 12 3z"
              fill="#ffffff"
              fill-opacity="0.92"
            />
            <path d="M12 6.8v9.6" stroke="#668a72" stroke-width="1.5" stroke-linecap="round" />
            <path
              d="M12 11.2c1.6-.4 2.7-1.3 3.2-2.6M12 14.2c-1.5-.4-2.6-1.3-3.1-2.6"
              stroke="#668a72"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
        </div>

        <div>
          <span class="auth-brand__eyebrow">Health Diet System</span>
          <h1 class="auth-brand__title">开启你的<br />个性化饮食健康计划</h1>
          <p class="auth-brand__desc">
            建立账号后完善健康档案，系统将结合饮食目标、身体情况与营养数据生成专属推荐。
          </p>
        </div>

        <ul class="auth-brand__points">
          <li class="auth-brand__point">个性化食谱推荐</li>
          <li class="auth-brand__point">健康档案与目标管理</li>
          <li class="auth-brand__point">饮食记录与智能分析</li>
        </ul>
      </section>

      <!-- 右：注册表单区 -->
      <section class="auth-panel auth-panel--dense">
        <h2 class="auth-panel__title">创建账号</h2>
        <p class="auth-panel__desc">填写基础账号信息，下一步完善健康档案</p>

        <div class="auth-tabs">
          <button type="button" class="auth-tab is-active">账号注册</button>
        </div>

        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="rules"
          label-position="top"
          class="auth-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="registerForm.username" placeholder="请输入用户名" />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input v-model="registerForm.email" placeholder="请输入邮箱地址" />
          </el-form-item>

          <el-form-item label="手机号" prop="phone">
            <el-input v-model="registerForm.phone" placeholder="请输入手机号" />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              show-password
              placeholder="请输入密码"
            />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              show-password
              placeholder="请再次输入密码"
            />
          </el-form-item>

          <el-form-item>
            <el-button class="auth-submit" @click="register" :loading="loading">下一步</el-button>
          </el-form-item>
        </el-form>

        <div class="auth-footer">
          <span>已有账号？</span>
          <el-link @click="goToLogin">立即登录</el-link>
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

<!-- 样式见 src/styles/auth.css（登录/注册共用一份，不再各写一遍） -->
