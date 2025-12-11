"use client";

interface HintButtonsProps {
  hintLevel: number;
  onIncrease: () => void;
  onDecrease: () => void;
}

export default function HintButtons({
  hintLevel,
  onIncrease,
  onDecrease,
}: HintButtonsProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
      <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
        Need more guidance? Adjust the hint level:
      </p>
      <div className="flex gap-2">
        <button
          onClick={onDecrease}
          disabled={hintLevel === 0}
          className="px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ← Less Help
        </button>
        <div className="flex-1 flex items-center justify-center">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Level {hintLevel}/5
          </span>
        </div>
        <button
          onClick={onIncrease}
          disabled={hintLevel === 5}
          className="px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          More Help →
        </button>
      </div>
    </div>
  );
}
