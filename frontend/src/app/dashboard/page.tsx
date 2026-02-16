'use client'

import { useState, useEffect } from 'react'
import { Shield, Building2, Users, Bell } from 'lucide-react'
import api from '@/lib/api'

interface Stats {
  totalOrganizations: number
  totalUsers: number
  activeNotifications: number
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Fetch basic stats (you can expand this based on your needs)
        setStats({
          totalOrganizations: 0,
          totalUsers: 0,
          activeNotifications: 0,
        })
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-red-200 border-t-red-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-black font-bold">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <div className="mb-8">
        <h1 className="text-3xl font-black text-black flex items-center gap-3">
          <Shield className="h-8 w-8 text-red-600" />
          Admin Dashboard
        </h1>
        <p className="mt-2 text-black font-bold">
          System administration and management
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-bold text-gray-600 uppercase tracking-wide">Organizations</p>
              <p className="text-3xl font-black text-black">{stats?.totalOrganizations || 0}</p>
            </div>
            <Building2 className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-bold text-gray-600 uppercase tracking-wide">Users</p>
              <p className="text-3xl font-black text-black">{stats?.totalUsers || 0}</p>
            </div>
            <Users className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-bold text-gray-600 uppercase tracking-wide">Active Notifications</p>
              <p className="text-3xl font-black text-black">{stats?.activeNotifications || 0}</p>
            </div>
            <Bell className="h-8 w-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-black mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a
            href="/dashboard/organizations"
            className="flex items-center gap-3 p-4 bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200 transition-colors"
          >
            <Building2 className="h-6 w-6 text-blue-600" />
            <div>
              <p className="font-bold text-blue-800">Manage Organizations</p>
              <p className="text-sm text-blue-600">View and manage all organizations</p>
            </div>
          </a>

          <a
            href="/dashboard/users"
            className="flex items-center gap-3 p-4 bg-green-50 hover:bg-green-100 rounded-lg border border-green-200 transition-colors"
          >
            <Users className="h-6 w-6 text-green-600" />
            <div>
              <p className="font-bold text-green-800">Manage Users</p>
              <p className="text-sm text-green-600">View and manage all users</p>
            </div>
          </a>

          <a
            href="/dashboard/notifications"
            className="flex items-center gap-3 p-4 bg-orange-50 hover:bg-orange-100 rounded-lg border border-orange-200 transition-colors"
          >
            <Bell className="h-6 w-6 text-orange-600" />
            <div>
              <p className="font-bold text-orange-800">Manage Notifications</p>
              <p className="text-sm text-orange-600">Create and manage system notifications</p>
            </div>
          </a>

          <a
            href="/dashboard/settings"
            className="flex items-center gap-3 p-4 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors"
          >
            <Shield className="h-6 w-6 text-gray-600" />
            <div>
              <p className="font-bold text-gray-800">System Settings</p>
              <p className="text-sm text-gray-600">Configure system parameters</p>
            </div>
          </a>
        </div>
      </div>
    </div>
  )
}

