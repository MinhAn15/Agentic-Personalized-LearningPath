# 🎓 Personalized Learning Path - Project Summary

> **AI-powered adaptive learning platform** với 6 intelligent agents làm việc cùng nhau để tối ưu hóa lộ trình học tập cá nhân.

---

## 📌 Project Overview

| Attribute        | Value                                 |
| ---------------- | ------------------------------------- |
| **Project Name** | Agentic Personalized Learning Path    |
| **Type**         | Thesis/Research Project               |
| **Domain**       | AI in Education (EdTech)              |
| **Tech Stack**   | FastAPI + Next.js + Neo4j + LangChain |
| **Total LOC**    | ~8,000+ lines                         |
| **Duration**     | 12 weeks implementation               |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js 14)                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Landing │ │Dashboard│ │ Tutor   │ │Progress │           │
│  │  Page   │ │  Page   │ │  Page   │ │  Page   │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       └───────────┴───────────┴───────────┘                 │
│                         ↓ API Calls                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              6 AI AGENTS SYSTEM                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │   │
│  │  │Knowledge │ │ Profiler │ │   Path   │            │   │
│  │  │Extraction│ │  Agent   │ │ Planner  │            │   │
│  │  │  Agent   │ │          │ │  Agent   │            │   │
│  │  └──────────┘ └──────────┘ └──────────┘            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │   │
│  │  │  Tutor   │ │Evaluator │ │   KAG    │            │   │
│  │  │  Agent   │ │  Agent   │ │  Agent   │            │   │
│  │  └──────────┘ └──────────┘ └──────────┘            │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↓                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ PostgreSQL  │ │   Neo4j     │ │   Redis     │          │
│  │  (Profiles) │ │(KnowledgeG.)│ │  (Cache)    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 6 AI Agents

### 1. Knowledge Extraction Agent

- **Purpose**: Trích xuất concepts và relationships từ course content
- **Input**: Text/PDF/Markdown content
- **Output**: Knowledge graph nodes + edges
- **Tech**: LangChain + Gemini LLM

### 2. Profiler Agent

- **Purpose**: Xây dựng learner profile, track knowledge state
- **Features**:
  - Initial assessment
  - Learning style detection
  - Gap analysis
  - Mastery tracking

### 3. Path Planner Agent

- **Purpose**: Tối ưu hóa learning path với RL
- **Algorithm**: Multi-armed bandit (UCB strategy)
- **Features**:
  - Prerequisite-aware sequencing
  - Success probability estimation
  - Dynamic re-planning

### 4. Tutor Agent

- **Purpose**: Socratic teaching với Harvard 7 Principles
- **Features**:
  - 5-level hint system
  - Progressive guidance
  - Follow-up questions
  - Productive struggle encouragement

### 5. Evaluator Agent

- **Purpose**: Assessment và feedback generation
- **Error Types**:
  - CARELESS
  - INCOMPLETE
  - PROCEDURAL
  - CONCEPTUAL
- **Output**: Score + Misconception + Personalized feedback

### 6. KAG (Knowledge Analytics Group) Agent

- **Purpose**: System-wide pattern analysis
- **Features**:
  - Common misconception detection
  - Bottleneck identification
  - Course improvement recommendations

---

## 💻 Technology Stack

### Backend

| Technology       | Purpose            |
| ---------------- | ------------------ |
| Python 3.11      | Core language      |
| FastAPI          | REST API framework |
| LangChain        | LLM orchestration  |
| Gemini 1.5 Flash | LLM model          |
| Neo4j            | Knowledge graph DB |
| PostgreSQL       | Relational data    |
| Redis            | Caching layer      |
| Pydantic         | Data validation    |

### Frontend

| Technology  | Purpose          |
| ----------- | ---------------- |
| Next.js 14  | React framework  |
| TypeScript  | Type safety      |
| TailwindCSS | Styling          |
| React Hooks | State management |

### DevOps

| Technology     | Purpose                 |
| -------------- | ----------------------- |
| Docker Compose | Container orchestration |
| Vercel         | Frontend hosting        |
| GitHub         | Version control         |

---

## 📁 Project Structure

