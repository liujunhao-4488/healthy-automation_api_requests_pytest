/* ============================================================
   app.js · 应用外壳逻辑（鉴权、导航激活、图标、Toast、Modal）
   ============================================================ */
(function () {
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  const UI = {
    $: $,
    $$: $$,

    esc(s) {
      return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    },

    toast(message, type) {
      let wrap = $('.toast-wrap');
      if (!wrap) {
        wrap = document.createElement('div');
        wrap.className = 'toast-wrap';
        document.body.appendChild(wrap);
      }
      const el = document.createElement('div');
      el.className = 'toast' + (type === 'error' ? ' error' : '');
      const icon = type === 'error' ? 'alert' : 'check-circle';
      el.innerHTML = '<i class="ic" data-ic="' + icon + '"></i><span>' + this.esc(message) + '</span>';
      wrap.appendChild(el);
      Icons.hydrate(el);
      setTimeout(function () {
        el.style.opacity = '0';
        el.style.transform = 'translateY(6px)';
        el.style.transition = 'opacity .2s, transform .2s';
        setTimeout(function () { el.remove(); }, 220);
      }, 2600);
    },

    openModal(id) {
      const el = typeof id === 'string' ? document.getElementById(id) : id;
      if (!el) return;
      el.classList.add('open');
      document.body.style.overflow = 'hidden';
      const focusable = el.querySelector('input, textarea, select, button');
      if (focusable) setTimeout(function () { focusable.focus(); }, 120);
    },

    closeModal(id) {
      const el = typeof id === 'string' ? document.getElementById(id) : id;
      if (!el) return;
      el.classList.remove('open');
      document.body.style.overflow = '';
    },

    confirm(message, onConfirm, opts) {
      const o = opts || {};
      const overlay = document.createElement('div');
      overlay.className = 'overlay open';
      overlay.innerHTML =
        '<div class="modal" style="width:min(400px,100%)">' +
          '<div class="modal-hd"><div><h3>' + this.esc(o.title || '确认操作') + '</h3></div>' +
          '<button class="modal-close" data-close><i class="ic" data-ic="x"></i></button></div>' +
          '<div class="modal-bd"><p class="muted" style="font-size:13px">' + this.esc(message) + '</p></div>' +
          '<div class="modal-ft"><button class="btn btn-outline btn-sm" data-cancel>取消</button>' +
          '<button class="btn ' + (o.danger ? 'btn-danger' : 'btn-primary') + ' btn-sm" data-ok>' + this.esc(o.okText || '确认') + '</button></div>' +
        '</div>';
      document.body.appendChild(overlay);
      Icons.hydrate(overlay);
      const close = function () {
        overlay.classList.remove('open');
        document.body.style.overflow = '';
        setTimeout(function () { overlay.remove(); }, 220);
      };
      overlay.querySelector('[data-close]').onclick = close;
      overlay.querySelector('[data-cancel]').onclick = close;
      overlay.querySelector('[data-ok]').onclick = function () {
        close();
        if (onConfirm) onConfirm();
      };
      overlay.addEventListener('click', function (e) {
        if (e.target === overlay) close();
      });
    },

    loading(btn, on, text) {
      if (!btn) return;
      if (on) {
        btn.dataset.oldHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span><span>' + this.esc(text || '处理中') + '</span>';
      } else {
        btn.disabled = false;
        if (btn.dataset.oldHtml) btn.innerHTML = btn.dataset.oldHtml;
      }
    },

    // 页面加载骨架：替换容器内容
    skeleton(container, lines) {
      if (!container) return;
      let html = '';
      for (let i = 0; i < (lines || 3); i++) {
        html += '<div class="sk" style="height:14px;margin-bottom:10px;width:' + (90 - i * 12) + '%"></div>';
      }
      container.innerHTML = html;
    },

    empty(title, desc, icon) {
      return '<div class="empty"><div class="empty-ico"><i class="ic" data-ic="' + (icon || 'bowl') + '"></i></div>' +
        '<h4>' + this.esc(title) + '</h4><p>' + this.esc(desc || '') + '</p></div>';
    },

    num(n) {
      return Number(n || 0).toLocaleString('zh-CN');
    }
  };

  const App = {
    boot() {
      const page = document.body.dataset.page || '';
      const session = Store.session();

      if (page !== 'login' && !session) {
        location.replace('../index.html');
        return false;
      }

      if (session) {
        document.body.dataset.role = session.role || 'user';
        const name = $('#navUserName');
        const role = $('#navUserRole');
        const avatar = $('#navAvatar');
        if (name) name.textContent = session.username;
        if (role) role.textContent = session.role === 'admin' ? '管理员 · 平台运营' : '普通用户';
        if (avatar) avatar.textContent = (session.username || '用')[0];
      }

      $$('.nav-item').forEach(function (a) {
        if (a.dataset.nav === page) a.classList.add('is-active');
        else a.classList.remove('is-active');
      });

      const badge = $('#navNotifBadge');
      if (badge) {
        const n = Store.unreadCount();
        badge.textContent = n;
        badge.style.display = n ? 'grid' : 'none';
      }

      const menuBtn = $('.mobile-menu-btn');
      const nav = $('.app-nav');
      const scrim = $('.nav-scrim');
      if (menuBtn && nav) {
        menuBtn.addEventListener('click', function () {
          nav.classList.add('is-open');
          if (scrim) scrim.classList.add('is-open');
        });
      }
      if (scrim) {
        scrim.addEventListener('click', function () {
          nav.classList.remove('is-open');
          scrim.classList.remove('is-open');
        });
      }

      const logout = $('#navLogout');
      if (logout) {
        logout.addEventListener('click', function () {
          UI.confirm('退出后需要重新登录，未提交的记录草稿将保留在本机。', function () {
            Store.logout();
            location.href = '../index.html';
          }, { title: '退出登录', okText: '退出', danger: true });
        });
      }

      Icons.hydrate();
      return true;
    },

    refreshBadge() {
      const badge = $('#navNotifBadge');
      if (!badge) return;
      const n = Store.unreadCount();
      badge.textContent = n;
      badge.style.display = n ? 'grid' : 'none';
    },

    greeting() {
      const h = new Date().getHours();
      if (h < 6) return '夜深了';
      if (h < 11) return '早上好';
      if (h < 14) return '中午好';
      if (h < 18) return '下午好';
      return '晚上好';
    },

    userName() {
      const s = Store.session();
      return s ? s.username : '朋友';
    }
  };

  window.UI = UI;
  window.App = App;

  // 外壳在脚本执行时立即挂载（脚本位于每个页面 body 末尾）
  if (document.body) App.boot();
  else document.addEventListener('DOMContentLoaded', function () { App.boot(); });

  // 弹窗通用关闭：ESC / 点击蒙层
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    const open = $('.overlay.open');
    if (open) {
      open.classList.remove('open');
      document.body.style.overflow = '';
    }
  });
  document.addEventListener('click', function (e) {
    const closer = e.target.closest('[data-close-modal]');
    if (closer) {
      const overlay = closer.closest('.overlay');
      if (overlay) {
        overlay.classList.remove('open');
        document.body.style.overflow = '';
      }
    }
  });
})();
