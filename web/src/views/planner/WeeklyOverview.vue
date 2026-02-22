<script setup lang="ts">
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { planApi } from '@/api/plan'
import { useHouseholdStore } from '@/stores/household'
import { usePlanStore } from '@/stores/plan'
import type { ConfirmedAssignment } from '@/types'
import { DAY_LABELS, MEAL_TYPE_LABELS } from '@/types'
import { formatWeekRange } from '@/utils/date'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const planStore = usePlanStore()
const householdStore = useHouseholdStore()

const confirmedAssignments = ref<ConfirmedAssignment[]>([])

const hasConfirmedPlan = computed(() => confirmedAssignments.value.length > 0)

const planPdfUrl = computed(() => planApi.getPlanPdfUrl(planStore.weekStartDate))

onMounted(async () => {
  await Promise.all([
    planStore.fetchTemplate(),
    householdStore.fetchMembers(),
    fetchConfirmedPlan(),
  ])
})

async function fetchConfirmedPlan() {
  try {
    const res = await planApi.getConfirmedPlan(planStore.weekStartDate)
    confirmedAssignments.value = res.data.assignments
  } catch {
    // Non-fatal — plan may not exist yet for this week
  }
}

function confirmedRecipe(slotId: string): ConfirmedAssignment['recipe'] | null {
  return confirmedAssignments.value.find((a) => a.slot_id === slotId)?.recipe ?? null
}

function servingTotal(slot: { member_ids: string[]; days: string[] }): string {
  const total = householdStore.members
    .filter((m) => slot.member_ids.includes(m.id))
    .reduce((s, m) => s + m.serving_size, 0)
  const scaled = Math.round(total * slot.days.length * 100) / 100
  return `${scaled} servings × ${slot.days.length} nights`
}

function suggest() {
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
            <div class="slot-item__top">
              <div class="slot-item__left">
                <span class="chip">{{ MEAL_TYPE_LABELS[slot.meal_type] }}</span>
                <h3 class="slot-item__name">{{ slot.name }}</h3>
                <p class="slot-item__days">
                  {{ slot.days.map((d) => DAY_LABELS[d]).join(' · ') }}
                </p>
              </div>
              <p class="slot-item__total">{{ servingTotal(slot) }}</p>
            </div>
            <div v-if="confirmedRecipe(slot.id)" class="slot-item__recipe">
              <span class="slot-item__recipe-emoji">{{ confirmedRecipe(slot.id)!.emoji }}</span>
              <span class="slot-item__recipe-name">{{ confirmedRecipe(slot.id)!.name }}</span>
            </div>
            <div v-else class="slot-item__recipe slot-item__recipe--empty">
              No recipe planned yet
            </div>
          </div>
        </div>

        <button class="btn btn--primary btn--full suggest-btn" @click="suggest">
          ✨ {{ hasConfirmedPlan ? 'Re-plan This Week' : 'Start Planning' }}
        </button>

        <div v-if="hasConfirmedPlan" class="confirmed-actions">
          <router-link class="btn btn--ghost btn--full" :to="`/grocery`">
            🛒 View Grocery List
          </router-link>
          <a
            class="btn btn--ghost btn--full"
            :href="planPdfUrl"
            target="_blank"
            download
          >📥 Download Plan PDF</a>
        </div>
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

.slot-item {
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow: hidden;
}

.slot-item__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.75rem 0.875rem 0.625rem;
}

.slot-item__left { display: flex; flex-direction: column; gap: 0.25rem; }
.slot-item__name { font-family: var(--font-display); font-size: 1.0625rem; }
.slot-item__days { font-size: 0.8125rem; color: var(--ink-light); }
.slot-item__total { font-size: 0.75rem; color: var(--ink-light); white-space: nowrap; text-align: right; flex-shrink: 0; }

.slot-item__recipe {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.875rem 0.625rem;
  border-top: 1px solid var(--border);
  background: var(--cream);
}

.slot-item__recipe--empty {
  font-size: 0.8125rem;
  color: var(--ink-light);
  font-style: italic;
}

.slot-item__recipe-emoji { font-size: 1.125rem; flex-shrink: 0; }
.slot-item__recipe-name { font-size: 0.9375rem; font-weight: 500; }

.suggest-btn { margin-top: 0.5rem; }

.confirmed-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.empty-state { text-align: center; padding: 3rem 0; display: flex; flex-direction: column; gap: 1rem; align-items: center; color: var(--ink-light); }
</style>