```
Agentic-Personalized-LearningPath/
├── backend/
│   ├── agents/
│   │   ├── knowledge_extraction_agent.py
│   │   ├── profiler_agent.py
│   │   ├── path_planner_agent.py
│   │   ├── tutor_agent.py
│   │   ├── evaluator_agent.py
│   │   └── kag_agent.py
│   ├── api/
│   │   ├── profiler_routes.py
│   │   ├── path_routes.py
│   │   ├── tutor_routes.py
│   │   ├── evaluator_routes.py
│   │   └── kag_routes.py
│   ├── core/
│   │   ├── base_agent.py
│   │   ├── state_manager.py
│   │   ├── event_bus.py
│   │   └── rl_engine.py
│   ├── database/
│   │   ├── postgres.py
│   │   ├── neo4j.py
│   │   └── redis.py
│   ├── main.py
│   └── config.py
├── frontend/
│   ├── app/
│   │   ├── page.tsx (landing)
│   │   ├── dashboard/page.tsx
│   │   ├── tutor/page.tsx
│   │   ├── quiz/page.tsx
│   │   ├── progress/page.tsx
│   │   └── auth/
│   ├── components/
│   │   ├── LoadingSpinner.tsx
│   │   ├── ErrorBoundary.tsx
│   │   ├── Toast.tsx
│   │   └── ...
│   ├── hooks/
│   │   ├── useLearner.ts
│   │   ├── useTutorSession.ts
│   │   └── useProgress.ts
│   └── lib/
│       ├── api.ts
│       └── auth-context.tsx
├── SETUP.md
├── DEPLOYMENT.md
├── requirements.txt
└── docker-compose.yml
```

---

## 🎯 Key Features

### For Learners

- ✅ Personalized learning paths
- ✅ Socratic teaching method
- ✅ Real-time progress tracking
- ✅ Adaptive difficulty
- ✅ Misconception detection

### For Instructors

- ✅ Content upload & extraction
- ✅ Knowledge graph visualization
- ✅ Analytics dashboard
- ✅ Course improvement insights

### Technical

- ✅ Multi-agent coordination
- ✅ RL-based optimization
- ✅ Knowledge graph powered
- ✅ Real-time evaluation
- ✅ Scalable architecture

---

## 📊 Learning Flow

```
1. SIGN UP
   └── Profiler Agent creates learner profile

2. SET GOAL
   └── Path Planner generates optimized path

3. LEARN CONCEPT
   └── Tutor Agent provides Socratic guidance

4. ANSWER QUESTION
   └── Evaluator Agent scores & classifies errors

5. GET FEEDBACK
   └── Personalized feedback + misconception detection

6. UPDATE MASTERY
   └── Progress tracked, path adjusted

7. REPEAT → GOAL ACHIEVED! 🎉
```

---

## 🔗 API Endpoints

| Endpoint                      | Method | Purpose          |
| ----------------------------- | ------ | ---------------- |
| `/health`                     | GET    | Health check     |
| `/api/v1/agents/profiler`     | POST   | Create profile   |
| `/api/v1/paths/plan`          | POST   | Generate path    |
| `/api/v1/tutoring/ask`        | POST   | Get guidance     |
| `/api/v1/evaluation/evaluate` | POST   | Evaluate answer  |
| `/api/v1/analysis/analyze`    | POST   | System analytics |

---

## 🚀 Quick Start

```bash
# 1. Clone repo
git clone <repo-url>
cd Agentic-Personalized-LearningPath

# 2. Setup backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 3. Setup frontend
cd frontend
npm install

# 4. Start services
docker-compose up -d  # Databases
uvicorn backend.main:app --reload  # Backend
npm run dev  # Frontend

# 5. Access
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Neo4j: http://localhost:7474
```

---

## 📈 Future Improvements

1. **Real WebSocket** - Live progress updates
2. **Voice interaction** - Speech-to-text tutoring
3. **Mobile app** - React Native client
4. **More LLM options** - OpenAI, Claude, local models
5. **A/B testing** - Compare teaching strategies
6. **Gamification** - Points, badges, leaderboards
7. **Group learning** - Collaborative features
8. **Content marketplace** - Share courses

---

## 📝 Research Contributions

1. **Multi-Agent Architecture** for personalized learning
2. **RL-based Path Optimization** with bandit strategies
3. **Socratic AI Tutor** implementing Harvard principles
4. **Error Classification System** for misconception detection
5. **Knowledge Graph Integration** for prerequisite tracking

---

## 👤 Author

- **Name**: [Your Name]
- **Thesis**: Master's Thesis in AI/Education
- **University**: [University Name]
- **Year**: 2025

---

## 📚 References

1. Harvard 7 Principles of Learning
2. Reinforcement Learning for Education
3. Knowledge Graphs in EdTech
4. Socratic Method in AI Tutoring
5. Multi-Agent Systems for Personalization
