"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient, LearnerProfile, ProgressData } from "@/lib/api";

interface UseLearnerState {
  profile: LearnerProfile | null;
  progress: ProgressData | null;
  isLoading: boolean;
  error: string | null;
}

export function useLearner(learnerId: string | null) {
  const [state, setState] = useState<UseLearnerState>({
    profile: null,
    progress: null,
    isLoading: true,
    error: null,
  });

  const fetchProfile = useCallback(async () => {
    if (!learnerId) {
      setState(prev => ({ ...prev, isLoading: false }));
      return;
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const profileData = await apiClient.getLearnerProfile(learnerId);
      setState(prev => ({ ...prev, profile: profileData, isLoading: false }));
      return profileData;
    } catch (error) {
      // Return mock data if API fails
      const mockProfile: LearnerProfile = {
        id: learnerId,
        name: learnerId.split("@")[0] || "Learner",
        email: learnerId,
        learning_goal: "Master SQL JOINs in 14 days",
        days_remaining: 10,
        success_probability: 0.92,
        current_concept: "INNER_JOIN",
      };
      setState(prev => ({ ...prev, profile: mockProfile, isLoading: false }));
      return mockProfile;
    }
  }, [learnerId]);

  const fetchProgress = useCallback(async () => {
    if (!learnerId) return;

    try {
      const progressData = await apiClient.getProgressData(learnerId);
      setState(prev => ({ ...prev, progress: progressData }));
      return progressData;
    } catch (error) {
      // Return mock progress if API fails
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
      setState(prev => ({ ...prev, progress: mockProgress }));
      return mockProgress;
    }
  }, [learnerId]);

  const updateGoal = useCallback(async (goal: string, durationDays: number) => {
    if (!learnerId) return;

    try {
      await apiClient.updateLearnerGoal(learnerId, goal, durationDays);
      await fetchProfile();
    } catch (error) {
      console.error("Failed to update goal:", error);
      throw error;
    }
  }, [learnerId, fetchProfile]);

  // Fetch data on mount
  useEffect(() => {
    const loadData = async () => {
      await Promise.all([fetchProfile(), fetchProgress()]);
    };
    loadData();
  }, [fetchProfile, fetchProgress]);

  return {
    ...state,
    fetchProfile,
    fetchProgress,
    updateGoal,
    refetch: () => Promise.all([fetchProfile(), fetchProgress()]),
  };
}
