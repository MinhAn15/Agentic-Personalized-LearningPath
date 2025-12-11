interface LearningPathCardProps {
  concept: {
    id: string
    name: string
    mastery: number
    status: 'completed' | 'in_progress' | 'locked'
    estimatedHours: number
  }
  onClick?: () => void
}

export default function LearningPathCard({ concept, onClick }: LearningPathCardProps) {
  const statusColors = {
    completed: 'border-green-500 bg-green-500/10',
    in_progress: 'border-primary-500 bg-primary-500/10',
    locked: 'border-gray-600 bg-gray-800/50 opacity-60',
  }

  const statusIcons = {
    completed: '✅',
    in_progress: '📖',
    locked: '🔒',
  }

  return (
    <button
      onClick={onClick}
      disabled={concept.status === 'locked'}
      className={`w-full text-left p-4 rounded-xl border-2 ${statusColors[concept.status]} transition-all duration-300 hover:scale-102 disabled:cursor-not-allowed`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{statusIcons[concept.status]}</span>
          <div>
            <h3 className="font-semibold text-white">{concept.name}</h3>
            <p className="text-sm text-gray-400">{concept.estimatedHours}h estimated</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold text-white">{concept.mastery}%</p>
          <p className="text-xs text-gray-400">mastery</p>
        </div>
      </div>
      
      {/* Progress bar */}
      {concept.status !== 'locked' && (
        <div className="mt-3 w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full ${concept.status === 'completed' ? 'bg-green-500' : 'bg-primary-500'}`}
            style={{ width: `${concept.mastery}%` }}
          />
        </div>
      )}
    </button>
  )
}

export function LearningPathList() {
  const concepts = [
    { id: '1', name: 'Introduction to SQL', mastery: 100, status: 'completed' as const, estimatedHours: 2 },
    { id: '2', name: 'SELECT Statements', mastery: 100, status: 'completed' as const, estimatedHours: 3 },
    { id: '3', name: 'WHERE Clause', mastery: 75, status: 'in_progress' as const, estimatedHours: 4 },
    { id: '4', name: 'JOIN Operations', mastery: 0, status: 'locked' as const, estimatedHours: 5 },
    { id: '5', name: 'Aggregation Functions', mastery: 0, status: 'locked' as const, estimatedHours: 4 },
    { id: '6', name: 'Subqueries', mastery: 0, status: 'locked' as const, estimatedHours: 6 },
  ]

  return (
    <div className="space-y-3">
      {concepts.map((concept) => (
        <LearningPathCard key={concept.id} concept={concept} />
      ))}
    </div>
  )
}
