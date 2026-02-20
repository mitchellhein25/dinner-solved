<script setup lang="ts">
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { useHouseholdStore } from '@/stores/household'
import { useOnboardingStore } from '@/stores/onboarding'
import { usePlanStore } from '@/stores/plan'
import type { MealSlot } from '@/types'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const householdStore = useHouseholdStore()
const planStore = usePlanStore()
const onboardingStore = useOnboardingStore()

const DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
const DAY_LABELS: Record<string, string> = {
  mon: 'M', tue: 'T', wed: 'W', thu: 'T', fri: 'F', sat: 'S', sun: 'S',
}
const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack']

const slots = ref<MealSlot[]>([])
const saving = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  await householdStore.fetchMembers()
})

function addSlot() {
  slots.value.push({
    id: crypto.randomUUID(),
    name: '',
    meal_type: 'dinner',
    days: ['mon', 'tue', 'wed', 'thu', 'fri'],
    member_ids: householdStore.members.map((m) => m.id),
  })
}

function removeSlot(idx: number) {
  slots.value.splice(idx, 1)
}

function toggleDay(slot: MealSlot, day: string) {
  const i = slot.days.indexOf(day)
  if (i === -1) slot.days.push(day)
  else slot.days.splice(i, 1)
}

function toggleMember(slot: MealSlot, id: string) {
  const i = slot.member_ids.indexOf(id)
  if (i === -1) slot.member_ids.push(id)
  else slot.member_ids.splice(i, 1)
}

function servingTotal(slot: MealSlot): string {
  const memberServing = householdStore.members
    .filter((m) => slot.member_ids.includes(m.id))
    .reduce((sum, m) => sum + m.serving_size, 0)
  const total = Math.round(memberServing * slot.days.length * 100) / 100
  return `${total} servings × ${slot.days.length} nights`
}

async function finish() {
  if (slots.value.length === 0) {
    error.value = 'Add at least one meal slot.'
    return
  }
  for (const s of slots.value) {
    if (!s.name.trim()) { error.value = 'All slots need a name.'; return }
    if (s.days.length === 0) { error.value = `"${s.name}" needs at least one day.`; return }
    if (s.member_ids.length === 0) { error.value = `"${s.name}" needs at least one member.`; return }
  }

  saving.value = true
  error.value = null
  try {
    await planStore.saveTemplate({
      id: crypto.randomUUID(),
      slots: slots.value,
    })
    onboardingStore.complete()
    router.push('/')
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="onboard">
    <div class="onboard__progress">
      <div class="onboard__progress-fill" style="width: 75%"></div>
    </div>

    <div class="onboard__body">
      <h2 class="step-title">Build your meal template</h2>
      <p class="step-desc">
        Slots repeat every week. A "Weekday Dinners" slot covering Monday–Friday
        needs just one recipe suggestion — the app scales it for the whole week.
      </p>

      <div class="slots">
        <div v-for="(slot, i) in slots" :key="slot.id" class="slot-card card">
          <div class="slot-card__header">
            <input
              v-model="slot.name"
              class="input slot-card__name"
              placeholder="Slot name, e.g. Weekday Dinners"
            />
            <button class="btn btn--sm btn--danger" @click="removeSlot(i)">✕</button>
          </div>

          <div class="slot-card__row">
            <span class="label">Type</span>
            <select v-model="slot.meal_type" class="input select">
              <option v-for="t in MEAL_TYPES" :key="t" :value="t">
                {{ t.charAt(0).toUpperCase() + t.slice(1) }}
              </option>
            </select>
          </div>

          <div class="slot-card__row">
            <span class="label">Days</span>
            <div class="day-row">
              <button
                v-for="day in DAYS"
                :key="day"
                class="day-btn"
                :class="{ 'day-btn--active': slot.days.includes(day) }"
                type="button"
                @click="toggleDay(slot, day)"
              >
                {{ DAY_LABELS[day] }}
              </button>
            </div>
          </div>

          <div class="slot-card__row">
            <span class="label">Members</span>
            <div class="member-chips">
              <button
                v-for="m in householdStore.members"
                :key="m.id"
                class="member-chip"
                :class="{ 'member-chip--active': slot.member_ids.includes(m.id) }"
                type="button"
                @click="toggleMember(slot, m.id)"
              >
                {{ m.emoji }} {{ m.name }}
              </button>
            </div>
          </div>

          <p v-if="slot.days.length && slot.member_ids.length" class="slot-card__total">
            📊 {{ servingTotal(slot) }}
          </p>
        </div>
      </div>

      <button class="btn btn--ghost btn--full" style="margin-top: 0.75rem" @click="addSlot">
        + Add meal slot
      </button>

      <div v-if="error" class="error-banner" style="margin-top: 1rem">{{ error }}</div>
    </div>

    <div class="onboard__footer">
      <button class="btn btn--ghost" @click="router.back()">← Back</button>
      <button class="btn btn--primary btn--full" :disabled="saving" @click="finish">
        <LoadingSpinner v-if="saving" size="sm" />
        <span v-else>Finish Setup →</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.step-title { font-family: var(--font-display); font-size: 1.75rem; margin-bottom: 0.5rem; }
.step-desc { font-size: 0.9375rem; color: var(--ink-light); margin-bottom: 1.5rem; line-height: 1.6; }
.slots { display: flex; flex-direction: column; gap: 1rem; }
.slot-card { display: flex; flex-direction: column; gap: 0.875rem; }
.slot-card__header { display: flex; gap: 0.5rem; align-items: center; }
.slot-card__name { flex: 1; }
.slot-card__row { display: flex; flex-direction: column; gap: 0.375rem; }
.slot-card__total { font-size: 0.8125rem; color: var(--green); font-weight: 500; }
.day-row { display: flex; gap: 0.375rem; flex-wrap: wrap; }
.day-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1.5px solid var(--border); background: transparent;
  font-size: 0.75rem; font-weight: 600; cursor: pointer;
  transition: all 0.15s;
}
.day-btn--active { background: var(--accent); border-color: var(--accent); color: #fff; }
.member-chips { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.member-chip {
  padding: 0.3rem 0.75rem; border-radius: 99px;
  border: 1.5px solid var(--border); background: transparent;
  font-size: 0.875rem; cursor: pointer; transition: all 0.15s;
}
.member-chip--active { background: var(--accent-light); border-color: var(--accent); color: var(--accent); }
</style>
