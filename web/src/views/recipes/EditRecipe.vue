<script setup lang="ts">
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import RecipeForm from '@/components/RecipeForm.vue'
import { recipesApi } from '@/api/recipes'
import type { RecipeDraft } from '@/types'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const id = route.params.id as string

const loading = ref(true)
const loadError = ref<string | null>(null)
const initialData = ref<RecipeDraft | null>(null)

const saving = ref(false)
const saveError = ref<string | null>(null)

onMounted(async () => {
  try {
    const recipe = await recipesApi.getRecipe(id)
    initialData.value = {
      name: recipe.name,
      emoji: recipe.emoji,
      prep_time: recipe.prep_time,
      ingredients: recipe.ingredients,
      key_ingredients: recipe.key_ingredients,
      source_url: recipe.source_url,
      cooking_instructions: recipe.cooking_instructions,
    }
  } catch {
    loadError.value = 'Could not load recipe.'
  } finally {
    loading.value = false
  }
})

async function handleSave(draft: RecipeDraft) {
  saving.value = true
  saveError.value = null
  try {
    await recipesApi.updateRecipeFull(id, draft)
    router.push(`/recipes/${id}`)
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    if (e?.response?.status === 409) {
      saveError.value = typeof detail === 'string' ? detail : 'A recipe with that name already exists.'
    } else {
      saveError.value = 'Failed to save changes.'
    }
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.push(`/recipes/${id}`)
}
</script>

<template>
  <div class="page">
    <nav class="page__nav">
      <router-link class="btn btn--ghost btn--sm" :to="`/recipes/${id}`">← Recipe</router-link>
      <span class="page__nav-brand">Edit Recipe</span>
      <span />
    </nav>

    <div class="page__body container">
      <div v-if="loading" class="center-loading">
        <LoadingSpinner />
      </div>

      <div v-else-if="loadError" class="error-banner">{{ loadError }}</div>

      <template v-else-if="initialData">
        <div v-if="saveError" class="error-banner" style="margin-bottom: 1rem">{{ saveError }}</div>
        <RecipeForm
          :initial-data="initialData"
          :loading="saving"
          submit-label="Save Changes"
          @submit="handleSave"
          @cancel="handleCancel"
        />
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
</style>
