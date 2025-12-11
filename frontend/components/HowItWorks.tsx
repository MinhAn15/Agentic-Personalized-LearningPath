export default function HowItWorks() {
  const steps = [
    {
      number: '01',
      title: 'Upload Your Course',
      description: 'Upload PDFs, documents, or paste text. Our Knowledge Extraction Agent builds a concept graph.',
      icon: '📄',
    },
    {
      number: '02',
      title: 'Tell Us About You',
      description: 'Share your goals, timeline, and learning preferences. The Profiler Agent creates your profile.',
      icon: '🎯',
    },
    {
      number: '03',
      title: 'Get Your Path',
      description: 'Path Planner uses RL to create your optimal learning sequence, respecting prerequisites.',
      icon: '🛤️',
    },
    {
      number: '04',
      title: 'Learn with Socratic Tutor',
      description: 'Ask questions and get guided to answers through the Socratic method - no direct answers!',
      icon: '💬',
    },
    {
      number: '05',
      title: 'Practice & Evaluate',
      description: 'Answer questions, get scored, and receive personalized feedback on your understanding.',
      icon: '✏️',
    },
    {
      number: '06',
      title: 'Track & Improve',
      description: 'Watch your mastery grow. The system adapts in real-time based on your performance.',
      icon: '📈',
    },
  ]

  return (
    <section id="how-it-works" className="py-20 bg-gray-800/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            How It <span className="gradient-text">Works</span>
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            From course upload to mastery in 6 simple steps
          </p>
        </div>

        {/* Steps */}
        <div className="relative">
          {/* Connecting line */}
          <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary-500 via-accent-500 to-primary-500" />
          
          <div className="space-y-12">
            {steps.map((step, index) => (
              <div
                key={index}
                className={`flex items-center gap-8 ${
                  index % 2 === 0 ? 'lg:flex-row' : 'lg:flex-row-reverse'
                }`}
              >
                {/* Content */}
                <div className={`flex-1 ${index % 2 === 0 ? 'lg:text-right' : 'lg:text-left'}`}>
                  <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700 hover:border-primary-500/50 transition-all duration-300">
                    <div className="flex items-center gap-4 mb-4">
                      <span className="text-4xl">{step.icon}</span>
                      <div>
                        <span className="text-primary-400 font-mono text-sm">Step {step.number}</span>
                        <h3 className="text-xl font-semibold text-white">{step.title}</h3>
                      </div>
                    </div>
                    <p className="text-gray-400">{step.description}</p>
                  </div>
                </div>

                {/* Center dot */}
                <div className="hidden lg:flex items-center justify-center w-12 h-12 bg-gradient-to-br from-primary-500 to-accent-500 rounded-full text-white font-bold z-10">
                  {step.number}
                </div>

                {/* Spacer */}
                <div className="hidden lg:block flex-1" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
