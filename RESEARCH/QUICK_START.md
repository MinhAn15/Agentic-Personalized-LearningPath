# ⚡ QUICK START GUIDE - BẮT ĐẦU TRONG 30 PHÚT

## 🎯 Mục tiêu
Xây dựng và chạy hệ thống đầu tiên trên máy local (Google AntiGravity IDE)

## 📦 Yêu cầu
- Python 3.11+
- Node.js 18+
- Docker + Docker Compose
- Git
- OpenAI API key (hoặc Google/Anthropic)

---

## PHASE 1: SETUP (5 phút)

### Step 1.1: Clone Repository

```bash
# Tạo workspace folder
mkdir ~/personalized-learning-path
cd ~/personalized-learning-path

# Initialize Git
git init
git remote add origin https://github.com/YOUR_USERNAME/personalized-learning-path-kg-llm.git

# Create folder structure
mkdir backend frontend database docs scripts
```

### Step 1.2: Backend Setup

```bash
cd backend

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows

# Copy environment file
cat > .env << 'EOF'
API_TITLE=Personalized Learning Path System
API_VERSION=1.0.0
DEBUG=True
SECRET_KEY=dev-secret-key-12345

# Database
POSTGRES_URL=postgresql://user:password@localhost/learning_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=learning_db

# Neo4j (Aura Cloud)
NEO4J_URI=neo4j+s://xxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# Redis
REDIS_URL=redis://localhost:6379

# LLM
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o

# RAG
CHROMA_PATH=./chroma_data
EMBEDDING_MODEL=text-embedding-3-small
EOF

# Install dependencies
pip install fastapi uvicorn pydantic neo4j psycopg2-binary redis \
    openai llama-index llama-index-llms-openai llama-index-graph-stores-neo4j \
    chromadb python-dotenv
```

### Step 1.3: Frontend Setup

```bash
cd ../frontend

# Create Next.js project
npm create next-app@latest . --typescript --tailwind

# Install additional dependencies
npm install @hookform/resolvers zustand axios socket.io-client
```

### Step 1.4: Database Setup (Docker)

```bash
cd ..

# Start database services
docker-compose up -d postgres neo4j redis

# Wait for Neo4j to be ready
sleep 15

# Verify connections
curl http://localhost:7474  # Neo4j UI should be available
```

---

## PHASE 2: CORE BACKEND (10 phút)

### Step 2.1: Create BaseAgent

**File: `backend/agents/base.py`**

```python
from abc import ABC, abstractmethod
from typing import Any, Dict
from datetime import datetime
import logging

class BaseAgent(ABC):
    def __init__(self, agent_id: str, llm=None):
        self.agent_id = agent_id
        self.llm = llm
        self.logger = logging.getLogger(agent_id)
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass
    
    def log(self, message: str, level: str = 'INFO'):
        getattr(self.logger, level.lower())(f"[{self.agent_id}] {message}")
```

### Step 2.2: Create FastAPI App

**File: `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Personalized Learning Path System",
    version="1.0.0",
    description="Multi-Agent AI Learning System with KG + LLM"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/learner/profile/create")
async def create_profile(query: str, pretest_score: float = 0.5):
    return {
        "learner_id": "test_001",
        "goal": query,
        "skill_level": "INTERMEDIATE"
    }

@app.get("/")
async def root():
    return {"message": "Welcome to Personalized Learning Path System"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

### Step 2.3: Test Backend

```bash
cd backend
python main.py

# In another terminal, test the API
curl http://localhost:8000/health
# Response: {"status":"healthy","version":"1.0.0"}
```

---

## PHASE 3: SIMPLE FRONTEND (8 phút)

### Step 3.1: Create Learner Dashboard

**File: `frontend/app/page.tsx`**

```typescript
'use client'

import { useState } from 'react'

export default function Home() {
  const [loading, setLoading] = useState(false)
  const [learnerId, setLearnerId] = useState('')

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    
    const query = (e.target as any).query.value
    const pretest = parseFloat((e.target as any).pretest.value)

    try {
      const res = await fetch('http://localhost:8000/api/learner/profile/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, pretest_score: pretest })
      })
      
      const data = await res.json()
      setLearnerId(data.learner_id)
      alert('Profile created! ID: ' + data.learner_id)
    } catch (error) {
      alert('Error: ' + error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 p-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-3xl font-bold mb-6">🎓 Learning Path Creator</h1>
        
        <form onSubmit={handleCreateProfile} className="space-y-4">
          <div>
            <label className="block font-semibold mb-2">What do you want to learn?</label>
            <input 
              type="text" 
              name="query"
              placeholder="e.g., SQL Joins in 2 weeks"
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block font-semibold mb-2">Pre-test Score (0-1)</label>
            <input 
              type="number" 
              name="pretest"
              min="0" 
              max="1" 
              step="0.1"
              defaultValue="0.5"
              className="w-full px-4 py-2 border rounded-lg"
            />
          </div>

          <button 
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Learning Path 🚀'}
          </button>
        </form>

        {learnerId && (
          <div className="mt-4 p-4 bg-green-100 border border-green-400 rounded">
            <p className="text-sm">Your Learner ID: <code>{learnerId}</code></p>
          </div>
        )}
      </div>
    </main>
  )
}
```

### Step 3.2: Run Frontend

```bash
cd frontend
npm run dev

