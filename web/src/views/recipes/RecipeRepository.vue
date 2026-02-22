<script setup lang="ts">
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { useRecipesStore } from '@/stores/recipes'
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const recipesStore = useRecipesStore()

onMounted(() => recipesStore.fetchRecipes())

watch([() => recipesStore.sort, () => recipesStore.favoritesOnly], () => {
  recipesStore.fetchRecipes()
})
</script>

<template>
  <div class="page">
    <nav class="page__nav">
      <router-link class="btn btn--ghost btn--sm" to="/">← Home</router-link>
      <span class="page__nav-brand">My Recipes</span>
      <router-link class="btn btn--ghost btn--sm" to="/settings">Settings</router-link>
    </nav>

    <div class="page__body container">
      <div class="filter-bar">
        <select v-model="recipesStore.sort" class="input select filter-bar__sort">
          <option value="recent">Most Recent</option>
          <option value="most_used">Most Used</option>
          <option value="alpha">A–Z</option>
          <option value="favorites_first">Favorites First</option>
        </select>
        <button
          class="btn btn--sm"
          :class="recipesStore.favoritesOnly ? 'btn--primary' : 'btn--ghost'"
          @click="recipesStore.favoritesOnly = !recipesStore.favoritesOnly"
        >
          ♥ Favorites
        </button>
      </div>

      <div v-if="recipesStore.loading" class="center-loading">
        <LoadingSpinner />
      </div>

      <div v-else-if="recipesStore.error" class="error-banner">
        {{ recipesStore.error }}
      </div>

      <div v-else-if="recipesStore.recipes.length === 0" class="empty-state">
        <p>No recipes yet.</p>
        <p class="empty-state__hint">Confirm a meal plan to start building your history.</p>
      </div>

      <div v-else class="recipe-grid">
        <button
          v-for="recipe in recipesStore.recipes"
          :key="recipe.id"
          class="recipe-card card"
          @click="router.push(`/recipes/${recipe.id}`)"
        >
          <div class="recipe-card__header">
            <span class="recipe-card__emoji">{{ recipe.emoji }}</span>
            <span v-if="recipe.is_favorite" class="recipe-card__fav" title="Favorite">♥</span>
          </div>
          <h3 class="recipe-card__name">{{ recipe.name }}</h3>
          <p class="recipe-card__ingredients">{{ recipe.key_ingredients.join(', ') }}</p>
          <div class="recipe-card__footer">
            <span class="recipe-card__meta">{{ recipe.prep_time }} min</span>
            <span class="recipe-card__used">Used {{ recipe.times_used }}×</span>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.center-loading {
  display: flex;
  justify-content: center;
  padding: 3rem 0;
}

.filter-bar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 1.25rem;
}

.filter-bar__sort {
  flex: 1;
  min-width: 0;
}

.empty-state {
  text-align: center;
  padding: 3rem 0;
  color: var(--ink-light);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.empty-state__hint {
  font-size: 0.875rem;
}

.recipe-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

@media (min-width: 480px) {
  .recipe-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.recipe-card {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  padding: 0.875rem;
  text-align: left;
  cursor: pointer;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: border-color 0.15s, box-shadow 0.15s;
  width: 100%;
}

.recipe-card:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow);
}

.recipe-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.recipe-card__emoji {
  font-size: 1.75rem;
  line-height: 1;
}

.recipe-card__fav {
  color: #e05c5c;
  font-size: 0.875rem;
}

.recipe-card__name {
  font-family: var(--font-display);
  font-size: 0.9375rem;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.recipe-card__ingredients {
  font-size: 0.75rem;
  color: var(--ink-light);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.recipe-card__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.25rem;
}

.recipe-card__meta {
  font-size: 0.75rem;
  color: var(--ink-light);
}

.recipe-card__used {
  font-size: 0.75rem;
  color: var(--ink-light);
}
</style>
