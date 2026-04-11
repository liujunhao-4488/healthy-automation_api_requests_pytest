<template>
  <div class="profile-page">
    <section class="profile-hero">
      <div class="profile-main">
        <el-avatar :size="88" :src="profile.avatar || ''" class="profile-avatar">
          {{ avatarFallback }}
        </el-avatar>
        <div class="profile-copy">
          <p class="eyebrow">PROFILE CENTER</p>
          <h2>{{ profile.username || '未设置用户名' }}</h2>
          <p>{{ profile.email || '未设置邮箱' }}</p>
          <div class="profile-tags">
            <el-tag type="success" effect="plain">
              {{ userStore.isAdmin ? '管理员账号' : '普通用户' }}
            </el-tag>
            <el-tag effect="plain">{{ profile.phone || '未绑定手机号' }}</el-tag>
          </div>
        </div>
      </div>
      <div class="hero-actions">
        <el-button class="soft-button" @click="openEditDialog">编辑资料</el-button>
        <el-button plain @click="openPreferenceDialog">饮食偏好</el-button>
      </div>
    </section>

    <el-row :gutter="20" class="summary-grid">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="summary-card accent-sand">
          <span>注册时间</span>
          <strong>{{ formatDate(profile.createTime) }}</strong>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="summary-card accent-green">
          <span>当前体重</span>
          <strong>{{ displayValue(userStore.healthInfo?.weight, 'kg') }}</strong>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="summary-card accent-cream">
          <div class="summary-meta"><el-icon class="summary-icon"><TrendCharts /></el-icon><span>BMI</span></div>
          <strong>{{ displayValue(userStore.healthInfo?.bmi) }}</strong>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="summary-card accent-mint">
          <span>当前目标</span>
          <strong>{{ goalTypeLabel }}</strong>
        </div>
      </el-col>
    </el-row>

    <div class="content-grid">
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="section-head">
            <span>账号资料</span>
          </div>
        </template>
        <div class="info-list">
          <div class="info-item">
            <label>用户名</label>
            <span>{{ profile.username || '--' }}</span>
          </div>
          <div class="info-item">
            <label>邮箱</label>
            <span>{{ profile.email || '--' }}</span>
          </div>
          <div class="info-item">
            <label>手机号</label>
            <span>{{ profile.phone || '--' }}</span>
          </div>
          <div class="info-item">
            <label>头像状态</label>
            <span>{{ profile.avatar ? '已设置头像' : '未设置头像' }}</span>
          </div>
        </div>
      </el-card>

      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="section-head">
            <span>健康档案摘要</span>
            <el-button text @click="router.push('/dashboard/health-info')">查看详情</el-button>
          </div>
        </template>
        <div class="info-list">
          <div class="info-item">
            <label>年龄</label>
            <span>{{ displayValue(userStore.healthInfo?.age, '岁') }}</span>
          </div>
          <div class="info-item">
            <label>性别</label>
            <span>{{ userStore.healthInfo?.gender || '--' }}</span>
          </div>
          <div class="info-item">
            <label>身高</label>
            <span>{{ displayValue(userStore.healthInfo?.height, 'cm') }}</span>
          </div>
          <div class="info-item">
            <label>基础代谢</label>
            <span>{{ displayValue(userStore.healthInfo?.bmr, 'kcal') }}</span>
          </div>
          <div class="info-item">
            <label>活动水平</label>
            <span>{{ activityLabel }}</span>
          </div>
          <div class="info-item">
            <label>慢性疾病</label>
            <span>{{ userStore.healthInfo?.chronicDiseases || '无' }}</span>
          </div>
        </div>
      </el-card>
    </div>

    <div class="content-grid">
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="section-head">
            <span>饮食目标摘要</span>
            <el-button text @click="router.push('/dashboard/diet-goal')">查看详情</el-button>
          </div>
        </template>
        <div class="goal-metrics">
          <div class="goal-metric">
            <span>目标类型</span>
            <strong>{{ goalTypeLabel }}</strong>
          </div>
          <div class="goal-metric">
            <span>目标体重</span>
            <strong>{{ displayValue(userStore.dietGoal?.targetWeight, 'kg') }}</strong>
          </div>
          <div class="goal-metric">
            <span>目标热量</span>
            <strong>{{ displayValue(userStore.dietGoal?.targetCalories, 'kcal') }}</strong>
          </div>
          <div class="goal-metric">
            <span>饮水目标</span>
            <strong>{{ displayValue(userStore.dietGoal?.waterTarget, 'ml') }}</strong>
          </div>
        </div>
      </el-card>

      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="section-head">
            <span>饮食偏好</span>
            <el-button text @click="openPreferenceDialog">编辑偏好</el-button>
          </div>
        </template>
        <div class="preference-grid">
          <div class="preference-card">
            <span>饮食类型</span>
            <strong>{{ preference.dietType || '未设置' }}</strong>
          </div>
          <div class="preference-card">
            <span>每日餐次</span>
            <strong>{{ preference.mealFrequency || 3 }} 餐/天</strong>
          </div>
          <div class="preference-card">
            <span>忌口/过敏</span>
            <strong>{{ preference.allergies || '未设置' }}</strong>
          </div>
          <div class="preference-card">
            <span>喜欢食材</span>
            <strong>{{ preference.favorites || '未设置' }}</strong>
          </div>
          <div class="preference-card">
            <span>不喜欢食材</span>
            <strong>{{ preference.dislikes || '未设置' }}</strong>
          </div>
          <div class="preference-card">
            <span>零食偏好</span>
            <strong>{{ preference.snackPreference === 0 ? '尽量不吃零食' : '可接受少量零食' }}</strong>
          </div>
        </div>
      </el-card>
    </div>

    <el-card class="info-card" shadow="never">
      <template #header>
        <div class="section-head">
          <span>快捷入口</span>
        </div>
      </template>
