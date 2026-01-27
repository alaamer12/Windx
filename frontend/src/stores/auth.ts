import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/services/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
    const user = ref<User | null>(null)
    const token = ref<string | null>(localStorage.getItem('access_token'))

    const isAuthenticated = computed(() => !!token.value && !!user.value)
    const isSuperuser = computed(() => user.value?.is_superuser ?? false)
    const isInitialized = ref(false)
    let initPromise: Promise<void> | null = null

    async function login(username: string, password: string) {
        try {
            const response = await apiClient.post('/api/v1/auth/login', {
                username,
                password
            })

            token.value = response.data.access_token
            localStorage.setItem('access_token', token.value!)

            await fetchCurrentUser()
            return { success: true }
        } catch (error: any) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Login failed'
            }
        }
    }

    async function fetchCurrentUser() {
        try {
            const response = await apiClient.get('/api/v1/auth/me')
            user.value = response.data
        } catch (error: any) {
            const is401 = error.response?.status === 401
            const isDev = import.meta.env.DEV

            if (is401 || (!isDev && error.response?.status === 403)) {
                logout()
            }
            throw error
        }
    }

    function logout() {
        user.value = null
        token.value = null
        localStorage.removeItem('access_token')
    }

    // Timeout wrapper to prevent infinite loading
    function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
        return Promise.race([
            promise,
            new Promise<T>((_, reject) =>
                setTimeout(() => reject(new Error('Request timeout')), timeoutMs)
            )
        ])
    }

    function initialize() {
        if (initPromise) return initPromise

        if (token.value) {
            // Add 10 second timeout to prevent infinite loading if backend is down
            initPromise = withTimeout(fetchCurrentUser(), 10000)
                .catch((error) => {
                    console.error('[Auth] Initialization failed:', error.message || error)
                    logout()

                    // Show user-friendly error if backend is unreachable
                    if (error.message === 'Request timeout' || error.code === 'ERR_NETWORK') {
                        console.error('[Auth] Backend appears to be down or unreachable')
                    }
                })
                .finally(() => {
                    isInitialized.value = true
                })
        } else {
            isInitialized.value = true
            initPromise = Promise.resolve()
        }
        return initPromise
    }

    // Start initialization immediately
    initialize()

    return {
        user,
        token,
        isAuthenticated,
        isSuperuser,
        isInitialized,
        initialize,
        login,
        logout,
        fetchCurrentUser
    }
})
