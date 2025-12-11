'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiClient } from '@/lib/api'

export default function UploadPage() {
  const router = useRouter()
  const [content, setContent] = useState('')
  const [courseId, setCourseId] = useState('')
  const [contentType, setContentType] = useState('text')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim() || !courseId.trim()) return

    setIsLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await apiClient.extractKnowledge(
        courseId,
        content,
        contentType
      ) as { concepts?: Array<{ name: string; type: string }>; error?: string };

      if (response.error) {
        setError(response.error)
      } else {
        setResult(response)
      }
    } catch (err) {
      setError('Failed to process content. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 py-12">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Link href="/dashboard" className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">
            ← Back to Dashboard
          </Link>
        </div>

        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
            📄 Upload Course Content
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Paste your course materials and let AI extract concepts and relationships
          </p>
        </div>

        {/* Upload Form */}
        <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-800 rounded-lg p-8 border border-slate-200 dark:border-slate-700">
          {/* Course ID */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-900 dark:text-white mb-2">
              Course Name / ID
            </label>
            <input
              type="text"
              value={courseId}
              onChange={(e) => setCourseId(e.target.value)}
              placeholder="e.g., SQL Fundamentals"
              className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* Content Type */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-900 dark:text-white mb-2">
              Content Type
            </label>
            <div className="grid grid-cols-3 gap-4">
              {[
                { value: 'text', label: '📝 Text', desc: 'Plain text content' },
                { value: 'markdown', label: '📋 Markdown', desc: 'Formatted text' },
                { value: 'pdf_text', label: '📄 PDF Text', desc: 'Extracted from PDF' },
              ].map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setContentType(type.value)}
                  className={`p-4 rounded-lg border-2 transition-all text-left ${
                    contentType === type.value
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500'
                  }`}
                >
                  <p className="text-lg mb-1 text-slate-900 dark:text-white">{type.label}</p>
                  <p className="text-xs text-slate-600 dark:text-slate-400">{type.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Content Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-900 dark:text-white mb-2">
              Course Content
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste your course content here...

Example:
SQL WHERE Clause

The WHERE clause is used to filter records.
It is used to extract only those records that fulfill a specified condition.

WHERE Syntax:
SELECT column1, column2, ...
FROM table_name
WHERE condition;

Prerequisites: SELECT statement, FROM clause
Related concepts: AND, OR, NOT operators"
              className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
              rows={15}
              required
            />
            <p className="text-slate-600 dark:text-slate-400 text-sm mt-2">
              {content.length} characters • {content.split(/\s+/).filter(Boolean).length} words
            </p>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading || !content.trim() || !courseId.trim()}
            className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Extracting Knowledge...
              </span>
            ) : (
              '🧠 Extract Concepts with AI →'
            )}
          </button>
        </form>

        {/* Error */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-8 bg-white dark:bg-slate-800 rounded-lg p-8 border border-slate-200 dark:border-slate-700">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              ✅ Knowledge Extracted!
            </h2>

            <div className="space-y-4">
              {/* Concepts */}
              <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <h3 className="text-slate-700 dark:text-slate-300 mb-2">Concepts Found:</h3>
                <div className="flex flex-wrap gap-2">
                  {(result.concepts || ['WHERE Clause', 'Filter', 'Condition']).map((concept: string, i: number) => (
                    <span key={i} className="px-3 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 rounded-full text-sm">
                      {concept}
                    </span>
                  ))}
                </div>
              </div>

              {/* Relationships */}
              <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <h3 className="text-slate-700 dark:text-slate-300 mb-2">Relationships:</h3>
                <div className="space-y-2">
                  {(result.relationships || [
                    { from: 'SELECT', to: 'WHERE', type: 'PREREQUISITE' },
                    { from: 'WHERE', to: 'AND/OR', type: 'LEADS_TO' },
                  ]).map((rel: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <span className="text-slate-900 dark:text-white">{rel.from}</span>
                      <span className="text-slate-400">→</span>
                      <span className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400 rounded text-xs">
                        {rel.type}
                      </span>
                      <span className="text-slate-400">→</span>
                      <span className="text-slate-900 dark:text-white">{rel.to}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-4 mt-6">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
                >
                  Go to Dashboard →
                </button>
                <button
                  onClick={() => {
                    setContent('')
                    setCourseId('')
                    setResult(null)
                  }}
                  className="px-6 py-3 border border-slate-300 dark:border-slate-600 text-slate-900 dark:text-white rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition"
                >
                  Upload More
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tips */}
        <div className="mt-8 p-6 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
          <h3 className="text-slate-900 dark:text-white font-semibold mb-3">💡 Tips for Best Results</h3>
          <ul className="space-y-2 text-slate-600 dark:text-slate-400 text-sm">
            <li>• Include clear concept definitions</li>
            <li>• Mention prerequisites explicitly (e.g., &quot;Requires knowledge of...&quot;)</li>
            <li>• Indicate difficulty level if possible</li>
            <li>• Include examples for complex concepts</li>
            <li>• Break down large topics into sections</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
