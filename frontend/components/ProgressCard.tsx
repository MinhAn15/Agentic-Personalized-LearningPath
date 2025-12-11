interface ProgressCardProps {
  title: string
  value: number
  maxValue: number
  unit: string
  icon: string
  color: 'primary' | 'accent' | 'green' | 'orange'
}

export default function ProgressCard({ title, value, maxValue, unit, icon, color }: ProgressCardProps) {
  const percentage = Math.round((value / maxValue) * 100)
  
  const colorClasses = {
    primary: 'from-primary-500 to-primary-600',
    accent: 'from-accent-500 to-accent-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
  }

  const bgColorClasses = {
    primary: 'bg-primary-500',
    accent: 'bg-accent-500',
    green: 'bg-green-500',
    orange: 'bg-orange-500',
  }

  return (
    <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700 hover:border-gray-600 transition-all duration-300">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">
            {value}<span className="text-lg text-gray-400">/{maxValue} {unit}</span>
          </p>
        </div>
        <div className={`w-12 h-12 bg-gradient-to-br ${colorClasses[color]} rounded-xl flex items-center justify-center`}>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${bgColorClasses[color]} rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-right text-gray-400 text-sm mt-2">{percentage}% complete</p>
    </div>
  )
}
