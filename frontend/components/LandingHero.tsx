import Link from 'next/link'

export default function LandingHero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-primary-900/20 to-gray-900" />
      
      {/* Animated orbs */}
      <div className="absolute top-20 left-20 w-72 h-72 bg-primary-500/30 rounded-full blur-3xl animate-float" />
      <div className="absolute bottom-20 right-20 w-96 h-96 bg-accent-500/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
      
      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="animate-slide-up">
          {/* Badge */}
          <div className="inline-flex items-center px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-full mb-8">
            <span className="text-primary-400 text-sm font-medium">
              🚀 Powered by 6 AI Agents
            </span>
          </div>
          
          {/* Main heading */}
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            Learn Smarter with
            <span className="block gradient-text">AI-Powered Tutoring</span>
          </h1>
          
          {/* Subheading */}
          <p className="text-xl md:text-2xl text-gray-400 max-w-3xl mx-auto mb-10">
            Personalized learning paths that adapt to YOU. Experience Socratic tutoring, 
            intelligent assessments, and knowledge graph-based recommendations.
          </p>
          
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/signup" className="btn-primary text-lg px-8 py-4">
              Start Learning Free →
            </Link>
            <Link href="#how-it-works" className="btn-secondary text-lg px-8 py-4">
              See How It Works
            </Link>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-3 gap-8 max-w-2xl mx-auto mt-16">
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-primary-400">6</div>
              <div className="text-gray-400 text-sm">AI Agents</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-accent-400">7</div>
              <div className="text-gray-400 text-sm">Harvard Principles</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-green-400">∞</div>
              <div className="text-gray-400 text-sm">Personalization</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
