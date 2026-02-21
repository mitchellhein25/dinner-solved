import { computed, ref } from 'vue'

/**
 * Encapsulates save state: dirty detection, loading, success flash, and error.
 *
 * @param getSnapshot  - returns the current data to compare against the last save
 * @param saveFn       - async function that performs the actual save
 * @param successDuration - ms to show the success state before resetting (default 2500)
 */
export function useSaveState(
  getSnapshot: () => unknown,
  saveFn: () => Promise<void>,
  successDuration = 2500,
) {
  const savedSnapshot = ref('')
  const saving = ref(false)
  const success = ref(false)
  const error = ref<string | null>(null)

  const isDirty = computed(() => JSON.stringify(getSnapshot()) !== savedSnapshot.value)

  /** Call after initial data load to baseline the snapshot. */
  function markSaved() {
    savedSnapshot.value = JSON.stringify(getSnapshot())
  }

  async function save() {
    saving.value = true
    success.value = false
    error.value = null
    try {
      await saveFn()
      markSaved()
      success.value = true
      setTimeout(() => { success.value = false }, successDuration)
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      saving.value = false
    }
  }

  return { isDirty, saving, success, error, save, markSaved }
}
