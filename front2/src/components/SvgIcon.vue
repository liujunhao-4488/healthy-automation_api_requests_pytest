<script setup>
/* ============================================================
   SvgIcon.vue · 内联 SVG 图标
   ------------------------------------------------------------
   替代静态版的 <i class="ic" data-ic="home"></i> + Icons.hydrate()
   现在直接写 <SvgIcon name="home" /> 即可，不需要再手动 hydrate
   ============================================================ */
import { computed } from 'vue'
import { ICONS } from './icons'

const props = defineProps({
  name: { type: String, required: true },
  strokeWidth: { type: [Number, String], default: 1.75 }
})

const inner = computed(() => ICONS[props.name] || '')
</script>

<template>
  <svg
    v-if="inner"
    class="ic"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    v-html="inner"
  />
</template>
