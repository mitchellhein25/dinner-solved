<script setup lang="ts">
import LoadingSpinner from './LoadingSpinner.vue'
import { ref } from 'vue'

const props = defineProps<{ loading?: boolean; placeholder?: string }>()
const emit = defineEmits<{ send: [message: string] }>()

const message = ref('')

function submit() {
  const text = message.value.trim()
  if (!text || props.loading) return
  emit('send', text)
  message.value = ''
}
</script>

<template>
  <div class="chat-input">
    <input
      v-model="message"
      class="input chat-input__field"
      type="text"
      :placeholder="placeholder ?? 'Swap something? e.g. &quot;make Friday lighter&quot;'"
      :disabled="loading"
      @keydown.enter.prevent="submit"
    />
    <button class="btn btn--primary chat-input__btn" :disabled="loading || !message.trim()" @click="submit">
      <LoadingSpinner v-if="loading" size="sm" />
      <span v-else>Send</span>
    </button>
  </div>
</template>

<style scoped>
.chat-input {
  display: flex;
  gap: 0.5rem;
}
.chat-input__field {
  flex: 1;
}
.chat-input__btn {
  flex-shrink: 0;
}
</style>
