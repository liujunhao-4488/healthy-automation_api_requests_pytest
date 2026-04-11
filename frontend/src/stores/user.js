import { defineStore } from 'pinia';

const STORAGE_KEY = 'health-user';
const RECENT_ACCOUNTS_KEY = 'health-recent-accounts';
const INGREDIENT_ASSISTANT_HISTORY_PREFIX = 'health-ingredient-assistant-history';

const buildIngredientHistoryKey = (user) => {
  const identifier = user?.userId || user?.email || 'guest';
  return `${INGREDIENT_ASSISTANT_HISTORY_PREFIX}:${identifier}`;
};

const loadIngredientAssistantHistory = (user) => {
  const raw = localStorage.getItem(buildIngredientHistoryKey(user));
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    return [];
  }
};

const persistIngredientAssistantHistory = (user, history) => {
  localStorage.setItem(
    buildIngredientHistoryKey(user),
    JSON.stringify(Array.isArray(history) ? history : [])
  );
};

const loadPersistedUser = () => {
  const token = localStorage.getItem('token') || '';
  const raw = localStorage.getItem(STORAGE_KEY);

  if (!raw) {
    return {
      userId: null,
      username: '',
      email: '',
      phone: '',
      avatar: '',
      role: 'user',
      token,
      healthInfo: null,
      healthAnalysis: null,
      dietGoal: null,
      dietGoalMeta: null,
      healthHistory: [],
      recipeRecommendations: null,
      ingredientAssistantHistory: []
    };
  }

  try {
    const persisted = JSON.parse(raw);
    return {
      userId: persisted.userId ?? null,
      username: persisted.username ?? '',
      email: persisted.email ?? '',
      phone: persisted.phone ?? '',
      avatar: persisted.avatar ?? '',
      role: persisted.role ?? 'user',
      token: persisted.token || token,
      healthInfo: persisted.healthInfo ?? null,
      healthAnalysis: persisted.healthAnalysis ?? null,
      dietGoal: persisted.dietGoal ?? null,
      dietGoalMeta: persisted.dietGoalMeta ?? null,
      healthHistory: Array.isArray(persisted.healthHistory) ? persisted.healthHistory : [],
      recipeRecommendations: persisted.recipeRecommendations ?? null,
      ingredientAssistantHistory: loadIngredientAssistantHistory(persisted)
    };
  } catch (error) {
    return {
      userId: null,
      username: '',
      email: '',
      phone: '',
      avatar: '',
      role: 'user',
      token,
      healthInfo: null,
      healthAnalysis: null,
      dietGoal: null,
      dietGoalMeta: null,
      healthHistory: [],
      recipeRecommendations: null,
      ingredientAssistantHistory: loadIngredientAssistantHistory()
    };
  }
};

const normalizeHealthSnapshot = (info) => ({
  date: new Date().toISOString(),
  weight: info?.weight ?? null,
  bmi: info?.bmi ?? null,
  bmr: info?.bmr ?? null
});

const isHealthProfileComplete = (info) =>
  Boolean(
    info &&
    info.age &&
    info.gender &&
    info.height &&
    info.weight &&
    info.activityLevel
  );

const loadRecentAccounts = () => {
  const raw = localStorage.getItem(RECENT_ACCOUNTS_KEY);

  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    return [];
  }
};

