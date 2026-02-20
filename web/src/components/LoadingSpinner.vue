<script setup lang="ts">
defineProps<{ size?: 'sm' | 'md' }>()
</script>

<template>
  <span class="spinner" :class="size === 'sm' ? 'spinner--sm' : ''"></span>
</template>

<style scoped>
.spinner {
  display: inline-block;
  width: 24px;
  height: 24px;
  border: 2.5px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.spinner--sm {
  width: 16px;
  height: 16px;
  border-width: 2px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
