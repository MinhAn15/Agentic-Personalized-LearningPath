"use client";

interface FeedbackCardProps {
  score: number;
  feedback: string;
  misconception?: string;
}

export default function FeedbackCard({
  score,
  feedback,
  misconception,
}: FeedbackCardProps) {
  const isCorrect = score >= 0.8;

  return (
    <div
      className={`rounded-lg border p-6 ${
        isCorrect
          ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
          : "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
      }`}
    >
      {/* Score */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-slate-900 dark:text-white">
          {isCorrect ? "✅ Great Job!" : "📊 Let's Learn More"}
        </h2>
        <span
          className={`text-2xl font-bold ${
            isCorrect
              ? "text-green-600 dark:text-green-400"
              : "text-blue-600 dark:text-blue-400"
          }`}
        >
          {(score * 100).toFixed(0)}%
        </span>
      </div>

      {/* Misconception */}
      {misconception && (
        <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded">
          <p className="text-sm text-yellow-800 dark:text-yellow-300">
            <strong>Insight:</strong> {misconception}
          </p>
        </div>
      )}

      {/* Feedback */}
      <div className="mb-4">
        <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
          {feedback}
        </p>
      </div>
    </div>
  );
}
