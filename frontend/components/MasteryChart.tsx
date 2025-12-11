"use client";

interface MasteryDataItem {
  concept: string;
  mastery: number;
  difficulty: number;
}

interface MasteryChartProps {
  data: MasteryDataItem[];
}

export default function MasteryChart({ data }: MasteryChartProps) {
  const getBarColor = (mastery: number) => {
    if (mastery >= 80) return "bg-green-500";
    if (mastery >= 50) return "bg-yellow-500";
    if (mastery > 0) return "bg-blue-500";
    return "bg-slate-300 dark:bg-slate-600";
  };

  const maxMastery = Math.max(...data.map((d) => d.mastery), 100);

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
        Mastery by Concept
      </h3>

      {/* Horizontal Bar Chart */}
      <div className="space-y-3">
        {data.map((item) => (
          <div key={item.concept} className="flex items-center gap-3">
            <div className="w-24 text-sm font-medium text-slate-700 dark:text-slate-300 truncate">
              {item.concept}
            </div>
            <div className="flex-1 h-6 bg-slate-200 dark:bg-slate-700 rounded overflow-hidden relative">
              <div
                className={`h-full ${getBarColor(item.mastery)} transition-all duration-500`}
                style={{ width: `${(item.mastery / maxMastery) * 100}%` }}
              />
              <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-medium text-slate-600 dark:text-slate-300">
                {item.mastery}%
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded"></div>
          <span className="text-xs text-slate-600 dark:text-slate-400">Mastered (80%+)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-yellow-500 rounded"></div>
          <span className="text-xs text-slate-600 dark:text-slate-400">Good (50-79%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-500 rounded"></div>
          <span className="text-xs text-slate-600 dark:text-slate-400">Learning (1-49%)</span>
        </div>
      </div>
    </div>
  );
}
