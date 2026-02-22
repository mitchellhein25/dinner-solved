<script setup lang="ts">
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { useHouseholdStore } from '@/stores/household'
import { usePlanStore } from '@/stores/plan'
import { DAY_LABELS, MEAL_TYPE_LABELS } from '@/types'
import { formatWeekRange } from '@/utils/date'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const planStore = usePlanStore()
const householdStore = useHouseholdStore()

onMounted(async () => {
  await Promise.all([planStore.fetchTemplate(), householdStore.fetchMembers()])
})

function servingTotal(slot: { member_ids: string[]; days: string[] }): string {
  const total = householdStore.members
    .filter((m) => slot.member_ids.includes(m.id))
    .reduce((s, m) => s + m.serving_size, 0)
  const scaled = Math.round(total * slot.days.length * 100) / 100
  return `${scaled} servings × ${slot.days.length} nights`
}

async function suggest() {
  router.push('/suggestions')
}
</script>

<template>
  <div class="page">
    <nav class="page__nav">
      <router-link class="btn btn--ghost btn--sm" to="/recipes">Recipes</router-link>
      <span class="page__nav-brand">Dinner Solved</span>
      <router-link class="btn btn--ghost btn--sm" to="/settings">Settings</router-link>
    </nav>

    <div class="page__body container">
      <div v-if="planStore.loading" class="center-loading">
        <LoadingSpinner />
      </div>

      <template v-else-if="planStore.template">
        <div class="week-header">
          <h1 class="week-header__title">Your Week</h1>
          <p class="week-header__range">{{ formatWeekRange(planStore.weekStartDate) }}</p>
        </div>

        <div class="slot-list">
          <div
            v-for="slot in planStore.template.slots"
            :key="slot.id"
            class="slot-item card"
          >
            <div class="slot-item__left">
              <span class="chip">{{ MEAL_TYPE_LABELS[slot.meal_type] }}</span>
              <h3 class="slot-item__name">{{ slot.name }}</h3>
              <p class="slot-item__days">
                {{ slot.days.map((d) => DAY_LABELS[d]).join(' · ') }}
              </p>
            </div>
            <p class="slot-item__total">{{ servingTotal(slot) }}</p>
          </div>
        </div>

        <button class="btn btn--primary btn--full suggest-btn" @click="suggest">
          ✨ Start Planning
        </button>
      </template>

      <div v-else class="empty-state">
        <p>No meal template found.</p>
        <router-link class="btn btn--ghost" to="/onboarding/template">
          Set up template
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.center-loading { display: flex; justify-content: center; padding: 3rem 0; }
.week-header { margin-bottom: 1.5rem; }
.week-header__title { font-family: var(--font-display); font-size: 2rem; font-weight: 300; }
.week-header__range { color: var(--ink-light); font-size: 0.9375rem; }
.slot-list { display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1.5rem; }
.slot-item { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
.slot-item__left { display: flex; flex-direction: column; gap: 0.25rem; }
.slot-item__name { font-family: var(--font-display); font-size: 1.0625rem; }
.slot-item__days { font-size: 0.8125rem; color: var(--ink-light); }
.slot-item__total { font-size: 0.75rem; color: var(--ink-light); white-space: nowrap; text-align: right; }
.suggest-btn { margin-top: 0.5rem; }
.empty-state { text-align: center; padding: 3rem 0; display: flex; flex-direction: column; gap: 1rem; align-items: center; color: var(--ink-light); }
</style>