<div class="shortcut-grid">
        <button class="shortcut-card" @click="router.push('/dashboard/diet-record')">
          <strong>查看饮食记录</strong>
          <span>检查每日摄入与趋势分析</span>
        </button>
        <button class="shortcut-card" @click="router.push('/dashboard/custom-recipe')">
          <strong>我的自定义食谱</strong>
          <span>管理自己的食谱与营养分析</span>
        </button>
        <button class="shortcut-card" @click="router.push('/dashboard/collected-articles')">
          <strong>我的收藏文章</strong>
          <span>查看已收藏的健康知识文章</span>
        </button>
        <button class="shortcut-card" @click="router.push('/dashboard/collected-recipes')">
          <strong>我的收藏食谱</strong>
          <span>查看已经收藏的系统食谱和自定义食谱</span>
        </button>
      </div>
    </el-card>

    <el-card v-if="false" class="info-card" shadow="never">
      <template #header>
        <div class="section-head">
          <span>我的收藏食谱</span>
          <el-tag type="warning" effect="plain">{{ collectedRecipes.length }} 道</el-tag>
        </div>
      </template>
      <div v-if="collectedRecipes.length" class="collection-list">
        <button
          v-for="recipe in collectedRecipes.slice(0, 5)"
          :key="recipe.id"
          class="collection-row"
          @click="router.push('/dashboard/recipe-recommend')"
        >
          <strong>{{ recipe.name }}</strong>
          <span>{{ recipe.description || '已加入收藏，方便后续再次查看' }}</span>
        </button>
      </div>
      <el-empty v-else description="还没有收藏食谱" />
    </el-card>

    <el-dialog v-model="dialogVisible" title="编辑个人资料" width="520px" class="profile-dialog">
      <div class="profile-edit-dialog">
        <div class="dialog-avatar-section">
          <el-avatar :size="132" :src="editForm.avatar || ''" class="dialog-avatar-preview">
            {{ editAvatarFallback }}
          </el-avatar>
          <input ref="avatarInputRef" type="file" accept="image/*" class="avatar-file-input" @change="handleAvatarChange">
          <el-button class="dialog-avatar-btn" @click="avatarInputRef?.click()">更换头像</el-button>
          <span class="avatar-upload-tip">支持本地图片上传，建议选择 2MB 以内的 JPG/PNG 图片</span>
        </div>

        <el-form :model="editForm" label-position="top" class="profile-edit-form">
          <el-form-item label="用户名">
            <el-input v-model="editForm.username" maxlength="50" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="editForm.phone" maxlength="11" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="preferenceDialogVisible" title="饮食偏好设置" width="620px">
      <el-form :model="preferenceForm" label-width="100px">
        <el-form-item label="饮食类型">
          <el-input v-model="preferenceForm.dietType" placeholder="如清淡、低糖、高蛋白、素食等" />
        </el-form-item>
        <el-form-item label="过敏/忌口">
          <el-input
            v-model="preferenceForm.allergies"
            type="textarea"
            :rows="2"
            placeholder="如海鲜、花生、乳糖不耐受"
          />
        </el-form-item>
        <el-form-item label="不喜欢食材">
          <el-input v-model="preferenceForm.dislikes" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="喜欢食材">
          <el-input v-model="preferenceForm.favorites" type="textarea" :rows="2" />
        </el-form-item>
        <div class="grid-two">
          <el-form-item label="每日餐次">
            <el-input-number v-model="preferenceForm.mealFrequency" :min="1" :max="8" />
          </el-form-item>
          <el-form-item label="零食偏好">
            <el-switch
              v-model="preferenceSnackSwitch"
              inline-prompt
              active-text="会吃"
              inactive-text="不吃"
            />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="preferenceDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="preferenceSaving" @click="savePreference">保存偏好</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { Calendar, CollectionTag, DataAnalysis, Document, EditPen, Memo, Reading, Star, TrendCharts, User } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';
