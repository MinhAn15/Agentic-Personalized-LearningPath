import Navigation from "@/components/Navigation";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-900">
      <Navigation />

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center space-y-6">
          <h1 className="text-5xl md:text-6xl font-bold text-slate-900 dark:text-white">
            Learn at Your Own Pace
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
            AI-powered personalized learning paths designed just for you.
            Learn faster, retain better, achieve more.
          </p>
          <div className="flex gap-4 justify-center pt-4">
            <Link
              href="/auth/signup"
              className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
            >
              Start Learning Today
            </Link>
            <Link
              href="#features"
              className="px-8 py-4 border border-slate-300 dark:border-slate-600 text-slate-900 dark:text-white rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition font-semibold"
            >
              Learn More
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-20 grid grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-4xl font-bold text-blue-600">92%</div>
            <p className="text-slate-600 dark:text-slate-400">Success Rate</p>
          </div>
          <div>
            <div className="text-4xl font-bold text-blue-600">10k+</div>
            <p className="text-slate-600 dark:text-slate-400">Learners</p>
          </div>
          <div>
            <div className="text-4xl font-bold text-blue-600">6</div>
            <p className="text-slate-600 dark:text-slate-400">AI Agents</p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-slate-50 dark:bg-slate-800 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center text-slate-900 dark:text-white mb-16">
            Why Choose PathAI?
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white dark:bg-slate-700 p-8 rounded-lg border border-slate-200 dark:border-slate-600">
              <div className="text-3xl mb-4">🎯</div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                Personalized Paths
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                AI-optimized learning sequences respect your pace and learning style.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white dark:bg-slate-700 p-8 rounded-lg border border-slate-200 dark:border-slate-600">
              <div className="text-3xl mb-4">🧑‍🏫</div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                Socratic Teaching
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                Learn through guided questions, not direct answers. Deeper understanding.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white dark:bg-slate-700 p-8 rounded-lg border border-slate-200 dark:border-slate-600">
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                Intelligent Assessment
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                Get personalized feedback that addresses YOUR misconceptions.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-white dark:bg-slate-700 p-8 rounded-lg border border-slate-200 dark:border-slate-600">
              <div className="text-3xl mb-4">📈</div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                Real Progress
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                Track mastery by concept. See your improvement over time.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="bg-white dark:bg-slate-700 p-8 rounded-lg border border-slate-200 dark:border-slate-600">
              <div className="text-3xl mb-4">🚀</div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                Fast Results
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                Science-based teaching methods accelerate learning.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="bg-white dark:bg-slate-700 p-8 rounded-lg border border-slate-200 dark:border-slate-600">
              <div className="text-3xl mb-4">🤖</div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                AI Powered
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                6 intelligent agents work together for your success.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-blue-600 text-white py-16">
        <div className="max-w-4xl mx-auto text-center px-4">
          <h2 className="text-4xl font-bold mb-6">Ready to Transform Your Learning?</h2>
          <p className="text-lg mb-8 opacity-90">
            Join thousands of learners already using AI-powered personalized paths.
          </p>
          <Link
            href="/auth/signup"
            className="inline-block px-8 py-4 bg-white text-blue-600 rounded-lg hover:bg-slate-100 transition font-semibold"
          >
            Start Free Today
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p>&copy; 2025 PathAI. Powered by AI. Built on Learning Science.</p>
        </div>
      </footer>
    </div>
  );
}
