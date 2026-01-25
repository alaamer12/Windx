<template>
  <div class="not-found">
    <h1>404</h1>
    <p>Page not found</p>
    <router-link to="/dashboard" class="btn btn-primary">
      Go to Dashboard
    </router-link>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
  padding: 2rem;
}

h1 {
  font-size: 6rem;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 1rem;
}

p {
  font-size: 1.5rem;
  color: var(--text-light);
  margin-bottom: 2rem;
}
</style>
