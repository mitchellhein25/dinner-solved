<script setup lang="ts">
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { useHouseholdStore } from '@/stores/household'
import type { HouseholdMember } from '@/types'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const store = useHouseholdStore()

const members = ref<HouseholdMember[]>([])
const saving = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  await store.fetchMembers()
  // Deep copy so we can edit locally
  members.value = store.members.map((m) => ({ ...m }))
})

const STEP = 0.25
const MIN = 0.25
const MAX = 4.0

function adjust(member: HouseholdMember, delta: number) {
  const next = Math.round((member.serving_size + delta) * 100) / 100
  if (next < MIN || next > MAX) return
  member.serving_size = next
}

async function next() {
  saving.value = true
  error.value = null
  try {
    await store.saveMembers(members.value)
    router.push('/onboarding/template')
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
      <div class="onboard__progress-fill" style="width: 50%"></div>
    </div>

    <div class="onboard__body">
      <h2 class="step-title">How much does each person eat?</h2>
      <p class="step-desc">
        <strong>1.0</strong> = one standard adult serving. Adjust up or down so
        the grocery list is always exactly right. Kids are often 0.25–0.5;
        big eaters might be 1.5.
      </p>

      <div class="size-list">
        <div v-for="member in members" :key="member.id" class="size-row">
          <span class="size-row__emoji">{{ member.emoji }}</span>
          <span class="size-row__name">{{ member.name }}</span>
          <div class="stepper">
            <button
              class="stepper__btn"
              :disabled="member.serving_size <= MIN"
              @click="adjust(member, -STEP)"
            >
              −
            </button>
            <span class="stepper__val">{{ member.serving_size.toFixed(2) }}</span>
            <button
              class="stepper__btn"
              :disabled="member.serving_size >= MAX"
              @click="adjust(member, STEP)"
            >
              +
            </button>
          </div>
        </div>
      </div>

      <div v-if="error" class="error-banner" style="margin-top: 1rem">{{ error }}</div>
    </div>

    <div class="onboard__footer">
      <button class="btn btn--ghost" @click="router.back()">← Back</button>
      <button class="btn btn--primary btn--full" :disabled="saving" @click="next">
        <LoadingSpinner v-if="saving" size="sm" />
        <span v-else>Continue →</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.step-title {
  font-family: var(--font-display);
  font-size: 1.75rem;
  margin-bottom: 0.5rem;
}
.step-desc {
  font-size: 0.9375rem;
  color: var(--ink-light);
  margin-bottom: 1.5rem;
  line-height: 1.6;
}
.size-list {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}
.size-row {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.875rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.size-row__emoji {
  font-size: 1.5rem;
}
.size-row__name {
  flex: 1;
  font-weight: 500;
}
.stepper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.stepper__btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1.5px solid var(--border);
  background: var(--card-bg);
  font-size: 1.125rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.15s;
}
.stepper__btn:not(:disabled):hover {
  border-color: var(--accent);
  color: var(--accent);
}
.stepper__btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.stepper__val {
  font-size: 1rem;
  font-weight: 600;
  min-width: 3ch;
  text-align: center;
}
</style>
