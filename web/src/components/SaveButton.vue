<script setup lang="ts">
import LoadingSpinner from './LoadingSpinner.vue'

defineProps<{
  label: string
  isDirty: boolean
  saving: boolean
  success: boolean
}>()

defineEmits<{ save: [] }>()
</script>

<template>
  <div class="save-bar">
    <span v-if="isDirty && !saving" class="unsaved-hint">● Unsaved changes</span>
    <button
      class="btn btn--full"
      :class="success ? 'btn--success' : isDirty ? 'btn--primary' : 'btn--ghost'"
      :disabled="saving || (!isDirty && !success)"
      @click="$emit('save')"
    >
      <LoadingSpinner v-if="saving" size="sm" />
      <span v-else-if="success">✓ Saved</span>
      <span v-else>{{ label }}</span>
    </button>
  </div>
</template>

<style scoped>
.save-bar { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.375rem; }
.unsaved-hint { font-size: 0.8125rem; color: var(--accent); font-weight: 500; }
.btn--success { background: #16a34a; color: #fff; border-color: #16a34a; }
.btn--success:hover { background: #15803d; border-color: #15803d; }
</style>
