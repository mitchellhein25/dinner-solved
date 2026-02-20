<script setup lang="ts">
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { useHouseholdStore } from '@/stores/household'
import type { HouseholdMember } from '@/types'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const store = useHouseholdStore()

const EMOJIS = ['👩', '👨', '👧', '👦', '👶', '🧒', '👴', '👵', '🧑']

const members = ref<HouseholdMember[]>([])
const nameInput = ref('')
const emojiInput = ref('👩')
const error = ref<string | null>(null)
const saving = ref(false)

function addMember() {
  const name = nameInput.value.trim()
  if (!name) return
  members.value.push({
    id: crypto.randomUUID(),
    name,
    emoji: emojiInput.value,
    serving_size: 1.0,
  })
  nameInput.value = ''
}

function removeMember(idx: number) {
  members.value.splice(idx, 1)
}

async function next() {
  if (members.value.length === 0) {
    error.value = 'Add at least one household member to continue.'
    return
  }
  saving.value = true
  error.value = null
  try {
    await store.saveMembers(members.value)
    router.push('/onboarding/sizes')
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
      <div class="onboard__progress-fill" style="width: 25%"></div>
    </div>

    <div class="onboard__body">
      <h2 class="step-title">Who's in your household?</h2>
      <p class="step-desc">
        Add everyone who eats meals at home. You'll set how much each person
        eats in the next step — so recipes scale perfectly.
      </p>

      <!-- Add member form -->
      <div class="add-form">
        <div class="add-form__emoji-row">
          <button
            v-for="e in EMOJIS"
            :key="e"
            class="emoji-btn"
            :class="{ 'emoji-btn--active': emojiInput === e }"
            type="button"
            @click="emojiInput = e"
          >
            {{ e }}
          </button>
        </div>
        <div class="add-form__row">
          <input
            v-model="nameInput"
            class="input"
            type="text"
            placeholder="Name (e.g. Mitch)"
            maxlength="40"
            @keydown.enter.prevent="addMember"
          />
          <button class="btn btn--ghost" type="button" @click="addMember">Add</button>
        </div>
      </div>

      <!-- Member list -->
      <div v-if="members.length" class="member-list">
        <div v-for="(m, i) in members" :key="m.id" class="member-row">
          <span class="member-row__emoji">{{ m.emoji }}</span>
          <span class="member-row__name">{{ m.name }}</span>
          <button class="btn btn--sm btn--danger" @click="removeMember(i)">Remove</button>
        </div>
      </div>
      <p v-else class="empty-hint">No members added yet.</p>

      <div v-if="error" class="error-banner" style="margin-top: 1rem">{{ error }}</div>
    </div>

    <div class="onboard__footer">
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
.add-form {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  margin-bottom: 1.25rem;
}
.add-form__emoji-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}
.emoji-btn {
  font-size: 1.5rem;
  background: none;
  border: 2px solid transparent;
  border-radius: 8px;
  padding: 0.125rem 0.25rem;
  cursor: pointer;
  transition: border-color 0.15s;
}
.emoji-btn--active {
  border-color: var(--accent);
}
.add-form__row {
  display: flex;
  gap: 0.5rem;
}
.member-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.member-row {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.member-row__emoji {
  font-size: 1.5rem;
}
.member-row__name {
  flex: 1;
  font-weight: 500;
}
.empty-hint {
  color: var(--ink-light);
  font-size: 0.875rem;
  text-align: center;
  padding: 1.5rem 0;
}
</style>
