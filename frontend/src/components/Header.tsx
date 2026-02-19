'use client'

import { useState } from 'react'
import { LogOut, User, Settings, ChevronDown, Shield } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useRouter } from 'next/navigation'

export function Header() {
  const [showProfileMenu, setShowProfileMenu] = useState(false)

  const { user, logout } = useAuthStore()
  const router = useRouter()

  const handleLogout = () => {
    logout()
    setShowProfileMenu(false)
    router.push('/login')
  }

  const handleSettingsClick = () => {
    setShowProfileMenu(false)
    router.push('/dashboard/settings')
  }

  const handleOutsideClick = () => {
    setShowProfileMenu(false)
  }

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8 relative">
      <div className="flex-1"></div>

      <div className="flex items-center gap-4">
        {/* Profile Menu */}
        <div className="relative">
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-3 pl-4 border-l border-gray-200 hover:bg-gray-50 rounded-lg p-2 transition-colors"
          >
            <div className="text-right">
              <p className="text-sm font-bold text-black">
                {user?.full_name || user?.first_name || 'Admin'}
              </p>
              <p className="text-xs font-semibold text-gray-700">Administrator</p>
            </div>
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
              <Shield className="h-5 w-5 text-primary-600" />
            </div>
            <ChevronDown className={`h-4 w-4 text-gray-600 transition-transform ${showProfileMenu ? 'rotate-180' : ''}`} />
          </button>

          {/* Dropdown Menu */}
          {showProfileMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={handleOutsideClick}
              />

              <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-20 py-2">
                <button
                  onClick={handleSettingsClick}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <Settings className="h-4 w-4" />
                  Profile Settings
                </button>

                <div className="border-t border-gray-100 my-1"></div>

                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

