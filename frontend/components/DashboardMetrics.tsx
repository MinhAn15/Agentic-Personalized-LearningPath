interface MetricCardProps {
  title: string
  value: string
  change?: string
  changeType?: 'positive' | 'negative' | 'neutral'
  icon: string
}

export function MetricCard({ title, value, change, changeType = 'neutral', icon }: MetricCardProps) {
  const changeColors = {
    positive: 'text-green-400',
    negative: 'text-red-400',
    neutral: 'text-gray-400',
  }

  return (
    <div className="bg-gray-800/50 rounded-xl p-5 border border-gray-700">
      <div className="flex items-center justify-between">
        <span className="text-2xl">{icon}</span>
        {change && (
          <span className={`text-sm ${changeColors[changeType]}`}>
            {changeType === 'positive' && '↑'}
            {changeType === 'negative' && '↓'}
            {change}
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-white mt-3">{value}</p>
      <p className="text-gray-400 text-sm">{title}</p>
    </div>
  )
}

export function DashboardMetrics() {
  const metrics = [
    { title: 'Concepts Mastered', value: '12', change: '+3 this week', changeType: 'positive' as const, icon: '🎯' },
    { title: 'Study Streak', value: '7 days', change: '+2 days', changeType: 'positive' as const, icon: '🔥' },
    { title: 'Time Studied', value: '24h', change: 'This month', changeType: 'neutral' as const, icon: '⏱️' },
    { title: 'Quiz Accuracy', value: '85%', change: '+5%', changeType: 'positive' as const, icon: '📊' },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, index) => (
        <MetricCard key={index} {...metric} />
      ))}
    </div>
  )
}