import { useUserStore } from '../stores/user';
import userApi from '../api/user';

const router = useRouter();
const userStore = useUserStore();
const dialogVisible = ref(false);
const preferenceDialogVisible = ref(false);
const saving = ref(false);
const preferenceSaving = ref(false);
const collectedRecipes = ref([]);
const avatarInputRef = ref(null);

const profile = reactive({
  userId: null,
  username: '',
  email: '',
  phone: '',
  avatar: '',
  createTime: '',
  updateTime: '',
  role: 'user'
});

const editForm = reactive({
  username: '',
  phone: '',
  avatar: ''
});

const preference = reactive({
  dietType: '',
  allergies: '',
  dislikes: '',
  favorites: '',
  mealFrequency: 3,
  snackPreference: 1
});

const preferenceForm = reactive({
  dietType: '',
  allergies: '',
  dislikes: '',
  favorites: '',
  mealFrequency: 3,
  snackPreference: 1
});

const goalLabelMap = {
  fat_loss: '减肥减脂',
  muscle_toning: '增肌塑形',
  weight_maintenance: '维持体重',
  healthy_weight_gain: '健康增重',
  blood_sugar_control: '控糖饮食',
  lipid_control: '控脂降脂',
  low_sodium: '控压低盐',
  pregnancy_nutrition: '孕妇营养',
  child_growth: '儿童成长',
  senior_wellness: '老年养生'
};

const activityMap = {
  sedentary: '久坐',
  lightly_active: '轻度活动',
  moderately_active: '中度活动',
  very_active: '高强度活动',
  extra_active: '超高强度活动'
};

const avatarFallback = computed(() => (profile.username || userStore.username || 'U').trim().charAt(0).toUpperCase());
const editAvatarFallback = computed(() => (editForm.username || profile.username || 'U').trim().charAt(0).toUpperCase());
const goalTypeLabel = computed(() => goalLabelMap[userStore.dietGoal?.goalType] || '--');
const activityLabel = computed(() => activityMap[userStore.healthInfo?.activityLevel] || '--');
const preferenceSnackSwitch = computed({
  get: () => preferenceForm.snackPreference !== 0,
  set: (value) => {
    preferenceForm.snackPreference = value ? 1 : 0;
  }
});

const displayValue = (value, unit = '') => {
  if (value === null || value === undefined || value === '') return '--';
  const normalizedValue =
    typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(1)) : value;
  return `${normalizedValue}${unit ? ` ${unit}` : ''}`;
};

const formatDate = (value) => {
  if (!value) return '--';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '--' : date.toLocaleDateString('zh-CN');
};

