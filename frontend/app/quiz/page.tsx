'use client'

import { useState } from 'react'
import { useEvaluator } from '@/hooks/useApi'
import Link from 'next/link'

interface Question {
  id: string
  conceptId: string
  question: string
  expectedAnswer: string
  explanation: string
}

const sampleQuestions: Question[] = [
  {
    id: '1',
    conceptId: 'SQL_WHERE',
    question: 'What does the WHERE clause do in SQL?',
    expectedAnswer: 'WHERE filters rows based on specified conditions',
    explanation: 'WHERE is used to filter records that meet certain conditions before they are returned.',
  },
  {
    id: '2',
    conceptId: 'SQL_SELECT',
    question: 'How do you select all columns from a table?',
    expectedAnswer: 'SELECT * FROM table_name',
    explanation: 'The asterisk (*) is a wildcard that selects all columns.',
  },
  {
    id: '3',
    conceptId: 'SQL_JOIN',
    question: 'What is the purpose of JOIN in SQL?',
    expectedAnswer: 'JOIN combines rows from two or more tables based on a related column',
    explanation: 'JOIN is used to combine data from multiple tables using common columns.',
  },
]

export default function QuizPage() {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answer, setAnswer] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [results, setResults] = useState<Array<{
    question: Question
    answer: string
    score: number
    errorType: string
    feedback: string
  }>>([])
  const [quizComplete, setQuizComplete] = useState(false)

  const { result, isLoading, error, evaluate } = useEvaluator()

  const question = sampleQuestions[currentQuestion]

  const handleSubmit = async () => {
    if (!answer.trim() || isLoading) return

    const learnerId = localStorage.getItem('learner_id') || 'demo_user'

    const evalResult = await evaluate(
      learnerId,
      question.conceptId,
      answer,
      question.expectedAnswer,
      question.explanation
    )

    if (evalResult) {
      setResults(prev => [...prev, {
        question,
        answer,
        score: evalResult.score,
        errorType: evalResult.error_type,
        feedback: evalResult.feedback,
      }])
      setSubmitted(true)
    }
  }

  const handleNext = () => {
    if (currentQuestion < sampleQuestions.length - 1) {
      setCurrentQuestion(prev => prev + 1)
      setAnswer('')
      setSubmitted(false)
    } else {
      setQuizComplete(true)
    }
  }

  const calculateTotalScore = () => {
    if (results.length === 0) return 0
    const total = results.reduce((sum, r) => sum + r.score, 0)
    return Math.round((total / results.length) * 100)
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400'
    if (score >= 0.5) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getErrorTypeColor = (type: string) => {
    switch (type) {
      case 'CORRECT': return 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400'
      case 'CARELESS': return 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400'
      case 'INCOMPLETE': return 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400'
      case 'PROCEDURAL': return 'bg-orange-100 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400'
      case 'CONCEPTUAL': return 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400'
      default: return 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
    }
  }

  if (quizComplete) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 py-12">
        <div className="max-w-3xl mx-auto px-4">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">Quiz Complete! 🎉</h1>
            <div className="text-6xl font-bold text-blue-600 mb-2">
              {calculateTotalScore()}%
            </div>
            <p className="text-slate-600 dark:text-slate-400">Your Score</p>
          </div>

          {/* Results Summary */}
          <div className="space-y-4 mb-8">
            {results.map((r, index) => (
              <div key={index} className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                <div className="flex items-start justify-between mb-2">
                  <p className="text-slate-900 dark:text-white font-medium">Q{index + 1}: {r.question.question}</p>
                  <span className={`px-2 py-1 rounded text-xs ${getErrorTypeColor(r.errorType)}`}>
                    {r.errorType}
                  </span>
                </div>
                <p className="text-slate-600 dark:text-slate-400 text-sm mb-2">Your answer: {r.answer}</p>
                <p className="text-slate-700 dark:text-slate-300 text-sm">{r.feedback}</p>
                <div className="mt-2">
                  <span className={`text-lg font-bold ${getScoreColor(r.score)}`}>
                    {Math.round(r.score * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-4 justify-center">
            <Link 
              href="/dashboard" 
              className="px-6 py-3 border border-slate-300 dark:border-slate-600 text-slate-900 dark:text-white rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition"
            >
              ← Back to Dashboard
            </Link>
            <button
              onClick={() => {
                setCurrentQuestion(0)
                setAnswer('')
                setSubmitted(false)
                setResults([])
                setQuizComplete(false)
              }}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Retry Quiz
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 py-12">
      <div className="max-w-3xl mx-auto px-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Link href="/dashboard" className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">
            ← Back to Dashboard
          </Link>
        </div>

        {/* Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-600 dark:text-slate-400">
              Question {currentQuestion + 1} of {sampleQuestions.length}
            </span>
            <span className="text-slate-600 dark:text-slate-400">
              {question.conceptId}
            </span>
          </div>
          <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-300"
              style={{ width: `${((currentQuestion + 1) / sampleQuestions.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Question Card */}
        <div className="bg-white dark:bg-slate-800 rounded-lg p-8 border border-slate-200 dark:border-slate-700 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-3xl">❓</span>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{question.question}</h2>
          </div>

          {!submitted ? (
            <>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Type your answer here..."
                className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none mt-4"
                rows={4}
              />

              <button
                onClick={handleSubmit}
                disabled={!answer.trim() || isLoading}
                className="w-full mt-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
              >
                {isLoading ? 'Evaluating...' : 'Submit Answer'}
              </button>
            </>
          ) : result && (
            <div className="mt-6 space-y-4">
              {/* Score */}
              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <span className="text-slate-700 dark:text-slate-300">Your Score</span>
                <span className={`text-3xl font-bold ${getScoreColor(result.score)}`}>
                  {Math.round(result.score * 100)}%
                </span>
              </div>

              {/* Error Type */}
              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <span className="text-slate-700 dark:text-slate-300">Classification</span>
                <span className={`px-3 py-1 rounded-lg ${getErrorTypeColor(result.error_type)}`}>
                  {result.error_type}
                </span>
              </div>

              {/* Feedback */}
              <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <p className="text-slate-700 dark:text-slate-300 mb-2">Feedback:</p>
                <p className="text-slate-900 dark:text-white">{result.feedback}</p>
              </div>

              {/* Misconception */}
              {result.misconception && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-red-700 dark:text-red-300 mb-1">⚠️ Misconception Detected:</p>
                  <p className="text-slate-900 dark:text-white">{result.misconception}</p>
                </div>
              )}

              {/* Expected Answer */}
              <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <p className="text-green-700 dark:text-green-300 mb-1">✅ Expected Answer:</p>
                <p className="text-slate-900 dark:text-white">{question.expectedAnswer}</p>
              </div>

              <button 
                onClick={handleNext} 
                className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
              >
                {currentQuestion < sampleQuestions.length - 1 ? 'Next Question →' : 'View Results'}
              </button>
            </div>
          )}

          {error && (
            <p className="text-red-600 dark:text-red-400 text-sm mt-4">{error}</p>
          )}
        </div>
      </div>
    </div>
  )
}
