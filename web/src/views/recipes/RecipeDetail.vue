<script setup lang="ts">
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { recipesApi } from '@/api/recipes'
import { useRecipesStore } from '@/stores/recipes'
import { CATEGORY_LABELS } from '@/types'
import type { Ingredient, RecipeDetail } from '@/types'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const recipesStore = useRecipesStore()

const recipe = ref<RecipeDetail | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const togglingFavorite = ref(false)
const generatingInstructions = ref(false)

// Edit state
const editing = ref(false)
const editName = ref('')
const editEmoji = ref('')
const editError = ref<string | null>(null)
const saving = ref(false)

// Delete state
const deleting = ref(false)
const downloadingPdf = ref(false)

const groupedIngredients = computed(() => {
  if (!recipe.value) return {} as Record<string, Ingredient[]>
  const groups: Record<string, Ingredient[]> = {}
  for (const ing of recipe.value.ingredients) {
    if (!groups[ing.category]) groups[ing.category] = []
    groups[ing.category].push(ing)
  }
  return groups
})

onMounted(async () => {
  try {
    recipe.value = await recipesApi.getRecipe(route.params.id as string)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }

  // Non-blocking: generate instructions if they don't exist
  if (recipe.value && recipe.value.cooking_instructions === null) {
    generatingInstructions.value = true
    try {
      const updated = await recipesApi.generateInstructions(recipe.value.id)
      recipe.value = updated
    } catch {
      // Non-fatal — just leave instructions as null
    } finally {
      generatingInstructions.value = false
    }
  }
})

async function toggleFavorite() {
  if (!recipe.value) return
  togglingFavorite.value = true
  try {
    const updated = await recipesStore.toggleFavorite(recipe.value.id)
    if (updated) recipe.value = updated
  } finally {
    togglingFavorite.value = false
  }
}

function startEdit() {
  if (!recipe.value) return
  editName.value = recipe.value.name
  editEmoji.value = recipe.value.emoji
  editError.value = null
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  editError.value = null
}

async function saveEdit() {
  if (!recipe.value) return
  saving.value = true
  editError.value = null
  try {
    const updated = await recipesApi.updateRecipe(recipe.value.id, editName.value.trim(), editEmoji.value.trim())
    recipe.value = updated
    editing.value = false
  } catch (e: any) {
    if (e?.response?.status === 409) {
      editError.value = 'A recipe with that name already exists.'
    } else {
      editError.value = 'Failed to save changes.'
    }
  } finally {
    saving.value = false
  }
}

async function downloadPdf() {
  if (!recipe.value) return
  downloadingPdf.value = true
  try {
    await recipesApi.downloadRecipePdf(recipe.value.id, recipe.value.name)
  } finally {
    downloadingPdf.value = false
  }
}