const syncProfile = (data) => {
  profile.userId = data.userId ?? userStore.userId;
  profile.username = data.username ?? userStore.username;
  profile.email = data.email ?? userStore.email;
  profile.phone = data.phone ?? userStore.phone;
  profile.avatar = data.avatar ?? userStore.avatar;
  profile.createTime = data.createTime || profile.createTime;
  profile.updateTime = data.updateTime || profile.updateTime;
  profile.role = data.role || userStore.role;

  userStore.updateProfile({
    username: profile.username,
    email: profile.email,
    phone: profile.phone,
    avatar: profile.avatar,
    role: profile.role
  });
};

const syncPreference = (data = {}) => {
  preference.dietType = data.dietType || '';
  preference.allergies = data.allergies || '';
  preference.dislikes = data.dislikes || '';
  preference.favorites = data.favorites || '';
  preference.mealFrequency = data.mealFrequency || 3;
  preference.snackPreference = data.snackPreference ?? 1;
};

const loadProfile = async () => {
  try {
    const response = await userApi.getProfile();
    if (response.code === 200 && response.data) {
      syncProfile(response.data);
      return;
    }
  } catch (error) {
    console.error('获取个人资料失败:', error);
  }

  syncProfile({
    userId: userStore.userId,
    username: userStore.username,
    email: userStore.email,
    phone: userStore.phone,
    avatar: userStore.avatar,
    role: userStore.role
  });
};

const loadPreference = async () => {
  try {
    const response = await userApi.getDietPreference();
    if (response.code === 200) {
      syncPreference(response.data);
    }
  } catch (error) {
    console.error('获取饮食偏好失败:', error);
  }
};

const openEditDialog = () => {
  editForm.username = profile.username;
  editForm.phone = profile.phone;
  editForm.avatar = profile.avatar;
  dialogVisible.value = true;
};

const handleAvatarChange = (event) => {
  const file = event?.target?.files?.[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件');
    event.target.value = '';
    return;
  }

  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning('头像图片请控制在 2MB 以内');
    event.target.value = '';
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    editForm.avatar = typeof reader.result === 'string' ? reader.result : '';
  };
  reader.onerror = () => {
    ElMessage.error('读取图片失败，请重新选择');
  };
  reader.readAsDataURL(file);
  event.target.value = '';
};

const openPreferenceDialog = () => {
  preferenceForm.dietType = preference.dietType;
  preferenceForm.allergies = preference.allergies;
  preferenceForm.dislikes = preference.dislikes;
  preferenceForm.favorites = preference.favorites;
  preferenceForm.mealFrequency = preference.mealFrequency;
  preferenceForm.snackPreference = preference.snackPreference;
  preferenceDialogVisible.value = true;
};

const saveProfile = async () => {
  saving.value = true;
  try {
    const response = await userApi.updateProfile({
      username: editForm.username,
      phone: editForm.phone,
      avatar: editForm.avatar
    });

    if (response.code === 200 && response.data) {
      syncProfile(response.data);
      dialogVisible.value = false;
      ElMessage.success('个人资料已更新');
      return;
    }

    ElMessage.error(response.message || '保存失败');
  } catch (error) {
    ElMessage.error(error.message || '保存失败，请检查输入内容');
  } finally {
    saving.value = false;
  }
};

const savePreference = async () => {
  preferenceSaving.value = true;
  try {
    const response = await userApi.updateDietPreference({
      dietType: preferenceForm.dietType,
      allergies: preferenceForm.allergies,
      dislikes: preferenceForm.dislikes,
      favorites: preferenceForm.favorites,
      mealFrequency: preferenceForm.mealFrequency,
      snackPreference: preferenceForm.snackPreference
    });

    if (response.code === 200) {
      syncPreference(response.data);
      preferenceDialogVisible.value = false;
      ElMessage.success('饮食偏好已更新');
      return;
    }

    ElMessage.error(response.message || '保存饮食偏好失败');
  } catch (error) {
    ElMessage.error(error.message || '保存饮食偏好失败');
  } finally {
    preferenceSaving.value = false;
  }
};

