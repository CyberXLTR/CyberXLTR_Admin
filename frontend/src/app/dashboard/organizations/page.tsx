'use client'

import { useState, useEffect } from 'react'
import { Building2, Plus, X, Loader2, RefreshCw, Search } from 'lucide-react'
import { toast } from 'sonner'
import api from '@/lib/api'

interface Organization {
  id: string
  name: string
  url: string
  subscription_tier: string
  is_active: boolean
  created_at: string
  billing_email?: string
  support_email?: string
  phone?: string
  company_address?: string
}

const subscriptionTiers = ['starter', 'professional', 'enterprise']

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [creating, setCreating] = useState(false)
  const [search, setSearch] = useState('')

  // Create form state
  const [form, setForm] = useState({
    name: '',
    url: '',
    subscription_tier: 'starter',
    billing_email: '',
    support_email: '',
    phone: '',
    company_address: '',
  })

  useEffect(() => {
    fetchOrganizations()
  }, [])

  const fetchOrganizations = async () => {
    try {
      const response = await api.get('/api/v1/organizations/')
      setOrganizations(response.data.organizations || [])
    } catch (error) {
      console.error('Failed to fetch organizations:', error)
      toast.error('Failed to fetch organizations')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    try {
      const response = await api.post('/api/v1/organizations/', form)
      if (response.data.success) {
        toast.success(`Organization "${form.name}" created successfully!`)
        setShowCreateModal(false)
        setForm({ name: '', url: '', subscription_tier: 'starter', billing_email: '', support_email: '', phone: '', company_address: '' })
        fetchOrganizations()
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail
      toast.error(typeof detail === 'string' ? detail : 'Failed to create organization')
    } finally {
      setCreating(false)
    }
  }

  const handleToggleStatus = async (org: Organization) => {
    try {
      if (org.is_active) {
        await api.delete(`/api/v1/organizations/${org.id}`)
        toast.success(`Organization "${org.name}" deactivated`)
      } else {
        await api.post(`/api/v1/organizations/${org.id}/reactivate`)
        toast.success(`Organization "${org.name}" reactivated`)
      }
      fetchOrganizations()
    } catch (error: any) {
      toast.error('Failed to update organization status')
    }
  }

  const filteredOrgs = organizations.filter(org =>
    org.name.toLowerCase().includes(search.toLowerCase()) ||
    org.url.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-black text-black flex items-center gap-3">
            <Building2 className="h-8 w-8 text-primary-600" />
            Organizations
          </h1>
          <p className="text-black font-bold mt-1">{organizations.length} total organizations</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchOrganizations}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RefreshCw className="h-5 w-5 text-gray-600" />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 gradient-blue text-white font-bold py-2 px-4 rounded-lg hover:opacity-90 transition-opacity shadow-blue"
          >
            <Plus className="h-5 w-5" />
            Add Organization
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search organizations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">URL</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Subscription</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Created</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredOrgs.map((org) => (
              <tr key={org.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
                      <Building2 className="h-4 w-4 text-primary-600" />
                    </div>
                    <div className="text-sm font-bold text-black">{org.name}</div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{org.url}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs font-semibold rounded-full bg-primary-100 text-primary-800">
                    {org.subscription_tier}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    org.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {org.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(org.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <button
                    onClick={() => handleToggleStatus(org)}
                    className={`text-xs font-semibold px-3 py-1 rounded-lg transition-colors ${
                      org.is_active
                        ? 'text-red-600 hover:bg-red-50'
                        : 'text-green-600 hover:bg-green-50'
                    }`}
                  >
                    {org.is_active ? 'Deactivate' : 'Reactivate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredOrgs.length === 0 && (
          <div className="text-center py-12">
            <Building2 className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 font-semibold">No organizations found</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 text-primary-600 font-semibold hover:underline"
            >
              Create your first organization
            </button>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-black">Create Organization</h2>
              <button onClick={() => setShowCreateModal(false)} className="p-1 hover:bg-gray-100 rounded-lg">
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-semibold text-black mb-1">Organization Name *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Acme Corp"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-black mb-1">URL *</label>
                <input
                  type="text"
                  value={form.url}
                  onChange={(e) => setForm(prev => ({ ...prev, url: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="acme-corp"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Unique identifier for the organization</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-black mb-1">Subscription Tier</label>
                <select
                  value={form.subscription_tier}
                  onChange={(e) => setForm(prev => ({ ...prev, subscription_tier: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {subscriptionTiers.map(tier => (
                    <option key={tier} value={tier}>{tier.charAt(0).toUpperCase() + tier.slice(1)}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-black mb-1">Billing Email</label>
                  <input
                    type="email"
                    value={form.billing_email}
                    onChange={(e) => setForm(prev => ({ ...prev, billing_email: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="billing@acme.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-black mb-1">Support Email</label>
                  <input
                    type="email"
                    value={form.support_email}
                    onChange={(e) => setForm(prev => ({ ...prev, support_email: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="support@acme.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-black mb-1">Phone</label>
                <input
                  type="tel"
                  value={form.phone}
                  onChange={(e) => setForm(prev => ({ ...prev, phone: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="+1234567890"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-black mb-1">Company Address</label>
                <input
                  type="text"
                  value={form.company_address}
                  onChange={(e) => setForm(prev => ({ ...prev, company_address: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="123 Main St, City, Country"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 gradient-blue text-white font-semibold py-2 px-4 rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 shadow-blue"
                >
                  {creating ? 'Creating...' : 'Create Organization'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