async function deleteRecipe() {
  if (!recipe.value) return
  if (!confirm(`Delete "${recipe.value.name}"? This cannot be undone.`)) return
  deleting.value = true
  try {
    await recipesApi.deleteRecipe(recipe.value.id)
    router.push('/recipes')
  } catch {
    // Show inline error
    error.value = 'Failed to delete recipe.'
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="page">
    <nav class="page__nav">
      <router-link class="btn btn--ghost btn--sm" to="/recipes">← Recipes</router-link>
      <span class="page__nav-brand">{{ recipe?.name ?? 'Recipe' }}</span>
      <button
        v-if="recipe"
        class="btn btn--sm fav-btn"
        :class="recipe.is_favorite ? 'fav-btn--active' : 'btn--ghost'"
        :disabled="togglingFavorite"
        :title="recipe.is_favorite ? 'Remove from favorites' : 'Add to favorites'"
        @click="toggleFavorite"
      >
        <LoadingSpinner v-if="togglingFavorite" size="sm" />
        <span v-else>{{ recipe.is_favorite ? '♥' : '♡' }}</span>
      </button>
      <span v-else />
    </nav>

    <div class="page__body container">
      <div v-if="loading" class="center-loading">
        <LoadingSpinner />
      </div>

      <div v-else-if="error" class="error-banner">
        {{ error }}
      </div>

      <template v-else-if="recipe">
        <!-- Hero — normal or edit mode -->
        <div v-if="!editing" class="hero">
          <span class="hero__emoji">{{ recipe.emoji }}</span>
          <div class="hero__body">
            <h1 class="hero__name">{{ recipe.name }}</h1>
            <div class="hero__chips">
              <span class="chip">{{ recipe.prep_time }} min</span>
              <span class="chip">Used {{ recipe.times_used }}×</span>
            </div>
          </div>
          <button class="btn btn--ghost btn--sm hero__edit-btn" title="Edit name / emoji" @click="startEdit">
            ✏️
          </button>
        </div>

        <div v-else class="hero-edit card">
          <div class="hero-edit__row">
            <input v-model="editEmoji" class="input hero-edit__emoji" maxlength="4" placeholder="😊" />
            <input v-model="editName" class="input hero-edit__name" placeholder="Recipe name" @keyup.enter="saveEdit" @keyup.escape="cancelEdit" />
          </div>
          <div v-if="editError" class="error-banner" style="margin-top: 0.5rem">{{ editError }}</div>
          <div class="hero-edit__actions">
            <button class="btn btn--ghost btn--sm" :disabled="saving" @click="cancelEdit">Cancel</button>
            <button class="btn btn--primary btn--sm" :disabled="saving || !editName.trim()" @click="saveEdit">
              <LoadingSpinner v-if="saving" size="sm" />
              <span v-else>Save</span>
            </button>
          </div>
        </div>

        <!-- Key ingredients -->
        <section class="section">
          <h2 class="section__title">Key Ingredients</h2>
          <div class="key-ingredients">
            <span v-for="ing in recipe.key_ingredients" :key="ing" class="chip">{{ ing }}</span>
          </div>
        </section>

        <!-- Full ingredients grouped by category -->
        <section class="section">
          <h2 class="section__title">Ingredients</h2>
          <div
            v-for="(items, category) in groupedIngredients"
            :key="category"
            class="ingredient-group"
          >
            <p class="ingredient-group__label">{{ CATEGORY_LABELS[category] ?? category }}</p>
            <div class="ingredient-list">
              <div v-for="ing in items" :key="ing.name" class="ingredient-row">
                <span class="ingredient-row__name">{{ ing.name }}</span>
                <span class="ingredient-row__qty">{{ ing.quantity }} {{ ing.unit }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Cooking instructions -->
        <section class="section">
          <h2 class="section__title">Instructions</h2>
          <div v-if="generatingInstructions" class="instructions-loading">
            <LoadingSpinner size="sm" />
            <span>Generating instructions…</span>
          </div>
          <div v-else-if="recipe.cooking_instructions === null" class="instructions-loading">
            <span class="instructions-loading__none">Instructions not yet generated.</span>
          </div>
          <ol v-else class="instructions-list">
            <li
              v-for="(step, i) in recipe.cooking_instructions"
              :key="i"
              class="instruction-step"
            >
              {{ step }}
            </li>
          </ol>
        </section>

        <!-- Actions row -->
        <div class="actions-row">
          <button
            class="btn btn--ghost btn--sm"
            :disabled="downloadingPdf"
            @click="downloadPdf"
          >
            <LoadingSpinner v-if="downloadingPdf" size="sm" />
            <span v-else>📄 Download PDF</span>
          </button>
          <button
            class="btn btn--ghost btn--sm delete-btn"
            :disabled="deleting"
            @click="deleteRecipe"
          >
            <LoadingSpinner v-if="deleting" size="sm" />
            <span v-else>🗑 Delete</span>
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.center-loading {
  display: flex;
  justify-content: center;
  padding: 3rem 0;
}

.fav-btn {
  min-width: 2.25rem;
  font-size: 1.125rem;
}

.fav-btn--active {
  color: #e05c5c;
  border-color: #e05c5c;
  background: #fff5f5;
}

.hero {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.75rem;
}

.hero__emoji {
  font-size: 3rem;
  line-height: 1;
  flex-shrink: 0;
}

.hero__body {
  flex: 1;
  min-width: 0;
}

.hero__name {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 300;
  margin-bottom: 0.5rem;
}

.hero__chips {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.hero__edit-btn {
  flex-shrink: 0;
  font-size: 0.9rem;
}

.hero-edit {
  padding: 1rem;
  margin-bottom: 1.75rem;
}

.hero-edit__row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.hero-edit__emoji {
  width: 4rem;
  text-align: center;
  font-size: 1.5rem;
}

.hero-edit__name {
  flex: 1;
}

.hero-edit__actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 0.75rem;
}

.section {
  margin-bottom: 1.75rem;
}

.section__title {
  font-family: var(--font-display);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-light);
  margin-bottom: 0.75rem;
}

.key-ingredients {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.ingredient-group {
  margin-bottom: 1rem;
}

.ingredient-group__label {
  font-size: 0.8125rem;
  color: var(--ink-light);
  font-style: italic;
  margin-bottom: 0.375rem;
}

.ingredient-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.ingredient-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 0.75rem;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.ingredient-row__name {
  font-size: 0.9375rem;
}

.ingredient-row__qty {
  font-size: 0.875rem;
  color: var(--ink-light);
}

.instructions-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--ink-light);
  font-size: 0.9375rem;
  padding: 0.5rem 0;
}

.instructions-loading__none {
  font-style: italic;
}

.instructions-list {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  padding-left: 1.25rem;
}

.instruction-step {
  font-size: 0.9375rem;
  line-height: 1.6;
}

.actions-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-top: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.delete-btn {
  color: #c0392b;
  border-color: #e0837a;
}

.delete-btn:hover:not(:disabled) {
  background: #fff5f5;
}
</style>
