<script setup lang="ts">
import { ref } from 'vue'
import { authApi } from '@/api/auth'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const email = ref('')
const loading = ref(false)
const sent = ref(false)
const error = ref<string | null>(null)

async function requestLink() {
  if (!email.value.trim()) return
  loading.value = true
  error.value = null
  try {
    await authApi.requestLink(email.value.trim())
    sent.value = true
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card card">
      <div class="login-card__brand">🍽️</div>
      <h1 class="login-card__title">Dinner <em>Solved.</em></h1>

      <template v-if="!sent">
        <p class="login-card__sub">Enter your email to sign in or create an account.</p>
        <form class="login-card__form" @submit.prevent="requestLink">
          <input
            v-model="email"
            type="email"
            class="input"
            placeholder="you@example.com"
            autocomplete="email"
            required
          />
          <button class="btn btn--primary btn--full" type="submit" :disabled="loading">
            <LoadingSpinner v-if="loading" size="sm" />
            <span v-else>Send magic link</span>
          </button>
        </form>
        <div v-if="error" class="error-banner" style="margin-top: 0.75rem">{{ error }}</div>
      </template>

      <template v-else>
        <div class="login-card__sent">
          <div class="login-card__sent-icon">📬</div>
          <p>Check your inbox for <strong>{{ email }}</strong> — we sent a sign-in link.</p>
          <p class="text-muted" style="font-size: 0.875rem; margin-top: 0.5rem">
            The link expires in 15 minutes.
          </p>
          <button class="btn btn--ghost btn--sm" style="margin-top: 1rem" @click="sent = false">
            Use a different email
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: var(--bg);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 2rem 1.75rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.75rem;
}

.login-card__brand {
  font-size: 2.5rem;
}

.login-card__title {
  font-family: var(--font-display);
  font-size: 2rem;
  margin: 0;
}

.login-card__sub {
  color: var(--text-muted);
  margin: 0;
}

.login-card__form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.login-card__sent {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.login-card__sent-icon {
  font-size: 2rem;
}
</style>
