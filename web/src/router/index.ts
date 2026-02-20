import { createRouter, createWebHistory } from 'vue-router'

const HOUSEHOLD_KEY = 'dinner_solved_household_id'
const ONBOARDING_KEY = 'dinner_solved_onboarded'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // Auth
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/Login.vue'),
      meta: { public: true },
    },
    {
      path: '/auth/verify',
      name: 'auth-verify',
      component: () => import('@/views/auth/AuthVerify.vue'),
      meta: { public: true },
    },

    // Onboarding
    {
      path: '/welcome',
      name: 'welcome',
      component: () => import('@/views/onboarding/Welcome.vue'),
      meta: { onboarding: true },
    },
    {
      path: '/onboarding/household',
      name: 'onboarding-household',
      component: () => import('@/views/onboarding/HouseholdSetup.vue'),
      meta: { onboarding: true },
    },
    {
      path: '/onboarding/sizes',
      name: 'onboarding-sizes',
      component: () => import('@/views/onboarding/ServingSizes.vue'),
      meta: { onboarding: true },
    },
    {
      path: '/onboarding/template',
      name: 'onboarding-template',
      component: () => import('@/views/onboarding/MealTemplate.vue'),
      meta: { onboarding: true },
    },

    // Main app
    {
      path: '/',
      name: 'week',
      component: () => import('@/views/planner/WeeklyOverview.vue'),
    },
    {
      path: '/suggestions',
      name: 'suggestions',
      component: () => import('@/views/planner/RecipeSuggestions.vue'),
    },
    {
      path: '/grocery',
      name: 'grocery',
      component: () => import('@/views/planner/GroceryList.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/settings/Settings.vue'),
    },

    // Fallback
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  // Public routes (login, verify) — always allow
  if (to.meta.public) return

  const authenticated = localStorage.getItem(HOUSEHOLD_KEY) !== null
  if (!authenticated) {
    return { name: 'login' }
  }

  const onboarded = localStorage.getItem(ONBOARDING_KEY) === 'true'
  if (!onboarded && !to.meta.onboarding) {
    return { name: 'welcome' }
  }
  if (onboarded && to.name === 'welcome') {
    return { name: 'week' }
  }
})

export default router
