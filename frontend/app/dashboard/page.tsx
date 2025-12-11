"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useLearner } from "@/hooks/useLearner";

export default function Dashboard() {
  // Get user from localStorage (simulating auth)
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) {
      const user = JSON.parse(userData);
      setUserId(user.id || user.email);
    }
  }, []);

  const { profile, progress, isLoading, error } = useLearner(userId);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-slate-900">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading your profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-slate-900">
        <div className="text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <Link href="/" className="text-blue-600 hover:underline">Go to Home</Link>
        </div>
      </div>
    );
  }

  // Use profile data or defaults
  const name = profile?.name || "Learner";
  const goal = profile?.learning_goal || "Set your learning goal";
  const daysRemaining = profile?.days_remaining || progress?.days_remaining || 14;
  const successProbability = profile?.success_probability || 0.85;
  const currentConcept = profile?.current_concept || "SELECT";
  const concepts = progress?.concepts || [
    { name: "SELECT", mastery: 95, difficulty: 1 },
    { name: "WHERE", mastery: 80, difficulty: 2 },
    { name: "FROM", mastery: 85, difficulty: 1 },
    { name: "INNER_JOIN", mastery: 30, difficulty: 3 },
    { name: "LEFT_JOIN", mastery: 0, difficulty: 4 },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Header */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
              Welcome, {name}
            </h1>
            <p className="text-slate-600 dark:text-slate-400">{goal}</p>
          </div>
          <div className="flex gap-4">
            <Link
              href="/progress"
              className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition text-slate-700 dark:text-slate-300"
            >
              View Progress
            </Link>
            <button
              onClick={() => {
                localStorage.removeItem("token");
                localStorage.removeItem("user");
                window.location.href = "/";
              }}
              className="px-4 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Goal Progress */}
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-8 mb-8">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
            Your Learning Goal
          </h2>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Days Remaining */}
            <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Days Remaining</p>
              <p className="text-4xl font-bold text-blue-600 dark:text-blue-400">{daysRemaining}</p>
            </div>

            {/* Success Probability */}
            <div className="bg-green-50 dark:bg-green-900/20 p-6 rounded-lg border border-green-200 dark:border-green-800">
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Success Probability</p>
              <p className="text-4xl font-bold text-green-600 dark:text-green-400">
                {(successProbability * 100).toFixed(0)}%
              </p>
            </div>

            {/* Today's Concept */}
            <div className="bg-purple-50 dark:bg-purple-900/20 p-6 rounded-lg border border-purple-200 dark:border-purple-800">
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Today&apos;s Concept</p>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {currentConcept}
              </p>
            </div>
          </div>

          {/* Start Learning Button */}
          <Link
            href="/tutor"
            className="mt-6 inline-block px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
          >
            Start Today&apos;s Learning
          </Link>
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Link
            href="/tutor"
            className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 hover:border-blue-500 transition"
          >
            <span className="text-3xl mb-3 block">🧑‍🏫</span>
            <h3 className="font-semibold text-slate-900 dark:text-white mb-2">AI Tutor</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Get personalized guidance with Socratic method
            </p>
          </Link>

          <Link
            href="/quiz"
            className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 hover:border-blue-500 transition"
          >
            <span className="text-3xl mb-3 block">📝</span>
            <h3 className="font-semibold text-slate-900 dark:text-white mb-2">Take Quiz</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Test your knowledge and get feedback
            </p>
          </Link>

          <Link
            href="/upload"
            className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 hover:border-blue-500 transition"
          >
            <span className="text-3xl mb-3 block">📚</span>
            <h3 className="font-semibold text-slate-900 dark:text-white mb-2">Upload Content</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Add new learning materials
            </p>
          </Link>
        </div>

        {/* Progress by Concept */}
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
              Your Progress
            </h2>
            <Link
              href="/progress"
              className="text-blue-600 hover:underline text-sm"
            >
              View Details →
            </Link>
          </div>

          <div className="space-y-4">
            {concepts.map((concept) => (
              <div key={concept.name}>
                <div className="flex justify-between items-center mb-2">
                  <p className="font-semibold text-slate-900 dark:text-white">{concept.name}</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {concept.mastery}%
                  </p>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      concept.mastery >= 80
                        ? "bg-green-500"
                        : concept.mastery >= 50
                        ? "bg-yellow-500"
                        : concept.mastery > 0
                        ? "bg-blue-500"
                        : "bg-slate-300"
                    }`}
                    style={{ width: `${concept.mastery}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
