<script setup lang="ts">
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { preferencesApi } from '@/api/preferences'
import { useAuthStore } from '@/stores/auth'
import { useHouseholdStore } from '@/stores/household'
import { useOnboardingStore } from '@/stores/onboarding'
import type { HouseholdMember, UserPreferences } from '@/types'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const authStore = useAuthStore()
const householdStore = useHouseholdStore()
const onboardingStore = useOnboardingStore()

type Tab = 'household' | 'preferences'
const tab = ref<Tab>('household')

// ---- Household tab ----
const members = ref<HouseholdMember[]>([])
const savingMembers = ref(false)
const membersError = ref<string | null>(null)

const STEP = 0.25
const MIN = 0.25
const MAX = 4.0

function adjustServing(member: HouseholdMember, delta: number) {
  const next = Math.round((member.serving_size + delta) * 100) / 100
  if (next < MIN || next > MAX) return
  member.serving_size = next
}

async function saveMembers() {
  savingMembers.value = true
  membersError.value = null
  try {
    await householdStore.saveMembers(members.value)
  } catch (e) {
    membersError.value = (e as Error).message
  } finally {
    savingMembers.value = false
  }
}

// ---- Preferences tab ----
const prefs = ref<UserPreferences | null>(null)
const likedInput = ref('')
const dislikedInput = ref('')
const cuisineInput = ref('')
const savingPrefs = ref(false)
const prefsError = ref<string | null>(null)

function addLiked() {
  const v = likedInput.value.trim()
  if (!v || !prefs.value) return
  prefs.value.liked_ingredients.push(v)
  likedInput.value = ''
}
function removeLiked(i: number) { prefs.value?.liked_ingredients.splice(i, 1) }

function addDisliked() {
  const v = dislikedInput.value.trim()
  if (!v || !prefs.value) return
  prefs.value.disliked_ingredients.push(v)
  dislikedInput.value = ''
}
function removeDisliked(i: number) { prefs.value?.disliked_ingredients.splice(i, 1) }

function addCuisine() {
  const v = cuisineInput.value.trim()
  if (!v || !prefs.value) return
  prefs.value.cuisine_preferences.push(v)
  cuisineInput.value = ''
}
function removeCuisine(i: number) { prefs.value?.cuisine_preferences.splice(i, 1) }

async function savePrefs() {
  if (!prefs.value) return
  savingPrefs.value = true
  prefsError.value = null
  try {
    await preferencesApi.save(prefs.value)
  } catch (e) {
    prefsError.value = (e as Error).message
  } finally {
    savingPrefs.value = false
  }
}

function resetOnboarding() {
  onboardingStore.reset()
  router.push('/welcome')
}

function logout() {
  authStore.logout()
  router.replace('/login')
}

onMounted(async () => {
  await householdStore.fetchMembers()
  members.value = householdStore.members.map((m) => ({ ...m }))
  try {
    const res = await preferencesApi.get()
    prefs.value = res.data
  } catch {
    prefs.value = {
      id: crypto.randomUUID(),
      liked_ingredients: [],
      disliked_ingredients: [],
      cuisine_preferences: [],
    }
  }
})
</script>

