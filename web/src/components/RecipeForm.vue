<script setup lang="ts">
import type { Ingredient, RecipeDraft } from '@/types'
import { CATEGORY_LABELS } from '@/types'
import { reactive, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    initialData?: Partial<RecipeDraft>
    loading?: boolean
    submitLabel?: string
  }>(),
  { loading: false, submitLabel: 'Save Recipe' },
)

const emit = defineEmits<{
  submit: [draft: RecipeDraft]
  cancel: []
}>()

// ---------------------------------------------------------------------------
// Local form state
// ---------------------------------------------------------------------------

interface FormIngredient {
  name: string
  quantity: string
  unit: string
  category: string
}

const form = reactive({
  name: '',
  emoji: '🍽️',
  prep_time: 30,
  keyIngredientsText: '',  // comma-separated
  ingredients: [] as FormIngredient[],
  instructions: [] as string[],
  source_url: '',
})

function applyInitialData(data?: Partial<RecipeDraft>) {
  form.name = data?.name ?? ''
  form.emoji = data?.emoji ?? '🍽️'
  form.prep_time = data?.prep_time ?? 30
  form.keyIngredientsText = data?.key_ingredients?.join(', ') ?? ''
  form.source_url = data?.source_url ?? ''
  form.ingredients = (data?.ingredients ?? []).map((i) => ({
    name: i.name,
    quantity: String(i.quantity),
    unit: i.unit,
    category: i.category,
  }))
  form.instructions = [...(data?.cooking_instructions ?? [])]
}

// Seed form when initialData prop changes (e.g. URL import result arrives)
watch(() => props.initialData, applyInitialData, { immediate: true })

// ---------------------------------------------------------------------------
// Ingredient rows
// ---------------------------------------------------------------------------

function addIngredient() {
  form.ingredients.push({ name: '', quantity: '1', unit: 'whole', category: 'produce' })
}

function removeIngredient(index: number) {
  form.ingredients.splice(index, 1)
}

// ---------------------------------------------------------------------------
// Instruction steps
// ---------------------------------------------------------------------------

function addStep() {
  form.instructions.push('')
}

function removeStep(index: number) {
  form.instructions.splice(index, 1)
}

// ---------------------------------------------------------------------------
// Submit
// ---------------------------------------------------------------------------

function handleSubmit() {
  const key_ingredients = form.keyIngredientsText
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  const ingredients: Ingredient[] = form.ingredients
    .filter((i) => i.name.trim())
    .map((i) => ({
      name: i.name.trim(),
      quantity: parseFloat(i.quantity) || 0,
      unit: i.unit.trim() || 'whole',
      category: i.category,
    }))

  const cooking_instructions =
    form.instructions.filter((s) => s.trim()).length > 0
      ? form.instructions.filter((s) => s.trim())
      : null

  const draft: RecipeDraft = {
    name: form.name.trim(),
    emoji: form.emoji.trim() || '🍽️',
    prep_time: form.prep_time,
    key_ingredients,
    ingredients,
    cooking_instructions,
    source_url: form.source_url.trim() || null,
  }

  emit('submit', draft)
}

const UNITS = ['whole', 'lbs', 'oz', 'g', 'kg', 'cups', 'tbsp', 'tsp', 'ml', 'l', 'slices', 'cans', 'cloves', 'pinch']
const CATEGORIES = Object.entries(CATEGORY_LABELS).map(([value, label]) => ({ value, label }))
</script>

