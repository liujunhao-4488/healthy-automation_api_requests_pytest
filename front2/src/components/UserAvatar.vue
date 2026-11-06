<script setup>
/* ============================================================
   UserAvatar.vue · 统一头像组件
   ------------------------------------------------------------
   为什么单独抽一个组件：
     全站有 6 处显示用户头像（顶栏、个人中心、后台用户列表、
     评论、AI 助手消息），原先都是「取名字首字」的 span。
     要支持上传头像，这 6 处都得改成「有图用图、无图退回首字」，
     散落着改容易漏，也会让每处都重复一遍 img/error 处理。

   props：
     src   头像地址，支持 data URI（后端存的就是 base64）
     name  用户名，用于取首字和 alt
     size  'sm' | '' | 'lg' | 'xl'，对应全局已有尺寸类
     round 是否圆形（默认 true）

   设计要点：
     · picture 为空或加载失败时，自动退回「首字」而不是显示裂图；
     · 用 <img @error> 兜底，后端数据里存在损坏的 base64 也能降级；
     · 首字取用户名第一个字符，中文英文都适用（英文取大写）。
   ============================================================ */
import { ref, computed, watch } from 'vue'

const props = defineProps({
  src: { type: String, default: '' },
  name: { type: String, default: '' },
  size: { type: String, default: '' },
  round: { type: Boolean, default: true }
})

/** 图片加载失败标记；src 变化时重置，避免上一张的错误状态残留 */
const failed = ref(false)
watch(
  () => props.src,
  () => {
    failed.value = false
  }
)

/** 有地址且没失败才显示图片 */
const showImg = computed(() => !!props.src && !failed.value)

/** 首字：取用户名第一个字符；英文统一大写，没有名字用「用」 */
const initial = computed(() => {
  const n = String(props.name || '').trim()
  if (!n) return '用'
  return n.charAt(0).toUpperCase()
})

const sizeClass = computed(() => (props.size ? ' ' + props.size : ''))
</script>

<template>
  <span
    :class="['ua', sizeClass, { 'ua-round': round }]"
    :title="name || ''"
  >
    <img v-if="showImg" :src="src" :alt="name || '头像'" @error="failed = true" />
    <span v-else class="ua-initial">{{ initial }}</span>
  </span>
</template>

<style scoped>
.ua {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex: 0 0 auto;
  background: var(--green-100, #dcebe2);
  color: var(--green-800, #1f5b3e);
  font-weight: 600;
  line-height: 1;
  /* 尺寸由全局 .avatar / .nav-avatar 或 size prop 决定，
     这里只兜底一个默认宽度，避免无类名时塌陷 */
  width: 34px;
  height: 34px;
  font-size: 14px;
}

.ua-round {
  border-radius: 50%;
}

.ua img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.ua-initial {
  display: block;
  /* 首字在圆形里视觉居中，略上移一点点更平衡 */
  transform: translateY(-0.5px);
}

/* 尺寸变体：覆盖默认宽高与字号 */
.ua.sm {
  width: 26px;
  height: 26px;
  font-size: 12px;
}

.ua.lg {
  width: 56px;
  height: 56px;
  font-size: 20px;
}

.ua.xl {
  width: 84px;
  height: 84px;
  font-size: 30px;
}
</style>
