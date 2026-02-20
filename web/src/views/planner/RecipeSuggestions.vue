<script setup lang="ts">
import ChatInput from '@/components/ChatInput.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import RecipeCard from '@/components/RecipeCard.vue'
import { useHouseholdStore } from '@/stores/household'
import { usePlanStore } from '@/stores/plan'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const planStore = usePlanStore()
const householdStore = useHouseholdStore()

onMounted(async () => {
  await householdStore.fetchMembers()
  if (planStore.suggestions.length === 0) {
    await planStore.suggest()
  }
})

function servingTotal(slot: { member_ids: string[]; days: string[] }): number {
  const total = householdStore.members
    .filter((m) => slot.member_ids.includes(m.id))
    .reduce((s, m) => s + m.serving_size, 0)
  return Math.round(total * slot.days.length * 100) / 100
}

async function handleChat(message: string) {
  await planStore.refine(message)
}

async function confirm() {
  await planStore.confirm()
  router.push('/grocery')
}
</script>

<template>
  <div class="page">
    <nav class="page__nav">
      <router-link class="btn btn--ghost btn--sm" to="/">← Week</router-link>
      <span class="page__nav-brand">Recipe Suggestions</span>
      <div style="width: 72px"></div>
    </nav>

    <div class="page__body container">
      <!-- Loading state -->
      <div v-if="planStore.loading" class="loading-state">
        <LoadingSpinner />
        <p class="loading-state__text">Asking Claude for recipe ideas…</p>
      </div>

      <template v-else>
        <div v-if="planStore.error" class="error-banner" style="margin-bottom: 1rem">
          {{ planStore.error }}
          <button class="btn btn--sm btn--ghost" style="margin-left: 0.5rem" @click="planStore.suggest()">
            Retry
          </button>
        </div>

        <!-- Recipe cards -->
        <div class="suggestion-list">
          <RecipeCard
            v-for="s in planStore.suggestions"
            :key="s.slot.id"
            :slot="s.slot"
            :recipe="s.recipe"
            :total-servings="servingTotal(s.slot)"
          />
        </div>

        <!-- Chat -->
        <div class="chat-section">
          <p class="chat-section__hint">
            Not quite right? Ask to swap a recipe, change a cuisine, or make it lighter.
          </p>
          <ChatInput :loading="planStore.chatLoading" @send="handleChat" />
        </div>

        <!-- Confirm -->
        <button
          class="btn btn--primary btn--full confirm-btn"
          :disabled="planStore.suggestions.length === 0 || planStore.loading"
          @click="confirm"
        >
          Confirm Plan & See Grocery List →
        </button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.loading-state { display: flex; flex-direction: column; align-items: center; gap: 1rem; padding: 3rem 0; }
.loading-state__text { color: var(--ink-light); font-size: 0.9375rem; }
.suggestion-list { display: flex; flex-direction: column; gap: 0.875rem; margin-bottom: 1.5rem; }
.chat-section { margin-bottom: 1.25rem; }
.chat-section__hint { font-size: 0.875rem; color: var(--ink-light); margin-bottom: 0.5rem; }
.confirm-btn { margin-top: 0.5rem; }
</style>
