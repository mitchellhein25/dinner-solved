<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useOnboardingStore } from '@/stores/onboarding'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const onboardingStore = useOnboardingStore()

const error = ref<string | null>(null)

onMounted(async () => {
  const token = route.query.token as string | undefined
  if (!token) {
    error.value = 'No token found in URL.'
    return
  }
  try {
    const res = await authApi.verifyToken(token)
    authStore.setHousehold(res.data.household_id, res.data.email)
    if (res.data.is_onboarded) {
      onboardingStore.complete()
      router.replace('/')
    } else {
      router.replace('/welcome')
    }
  } catch {
    error.value = 'This link is invalid or has expired. Please request a new one.'
  }
})
</script>

<template>
  <div class="verify-page">
    <div class="verify-card card">
      <template v-if="!error">
        <LoadingSpinner />
        <p>Signing you in…</p>
      </template>
      <template v-else>
        <div style="font-size: 2rem">❌</div>
        <p class="verify-card__error">{{ error }}</p>
        <router-link class="btn btn--primary" to="/login">Back to sign in</router-link>
      </template>
    </div>
  </div>
</template>

<style scoped>
.verify-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: var(--bg);
}

.verify-card {
  width: 100%;
  max-width: 360px;
  padding: 2.5rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
}

.verify-card__error {
  color: var(--text-muted);
}
</style>
