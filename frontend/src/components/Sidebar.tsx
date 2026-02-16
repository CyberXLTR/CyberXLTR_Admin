'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard,
  Settings,
  Shield,
  Building2,
  Users,
  Bell,
  LogOut
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Organizations', href: '/dashboard/organizations', icon: Building2 },
  { name: 'Users', href: '/dashboard/users', icon: Users },
  { name: 'Notifications', href: '/dashboard/notifications', icon: Bell },
  { name: 'System Settings', href: '/dashboard/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  return (
    <div className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="h-20 flex items-center px-6 border-b border-gray-200">
        <Shield className="h-8 w-8 text-red-600 mr-3" />
        <div>
          <h1 className="text-xl font-black text-black">CyberXLTR</h1>
          <p className="text-xs font-bold text-red-600 tracking-wide">ADMIN PANEL</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? 'bg-red-50 text-red-700 font-bold'
                  : 'text-black font-semibold hover:bg-gray-50'
              }`}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* User Info & Logout */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex items-center mb-3">
          <div className="w-10 h-10 bg-red-600 rounded-full flex items-center justify-center mr-3">
            <Shield className="h-5 w-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold text-black truncate">
              {user?.full_name || user?.first_name || 'Admin'}
            </p>
            <p className="text-xs text-gray-600 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-lg transition-colors"
        >
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  )
}

