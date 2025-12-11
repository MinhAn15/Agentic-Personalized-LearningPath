"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useProgress } from "@/hooks/useProgress";

export default function ProgressPage() {
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) {
      const user = JSON.parse(userData);
      setUserId(user.id || user.email);
    }
  }, []);

  const { data: progress, isLoading, error, getChartData, getTimelineData } = useProgress(userId);

  const getBarColor = (mastery: number) => {
    if (mastery >= 80) return "bg-green-500";
    if (mastery >= 50) return "bg-yellow-500";
    if (mastery > 0) return "bg-blue-500";
    return "bg-slate-300 dark:bg-slate-600";
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-slate-900">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading progress...</p>
        </div>
      </div>
    );
  }

  const chartData = getChartData();
  const timelineData = getTimelineData();
  const averageMastery = progress?.average_mastery || 58;
  const conceptsLearned = progress?.concepts_learned || 3;
  const totalConcepts = progress?.total_concepts || 5;
  const daysRemaining = progress?.days_remaining || 10;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Header */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-8">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              Your Progress
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Track your mastery across all concepts
            </p>
          </div>
          <Link
            href="/dashboard"
            className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Overall Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
              Average Mastery
            </p>
            <p className="text-4xl font-bold text-blue-600 dark:text-blue-400">
              {averageMastery}%
            </p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
              Concepts Learned
            </p>
            <p className="text-4xl font-bold text-green-600 dark:text-green-400">
              {conceptsLearned}/{totalConcepts}
            </p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
              Days Remaining
            </p>
            <p className="text-4xl font-bold text-purple-600 dark:text-purple-400">
              {daysRemaining}
            </p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
              Success Probability
            </p>
            <p className="text-4xl font-bold text-orange-600 dark:text-orange-400">
              92%
            </p>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 mb-8">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6">
            Mastery by Concept
          </h2>
          <div className="space-y-4">
            {chartData.map((item) => (
              <div key={item.concept} className="flex items-center gap-4">
                <div className="w-24 text-sm font-medium text-slate-700 dark:text-slate-300">
                  {item.concept}
                </div>
                <div className="flex-1 h-8 bg-slate-200 dark:bg-slate-700 rounded-lg overflow-hidden">
                  <div
                    className={`h-full ${getBarColor(item.mastery)} transition-all duration-500 flex items-center justify-end pr-2`}
                    style={{ width: `${Math.max(item.mastery, 5)}%` }}
                  >
                    {item.mastery > 10 && (
                      <span className="text-xs font-bold text-white">
                        {item.mastery}%
                      </span>
                    )}
                  </div>
                </div>
                {item.mastery <= 10 && (
                  <span className="text-sm text-slate-600 dark:text-slate-400 w-12">
                    {item.mastery}%
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Detailed Progress */}
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 mb-8">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6">
            Detailed Progress
          </h2>
          <div className="space-y-4">
            {chartData.map((item) => (
              <div key={item.concept} className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {item.concept}
                  </span>
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    {item.mastery}% mastery • Difficulty: {"⭐".repeat(item.difficulty)}
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2">
                  <div
                    className={`${getBarColor(item.mastery)} h-2 rounded-full transition-all duration-300`}
                    style={{ width: `${item.mastery}%` }}
                  ></div>
                </div>
                <div className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                  {item.mastery >= 80 && "✅ Mastered! Great work."}
                  {item.mastery >= 50 && item.mastery < 80 && "📈 Good progress. Keep practicing!"}
                  {item.mastery > 0 && item.mastery < 50 && "🎯 In progress. You're learning!"}
                  {item.mastery === 0 && "🔒 Not started yet. Coming soon!"}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Timeline */}
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6">
            Learning Timeline
          </h2>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-200 dark:bg-slate-600"></div>
            <div className="space-y-6">
              {(timelineData.length > 0 ? timelineData : [
                { day: "Day 1-3", status: "completed", label: "SELECT, FROM basics" },
                { day: "Day 4-6", status: "completed", label: "WHERE conditions" },
                { day: "Day 7-10", status: "current", label: "INNER_JOIN mastery" },
                { day: "Day 11-14", status: "upcoming", label: "LEFT_JOIN, advanced queries" },
              ]).map((item, index) => (
                <div key={index} className="flex items-center gap-4 ml-4">
                  <div
                    className={`w-4 h-4 rounded-full -ml-6 ${
                      item.status === "completed"
                        ? "bg-green-500"
                        : item.status === "current"
                        ? "bg-blue-500 ring-4 ring-blue-200 dark:ring-blue-800"
                        : "bg-slate-300 dark:bg-slate-600"
                    }`}
                  ></div>
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">{item.day}</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{item.label}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
