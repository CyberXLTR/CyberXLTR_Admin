import { LucideIcon } from 'lucide-react'

type StatsCardProps = {
  title: string
  value: string
  change: string
  icon: LucideIcon
  color: string
}

const colorVariants: Record<string, string> = {
  blue: 'bg-blue-100 text-blue-600',
  green: 'bg-green-100 text-green-600',
  purple: 'bg-purple-100 text-purple-600',
  orange: 'bg-orange-100 text-orange-600',
}

export function StatsCard({ title, value, change, icon: Icon, color }: StatsCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorVariants[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
        <span className="text-sm font-bold text-green-600">{change}</span>
      </div>
      <h3 className="text-black text-sm font-bold mb-1">{title}</h3>
      <p className="text-3xl font-black text-black">{value}</p>
    </div>
  )
}

