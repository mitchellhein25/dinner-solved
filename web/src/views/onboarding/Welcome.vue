<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="welcome">
    <div class="welcome__inner">
      <div class="welcome__brand">🍽️</div>
      <h1 class="welcome__title">Dinner<br /><em>Solved.</em></h1>
      <p class="welcome__sub">
        Open the app. Get recipe suggestions. Confirm.<br />Grocery list done.
      </p>
      <p class="welcome__desc">
        Set up your household once — who eats what and how much — and every week
        the app suggests recipes scaled exactly for your family, then builds the
        grocery list automatically.
      </p>

      <div class="welcome__steps">
        <div class="welcome__step">
          <span class="welcome__step-num">1</span>
          <span>Tell us who's eating and how much they eat</span>
        </div>
        <div class="welcome__step">
          <span class="welcome__step-num">2</span>
          <span>Define your weekly meal slots once</span>
        </div>
        <div class="welcome__step">
          <span class="welcome__step-num">3</span>
          <span>Every week: confirm recipes, export grocery list</span>
        </div>
      </div>

      <button class="btn btn--primary btn--full" @click="router.push('/onboarding/household')">
        Get Started →
      </button>
    </div>
  </div>
</template>

<style scoped>
.welcome {
  min-height: 100dvh;
  background: var(--warm-white);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.25rem;
}
.welcome__inner {
  max-width: 480px;
  width: 100%;
}
.welcome__brand {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}
.welcome__title {
  font-family: var(--font-display);
  font-size: 3rem;
  font-weight: 300;
  line-height: 1.1;
  margin-bottom: 1rem;
  color: var(--ink);
}
.welcome__title em {
  color: var(--accent);
}
.welcome__sub {
  font-size: 1.0625rem;
  color: var(--ink-light);
  margin-bottom: 1.25rem;
  line-height: 1.5;
}
.welcome__desc {
  font-size: 0.9375rem;
  color: var(--ink-light);
  margin-bottom: 2rem;
  line-height: 1.6;
}
.welcome__steps {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 2rem;
}
.welcome__step {
  display: flex;
  align-items: flex-start;
  gap: 0.875rem;
  font-size: 0.9375rem;
}
.welcome__step-num {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 1px;
}
</style>
