<script setup>
/* 提示条容器：挂在 App.vue 根部一次即可 */
import { toasts } from '@/composables/useToast'
import SvgIcon from './SvgIcon.vue'
</script>

<template>
  <div class="toast-wrap">
    <TransitionGroup name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="toast"
        :class="{ error: t.type === 'error' }"
        :style="t.leaving ? 'opacity:0;transform:translateY(6px)' : ''"
      >
        <SvgIcon :name="t.type === 'error' ? 'alert' : 'check-circle'" />
        <span>{{ t.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
</style>
