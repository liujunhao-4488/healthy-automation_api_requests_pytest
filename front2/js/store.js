/* ============================================================
   store.js · 轻量状态层（localStorage 持久化）
   所有页面共享同一份用户 / 档案 / 目标 / 记录 / 收藏 / 通知状态
   ============================================================ */
(function () {
  const PREFIX = 'sh_';
  const K = {
    session: PREFIX + 'session',
    health: PREFIX + 'health',
    pref: PREFIX + 'pref',
    goal: PREFIX + 'goal',
    records: PREFIX + 'records',
    collectRecipe: PREFIX + 'collect_recipe',
    collectArticle: PREFIX + 'collect_article',
    likeArticle: PREFIX + 'like_article',
    readArticle: PREFIX + 'read_article',
    notif: PREFIX + 'notif',
    convos: PREFIX + 'convos',
    water: PREFIX + 'water'
  };

  function todayStr() {
    const d = new Date();
    const p = n => String(n).padStart(2, '0');
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  }
  const TODAY = todayStr();

  function read(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
      return fallback;
    }
  }
  function write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* 忽略配额异常 */ }
  }

  function seed() {
    if (!read(K.records)) {
      const seeded = DB.records.map(r => Object.assign({}, r, { date: TODAY }));
      write(K.records, seeded);
    }
    if (!read(K.collectRecipe)) write(K.collectRecipe, [1, 3]);
    if (!read(K.collectArticle)) write(K.collectArticle, [2]);
    if (!read(K.likeArticle)) write(K.likeArticle, [1]);
    if (!read(K.readArticle)) write(K.readArticle, [{ id: 2, date: '2026-10-21', duration: 186, done: true }]);
    if (!read(K.notif)) {
      write(K.notif, { read: DB.notifications.filter(n => n.read).map(n => n.id), deleted: [] });
    }
    if (!read(K.convos)) write(K.convos, DB.conversations);
    if (!read(K.water)) write(K.water, 4);
  }

  /* ---------------- 会话 ---------------- */
  const Store = {
    TODAY: TODAY,

    session() { return read(K.session, null); },
    login(email, password) {
      // TODO: 替换为 POST /auth/login（邮箱 + 密码，返回 token / userId / role）
      const user = DB.user;
      write(K.session, {
        userId: user.userId, username: user.username, email: email || user.email,
        role: user.role, token: 'mock-jwt-' + Date.now()
      });
      return this.session();
    },
    logout() { localStorage.removeItem(K.session); },
    updateProfile(patch) {
      // TODO: 替换为 PUT /user/profile
      const s = this.session();
      if (!s) return null;
      const next = Object.assign({}, s, patch);
      write(K.session, next);
      return next;
    },

    /* ---------------- 健康档案 ---------------- */
    health() { return read(K.health, DB.health); },
    saveHealth(patch) {
      // TODO: 替换为 POST /health/info
      const next = Object.assign({}, this.health(), patch, { updatedAt: this.now() });
      if (patch.height && patch.weight) {
        const h = patch.height / 100;
        next.bmi = +(patch.weight / (h * h)).toFixed(1);
        next.bmr = Math.round(10 * patch.weight + 6.25 * patch.height - 5 * (patch.age || 29) + (patch.gender === '男' ? 5 : -161));
      }
      write(K.health, next);
      return next;
    },

    /* ---------------- 饮食偏好 ---------------- */
    preferences() { return read(K.pref, DB.preferences); },
    savePreferences(patch) {
      // TODO: 替换为 PUT /user/preferences
      const next = Object.assign({}, this.preferences(), patch);
      write(K.pref, next);
      return next;
    },

    /* ---------------- 饮食目标 ---------------- */
    goal() { return read(K.goal, DB.goal); },
    saveGoal(patch) {
      // TODO: 替换为 POST /health/goal
      const next = Object.assign({}, this.goal(), patch);
      write(K.goal, next);
      return next;
    },

    /* ---------------- 饮食记录 ---------------- */
    records() { return read(K.records, []); },
    recordsByDate(date) { return this.records().filter(r => r.date === date); },
    addRecord(rec) {
      // TODO: 替换为 POST /record/submit（主记录 + 明细数组）
      const all = this.records();
      const item = Object.assign({
        id: 'r-' + Date.now(),
        date: rec.date || TODAY,
        time: rec.time || this.nowTime(),
        note: rec.note || '',
        items: rec.items || []
      }, rec);
      item.kcal = item.items.reduce((s, i) => s + (+i.kcal || 0), 0);
      item.p = +item.items.reduce((s, i) => s + (+i.p || 0), 0).toFixed(1);
      item.c = +item.items.reduce((s, i) => s + (+i.c || 0), 0).toFixed(1);
      item.f = +item.items.reduce((s, i) => s + (+i.f || 0), 0).toFixed(1);
      all.push(item);
      write(K.records, all);
      return item;
    },
    removeRecord(id) {
      // TODO: 替换为 DELETE /record/{recordId}（软删除）
      write(K.records, this.records().filter(r => r.id !== id));
    },
    totals(date) {
      const list = this.recordsByDate(date || TODAY);
      const sum = { kcal: 0, p: 0, c: 0, f: 0 };
      list.forEach(r => {
        (r.items || []).forEach(i => {
          sum.kcal += +i.kcal || 0;
          sum.p += +i.p || 0;
          sum.c += +i.c || 0;
          sum.f += +i.f || 0;
        });
      });
      sum.kcal = Math.round(sum.kcal);
      sum.p = +sum.p.toFixed(1);
      sum.c = +sum.c.toFixed(1);
      sum.f = +sum.f.toFixed(1);
      return sum;
    },
    trend() {
      // TODO: 替换为 GET /record/analysis/trend
      const t = DB.trend7.slice(0, 6).map(d => Object.assign({}, d));
      const todayTotals = this.totals(TODAY);
      t.push({ date: '今天', kcal: todayTotals.kcal, p: todayTotals.p, c: todayTotals.c, f: todayTotals.f });
      return t;
    },

    /* ---------------- 收藏 / 点赞 / 阅读 ---------------- */
    recipeCollected() { return read(K.collectRecipe, []); },
    isRecipeCollected(id) { return this.recipeCollected().includes(+id); },
    toggleRecipeCollect(id) {
      // TODO: 替换为 POST /recipe/collect/{recipeId}
      const list = this.recipeCollected().slice();
      const i = list.indexOf(+id);
      if (i > -1) list.splice(i, 1); else list.push(+id);
      write(K.collectRecipe, list);
      return i === -1;
    },
    articleCollected() { return read(K.collectArticle, []); },
    isArticleCollected(id) { return this.articleCollected().includes(+id); },
    toggleArticleCollect(id) {
      const list = this.articleCollected().slice();
      const i = list.indexOf(+id);
      if (i > -1) list.splice(i, 1); else list.push(+id);
      write(K.collectArticle, list);
      return i === -1;
    },
    articleLiked() { return read(K.likeArticle, []); },
    isArticleLiked(id) { return this.articleLiked().includes(+id); },
    toggleArticleLike(id) {
      const list = this.articleLiked().slice();
      const i = list.indexOf(+id);
      if (i > -1) list.splice(i, 1); else list.push(+id);
      write(K.likeArticle, list);
      return i === -1;
    },
    articleReads() { return read(K.readArticle, []); },
    markArticleRead(id, duration) {
      // TODO: 替换为 POST /article/read/{id}
      const list = this.articleReads().filter(r => r.id !== +id);
      list.unshift({ id: +id, date: TODAY, duration: duration || 120, done: true });
      write(K.readArticle, list.slice(0, 20));
    },

    /* ---------------- 通知 ---------------- */
    notifications() {
      const state = read(K.notif, { read: [], deleted: [] });
      return DB.notifications
        .filter(n => !state.deleted.includes(n.id))
        .map(n => Object.assign({}, n, { read: state.read.includes(n.id) }));
    },
    unreadCount() { return this.notifications().filter(n => !n.read).length; },
    markAllRead() {
      const state = read(K.notif, { read: [], deleted: [] });
      state.read = DB.notifications.map(n => n.id);
      write(K.notif, state);
    },
    markNotifRead(id) {
      const state = read(K.notif, { read: [], deleted: [] });
      if (!state.read.includes(+id)) { state.read.push(+id); write(K.notif, state); }
    },
    removeNotif(id) {
      const state = read(K.notif, { read: [], deleted: [] });
      if (!state.deleted.includes(+id)) { state.deleted.push(+id); write(K.notif, state); }
    },

    /* ---------------- AI 会话 ---------------- */
    conversations() { return read(K.convos, DB.conversations); },
    conversation(id) { return this.conversations().find(c => c.id === id); },
    saveConversation(conv) {
      const list = this.conversations().slice();
      const i = list.findIndex(c => c.id === conv.id);
      if (i > -1) list[i] = conv; else list.unshift(conv);
      write(K.convos, list);
      return conv;
    },
    removeConversation(id) {
      write(K.convos, this.conversations().filter(c => c.id !== id));
    },

    /* ---------------- 饮水 ---------------- */
    water() { return read(K.water, 4); },
    addWater(cup) {
      const v = Math.min(8, Math.max(0, cup));
      write(K.water, v);
      return v;
    },

    /* ---------------- 工具 ---------------- */
    now() {
      const d = new Date();
      const p = n => String(n).padStart(2, '0');
      return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
    },
    nowTime() {
      const d = new Date();
      const p = n => String(n).padStart(2, '0');
      return p(d.getHours()) + ':' + p(d.getMinutes());
    },
    dateLabel(date) {
      if (date === TODAY) return '今天';
      const d = new Date(date + 'T00:00:00');
      const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
      return (d.getMonth() + 1) + '月' + d.getDate() + '日 · ' + week[d.getDay()];
    }
  };

  seed();
  window.Store = Store;
})();
