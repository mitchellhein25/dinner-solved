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
const downloadingPdf = ref(false)

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

async function downloadPlanPdf() {
  downloadingPdf.value = true
  try {
    await planApi.downloadPlanPdf(planStore.weekStartDate)
  } finally {
    downloadingPdf.value = false
  }
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
          <p class="week-header__eyebrow">Your week</p>
          <h1 class="week-header__title">{{ formatWeekRange(planStore.weekStartDate) }}</h1>
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
              Not yet planned
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
          <button
            class="btn btn--ghost btn--full"
            :disabled="downloadingPdf"
            @click="downloadPlanPdf"
          >📥 Download Plan PDF</button>
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

.week-header { margin-bottom: 1.75rem; }
.week-header__eyebrow {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 0.25rem;
}
.week-header__title {
  font-family: var(--font-display);
  font-size: 2.25rem;
  font-weight: 400;
  font-style: italic;
  color: var(--ink);
  line-height: 1.15;
}

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
  padding: 0.75rem 1rem 0.625rem;
}

.slot-item__left { display: flex; flex-direction: column; gap: 0.25rem; }
.slot-item__name {
  font-family: var(--font-display);
  font-size: 1.0625rem;
  font-style: italic;
  font-weight: 400;
}
.slot-item__days { font-size: 0.8125rem; color: var(--ink-light); }
.slot-item__total { font-size: 0.75rem; color: var(--ink-light); white-space: nowrap; text-align: right; flex-shrink: 0; }

.slot-item__recipe {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem 1rem;
  border-top: 1px solid var(--border);
  background: var(--cream-dark);
}

.slot-item__recipe--empty {
  font-size: 0.8125rem;
  color: var(--ink-light);
  font-style: italic;
  background: var(--cream);
}

.slot-item__recipe-emoji { font-size: 1.375rem; flex-shrink: 0; }
.slot-item__recipe-name {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 400;
  font-style: italic;
  color: var(--ink);
}

.suggest-btn { margin-top: 0.5rem; }

.confirmed-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.empty-state { text-align: center; padding: 3rem 0; display: flex; flex-direction: column; gap: 1rem; align-items: center; color: var(--ink-light); }
</style>
