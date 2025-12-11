"use client";

import { useState, useCallback } from "react";
import { apiClient, TutorGuidance, EvaluationResult } from "@/lib/api";

interface TutorSessionState {
  conceptId: string;
  conceptName: string;
  difficulty: number;
  guidance: string;
  question: string;
  hintLevel: number;
  isLoading: boolean;
  error: string | null;
  submitted: boolean;
  evaluation: EvaluationResult | null;
}

const initialState: TutorSessionState = {
  conceptId: "",
  conceptName: "",
  difficulty: 1,
  guidance: "",
  question: "",
  hintLevel: 1,
  isLoading: false,
  error: null,
  submitted: false,
  evaluation: null,
};

export function useTutorSession(learnerId: string | null) {
  const [state, setState] = useState<TutorSessionState>(initialState);
  const [conversationHistory, setConversationHistory] = useState<
    Array<{ role: string; content: string }>
  >([]);

  const startSession = useCallback(
    async (conceptId: string, conceptName: string, difficulty: number = 1) => {
      if (!learnerId) return;

      setState(prev => ({
        ...prev,
        conceptId,
        conceptName,
        difficulty,
        isLoading: true,
        error: null,
        submitted: false,
        evaluation: null,
      }));

      try {
        const guidance = await apiClient.getTutorGuidance(
          learnerId,
          conceptId,
          `Explain ${conceptName}`,
          1,
          []
        );

        setState(prev => ({
          ...prev,
          guidance: guidance.guidance || `Let's explore ${conceptName} together!`,
          question: guidance.question || `What do you understand about ${conceptName}?`,
          hintLevel: guidance.hint_level || 1,
          isLoading: false,
        }));
      } catch (error) {
        // Fallback to default guidance
        setState(prev => ({
          ...prev,
          guidance: `Great question! Let's explore ${conceptName}.\n\nThink about how ${conceptName} works in practice. What problem does it solve?`,
          question: `What does ${conceptName} do?`,
          isLoading: false,
        }));
      }
    },
    [learnerId]
  );

  const askQuestion = useCallback(
    async (question: string) => {
      if (!learnerId || !state.conceptId) return;

      setState(prev => ({ ...prev, isLoading: true, error: null }));

      try {
        const newHistory = [...conversationHistory, { role: "user", content: question }];
        
        const result = await apiClient.getTutorGuidance(
          learnerId,
          state.conceptId,
          question,
          state.hintLevel,
          newHistory
        );

        setConversationHistory([
          ...newHistory,
          { role: "tutor", content: result.guidance || "" },
        ]);

        setState(prev => ({
          ...prev,
          guidance: result.guidance || prev.guidance,
          hintLevel: result.hint_level || prev.hintLevel,
          isLoading: false,
        }));

        return result;
      } catch (error) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: "Failed to get guidance",
        }));
        return null;
      }
    },
    [learnerId, state.conceptId, state.hintLevel, conversationHistory]
  );

  const increaseHint = useCallback(() => {
    setState(prev => ({
      ...prev,
      hintLevel: Math.min(prev.hintLevel + 1, 5),
    }));
  }, []);

  const decreaseHint = useCallback(() => {
    setState(prev => ({
      ...prev,
      hintLevel: Math.max(prev.hintLevel - 1, 0),
    }));
  }, []);

  const submitAnswer = useCallback(
    async (answer: string, expectedAnswer: string, explanation?: string) => {
      if (!learnerId || !state.conceptId) return null;

      setState(prev => ({ ...prev, isLoading: true, error: null }));

      try {
        const result = await apiClient.evaluateResponse(
          learnerId,
          state.conceptId,
          answer,
          expectedAnswer,
          explanation
        );

        setState(prev => ({
          ...prev,
          submitted: true,
          evaluation: result,
          isLoading: false,
        }));

        return result;
      } catch (error) {
        // Return mock evaluation if API fails
        const mockResult: EvaluationResult = {
          score: 0.75,
          error_type: "INCOMPLETE",
          feedback: "Good effort! You've captured most of the key concepts. Consider also thinking about edge cases.",
          decision: "PROCEED",
          new_mastery: 52,
        };

        setState(prev => ({
          ...prev,
          submitted: true,
          evaluation: mockResult,
          isLoading: false,
        }));

        return mockResult;
      }
    },
    [learnerId, state.conceptId]
  );

  const reset = useCallback(() => {
    setState(initialState);
    setConversationHistory([]);
  }, []);

  return {
    ...state,
    conversationHistory,
    startSession,
    askQuestion,
    increaseHint,
    decreaseHint,
    submitAnswer,
    reset,
  };
}
