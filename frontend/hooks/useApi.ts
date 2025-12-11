'use client'

import { useState, useCallback } from 'react'
import { api } from '@/lib/api'

interface UseApiState<T> {
  data: T | null
  isLoading: boolean
  error: string | null
}

export function useApi<T>() {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    isLoading: false,
    error: null,
  })

  const execute = useCallback(async (
    apiCall: () => Promise<{ data?: T; error?: string; status: number }>
  ) => {
    setState({ data: null, isLoading: true, error: null })
    
    try {
      const response = await apiCall()
      
      if (response.error) {
        setState({ data: null, isLoading: false, error: response.error })
        return null
      }
      
      setState({ data: response.data || null, isLoading: false, error: null })
      return response.data
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred'
      setState({ data: null, isLoading: false, error: errorMessage })
      return null
    }
  }, [])

  return { ...state, execute }
}

// ============= SPECIALIZED HOOKS =============

export function useLearnerProfile() {
  const { data, isLoading, error, execute } = useApi<any>()

  const fetchProfile = useCallback(async (learnerId: string) => {
    return execute(() => api.getProfile(learnerId))
  }, [execute])

  const createProfile = useCallback(async (profileData: {
    learner_id: string
    name: string
    goal: string
    preferred_learning_style: string
  }) => {
    return execute(() => api.createProfile(profileData))
  }, [execute])

  return { profile: data, isLoading, error, fetchProfile, createProfile }
}

export function useLearningPath() {
  const { data, isLoading, error, execute } = useApi<any>()

  const fetchPath = useCallback(async (learnerId: string) => {
    return execute(() => api.getLearningPath(learnerId))
  }, [execute])

  const planPath = useCallback(async (learnerId: string, goal?: string) => {
    return execute(() => api.planPath({ learner_id: learnerId, goal }))
  }, [execute])

  return { path: data, isLoading, error, fetchPath, planPath }
}

export function useTutor() {
  const { data, isLoading, error, execute } = useApi<{
    success: boolean
    guidance: string
    hint_level: number
    follow_up_question?: string
    source: string
  }>()

  const askQuestion = useCallback(async (
    learnerId: string,
    question: string,
    conceptId: string,
    hintLevel: number = 1,
    history: Array<{ role: string; content: string }> = []
  ) => {
    return execute(() => api.askTutor({
      learner_id: learnerId,
      question,
      concept_id: conceptId,
      hint_level: hintLevel,
      conversation_history: history,
    }))
  }, [execute])

  const increaseHint = useCallback(async (
    learnerId: string,
    question: string,
    conceptId: string,
    currentHintLevel: number
  ) => {
    return execute(() => api.increaseHint({
      learner_id: learnerId,
      question,
      concept_id: conceptId,
      hint_level: currentHintLevel,
    }))
  }, [execute])

  return { response: data, isLoading, error, askQuestion, increaseHint }
}

export function useEvaluator() {
  const { data, isLoading, error, execute } = useApi<{
    success: boolean
    score: number
    error_type: string
    misconception?: string
    feedback: string
    decision: string
    new_mastery: number
  }>()

  const evaluate = useCallback(async (
    learnerId: string,
    conceptId: string,
    response: string,
    expected: string,
    explanation?: string
  ) => {
    return execute(() => api.evaluateResponse({
      learner_id: learnerId,
      concept_id: conceptId,
      learner_response: response,
      expected_answer: expected,
      correct_answer_explanation: explanation,
    }))
  }, [execute])

  return { result: data, isLoading, error, evaluate }
}

export function useHealthCheck() {
  const { data, isLoading, error, execute } = useApi<{
    status: string
    version: string
    databases: Record<string, boolean>
    agents: Record<string, boolean>
  }>()

  const checkHealth = useCallback(async () => {
    return execute(() => api.healthCheck())
  }, [execute])

  return { health: data, isLoading, error, checkHealth }
}
