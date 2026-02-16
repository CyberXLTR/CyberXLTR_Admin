'use client'

import { Shield } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div>
      <h1 className="text-3xl font-black text-black flex items-center gap-3 mb-6">
        <Shield className="h-8 w-8 text-gray-600" />
        System Settings
      </h1>

      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">System settings configuration will be available here.</p>
      </div>
    </div>
  )
}

