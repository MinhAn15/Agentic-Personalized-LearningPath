interface FeatureCardProps {
  icon: string
  title: string
  description: string
  gradient: string
}

export default function FeatureCard({ icon, title, description, gradient }: FeatureCardProps) {
  return (
    <div className="group relative p-6 bg-gray-800/50 rounded-2xl border border-gray-700/50 hover:border-primary-500/50 transition-all duration-300 hover:transform hover:scale-105">
      {/* Gradient overlay on hover */}
      <div className={`absolute inset-0 ${gradient} opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity duration-300`} />
      
      {/* Icon */}
      <div className="relative z-10">
        <div className="w-14 h-14 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center mb-4 group-hover:animate-glow">
          <span className="text-2xl">{icon}</span>
        </div>
        
        {/* Title */}
        <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
        
        {/* Description */}
        <p className="text-gray-400 leading-relaxed">{description}</p>
      </div>
    </div>
  )
}

export function FeaturesSection() {
  const features = [
    {
      icon: '📚',
      title: 'Knowledge Extraction',
      description: 'AI automatically extracts concepts and relationships from your course materials.',
      gradient: 'bg-gradient-to-br from-blue-500 to-cyan-500',
    },
    {
      icon: '👤',
      title: 'Learner Profiling',
      description: 'Understand your learning style, goals, and current knowledge level.',
      gradient: 'bg-gradient-to-br from-purple-500 to-pink-500',
    },
    {
      icon: '🗺️',
      title: 'RL Path Planning',
      description: 'Reinforcement Learning optimizes your learning sequence in real-time.',
      gradient: 'bg-gradient-to-br from-green-500 to-emerald-500',
    },
    {
      icon: '🧑‍🏫',
      title: 'Socratic Tutoring',
      description: 'Harvard 7 principles guide you to discover answers yourself.',
      gradient: 'bg-gradient-to-br from-orange-500 to-red-500',
    },
    {
      icon: '📊',
      title: 'Smart Assessment',
      description: 'Error classification and personalized feedback for every response.',
      gradient: 'bg-gradient-to-br from-indigo-500 to-purple-500',
    },
    {
      icon: '📈',
      title: 'Pattern Analysis',
      description: 'System-wide insights improve course content continuously.',
      gradient: 'bg-gradient-to-br from-pink-500 to-rose-500',
    },
  ]

  return (
    <section id="features" className="py-20 bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="gradient-text">6 AI Agents</span> Working For You
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            A multi-agent system that orchestrates your entire learning journey
          </p>
        </div>

        {/* Features grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div key={index} className="animate-fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
              <FeatureCard {...feature} />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
