"use client";

interface TutorMessageProps {
  guidance: string;
  hintLevel: number;
}

export default function TutorMessage({ guidance, hintLevel }: TutorMessageProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
      <div className="flex items-start gap-4">
        {/* Tutor Avatar */}
        <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
          <span className="text-2xl">🧑‍🏫</span>
        </div>

        {/* Message */}
        <div className="flex-1">
          <h2 className="font-semibold text-slate-900 dark:text-white mb-3">
            Tutor&apos;s Guidance
          </h2>
          <div className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
            {guidance}
          </div>
          <div className="mt-4 text-sm text-slate-600 dark:text-slate-400">
            Hint Level: {hintLevel}/5
            {hintLevel === 0 && " (Productive struggle - you've got this!)"}
            {hintLevel === 1 && " (Gentle guidance)"}
            {hintLevel === 2 && " (Clarifying questions)"}
            {hintLevel === 3 && " (Partial example)"}
            {hintLevel === 4 && " (Full explanation)"}
            {hintLevel === 5 && " (Direct answer)"}
          </div>
        </div>
      </div>
    </div>
  );
}
