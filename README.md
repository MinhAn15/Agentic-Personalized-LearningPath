# 🎓 Personalized Learning Path

> AI-powered adaptive learning platform with 6 intelligent agents working together to optimize your learning journey.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)

## ✨ Features

- 🤖 **6 AI Agents** - Knowledge Extraction, Profiler, Path Planner, Tutor, Evaluator, KAG
- 🎯 **Personalized Paths** - RL-optimized learning sequences
- 🧑‍🏫 **Socratic Teaching** - Guide through questions, not answers
- 📊 **Real-time Analytics** - Track mastery and progress
- 🔄 **Adaptive Learning** - Adjusts to your pace and style

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Agentic-Personalized-LearningPath.git
cd Agentic-Personalized-LearningPath

# Start databases with Docker
docker-compose up -d

# Setup backend
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# Setup frontend
cd frontend
npm install

# Start services
uvicorn backend.main:app --reload  # Terminal 1
npm run dev                         # Terminal 2
```

### Access

- 🌐 Frontend: http://localhost:3000
- 🔌 Backend: http://localhost:8000
- 📊 Neo4j Browser: http://localhost:7474

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                 FRONTEND (Next.js 14)                    │
│   Landing → Dashboard → Tutor → Quiz → Progress          │
└────────────────────────┬─────────────────────────────────┘
                         │ REST API
┌────────────────────────▼─────────────────────────────────┐
│                  BACKEND (FastAPI)                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │              6 AI AGENTS                            │  │
│  │  Knowledge Extraction │ Profiler │ Path Planner   │  │
│  │  Tutor │ Evaluator │ KAG (Analytics)              │  │
│  └────────────────────────────────────────────────────┘  │
│                         │                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│  │PostgreSQL│ │  Neo4j   │ │  Redis   │                 │
│  └──────────┘ └──────────┘ └──────────┘                 │
└──────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
├── backend/
│   ├── agents/           # 6 AI Agents
│   ├── api/              # FastAPI routes
│   ├── core/             # Base classes
│   ├── database/         # DB connections
│   └── main.py           # Entry point
├── frontend/
│   ├── app/              # Next.js pages
│   ├── components/       # React components
│   ├── hooks/            # Custom hooks
│   └── lib/              # API client
├── SETUP.md              # Development setup
├── DEPLOYMENT.md         # Production deploy
└── PROJECT_SUMMARY.md    # Full documentation
```

## 🤖 The 6 Agents

| Agent                    | Purpose                                   |
| ------------------------ | ----------------------------------------- |
| **Knowledge Extraction** | Extracts concepts from course content     |
| **Profiler**             | Builds learner profiles & tracks progress |
| **Path Planner**         | Optimizes learning sequence with RL       |
| **Tutor**                | Socratic teaching with hint levels        |
| **Evaluator**            | Scores answers & detects misconceptions   |
| **KAG**                  | System-wide analytics & improvements      |

## 🎯 Learning Flow

1. **Sign Up** → Profile created
2. **Set Goal** → Path generated
3. **Learn** → Socratic guidance
4. **Answer** → Evaluation & feedback
5. **Progress** → Mastery updated
6. **Repeat** → Goal achieved! 🎉

## 📊 Tech Stack

| Layer         | Technologies                        |
| ------------- | ----------------------------------- |
| **Frontend**  | Next.js 14, TypeScript, TailwindCSS |
| **Backend**   | FastAPI, Python 3.11, LangChain     |
| **LLM**       | Google Gemini 1.5 Flash             |
| **Databases** | PostgreSQL, Neo4j, Redis            |
| **DevOps**    | Docker, Vercel                      |

## 📝 Documentation

- [Setup Guide](SETUP.md) - Development environment
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Project Summary](PROJECT_SUMMARY.md) - Full documentation

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 👤 Author

**Ly Minh An**

- GitHub: [@MinhAn15](https://github.com/MinhAn15)
- Project: Master's Thesis in AI/Education (2025)

---

⭐ Star this repo if you find it useful!
