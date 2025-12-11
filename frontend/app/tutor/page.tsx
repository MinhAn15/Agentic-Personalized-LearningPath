"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import TutorMessage from "@/components/TutorMessage";
import QuestionForm from "@/components/QuestionForm";
import FeedbackCard from "@/components/FeedbackCard";
import HintButtons from "@/components/HintButtons";
import { useTutorSession } from "@/hooks/useTutorSession";

export default function TutorPage() {
  const router = useRouter();
  const [userId, setUserId] = useState<string | null>(null);
  const [userAnswer, setUserAnswer] = useState("");

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) {
      const user = JSON.parse(userData);
      setUserId(user.id || user.email);
    }
  }, []);

  const {
    conceptId,
    conceptName,
    difficulty,
    guidance,
    question,
    hintLevel,
    isLoading,
    error,
    submitted,
    evaluation,
    startSession,
    increaseHint,
    decreaseHint,
    submitAnswer,
    reset,
  } = useTutorSession(userId);

  // Start session on load if we have a user
  useEffect(() => {
    if (userId && !conceptId) {
      startSession("SQL_INNER_JOIN", "INNER_JOIN", 3);
    }
  }, [userId, conceptId, startSession]);

  const handleSubmitAnswer = async () => {
    if (!userAnswer.trim()) return;

    await submitAnswer(
      userAnswer,
      "INNER_JOIN combines rows from two tables where BOTH have matching values in the join column",
      "INNER_JOIN returns only rows where the join condition is satisfied on BOTH tables. Rows without matches are excluded."
    );
  };

  const handleNextConcept = () => {
    reset();
    router.push("/dashboard");
  };

  const handleRetry = () => {
    setUserAnswer("");
    reset();
    if (userId) {
      startSession("SQL_INNER_JOIN", "INNER_JOIN", 3);
    }
  };

  // Default guidance if not loaded
  const displayGuidance = guidance || 
    "Great question! Think about what INNER_JOIN does...\n\nImagine you have two tables:\n- Table A: Customers (CustomerID, Name)\n- Table B: Orders (OrderID, CustomerID, Amount)\n\nWhat do you think INNER_JOIN does with these tables?\nDoes it combine ALL rows? Or only rows with matching IDs?";

  const displayQuestion = question || "What does INNER_JOIN do?";

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Header */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              {conceptName || "INNER_JOIN"}
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Difficulty: {"⭐".repeat(difficulty || 3)}
            </p>
          </div>
          <button
            onClick={() => router.push("/dashboard")}
            className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          >
            ← Back
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        {!submitted ? (
          // Learning Phase
          <div className="space-y-6">
            {/* Tutor Guidance */}
            <TutorMessage guidance={displayGuidance} hintLevel={hintLevel} />

            {/* Hint Controls */}
            <HintButtons
              hintLevel={hintLevel}
              onIncrease={increaseHint}
              onDecrease={decreaseHint}
            />

            {/* Question & Answer */}
            <QuestionForm
              question={displayQuestion}
              answer={userAnswer}
              onAnswerChange={setUserAnswer}
              onSubmit={handleSubmitAnswer}
              loading={isLoading}
            />

            {error && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-red-700 dark:text-red-400">{error}</p>
              </div>
            )}
          </div>
        ) : (
          // Feedback Phase
          <div className="space-y-6">
            {/* Your Answer */}
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
              <h2 className="font-semibold text-slate-900 dark:text-white mb-2">
                Your Answer:
              </h2>
              <p className="text-slate-700 dark:text-slate-300">{userAnswer}</p>
            </div>

            {/* Feedback */}
            {evaluation && (
              <FeedbackCard
                score={evaluation.score}
                feedback={evaluation.feedback}
                misconception={evaluation.misconception}
              />
            )}

            {/* Next Steps */}
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
              <h2 className="font-semibold text-slate-900 dark:text-white mb-4">
                What&apos;s Next?
              </h2>
              <div className="space-y-2 mb-6">
                <p className="text-slate-700 dark:text-slate-300">
                  ✅ You&apos;re making progress! Your mastery improved to{" "}
                  {evaluation?.new_mastery || 52}%.
                </p>
                <p className="text-slate-700 dark:text-slate-300">
                  → Decision: {evaluation?.decision || "PROCEED"} (
                  {evaluation?.decision === "PROCEED"
                    ? "Ready for next concept"
                    : evaluation?.decision === "REMEDIATE"
                    ? "Let&apos;s practice more"
                    : evaluation?.decision === "MASTERED"
                    ? "Excellent! Move on!"
                    : "Try an alternative approach"}
                  )
                </p>
              </div>
              <div className="flex gap-4">
                <button
                  onClick={handleNextConcept}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
                >
                  Continue Learning
                </button>
                <button
                  onClick={handleRetry}
                  className="px-6 py-2 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition text-slate-700 dark:text-slate-300"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
