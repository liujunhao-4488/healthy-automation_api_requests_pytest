<script setup>
/* 二次确认弹窗：全站共用一个，由 useConfirm() 控制 */
import { onMounted, onUnmounted } from 'vue'
import { confirmState, settleConfirm } from '@/composables/useConfirm'
import SvgIcon from './SvgIcon.vue'

function onKeydown(e) {
  if (e.key === 'Escape' && confirmState.open) settleConfirm(false)
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div
    class="overlay"
    :class="{ open: confirmState.open }"
    @click.self="settleConfirm(false)"
  >
    <div class="modal" style="width: min(400px, 100%)">
      <div class="modal-hd">
        <div><h3>{{ confirmState.title }}</h3></div>
        <button class="modal-close" @click="settleConfirm(false)">
          <SvgIcon name="x" />
        </button>
      </div>
      <div class="modal-bd">
        <p class="muted" style="font-size: 13px">{{ confirmState.message }}</p>
      </div>
      <div class="modal-ft">
        <button class="btn btn-outline btn-sm" @click="settleConfirm(false)">取消</button>
        <button
          class="btn btn-sm"
          :class="confirmState.danger ? 'btn-danger' : 'btn-primary'"
          @click="settleConfirm(true)"
        >
          {{ confirmState.okText }}
        </button>
      </div>
    </div>
  </div>
</template>
