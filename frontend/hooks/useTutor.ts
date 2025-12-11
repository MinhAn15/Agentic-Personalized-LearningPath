"use client";

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api";

interface TutorState {
  guidance: string;
  hintLevel: number;
  followUpQuestion?: string;
  isLoading: boolean;
  error: string | null;
}

interface EvaluationResult {
  score: number;
  errorType: string;
  misconception?: string;
  feedback: string;
  decision: string;
  newMastery: number;
}

export function useTutor(learnerId: string, conceptId: string) {
  const [state, setState] = useState<TutorState>({
    guidance: "",
    hintLevel: 1,
    isLoading: false,
    error: null,
  });

  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);

  const askQuestion = useCallback(
    async (question: string) => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const response = await apiClient.getTutorGuidance(
          learnerId,
          conceptId,
          question,
          state.hintLevel
        );

        if (response.error) {
          setState((prev) => ({ ...prev, isLoading: false, error: response.error! }));
          return null;
        }

        setState((prev) => ({
          ...prev,
          guidance: response.data?.guidance || "",
          hintLevel: response.data?.hint_level || prev.hintLevel,
          followUpQuestion: response.data?.follow_up_question,
          isLoading: false,
        }));

        return response.data;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Failed to get guidance";
        setState((prev) => ({ ...prev, isLoading: false, error: errorMessage }));
        return null;
      }
    },
    [learnerId, conceptId, state.hintLevel]
  );

  const increaseHint = useCallback(() => {
    setState((prev) => ({
      ...prev,
      hintLevel: Math.min(prev.hintLevel + 1, 5),
    }));
  }, []);

  const decreaseHint = useCallback(() => {
    setState((prev) => ({
      ...prev,
      hintLevel: Math.max(prev.hintLevel - 1, 0),
    }));
  }, []);

  const submitAnswer = useCallback(
    async (answer: string, expectedAnswer: string, explanation?: string) => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const response = await apiClient.evaluateResponse(
          learnerId,
          conceptId,
          answer,
          expectedAnswer,
          explanation
        );

        if (response.error) {
          setState((prev) => ({ ...prev, isLoading: false, error: response.error! }));
          return null;
        }

        const result: EvaluationResult = {
          score: response.data?.score || 0,
          errorType: response.data?.error_type || "UNKNOWN",
          misconception: response.data?.misconception,
          feedback: response.data?.feedback || "",
          decision: response.data?.decision || "PROCEED",
          newMastery: response.data?.new_mastery || 0,
        };

        setEvaluation(result);
        setState((prev) => ({ ...prev, isLoading: false }));

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Failed to evaluate answer";
        setState((prev) => ({ ...prev, isLoading: false, error: errorMessage }));
        return null;
      }
    },
    [learnerId, conceptId]
  );

  const reset = useCallback(() => {
    setState({
      guidance: "",
      hintLevel: 1,
      isLoading: false,
      error: null,
    });
    setEvaluation(null);
  }, []);

  return {
    ...state,
    evaluation,
    askQuestion,
    increaseHint,
    decreaseHint,
    submitAnswer,
    reset,
  };
}
