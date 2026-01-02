import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  role: 'admin' | 'user' | 'viewer'
  organization?: string
  createdAt: string
}

interface AuthState {
  // State
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (name: string, email: string, password: string) => Promise<void>
  updateProfile: (updates: Partial<User>) => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      
      setToken: (token) => set({ token }),
      
      login: async (email, password) => {
        set({ isLoading: true, error: null })
        try {
          // Simulate API call
          await new Promise((resolve) => setTimeout(resolve, 1000))
          
          // Mock user for demo
          const user: User = {
            id: '1',
            email,
            name: email.split('@')[0],
            role: 'admin',
            createdAt: new Date().toISOString(),
          }
          
          set({
            user,
            token: 'mock-jwt-token',
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error: any) {
          set({
            error: error.message || 'Login failed',
            isLoading: false,
          })
          throw error
        }
      },
      
      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        })
      },
      
      register: async (name, email, password) => {
        set({ isLoading: true, error: null })
        try {
          // Simulate API call
          await new Promise((resolve) => setTimeout(resolve, 1000))
          
          const user: User = {
            id: Date.now().toString(),
            email,
            name,
            role: 'user',
            createdAt: new Date().toISOString(),
          }
          
          set({
            user,
            token: 'mock-jwt-token',
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error: any) {
          set({
            error: error.message || 'Registration failed',
            isLoading: false,
          })
          throw error
        }
      },
      
      updateProfile: async (updates) => {
        set({ isLoading: true, error: null })
        try {
          // Simulate API call
          await new Promise((resolve) => setTimeout(resolve, 500))
          
          const currentUser = get().user
          if (currentUser) {
            set({
              user: { ...currentUser, ...updates },
              isLoading: false,
            })
          }
        } catch (error: any) {
          set({
            error: error.message || 'Update failed',
            isLoading: false,
          })
          throw error
        }
      },
      
      clearError: () => set({ error: null }),
    }),
    {
      name: 'gennet-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
