"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient, ProgressData } from "@/lib/api";

interface UseProgressState {
  data: ProgressData | null;
  isLoading: boolean;
  error: string | null;
}

export function useProgress(learnerId: string | null) {
  const [state, setState] = useState<UseProgressState>({
    data: null,
    isLoading: true,
    error: null,
  });

  const fetchProgress = useCallback(async () => {
    if (!learnerId) {
      setState(prev => ({ ...prev, isLoading: false }));
      return;
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const progressData = await apiClient.getProgressData(learnerId);
      setState({ data: progressData, isLoading: false, error: null });
      return progressData;
    } catch (error) {
      // Return mock data if API fails
      const mockProgress: ProgressData = {
        concepts: [
          { name: "SELECT", mastery: 95, difficulty: 1 },
          { name: "FROM", mastery: 85, difficulty: 1 },
          { name: "WHERE", mastery: 80, difficulty: 2 },
          { name: "INNER_JOIN", mastery: 30, difficulty: 3 },
          { name: "LEFT_JOIN", mastery: 0, difficulty: 4 },
        ],
        average_mastery: 58,
        concepts_learned: 3,
        total_concepts: 5,
        days_remaining: 10,
      };
      setState({ data: mockProgress, isLoading: false, error: null });
      return mockProgress;
    }
  }, [learnerId]);

  // Format data for charts
  const getChartData = useCallback(() => {
    if (!state.data) return [];
    return state.data.concepts.map(c => ({
      concept: c.name,
      mastery: c.mastery,
      difficulty: c.difficulty,
    }));
  }, [state.data]);

  const getTimelineData = useCallback(() => {
    if (!state.data) return [];
    
    const { concepts } = state.data;
    const phases = [];
    let dayCount = 1;

    // Group concepts into phases
    for (let i = 0; i < concepts.length; i += 2) {
      const group = concepts.slice(i, i + 2);
      const allMastered = group.every(c => c.mastery >= 80);
      const anyInProgress = group.some(c => c.mastery > 0 && c.mastery < 80);

      phases.push({
        day: `Day ${dayCount}-${dayCount + 3}`,
        label: group.map(c => c.name).join(", "),
        status: allMastered ? "completed" : anyInProgress ? "current" : "upcoming",
      });

      dayCount += 4;
    }

    return phases;
  }, [state.data]);

  useEffect(() => {
    fetchProgress();
  }, [fetchProgress]);

  return {
    ...state,
    fetchProgress,
    getChartData,
    getTimelineData,
    refetch: fetchProgress,
  };
}
