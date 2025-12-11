"use client";

interface QuestionFormProps {
  question: string;
  answer: string;
  onAnswerChange: (answer: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

export default function QuestionForm({
  question,
  answer,
  onAnswerChange,
  onSubmit,
  loading,
}: QuestionFormProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
      <h2 className="font-semibold text-slate-900 dark:text-white mb-4">
        🤔 Your Turn
      </h2>
      
      <div className="mb-4">
        <label className="block text-slate-700 dark:text-slate-300 font-medium mb-2">
          {question}
        </label>
        <textarea
          value={answer}
          onChange={(e) => onAnswerChange(e.target.value)}
          placeholder="Type your answer here... Think before you answer!"
          className="w-full h-24 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        />
      </div>

      <button
        onClick={onSubmit}
        disabled={loading || !answer.trim()}
        className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Evaluating..." : "Submit Answer"}
      </button>

      <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 text-center">
        Take your time. There&apos;s no rush. Think deeply!
      </p>
    </div>
  );
}
