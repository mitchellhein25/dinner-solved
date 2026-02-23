<script setup lang="ts">
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import RecipeForm from '@/components/RecipeForm.vue'
import { recipesApi } from '@/api/recipes'
import type { RecipeDetail, RecipeDraft } from '@/types'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

type Tab = 'url' | 'manual'
const tab = ref<Tab>('url')

// URL import state
const urlInput = ref('')
const importing = ref(false)
const importError = ref<string | null>(null)
const importedDraft = ref<RecipeDraft | null>(null)

// Shared save state
const saving = ref(false)
const saveError = ref<string | null>(null)

async function runImport() {
  const url = urlInput.value.trim()
  if (!url) return
  importing.value = true
  importError.value = null
  importedDraft.value = null

  try {
    const result: RecipeDetail = await recipesApi.importFromUrl(url)
    // Map RecipeDetail → RecipeDraft (strip server-managed fields)
    importedDraft.value = {
      name: result.name,
      emoji: result.emoji,
      prep_time: result.prep_time,
      ingredients: result.ingredients,
      key_ingredients: result.key_ingredients,
      source_url: result.source_url,
      cooking_instructions: result.cooking_instructions,
    }
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    importError.value = typeof detail === 'string' ? detail : 'Could not extract a recipe from that URL.'
  } finally {
    importing.value = false
  }
}

async function handleSave(draft: RecipeDraft) {
  saving.value = true
  saveError.value = null
  try {
    const created = await recipesApi.createRecipe(draft)
    router.push(`/recipes/${created.id}`)
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    if (e?.response?.status === 409) {
      saveError.value = typeof detail === 'string' ? detail : 'A recipe with that name already exists.'
    } else {
      saveError.value = 'Failed to save recipe.'
    }
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.push('/recipes')
}
</script>

<template>
  <div class="page">
    <nav class="page__nav">
      <router-link class="btn btn--ghost btn--sm" to="/recipes">← Recipes</router-link>
      <span class="page__nav-brand">Add Recipe</span>
      <span />
    </nav>

    <div class="page__body container">
      <!-- Tab switcher -->
      <div class="tabs">
        <button
          class="tab"
          :class="{ 'tab--active': tab === 'url' }"
          @click="tab = 'url'; importedDraft = null; importError = null"
        >
          From URL
        </button>
        <button
          class="tab"
          :class="{ 'tab--active': tab === 'manual' }"
          @click="tab = 'manual'"
        >
          Manual Entry
        </button>
      </div>

      <!-- URL import tab -->
      <template v-if="tab === 'url'">
        <div v-if="!importedDraft" class="url-panel">
          <p class="url-panel__hint">
            Paste any recipe URL — Dinner Solved will read the page and fill in the details for you to review.
          </p>

          <div class="url-row">
            <input
              v-model="urlInput"
              class="input"
              type="url"
              placeholder="https://www.allrecipes.com/recipe/…"
              :disabled="importing"
              @keyup.enter="runImport"
            />
            <button
              class="btn btn--primary"
              :disabled="importing || !urlInput.trim()"
              @click="runImport"
            >
              <LoadingSpinner v-if="importing" size="sm" />
              <span v-else>Import</span>
            </button>
          </div>

          <div v-if="importing" class="import-loading">
            <LoadingSpinner />
            <p>Reading the page and extracting the recipe…</p>
          </div>

          <div v-if="importError" class="error-banner">{{ importError }}</div>
        </div>

        <!-- Review / edit the parsed draft -->
        <template v-else>
          <div class="import-success-banner">
            ✓ Recipe imported — review and edit before saving.
          </div>
          <div v-if="saveError" class="error-banner">{{ saveError }}</div>
          <RecipeForm
            :initial-data="importedDraft"
            :loading="saving"
            submit-label="Save Recipe"
            @submit="handleSave"
            @cancel="importedDraft = null"
          />
        </template>
      </template>

      <!-- Manual entry tab -->
      <template v-else>
        <div v-if="saveError" class="error-banner" style="margin-bottom: 1rem">{{ saveError }}</div>
        <RecipeForm
          :loading="saving"
          submit-label="Save Recipe"
          @submit="handleSave"
          @cancel="handleCancel"
        />
      </template>
    </div>
  </div>
</template>

<style scoped>
.tabs {
  display: flex;
  gap: 0;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid var(--border);
}

.tab {
  padding: 0.625rem 1.25rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  font-family: var(--font-body);
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--ink-light);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.tab--active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.url-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.url-panel__hint {
  font-size: 0.9375rem;
  color: var(--ink-light);
  line-height: 1.6;
}

.url-row {
  display: flex;
  gap: 0.5rem;
}

.url-row .input {
  flex: 1;
}

.import-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
  color: var(--ink-light);
  font-size: 0.9375rem;
}

.import-success-banner {
  background: var(--green-light);
  border: 1px solid var(--green);
  color: var(--green);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1rem;
  font-size: 0.9375rem;
  font-weight: 500;
  margin-bottom: 1.25rem;
}
</style>
