<script setup>
/* 根组件：只放路由出口 + 两个全局浮层（提示条、确认框） */
import ToastHost from '@/components/ToastHost.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
</script>

<template>
  <RouterView />
  <ToastHost />
  <ConfirmDialog />
</template>
