'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import Image from 'next/image'
import {
  LayoutDashboard,
  Settings,
  Shield,
  Building2,
  Users,
  Bell,
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Organizations', href: '/dashboard/organizations', icon: Building2 },
  { name: 'Users', href: '/dashboard/users', icon: Users },
  { name: 'Notifications', href: '/dashboard/notifications', icon: Bell },
  { name: 'System Settings', href: '/dashboard/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200">
      {/* Logo */}
      <div className="h-32 flex flex-col justify-center px-6 border-b border-gray-200">
        <Image
          src="/logo.png"
          alt="CyberXLTR"
          width={180}
          height={60}
          className="h-20 w-auto"
        />
        <div className="flex items-center gap-2 mt-2">
          <Shield className="h-4 w-4 text-primary-600" />
          <p className="text-sm font-bold text-primary-600 tracking-wide">
            Admin Panel
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? 'bg-primary-50 text-primary-700 font-bold'
                  : 'text-black font-semibold hover:bg-gray-50'
              }`}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}