# Access at http://localhost:3000
```

---

## PHASE 4: QUICK INTEGRATION TEST (7 phút)

### Step 4.1: Test Full Flow

```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Test with curl
curl -X POST http://localhost:8000/api/learner/profile/create \
  -H "Content-Type: application/json" \
  -d '{"query":"Learn SQL in 2 weeks","pretest_score":0.65}'

# Response:
# {
#   "learner_id": "test_001",
#   "goal": "Learn SQL in 2 weeks",
#   "skill_level": "INTERMEDIATE"
# }
```

### Step 4.2: Frontend Test

Visit `http://localhost:3000` and:
1. Enter "Learn SQL Joins in 14 days"
2. Set pre-test score to 0.65
3. Click "Create Learning Path 🚀"
4. See success message with learner ID

---

## 🎉 NEXT STEPS - TÍCH HỢP AGENTS

Sau khi confirm mọi thứ hoạt động:

### 1. Add LLM Integration (5 phút)

**File: `backend/services/llm_service.py`**

```python
from openai import AsyncOpenAI
import os

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    async def complete(self, prompt: str, **kwargs):
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content

# Usage
llm = LLMService()
result = await llm.complete("Extract learning goal from: Learn SQL in 2 weeks")
print(result)
```

### 2. Add Knowledge Extraction Agent (10 phút)

**File: `backend/agents/knowledge_extraction.py`**

```python
from agents.base import BaseAgent
import json

class KnowledgeExtractionAgent(BaseAgent):
    async def execute(self, query: str) -> Dict:
        prompt = f"""
Extract learning information from: "{query}"

Return JSON:
{{
    "goal": "specific learning goal",
    "time_days": <number>,
    "style": "VISUAL|AUDITORY|READING|KINESTHETIC"
}}
"""
        result = await self.llm.complete(prompt)
        return json.loads(result)

# Usage
agent = KnowledgeExtractionAgent("extractor", llm)
result = await agent.execute("Learn SQL in 2 weeks")
# Output: {"goal": "SQL", "time_days": 14, "style": "VISUAL"}
```

### 3. Hook Agent to API

**Update `backend/main.py`**

```python
from services.llm_service import LLMService
from agents.knowledge_extraction import KnowledgeExtractionAgent

llm_service = LLMService()

@app.post("/api/learner/profile/create")
async def create_profile(query: str, pretest_score: float = 0.5):
    # Use agent!
    extractor = KnowledgeExtractionAgent("extractor", llm_service)
    parsed = await extractor.execute(query)
    
    return {
        "learner_id": "test_001",
        "goal": parsed['goal'],
        "time_days": parsed['time_days'],
        "skill_level": "INTERMEDIATE" if pretest_score >= 0.5 else "FOUNDATIONAL"
    }
```

---

## 🚀 GIT COMMIT WORKFLOW

```bash
# Initialize git repo
git config user.name "Your Name"
git config user.email "your@email.com"

# Make initial commit
git add .
git commit -m "Initial: Backend FastAPI + Frontend Next.js + Quick Start"

# Push to GitHub
git branch -M main
git push -u origin main

# Create feature branches for each agent
git checkout -b feat/profiler-agent
git checkout -b feat/planner-agent
git checkout -b feat/tutor-agent
```

---

## 📋 CHECKLIST HOÀN THÀNH

- [ ] Repository created on GitHub
- [ ] Backend running on `http://localhost:8000`
- [ ] Frontend running on `http://localhost:3000`
- [ ] API health check working
- [ ] Create profile form functional
- [ ] First commit pushed to main
- [ ] Docker services (postgres, neo4j, redis) running
- [ ] Environment variables configured

---

## 🆘 TROUBLESHOOTING

### Backend won't start
```bash
# Check port 8000 not in use
lsof -i :8000
# Kill if needed
kill -9 <PID>

# Reinstall dependencies
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Neo4j connection error
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Check logs
docker logs <neo4j-container-id>

# Reset Neo4j
docker-compose down
docker volume rm <neo4j-volume>
docker-compose up -d neo4j
```

### CORS errors in frontend
- Make sure backend CORS middleware allows `http://localhost:3000`
- Check Origin header in browser console

---

## 📚 NEXT RESOURCES

1. **IMPLEMENTATION_GUIDE.md** - Full 12-week roadmap with all agents
2. **ARCHITECTURE_DECISIONS.md** - Why each technology choice
3. **API_SPECIFICATION.md** - OpenAPI docs
4. **TESTING_STRATEGY.md** - Unit + integration tests

---

## ⏱️ TIMELINE

- **5 min**: Setup + Docker
- **10 min**: Backend core + API
- **8 min**: Frontend UI
- **7 min**: Integration test
- **Total: 30 minutes** ✅

**Bây giờ bạn sẵn sàng để mở rộng với các agents khác!** 🚀
