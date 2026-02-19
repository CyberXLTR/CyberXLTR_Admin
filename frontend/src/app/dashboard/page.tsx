'use client'

import { useState, useEffect } from 'react'
import { Building2, Users, Bell, RefreshCw, Loader2, Shield } from 'lucide-react'
import { StatsCard } from '@/components/StatsCard'
import Link from 'next/link'
import api from '@/lib/api'

interface Stats {
  totalOrganizations: number
  totalUsers: number
  activeNotifications: number
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({
    totalOrganizations: 0,
    totalUsers: 0,
    activeNotifications: 0,
  })
  const [isLoading, setIsLoading] = useState(true)

  const fetchStats = async () => {
    try {
      const [orgsRes, usersRes, notifsRes] = await Promise.allSettled([
        api.get('/api/v1/organizations/'),
        api.get('/api/v1/users/'),
        api.get('/api/v1/notifications/'),
      ])

      setStats({
        totalOrganizations: orgsRes.status === 'fulfilled' ? (orgsRes.value.data.total || orgsRes.value.data.organizations?.length || 0) : 0,
        totalUsers: usersRes.status === 'fulfilled' ? (usersRes.value.data.total || usersRes.value.data.users?.length || 0) : 0,
        activeNotifications: notifsRes.status === 'fulfilled' ? (notifsRes.value.data.notifications?.filter((n: any) => n.is_active).length || 0) : 0,
      })
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  const statCards = [
    {
      title: 'Organizations',
      value: stats.totalOrganizations.toString(),
      change: stats.totalOrganizations > 0 ? 'Active' : 'No data',
      icon: Building2,
      color: 'blue' as const,
    },
    {
      title: 'Users',
      value: stats.totalUsers.toString(),
      change: stats.totalUsers > 0 ? 'Registered' : 'No users',
      icon: Users,
      color: 'green' as const,
    },
    {
      title: 'Active Notifications',
      value: stats.activeNotifications.toString(),
      change: stats.activeNotifications > 0 ? 'Active' : 'None',
      icon: Bell,
      color: 'orange' as const,
    },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black text-black">Admin Dashboard</h1>
          <p className="text-black font-bold mt-1">System administration and management</p>
        </div>
        <button
          onClick={fetchStats}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Refresh data"
        >
          <RefreshCw className="h-5 w-5 text-gray-600" />
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {statCards.map((stat) => (
          <StatsCard key={stat.title} {...stat} />
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <h2 className="text-xl font-bold text-black mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Link
              href="/dashboard/organizations"
              className="flex items-center gap-3 p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all"
            >
              <div className="p-2 bg-primary-100 rounded-lg">
                <Building2 className="h-4 w-4 text-primary-600" />
              </div>
              <div>
                <p className="font-bold text-black text-sm">Manage Organizations</p>
                <p className="text-xs font-semibold text-gray-700">View & create organizations</p>
              </div>
            </Link>
            <Link
              href="/dashboard/users"
              className="flex items-center gap-3 p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all"
            >
              <div className="p-2 bg-green-100 rounded-lg">
                <Users className="h-4 w-4 text-green-600" />
              </div>
              <div>
                <p className="font-bold text-black text-sm">Manage Users</p>
                <p className="text-xs font-semibold text-gray-700">Add & manage users</p>
              </div>
            </Link>
            <Link
              href="/dashboard/notifications"
              className="flex items-center gap-3 p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all"
            >
              <div className="p-2 bg-orange-100 rounded-lg">
                <Bell className="h-4 w-4 text-orange-600" />
              </div>
              <div>
                <p className="font-bold text-black text-sm">Notifications</p>
                <p className="text-xs font-semibold text-gray-700">Create system notifications</p>
              </div>
            </Link>
            <Link
              href="/dashboard/settings"
              className="flex items-center gap-3 p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all"
            >
              <div className="p-2 bg-gray-100 rounded-lg">
                <Shield className="h-4 w-4 text-gray-600" />
              </div>
              <div>
                <p className="font-bold text-black text-sm">Profile & Settings</p>
                <p className="text-xs font-semibold text-gray-700">Configure system parameters</p>
              </div>
            </Link>
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <h2 className="text-xl font-bold text-black mb-4">System Status</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-100">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="font-semibold text-black text-sm">Admin Backend</span>
              </div>
              <span className="text-xs font-bold text-green-600">Operational</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-100">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="font-semibold text-black text-sm">CyberXLTR Backend</span>
              </div>
              <span className="text-xs font-bold text-green-600">Operational</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-100">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="font-semibold text-black text-sm">Database Sync</span>
              </div>
              <span className="text-xs font-bold text-green-600">Connected</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