onMounted(async () => {
  await Promise.all([loadProfile(), loadPreference()]);
});
</script>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.profile-hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 28px 30px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, rgba(196, 226, 210, 0.35), transparent 42%),
    linear-gradient(135deg, #f9fffb 0%, #edf7ef 100%);
  border: 1px solid #dcecdf;
}

.profile-main {
  display: flex;
  align-items: center;
  gap: 18px;
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.profile-avatar {
  box-shadow: 0 14px 30px rgba(76, 103, 81, 0.12);
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #6f8f72;
}

.profile-copy h2 {
  margin: 0;
  font-family: 'Noto Serif SC', serif;
  font-size: 30px;
  color: #334235;
}

.profile-copy p {
  margin: 8px 0 0;
  color: #6b796d;
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.section-title .el-icon {
  color: #6f8f72;
}

.profile-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.soft-button {
  border-color: #cfe0d2;
  color: #46614a;
  background: #f4fbf5;
}

.summary-grid {
  margin: 0;
}

.summary-card {
  min-height: 126px;
  padding: 22px;
  border-radius: 22px;
  color: #334235;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 12px 28px rgba(59, 79, 63, 0.06);
}

.summary-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.summary-card span {
  color: #738075;
}

.summary-icon {
  font-size: 18px;
}

.summary-card strong {
  font-size: 26px;
  font-weight: 600;
}

.accent-sand {
  background: linear-gradient(180deg, #fffaf4 0%, #f1e5d7 100%);
}

.accent-green {
  background: linear-gradient(180deg, #f4fbf5 0%, #dcefdc 100%);
}

.accent-cream {
  background: linear-gradient(180deg, #fcfbf6 0%, #ece7d8 100%);
}

.accent-mint {
  background: linear-gradient(180deg, #f3fcf7 0%, #d8eee3 100%);
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 22px;
}

.info-card {
  border: 1px solid #e4ecdf;
  border-radius: 22px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #334235;
  font-weight: 600;
}

.info-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.info-item,
.goal-metric,
.preference-card {
  padding: 16px 18px;
  border-radius: 16px;
  background: #f7faf6;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item label {
  font-size: 13px;
  color: #829084;
}

.info-item span,
.preference-card strong {
  color: #334235;
  line-height: 1.6;
}

.goal-metrics,
.preference-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.goal-metric span,
.preference-card span {
  display: block;
  color: #718073;
}

.goal-metric strong {
  color: #334235;
  font-size: 24px;
}

.collection-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.collection-row {
  border: 1px solid #dfe8df;
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f6fbf7 100%);
  padding: 16px 18px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.collection-row:hover,
.shortcut-card:hover {
  border-color: #a6c3ab;
  box-shadow: 0 12px 24px rgba(80, 108, 86, 0.08);
}

.collection-row strong,
.shortcut-card strong {
  display: block;
  margin-bottom: 6px;
  color: #334235;
}

.collection-row span,
.shortcut-card span {
  color: #738075;
  line-height: 1.6;
}

.shortcut-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.shortcut-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.shortcut-card {
  border: 1px solid #dfe8df;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f6fbf7 100%);
  padding: 18px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-edit-dialog {
  padding-top: 6px;
}

.dialog-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  margin-bottom: 22px;
}

.dialog-avatar-preview {
  box-shadow: 0 14px 30px rgba(52, 73, 94, 0.14);
}

.dialog-avatar-btn {
  min-width: 150px;
  height: 64px;
  border-radius: 24px;
  border: 1px solid #e8ebf0;
  background: linear-gradient(180deg, #ffffff 0%, #f2f4f7 100%);
  color: #223042;
  font-size: 16px;
}

.avatar-file-input {
  display: none;
}

.avatar-upload-tip {
  color: #7b8796;
  font-size: 13px;
  text-align: center;
  line-height: 1.5;
}

.profile-edit-form :deep(.el-form-item__label) {
  color: #5e6b7a;
}

@media (max-width: 960px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .profile-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-card strong,
  .goal-metric strong {
    font-size: 22px;
  }

  .info-list,
  .goal-metrics,
  .preference-grid,
  .shortcut-grid,
  .grid-two {
    grid-template-columns: 1fr;
  }
}
</style>
