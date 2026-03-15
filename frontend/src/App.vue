<template>
  <router-view></router-view>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=Noto+Serif+SC:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --color-primary: #7BA088;
  --color-primary-dark: #6A9177;
  --color-primary-light: #9BC1A8;
  --color-bg: #F7FAF8;
  --color-bg-card: #FFF;
  --color-text: #3D4A3E;
  --color-text-light: #5A6B5C;
  --color-text-muted: #8A9A8C;
  --color-border: #D8E4DC;
  --color-border-light: #E8F0EA;
  --color-accent: #D4A574;
  
  --font-serif: 'Noto Serif SC', 'Source Han Serif SC', serif;
  --font-sans: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
  
  --shadow-card: 8px 8px 24px rgba(61, 74, 62, 0.08);
  --shadow-card-hover: 12px 12px 32px rgba(61, 74, 62, 0.12);
  
  --radius-sm: 4px;
  --radius-md: 8px;
  
  --transition-fast: 0.2s ease;
  --transition-normal: 0.3s ease;
  --transition-smooth: 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: var(--font-sans);
  background-color: var(--color-bg);
  color: var(--color-text);
  line-height: 1.6;
  letter-spacing: 0.3px;
}

#app {
  width: 100%;
  min-height: 100vh;
}

.el-button--primary {
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-dark);
  --el-button-hover-border-color: var(--color-primary-dark);
  --el-button-active-bg-color: var(--color-primary-dark);
  --el-button-active-border-color: var(--color-primary-dark);
}

.el-input__wrapper {
  transition: all var(--transition-normal);
}

.el-input__wrapper:hover {
  box-shadow: none;
}

.el-input-number {
  line-height: 1;
}

.el-input-number .el-input__wrapper {
  padding: 0 12px;
  min-height: 40px;
  display: flex;
  align-items: center;
}

.el-input-number .el-input {
  display: flex;
  align-items: center;
}

.el-input-number .el-input__inner {
  height: 38px;
  line-height: 1;
  text-align: center;
}

.el-select .el-input__wrapper {
  box-shadow: none !important;
}

.el-form-item__label {
  font-family: var(--font-sans);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-normal);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all var(--transition-smooth);
}

.slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 768px) {
  html {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  html {
    font-size: 13px;
  }
}
</style>
