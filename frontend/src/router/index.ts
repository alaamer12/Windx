import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
    {
        path: '/',
        redirect: '/dashboard'
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/auth/LoginView.vue'),
        meta: { requiresAuth: false }
    },
    {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/profile-entry',
        name: 'ProfileEntry',
        component: () => import('@/views/entry/ProfileEntryView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/configurations',
        name: 'Configurations',
        component: () => import('@/views/ConfigurationsView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/customers',
        name: 'Customers',
        component: () => import('@/views/CustomersView.vue'),
        meta: { requiresAuth: true, requiresSuperuser: true }
    },
    {
        path: '/quotes',
        name: 'Quotes',
        component: () => import('@/views/QuotesView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/orders',
        name: 'Orders',
        component: () => import('@/views/OrdersView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/NotFoundView.vue')
    }
]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
    const authStore = useAuthStore()
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
    const requiresSuperuser = to.matched.some(record => record.meta.requiresSuperuser)

    if (requiresAuth && !authStore.isAuthenticated) {
        next({ name: 'Login', query: { redirect: to.fullPath } })
    } else if (requiresSuperuser && !authStore.isSuperuser) {
        next({ name: 'Dashboard' })
    } else {
        next()
    }
})

export default router
