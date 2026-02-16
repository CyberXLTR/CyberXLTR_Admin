import { create } from 'zustand'

interface User {
  id: string
  email: string
  first_name: string
  last_name?: string
  full_name?: string
  role: string
}

interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (user: User, token: string) => void
  logout: () => void
  initAuth: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  
  login: (user, token) => {
    localStorage.setItem('admin_token', token)
    localStorage.setItem('admin_user', JSON.stringify(user))
    set({ user, token, isAuthenticated: true })
  },
  
  logout: () => {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
    set({ user: null, token: null, isAuthenticated: false })
  },
  
  initAuth: () => {
    const token = localStorage.getItem('admin_token')
    const userStr = localStorage.getItem('admin_user')
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr)
        set({ user, token, isAuthenticated: true })
      } catch {
        localStorage.removeItem('admin_token')
        localStorage.removeItem('admin_user')
      }
    }
  },
}))

