import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export type Theme = 'light' | 'dark' | 'system'
export type ViewMode = 'grid' | 'table' | 'list'

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message?: string
  read: boolean
  timestamp: string
  link?: string
}

interface UIState {
  // Theme
  theme: Theme
  setTheme: (theme: Theme) => void
  
  // Sidebar
  sidebarOpen: boolean
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setSidebarCollapsed: (collapsed: boolean) => void
  
  // View preferences
  defaultViewMode: ViewMode
  setDefaultViewMode: (mode: ViewMode) => void
  
  // Notifications
  notifications: Notification[]
  unreadCount: number
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
  
  // Command palette
  commandPaletteOpen: boolean
  setCommandPaletteOpen: (open: boolean) => void
  toggleCommandPalette: () => void
  
  // Search
  globalSearch: string
  setGlobalSearch: (search: string) => void
  
  // Mobile
  isMobile: boolean
  setIsMobile: (mobile: boolean) => void
  
  // Loading states
  globalLoading: boolean
  setGlobalLoading: (loading: boolean) => void
  
  // Modal management
  activeModal: string | null
  modalData: any
  openModal: (modalId: string, data?: any) => void
  closeModal: () => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      // Theme
      theme: 'system',
      setTheme: (theme) => {
        set({ theme })
        // Apply theme to document
        const root = document.documentElement
        if (theme === 'system') {
          const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark'
            : 'light'
          root.classList.toggle('dark', systemTheme === 'dark')
        } else {
          root.classList.toggle('dark', theme === 'dark')
        }
      },
      
      // Sidebar
      sidebarOpen: true,
      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ 
        sidebarOpen: !state.sidebarOpen 
      })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      
      // View preferences
      defaultViewMode: 'grid',
      setDefaultViewMode: (mode) => set({ defaultViewMode: mode }),
      
      // Notifications
      notifications: [],
      unreadCount: 0,
      addNotification: (notification) => {
        const newNotification: Notification = {
          ...notification,
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
          read: false,
        }
        set((state) => ({
          notifications: [newNotification, ...state.notifications].slice(0, 50), // Keep max 50
          unreadCount: state.unreadCount + 1,
        }))
      },
      markAsRead: (id) => set((state) => {
        const notification = state.notifications.find((n) => n.id === id)
        if (notification && !notification.read) {
          return {
            notifications: state.notifications.map((n) =>
              n.id === id ? { ...n, read: true } : n
            ),
            unreadCount: Math.max(0, state.unreadCount - 1),
          }
        }
        return state
      }),
      markAllAsRead: () => set((state) => ({
        notifications: state.notifications.map((n) => ({ ...n, read: true })),
        unreadCount: 0,
      })),
      removeNotification: (id) => set((state) => {
        const notification = state.notifications.find((n) => n.id === id)
        return {
          notifications: state.notifications.filter((n) => n.id !== id),
          unreadCount: notification && !notification.read
            ? Math.max(0, state.unreadCount - 1)
            : state.unreadCount,
        }
      }),
      clearNotifications: () => set({ notifications: [], unreadCount: 0 }),
      
      // Command palette
      commandPaletteOpen: false,
      setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
      toggleCommandPalette: () => set((state) => ({ 
        commandPaletteOpen: !state.commandPaletteOpen 
      })),
      
      // Search
      globalSearch: '',
      setGlobalSearch: (search) => set({ globalSearch: search }),
      
      // Mobile
      isMobile: false,
      setIsMobile: (mobile) => set({ isMobile: mobile }),
      
      // Loading states
      globalLoading: false,
      setGlobalLoading: (loading) => set({ globalLoading: loading }),
      
      // Modal management
      activeModal: null,
      modalData: null,
      openModal: (modalId, data) => set({ activeModal: modalId, modalData: data }),
      closeModal: () => set({ activeModal: null, modalData: null }),
    }),
    {
      name: 'gennet-ui',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        defaultViewMode: state.defaultViewMode,
      }),
    }
  )
)