<template>
  <form class="recipe-form" @submit.prevent="handleSubmit">
    <!-- Basic info -->
    <div class="field-row field-row--basic">
      <div class="field field--emoji">
        <label class="label" for="rf-emoji">Emoji</label>
        <input id="rf-emoji" v-model="form.emoji" class="input" maxlength="4" placeholder="🍽️" />
      </div>
      <div class="field field--name">
        <label class="label" for="rf-name">Recipe Name</label>
        <input id="rf-name" v-model="form.name" class="input" placeholder="e.g. Lemon Herb Chicken" required />
      </div>
    </div>

    <div class="field-row">
      <div class="field">
        <label class="label" for="rf-prep">Prep Time (minutes)</label>
        <input id="rf-prep" v-model.number="form.prep_time" class="input" type="number" min="1" max="480" required />
      </div>
      <div class="field">
        <label class="label" for="rf-url">Source URL <span class="label-optional">(optional)</span></label>
        <input id="rf-url" v-model="form.source_url" class="input" type="url" placeholder="https://…" />
      </div>
    </div>

    <!-- Key ingredients -->
    <div class="field">
      <label class="label" for="rf-key">Key Ingredients <span class="label-optional">(comma-separated, used for display)</span></label>
      <input id="rf-key" v-model="form.keyIngredientsText" class="input" placeholder="e.g. chicken, lemon, garlic" />
    </div>

    <!-- Full ingredient list -->
    <div class="form-section">
      <div class="form-section__header">
        <h3 class="form-section__title">Ingredients <span class="label-optional">(per 1 serving)</span></h3>
        <button type="button" class="btn btn--ghost btn--sm" @click="addIngredient">+ Add</button>
      </div>

      <div v-if="form.ingredients.length === 0" class="form-section__empty">
        No ingredients added yet.
      </div>

      <div v-else class="ingredient-rows">
        <div v-for="(ing, i) in form.ingredients" :key="i" class="ingredient-row">
          <input v-model="ing.name" class="input ing-name" placeholder="Name" />
          <input v-model="ing.quantity" class="input ing-qty" type="number" min="0" step="any" placeholder="Qty" />
          <input v-model="ing.unit" class="input ing-unit" placeholder="Unit" list="rf-units" />
          <datalist id="rf-units">
            <option v-for="u in UNITS" :key="u" :value="u" />
          </datalist>
          <select v-model="ing.category" class="input select ing-cat">
            <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
          <button type="button" class="btn btn--danger btn--sm ing-remove" title="Remove" @click="removeIngredient(i)">×</button>
        </div>
      </div>
    </div>

    <!-- Cooking instructions -->
    <div class="form-section">
      <div class="form-section__header">
        <h3 class="form-section__title">Instructions <span class="label-optional">(optional)</span></h3>
        <button type="button" class="btn btn--ghost btn--sm" @click="addStep">+ Add Step</button>
      </div>

      <div v-if="form.instructions.length === 0" class="form-section__empty">
        No steps added. Instructions can also be AI-generated later.
      </div>

      <div v-else class="instruction-rows">
        <div v-for="(_, i) in form.instructions" :key="i" class="instruction-row">
          <span class="step-number">{{ i + 1 }}</span>
          <textarea
            v-model="form.instructions[i]"
            class="input step-textarea"
            rows="2"
            :placeholder="`Step ${i + 1}…`"
          />
          <button type="button" class="btn btn--danger btn--sm" title="Remove step" @click="removeStep(i)">×</button>
        </div>
      </div>
    </div>

    <!-- Form actions -->
    <div class="form-actions">
      <button type="button" class="btn btn--ghost" @click="emit('cancel')">Cancel</button>
      <button
        type="submit"
        class="btn btn--primary"
        :disabled="loading || !form.name.trim()"
      >
        {{ loading ? 'Saving…' : submitLabel }}
      </button>
    </div>
  </form>
</template>

<style scoped>
.recipe-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  flex: 1;
  min-width: 0;
}

.field-row {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
}

.field--emoji {
  flex: 0 0 5rem;
}

.field--name {
  flex: 1;
}

.label-optional {
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  color: var(--ink-light);
  font-size: 0.75rem;
}

/* Sections */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.form-section__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-section__title {
  font-family: var(--font-body);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--ink-light);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.form-section__empty {
  font-size: 0.875rem;
  color: var(--ink-light);
  font-style: italic;
  padding: 0.5rem 0;
}

/* Ingredient rows */
.ingredient-rows {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ingredient-row {
  display: grid;
  grid-template-columns: 1fr 4.5rem 5.5rem 7rem 2rem;
  gap: 0.375rem;
  align-items: center;
}

.ing-remove {
  padding: 0.375rem;
  font-size: 1rem;
  line-height: 1;
}

/* Instruction rows */
.instruction-rows {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.instruction-row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
}

.step-number {
  flex-shrink: 0;
  width: 1.5rem;
  height: 1.5rem;
  background: var(--accent);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  margin-top: 0.625rem;
}

.step-textarea {
  flex: 1;
  resize: vertical;
  min-height: 3rem;
}

/* Actions */
.form-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border);
}

/* Mobile — stack ingredients vertically */
@media (max-width: 540px) {
  .ingredient-row {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto;
  }

  .ing-name { grid-column: 1 / -1; }
  .ing-cat  { grid-column: 1 / -1; }
}
</style>