<template>
  <div class="page">
    <nav class="page__nav">
      <router-link class="btn btn--ghost btn--sm" to="/">← Home</router-link>
      <span class="page__nav-brand">Settings</span>
      <div style="width: 72px"></div>
    </nav>

    <div class="page__body container">
      <!-- Tabs -->
      <div class="tabs">
        <button class="tab" :class="{ 'tab--active': tab === 'household' }" @click="tab = 'household'">
          Household
        </button>
        <button class="tab" :class="{ 'tab--active': tab === 'preferences' }" @click="tab = 'preferences'">
          Preferences
        </button>
      </div>

      <!-- Household tab -->
      <div v-if="tab === 'household'">
        <h2 class="section-title">Members &amp; Serving Sizes</h2>
        <div class="member-list">
          <div v-for="member in members" :key="member.id" class="member-row card">
            <span class="member-row__emoji">{{ member.emoji }}</span>
            <span class="member-row__name">{{ member.name }}</span>
            <div class="stepper">
              <button class="stepper__btn" :disabled="member.serving_size <= MIN" @click="adjustServing(member, -STEP)">−</button>
              <span class="stepper__val">{{ member.serving_size.toFixed(2) }}</span>
              <button class="stepper__btn" :disabled="member.serving_size >= MAX" @click="adjustServing(member, STEP)">+</button>
            </div>
          </div>
        </div>
        <div v-if="membersError" class="error-banner" style="margin: 0.75rem 0">{{ membersError }}</div>
        <button class="btn btn--primary btn--full" style="margin-top: 1rem" :disabled="savingMembers" @click="saveMembers">
          <LoadingSpinner v-if="savingMembers" size="sm" />
          <span v-else>Save Household</span>
        </button>

        <div class="divider" style="margin: 2rem 0"></div>
        <h2 class="section-title">Meal Template</h2>
        <p class="text-muted" style="margin-bottom: 0.75rem">
          Re-run onboarding to reconfigure your meal template.
        </p>
        <button class="btn btn--ghost" @click="router.push('/onboarding/template')">
          Edit Template
        </button>

        <div class="divider" style="margin: 2rem 0"></div>
        <h2 class="section-title">Account</h2>
        <p class="text-muted" style="margin-bottom: 0.5rem; font-size: 0.875rem">
          Household ID: <code class="household-id">{{ authStore.householdId?.slice(0, 8) }}…</code>
        </p>
        <button class="btn btn--ghost btn--sm" style="margin-bottom: 1rem" @click="logout">
          Log Out
        </button>

        <div class="divider" style="margin: 2rem 0"></div>
        <button class="btn btn--danger btn--sm" @click="resetOnboarding">
          Reset Onboarding
        </button>
      </div>

      <!-- Preferences tab -->
      <div v-if="tab === 'preferences' && prefs">
        <h2 class="section-title">Food Preferences</h2>
        <p class="text-muted" style="margin-bottom: 1.25rem">
          Claude uses these to tailor recipe suggestions every week.
        </p>

        <div class="pref-section">
          <span class="label">Liked ingredients / cuisines</span>
          <div class="tag-row">
            <span v-for="(t, i) in prefs.liked_ingredients" :key="i" class="tag tag--green">
              {{ t }} <button @click="removeLiked(i)">✕</button>
            </span>
          </div>
          <div class="add-row">
            <input v-model="likedInput" class="input" placeholder="e.g. garlic" @keydown.enter.prevent="addLiked" />
            <button class="btn btn--ghost" @click="addLiked">Add</button>
          </div>
        </div>

        <div class="pref-section">
          <span class="label">Disliked / avoid</span>
          <div class="tag-row">
            <span v-for="(t, i) in prefs.disliked_ingredients" :key="i" class="tag tag--red">
              {{ t }} <button @click="removeDisliked(i)">✕</button>
            </span>
          </div>
          <div class="add-row">
            <input v-model="dislikedInput" class="input" placeholder="e.g. cilantro" @keydown.enter.prevent="addDisliked" />
            <button class="btn btn--ghost" @click="addDisliked">Add</button>
          </div>
        </div>

        <div class="pref-section">
          <span class="label">Preferred cuisines</span>
          <div class="tag-row">
            <span v-for="(t, i) in prefs.cuisine_preferences" :key="i" class="tag tag--accent">
              {{ t }} <button @click="removeCuisine(i)">✕</button>
            </span>
          </div>
          <div class="add-row">
            <input v-model="cuisineInput" class="input" placeholder="e.g. Italian" @keydown.enter.prevent="addCuisine" />
            <button class="btn btn--ghost" @click="addCuisine">Add</button>
          </div>
        </div>

        <div v-if="prefsError" class="error-banner" style="margin: 0.75rem 0">{{ prefsError }}</div>
        <button class="btn btn--primary btn--full" style="margin-top: 1rem" :disabled="savingPrefs" @click="savePrefs">
          <LoadingSpinner v-if="savingPrefs" size="sm" />
          <span v-else>Save Preferences</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tabs { display: flex; gap: 0; border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; margin-bottom: 1.5rem; }
.tab { flex: 1; padding: 0.625rem; background: transparent; border: none; font-family: var(--font-body); font-size: 0.9375rem; cursor: pointer; transition: background 0.15s; }
.tab--active { background: var(--accent); color: #fff; }
.section-title { font-family: var(--font-display); font-size: 1.25rem; margin-bottom: 0.875rem; }
.member-list { display: flex; flex-direction: column; gap: 0.625rem; }
.member-row { display: flex; align-items: center; gap: 0.75rem; padding: 0.875rem 1rem; }
.member-row__emoji { font-size: 1.375rem; }
.member-row__name { flex: 1; font-weight: 500; }
.stepper { display: flex; align-items: center; gap: 0.5rem; }
.stepper__btn { width: 30px; height: 30px; border-radius: 50%; border: 1.5px solid var(--border); background: transparent; cursor: pointer; font-size: 1rem; display: flex; align-items: center; justify-content: center; }
.stepper__btn:not(:disabled):hover { border-color: var(--accent); color: var(--accent); }
.stepper__btn:disabled { opacity: 0.35; cursor: not-allowed; }
.stepper__val { min-width: 3.5ch; text-align: center; font-weight: 600; }
.pref-section { margin-bottom: 1.25rem; display: flex; flex-direction: column; gap: 0.5rem; }
.tag-row { display: flex; gap: 0.375rem; flex-wrap: wrap; min-height: 28px; }
.tag { display: inline-flex; align-items: center; gap: 0.375rem; padding: 0.2rem 0.625rem; border-radius: 99px; font-size: 0.8125rem; }
.tag button { background: none; border: none; cursor: pointer; font-size: 0.7rem; opacity: 0.6; }
.tag--green { background: var(--green-light); color: var(--green); }
.tag--red { background: #fef2f2; color: #c0392b; }
.tag--accent { background: var(--accent-light); color: var(--accent); }
.add-row { display: flex; gap: 0.5rem; }
.household-id { font-size: 0.8125rem; background: var(--surface); padding: 0.1rem 0.4rem; border-radius: var(--radius-sm); letter-spacing: 0.03em; }
</style>
