const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface LearnerProfile {
  id: string;
  name: string;
  email: string;
  learning_goal: string;
  days_remaining: number;
  success_probability: number;
  current_concept: string;
}

export interface TutorGuidance {
  concept_id: string;
  guidance: string;
  question: string;
  hint_level: number;
  difficulty: number;
}

export interface EvaluationResult {
  score: number;
  error_type: string;
  misconception?: string;
  feedback: string;
  decision: "PROCEED" | "REMEDIATE" | "ALTERNATE" | "MASTERED";
  new_mastery: number;
}

export interface ProgressData {
  concepts: Array<{
    name: string;
    mastery: number;
    difficulty: number;
  }>;
  average_mastery: number;
  concepts_learned: number;
  total_concepts: number;
  days_remaining: number;
}

// API Client
export const apiClient = {
  // Helper function for requests
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || error.detail || "API request failed");
    }

    return response.json();
  },

  // ============== AUTH ==============
  async signup(name: string, email: string, password: string) {
    return this.request("/api/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    });
  },

  async signin(email: string, password: string) {
    return this.request("/api/v1/auth/signin", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  },

  // ============== LEARNER ==============
  async getLearnerProfile(learner_id: string): Promise<LearnerProfile> {
    return this.request(`/api/v1/learners/${learner_id}`);
  },

  async createLearnerProfile(data: {
    learner_id: string;
    name: string;
    goal: string;
    preferred_learning_style: string;
  }) {
    return this.request("/api/v1/agents/profiler", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateLearnerGoal(learner_id: string, goal: string, duration_days: number) {
    return this.request(`/api/v1/learners/${learner_id}/goal`, {
      method: "POST",
      body: JSON.stringify({ goal, duration_days }),
    });
  },

  // ============== PATH PLANNER ==============
  async getLearningPath(learner_id: string) {
    return this.request(`/api/v1/paths/learner/${learner_id}`);
  },

  async planLearningPath(learner_id: string, goal?: string) {
    return this.request("/api/v1/paths/plan", {
      method: "POST",
      body: JSON.stringify({ learner_id, goal }),
    });
  },

  async getNextConcept(learner_id: string) {
    return this.request("/api/v1/paths/next-concept", {
      method: "POST",
      body: JSON.stringify({ learner_id }),
    });
  },

  // ============== TUTOR ==============
  async getTutorGuidance(
    learner_id: string,
    concept_id: string,
    question: string,
    hint_level: number = 1,
    conversation_history: Array<{ role: string; content: string }> = []
  ): Promise<TutorGuidance> {
    return this.request("/api/v1/tutoring/ask", {
      method: "POST",
      body: JSON.stringify({ 
        learner_id, 
        concept_id, 
        question,
        hint_level,
        conversation_history 
      }),
    });
  },

  async increaseHint(
    learner_id: string,
    concept_id: string,
    question: string,
    hint_level: number
  ) {
    return this.request("/api/v1/tutoring/increase-hint", {
      method: "POST",
      body: JSON.stringify({ learner_id, concept_id, question, hint_level }),
    });
  },

  async getTutoringPrinciples() {
    return this.request("/api/v1/tutoring/principles");
  },

  // ============== EVALUATOR ==============
  async evaluateResponse(
    learner_id: string,
    concept_id: string,
    learner_response: string,
    expected_answer: string,
    correct_answer_explanation?: string
  ): Promise<EvaluationResult> {
    return this.request("/api/v1/evaluation/evaluate", {
      method: "POST",
      body: JSON.stringify({
        learner_id,
        concept_id,
        learner_response,
        expected_answer,
        correct_answer_explanation,
      }),
    });
  },

  async getErrorTypes() {
    return this.request("/api/v1/evaluation/error-types");
  },

  // ============== PROGRESS ==============
  async getProgressData(learner_id: string): Promise<ProgressData> {
    return this.request(`/api/v1/progress/${learner_id}`);
  },

  async getConceptMastery(learner_id: string, concept_id: string) {
    return this.request(`/api/v1/progress/${learner_id}/${concept_id}`);
  },

  // ============== KAG (System Analytics) ==============
  async analyzeSystemPatterns(analysis_depth: string = "deep", min_learners: number = 10) {
    return this.request("/api/v1/analysis/analyze", {
      method: "POST",
      body: JSON.stringify({ analysis_depth, min_learners }),
    });
  },

  async getSystemStatistics() {
    return this.request("/api/v1/analysis/statistics");
  },

  async getCourseRecommendations() {
    return this.request("/api/v1/analysis/recommendations");
  },

  // ============== KNOWLEDGE EXTRACTION ==============
  async extractKnowledge(course_id: string, content: string, content_type: string) {
    return this.request("/api/v1/agents/knowledge-extraction", {
      method: "POST",
      body: JSON.stringify({ course_id, content, content_type }),
    });
  },

  // ============== HEALTH ==============
  async checkHealth() {
    return this.request<{ status: string; version: string; agents: Record<string, boolean> }>("/health");
  },

  async getSystemStatus() {
    return this.request("/api/v1/system/status");
  },
};

export default apiClient;
