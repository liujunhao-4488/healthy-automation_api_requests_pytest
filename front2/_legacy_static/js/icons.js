/* ============================================================
   icons.js · 单图标体系（Lucide 内联 SVG，离线可用）
   用法：<i class="ic" data-ic="home"></i>，由 hydrate() 注入
   ============================================================ */
(function () {
  const P = {
    home: '<path d="M3 10.2 12 3l9 7.2"/><path d="M5 9.6V21h14V9.6"/><path d="M9.5 21v-6.5h5V21"/>',
    dashboard: '<rect x="3" y="3" width="7" height="9" rx="1.6"/><rect x="14" y="3" width="7" height="5" rx="1.6"/><rect x="14" y="12" width="7" height="9" rx="1.6"/><rect x="3" y="16" width="7" height="5" rx="1.6"/>',
    heart: '<path d="M20.8 5.6a5.2 5.2 0 0 0-7.4 0L12 7l-1.4-1.4a5.2 5.2 0 1 0-7.4 7.4l8.1 8.1a1 1 0 0 0 1.4 0l8.1-8.1a5.2 5.2 0 0 0 0-7.4Z"/>',
    'heart-pulse': '<path d="M20.8 5.6a5.2 5.2 0 0 0-7.4 0L12 7l-1.4-1.4a5.2 5.2 0 1 0-7.4 7.4l8.1 8.1a1 1 0 0 0 1.4 0l8.1-8.1a5.2 5.2 0 0 0 0-7.4Z"/><path d="M3.5 12.4h3.6l1.5-2.8 2.8 5.4 1.5-2.6h3.5"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2" fill="currentColor" stroke="none"/>',
    notebook: '<rect x="4" y="3" width="15" height="18" rx="2"/><path d="M8 3v18"/><path d="M11.5 8h4.5M11.5 12h4.5M11.5 16h3"/>',
    'book-open': '<path d="M12 6.5C10.5 5 8.5 4.5 4 4.5v14c4.5 0 6.5.5 8 2 1.5-1.5 3.5-2 8-2v-14c-4.5 0-6.5.5-8 2Z"/><path d="M12 6.5v14"/>',
    book: '<path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5A2.5 2.5 0 0 0 5 21.5v-17Z"/><path d="M5 19.5A2.5 2.5 0 0 1 7.5 17H19"/>',
    apple: '<path d="M12 7c3 0 5 2 5 5 0 4-3.5 8-5 9-1.5-1-5-5-5-9 0-3 2-5 5-5Z"/><path d="M12 7V4"/><path d="M12 4c1-1.5 3-2 4-1.5-.5 1.5-2 2.5-4 2.5"/><path d="M12 4c-1-1.5-3-2-4-1.5.5 1.5 2 2.5 4 2.5"/>',
    news: '<path d="M4 5h13a2 2 0 0 1 2 2v12H6a2 2 0 0 1-2-2V5Z"/><path d="M7 9.5h7M7 13h7M7 16.5h4"/><path d="M19 8.5h1a1 1 0 0 1 1 1v8a2 2 0 0 1-2 2"/>',
    sparkles: '<path d="m12 3 1.9 4.6L18.5 9.5l-4.6 1.9L12 16l-1.9-4.6L5.5 9.5l4.6-1.9Z"/><path d="M18.5 15.5l.8 1.9 2 .8-2 .8-.8 1.9-.8-1.9-2-.8 2-.8Z"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M5 21c0-3.9 3.1-7 7-7s7 3.1 7 7"/>',
    settings: '<path d="M4 6h9M17.5 6H20M4 12h3M11.5 12H20M4 18h9M17.5 18H20"/><circle cx="15.2" cy="6" r="2.2"/><circle cx="9.2" cy="12" r="2.2"/><circle cx="15.2" cy="18" r="2.2"/>',
    bell: '<path d="M18 8a6 6 0 1 0-12 0c0 6-2 7-2 7h16s-2-1-2-7Z"/><path d="M10.4 20a1.9 1.9 0 0 0 3.2 0"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20.5 20.5-3.6-3.6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 6.5"/>',
    'check-circle': '<circle cx="12" cy="12" r="9"/><path d="m8.4 12.2 2.5 2.5 4.7-5.2"/>',
    x: '<path d="m6 6 12 12M18 6 6 18"/>',
    'chevron-right': '<path d="m9 5 7 7-7 7"/>',
    'chevron-left': '<path d="m15 5-7 7 7 7"/>',
    'chevron-down': '<path d="m5 9 7 7 7-7"/>',
    flame: '<path d="M12 2.5c.8 3.2-1.8 4.4-1.8 6.8a1.8 1.8 0 0 0 3.6 0c0-.8 0-1.5-.4-2.2 2 1.4 3.6 3.7 3.6 6.2a6 6 0 0 1-12 0c0-4.6 4-7 7-10.8Z"/>',
    droplet: '<path d="M12 3s6 6.2 6 10a6 6 0 0 1-12 0c0-3.8 6-10 6-10Z"/>',
    wheat: '<path d="M12 21V9"/><path d="M12 9c-3 0-4-2-4-4 2 0 4 1 4 4Z"/><path d="M12 9c3 0 4-2 4-4-2 0-4 1-4 4Z"/><path d="M12 14.5c-3 0-4-2-4-4 2 0 4 1 4 4Z"/><path d="M12 14.5c3 0 4-2 4-4-2 0-4 1-4 4Z"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.2l3.4 2"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    'trend-up': '<path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    'trend-down': '<path d="m3 7 6 6 4-4 8 8"/><path d="M15 17h6v-6"/>',
    trash: '<path d="M4 7h16"/><path d="M9.5 7V4.8h5V7"/><path d="M6 7l1 14h10l1-14"/><path d="M10 11v6M14 11v6"/>',
    star: '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1L3.2 9.5l6.1-.9Z"/>',
    message: '<path d="M21 11.5a8.4 8.4 0 0 1-8.9 8.4 9.6 9.6 0 0 1-3.8-.8L3 21l1.9-4.6A8.4 8.4 0 1 1 21 11.5Z"/>',
    send: '<path d="M21 3 10.6 13.4"/><path d="M21 3l-6.7 18-3.7-7.6L3 9.7Z"/>',
    'arrow-right': '<path d="M4 12h16"/><path d="m14.5 6 6 6-6 6"/>',
    'arrow-left': '<path d="M20 12H4"/><path d="m9.5 6-6 6 6 6"/>',
    refresh: '<path d="M20 11a8 8 0 1 0-2.4 5.7"/><path d="M20 3.5v7.5h-7.5"/>',
    filter: '<path d="M4 5h16l-6.2 7.2V19l-3.6 2v-8.8Z"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    logout: '<path d="M9.5 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4.5"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9.5"/>',
    alert: '<path d="M10.3 4 2.6 17.4A2 2 0 0 0 4.3 20h15.4a2 2 0 0 0 1.7-2.6L13.7 4a2 2 0 0 0-3.4 0Z"/><path d="M12 9.5v4M12 17h.01"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="3"/>',
    bookmark: '<path d="M6.5 3h11a1 1 0 0 1 1 1v17l-6.5-3.8L5.5 21V4a1 1 0 0 1 1-1Z"/>',
    'thumbs-up': '<path d="M7 10.5V21H4.2V10.5H7Z"/><path d="M7 10.5 11 3.4a2 2 0 0 1 3 2v3.6h5a2 2 0 0 1 2 2.3l-1.2 7A2 2 0 0 1 17.8 21H7"/>',
    reply: '<path d="M9.5 17 4 11.5 9.5 6"/><path d="M20 18.5v-2.2a4.3 4.3 0 0 0-4.3-4.3H4"/>',
    more: '<circle cx="5" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="19" cy="12" r="1.4" fill="currentColor" stroke="none"/>',
    lock: '<rect x="4" y="10" width="16" height="11" rx="2.4"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="2.4"/><path d="m3.5 7.5 8.5 5.8 8.5-5.8"/>',
    phone: '<path d="M5 3h3.2l2 5-2.6 1.6a12.5 12.5 0 0 0 5.3 5.3L14.5 12l5 2v3.1a2.2 2.2 0 0 1-2.4 2.2A16.5 16.5 0 0 1 2.8 5.4 2.2 2.2 0 0 1 5 3Z"/>',
    shield: '<path d="M12 3 5 6v6c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6l-7-3Z"/><path d="m9 12 2.2 2.2L15.5 10"/>',
    activity: '<path d="M3 12h4l2.4-7 5.2 14 2.4-7H21"/>',
    users: '<circle cx="9" cy="8" r="3.6"/><path d="M2.6 20c0-3.6 2.9-6.5 6.4-6.5s6.4 2.9 6.4 6.5"/><path d="M16.2 5.1a3.6 3.6 0 0 1 0 6.9"/><path d="M18.2 13.8A6.4 6.4 0 0 1 21.6 20"/>',
    'file-text': '<path d="M14 3H6.5A1.5 1.5 0 0 0 5 4.5v15A1.5 1.5 0 0 0 6.5 21h11A1.5 1.5 0 0 0 19 19.5V8l-5-5Z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/>',
    utensils: '<path d="M6 3v6.5a2 2 0 0 0 4 0V3"/><path d="M8 9.5V21"/><path d="M15.5 3c-1.4 1.2-2 3.2-2 5.2s.6 3.1 2 3.4V21"/><path d="M17.8 3c1.2 1.3 1.8 3.2 1.8 5.2s-.6 3.1-1.8 3.4"/>',
    scale: '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M7.8 11a4.2 4.2 0 0 1 8.4 0"/><path d="m12 11-2.2 3"/><path d="M12 16h.01"/>',
    edit: '<path d="M4 20h4.2L19 9.2 14.8 5 4 15.8V20Z"/><path d="m13.2 6.6 4.2 4.2"/>',
    'shopping-bag': '<path d="M6 8h12l1 13H5L6 8Z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M19 5l-1.5 1.5M6.5 17.5 5 19"/>',
    coffee: '<path d="M4 8h13v6.5a4.5 4.5 0 0 1-4.5 4.5h-4A4.5 4.5 0 0 1 4 14.5V8Z"/><path d="M17 9.5h2a2.7 2.7 0 0 1 0 5.4h-2"/><path d="M7 3.5v2M11 3.5v2"/>',
    dumbbell: '<path d="M4 9.5v5M7 7.5v9M17 7.5v9M20 9.5v5M7 12h10"/>',
    play: '<circle cx="12" cy="12" r="9"/><path d="m10 8.2 6 3.8-6 3.8V8.2Z"/>',
    bowl: '<path d="M3.5 12h17"/><path d="M5 12a7 7 0 0 1 14 0"/><path d="M4.5 16.5h15a2 2 0 0 1-2 2h-11a2 2 0 0 1-2-2Z"/><path d="M8.5 8c0-1.8.8-3 2.5-3.4M15.5 8c0-1.8-.8-3-2.5-3.4"/>',
    salad: '<path d="M3 12.5h18"/><path d="M4.5 12.5a7.5 7.5 0 0 1 15 0"/><path d="M4 12.5h16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z"/>',
    'map-pin': '<path d="M12 21s7-5.4 7-11a7 7 0 1 0-14 0c0 5.6 7 11 7 11Z"/><circle cx="12" cy="10" r="2.6"/>',
    image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9.5" r="1.6"/><path d="m4 17 4.5-4.5 3.5 3.5 3-3 5 5"/>',
    'rotate-ccw': '<path d="M4 11a8 8 0 1 1 2.4 5.7"/><path d="M4 3.5V11h7.5"/>'
  };

  function svg(name) {
    const inner = P[name];
    if (!inner) return '';
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + inner + '</svg>';
  }

  function hydrate(root) {
    (root || document).querySelectorAll('[data-ic]').forEach(function (el) {
      if (el.dataset.icDone) return;
      const markup = svg(el.dataset.ic);
      if (!markup) return;
      el.innerHTML = markup;
      el.dataset.icDone = '1';
      el.classList.add('ic');
    });
  }

  window.Icons = { svg: svg, hydrate: hydrate, has: function (n) { return !!P[n]; } };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { hydrate(); });
  } else {
    hydrate();
  }
})();
