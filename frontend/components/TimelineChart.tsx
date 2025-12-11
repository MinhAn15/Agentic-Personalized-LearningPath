"use client";

interface TimelineItem {
  day: string;
  label: string;
  status: "completed" | "current" | "upcoming";
  date?: string;
}

interface TimelineChartProps {
  items: TimelineItem[];
  daysRemaining: number;
  goalDate: string;
}

export default function TimelineChart({ items, daysRemaining, goalDate }: TimelineChartProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          Learning Timeline
        </h3>
        <div className="text-right">
          <p className="text-sm text-slate-600 dark:text-slate-400">Goal: {goalDate}</p>
          <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
            {daysRemaining} days left
          </p>
        </div>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-slate-200 dark:bg-slate-600"></div>

        <div className="space-y-4">
          {items.map((item, index) => (
            <div key={index} className="flex items-start gap-4 pl-4">
              {/* Dot */}
              <div
                className={`w-4 h-4 rounded-full -ml-6 flex-shrink-0 mt-1 ${
                  item.status === "completed"
                    ? "bg-green-500"
                    : item.status === "current"
                    ? "bg-blue-500 ring-4 ring-blue-200 dark:ring-blue-800"
                    : "bg-slate-300 dark:bg-slate-600"
                }`}
              />

              {/* Content */}
              <div
                className={`flex-1 p-3 rounded-lg ${
                  item.status === "current"
                    ? "bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800"
                    : "bg-slate-50 dark:bg-slate-700"
                }`}
              >
                <div className="flex justify-between items-center">
                  <p className="font-medium text-slate-900 dark:text-white">{item.day}</p>
                  {item.status === "completed" && (
                    <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2 py-0.5 rounded">
                      ✓ Done
                    </span>
                  )}
                  {item.status === "current" && (
                    <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-2 py-0.5 rounded">
                      In Progress
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{item.label}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-700">
        <div className="flex justify-between text-sm text-slate-600 dark:text-slate-400 mb-2">
          <span>Overall Progress</span>
          <span>
            {items.filter((i) => i.status === "completed").length}/{items.length} phases
          </span>
        </div>
        <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all duration-500"
            style={{
              width: `${(items.filter((i) => i.status === "completed").length / items.length) * 100}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
}
