<script setup lang="ts">
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { groceryApi } from '@/api/grocery'
import { usePlanStore } from '@/stores/plan'
import type { GroceryListItem } from '@/types'
import { CATEGORY_LABELS } from '@/types'
import { computed, onMounted, ref } from 'vue'

const planStore = usePlanStore()

const exporting = ref(false)
const exportMsg = ref<string | null>(null)

onMounted(async () => {
  if (planStore.groceryItems.length === 0) {
    await planStore.fetchGroceryList()
  }
})

const byCategory = computed(() => {
  const groups: Record<string, GroceryListItem[]> = {}
  for (const item of planStore.groceryItems) {
    if (!groups[item.category]) groups[item.category] = []
    groups[item.category].push(item)
  }
  return groups
})

async function exportPdf() {
  exporting.value = true
  exportMsg.value = null
  try {
    await groceryApi.downloadGroceryPdf(planStore.weekStartDate)
  } catch (e) {
    exportMsg.value = 'PDF export failed: ' + (e as Error).message
  } finally {
    exporting.value = false
  }
}

async function exportCsv() {
  exporting.value = true
  exportMsg.value = null
  try {
    const res = await groceryApi.exportCsv(planStore.weekStartDate)
    const blob = new Blob([res.data.result], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `grocery-list-${planStore.weekStartDate}.csv`
    a.click()
    URL.revokeObjectURL(url)
    exportMsg.value = 'CSV downloaded.'
  } catch (e) {
    exportMsg.value = 'Export failed: ' + (e as Error).message
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div class="page">
    <nav class="page__nav">
      <router-link class="btn btn--ghost btn--sm" to="/">← Plan</router-link>
      <span class="page__nav-brand">Grocery List</span>
      <span />
    </nav>

    <div class="page__body container">
      <div v-if="planStore.loading" class="center-loading">
        <LoadingSpinner />
      </div>

      <template v-else>
        <div v-if="planStore.error" class="error-banner" style="margin-bottom: 1rem">
          {{ planStore.error }}
        </div>

        <div v-if="exportMsg" class="export-msg">{{ exportMsg }}</div>

        <div v-for="(items, category) in byCategory" :key="category" class="category-section">
          <h3 class="category-section__title">{{ CATEGORY_LABELS[category] ?? category }}</h3>
          <div class="item-list">
            <div v-for="item in items" :key="item.name + item.unit" class="item-row">
              <div class="item-row__left">
                <span class="item-row__name">{{ item.name }}</span>
                <span v-if="item.recipe_names.length > 0" class="item-row__recipes">
                  {{ item.recipe_names.join(', ') }}
                </span>
              </div>
              <span class="item-row__qty">{{ item.quantity }} {{ item.unit }}</span>
            </div>
          </div>
        </div>

        <div v-if="Object.keys(byCategory).length === 0" class="empty-state">
          <p>No grocery items yet.</p>
        </div>

        <div class="export-row">
          <button class="btn btn--ghost btn--full" :disabled="exporting" @click="exportCsv">
            <LoadingSpinner v-if="exporting" size="sm" />
            <span v-else>📄 Export CSV</span>
          </button>
          <button
            class="btn btn--ghost btn--full"
            :disabled="exporting"
            @click="exportPdf"
          >📥 Download PDF</button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.center-loading { display: flex; justify-content: center; padding: 3rem 0; }
.export-msg { background: var(--green-light); border: 1px solid var(--green); color: var(--green); border-radius: var(--radius-sm); padding: 0.75rem 1rem; font-size: 0.875rem; margin-bottom: 1rem; }
.category-section { margin-bottom: 1.5rem; }
.category-section__title { font-family: var(--font-display); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--ink-light); margin-bottom: 0.5rem; }
.item-list { display: flex; flex-direction: column; gap: 0.375rem; }
.item-row { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; padding: 0.5rem 0.75rem; background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius-sm); }
.item-row__left { display: flex; flex-direction: column; gap: 0.125rem; min-width: 0; }
.item-row__name { font-size: 0.9375rem; }
.item-row__recipes { font-size: 0.75rem; color: var(--ink-light); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-row__qty { font-size: 0.875rem; color: var(--ink-light); white-space: nowrap; flex-shrink: 0; }
.empty-state { text-align: center; padding: 2rem; color: var(--ink-light); }
.export-row { margin-top: 1.5rem; display: flex; flex-direction: column; gap: 0.5rem; }
</style>