export const useUserStore = defineStore('user', {
  state: () => loadPersistedUser(),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin',
    hasHealthInfo: (state) => !!state.healthInfo,
    hasDietGoal: (state) => !!state.dietGoal,
    hasCompletedHealthProfile: (state) => isHealthProfileComplete(state.healthInfo)
  },
  actions: {
    getRecentAccounts() {
      return loadRecentAccounts();
    },
    saveRecentAccount(account) {
      if (!account?.email || !account?.password) {
        return;
      }

      const current = loadRecentAccounts();
      const next = [
        {
          email: account.email,
          password: account.password,
          username: account.username || '',
          role: account.role || 'user',
          lastLoginAt: new Date().toISOString()
        },
        ...current.filter((item) => item.email !== account.email)
      ].slice(0, 5);

      localStorage.setItem(RECENT_ACCOUNTS_KEY, JSON.stringify(next));
    },
    removeRecentAccount(email) {
      const current = loadRecentAccounts();
      const next = current.filter((item) => item.email !== email);
      localStorage.setItem(RECENT_ACCOUNTS_KEY, JSON.stringify(next));
    },
    persistState() {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          userId: this.userId,
          username: this.username,
          email: this.email,
          phone: this.phone,
          avatar: this.avatar,
          role: this.role,
          token: this.token,
          healthInfo: this.healthInfo,
          healthAnalysis: this.healthAnalysis,
          dietGoal: this.dietGoal,
          dietGoalMeta: this.dietGoalMeta,
          healthHistory: this.healthHistory,
          recipeRecommendations: this.recipeRecommendations,
          ingredientAssistantHistory: this.ingredientAssistantHistory
        })
      );
    },
    setUser(user) {
      this.userId = user.userId;
      this.username = user.username;
      this.email = user.email || '';
      this.phone = user.phone || '';
      this.avatar = user.avatar || '';
      this.role = user.role || 'user';
      this.token = user.token || '';
      this.ingredientAssistantHistory = loadIngredientAssistantHistory({
        userId: this.userId,
        email: this.email
      });
      localStorage.setItem('token', this.token);
      this.persistState();
    },
    updateProfile(profile) {
      this.username = profile.username ?? this.username;
      this.email = profile.email ?? this.email;
      this.phone = profile.phone ?? this.phone;
      this.avatar = profile.avatar ?? this.avatar;
      this.role = profile.role || this.role;
      this.persistState();
    },
    setHealthInfo(info) {
      this.healthInfo = info;

      if (!info) {
        this.persistState();
        return;
      }

      const snapshot = normalizeHealthSnapshot(info);
      const previous = this.healthHistory[this.healthHistory.length - 1];
      const shouldAppend =
        !previous ||
        previous.weight !== snapshot.weight ||
        previous.bmi !== snapshot.bmi ||
        previous.bmr !== snapshot.bmr;

      if (shouldAppend) {
        this.healthHistory = [...this.healthHistory.slice(-9), snapshot];
      }

      this.persistState();
    },
    setHealthAnalysis(analysis) {
      this.healthAnalysis = analysis || null;
      this.persistState();
    },
    setDietGoal(goal) {
      this.dietGoal = goal;
      this.persistState();
    },
    setDietGoalMeta(meta) {
      this.dietGoalMeta = meta;
      this.persistState();
    },
    setRecipeRecommendations(recommendations) {
      this.recipeRecommendations = recommendations;
      this.persistState();
    },
    setIngredientAssistantHistory(history) {
      this.ingredientAssistantHistory = Array.isArray(history) ? history : [];
      persistIngredientAssistantHistory(
        {
          userId: this.userId,
          email: this.email
        },
        this.ingredientAssistantHistory
      );
      this.persistState();
    },
    clearIngredientAssistantHistory() {
      this.ingredientAssistantHistory = [];
      persistIngredientAssistantHistory(
        {
          userId: this.userId,
          email: this.email
        },
        []
      );
      this.persistState();
    },
    clearRecipeRecommendations() {
      this.recipeRecommendations = null;
      this.persistState();
    },
    logout() {
      this.userId = null;
      this.username = '';
      this.email = '';
      this.phone = '';
      this.avatar = '';
      this.role = 'user';
      this.token = '';
      this.healthInfo = null;
      this.healthAnalysis = null;
      this.dietGoal = null;
      this.dietGoalMeta = null;
      this.healthHistory = [];
      this.recipeRecommendations = null;
      this.ingredientAssistantHistory = loadIngredientAssistantHistory();
      localStorage.removeItem('token');
      localStorage.removeItem(STORAGE_KEY);
    }
  }
});

export { isHealthProfileComplete };
