# 🚀 SETUP AGENTIC-PERSONALIZED-LEARNINGPATH - STEP-BY-STEP GUIDE FOR ANTIGRAVITY

**Thời gian**: 45 phút  
**Công cụ**: AntiGravity + Terminal + GitHub  
**Kết quả**: Folder structure hoàn thiện + Remote GitHub repo  

---

## PHASE 0: CHUẨN BỊ (5 phút)

### Bước 1: Tại sao cần chuẩn bị?
```
Folder hiện tại: Agentic-Personalized-LearningPath/  (trống)
    ↓
Sau phase này:
    Agentic-Personalized-LearningPath/
    ├── .git/                          ← GitHub repo
    ├── .gitignore
    ├── README.md
    ├── requirements.txt
    ├── docker-compose.yml
    ├── backend/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── agents/
    │   ├── core/
    │   └── ...
    ├── frontend/
    │   ├── package.json
    │   ├── app/
    │   └── ...
    └── docs/
        ├── QUICK_START.md
        ├── IMPLEMENTATION_GUIDE.md
        └── ARCHITECTURE_DECISIONS.md
```

### Bước 2: Kiểm tra chuẩn bị
Mở Terminal trong AntiGravity (`Ctrl+`` hoặc Menu → Terminal)

Chạy lệnh:
```bash
git --version
python --version
node --version
docker --version
```

✅ Nếu tất cả chạy OK → Bắt đầu Phase 1
❌ Nếu thiếu công cụ → Cài đặt trước

---

## PHASE 1: GITHUB SETUP (10 phút)

### Bước 3: Tạo GitHub Repository

**3a. Trên GitHub Web (github.com)**
```
1. Đăng nhập GitHub account của bạn
2. Click "New" (nút xanh, top-left)
3. Repository name: Agentic-Personalized-LearningPath
4. Description: "Multi-Agent AI system for personalized learning paths using KG, LLM, and RL"
5. Visibility: Public ✅ (để advisor review)
6. Initialize repository: 
   - ❌ DO NOT check "Add a README file"
   - ❌ DO NOT check "Add .gitignore"
   - ❌ DO NOT check "Choose a license"
   → Để blank, vì chúng ta sẽ push từ local
7. Click "Create repository"

Copy URL từ "Quick setup" (HTTPS):
https://github.com/YOUR_USERNAME/Agentic-Personalized-LearningPath.git
```

**3b. Trong AntiGravity Terminal**
```bash
# Vào folder project
cd /path/to/Agentic-Personalized-LearningPath

# Khởi tạo Git
git init

# Kết nối với GitHub
git remote add origin https://github.com/YOUR_USERNAME/Agentic-Personalized-LearningPath.git

# Kiểm tra
git remote -v
# Output:
# origin  https://github.com/YOUR_USERNAME/Agentic-Personalized-LearningPath.git (fetch)
# origin  https://github.com/YOUR_USERNAME/Agentic-Personalized-LearningPath.git (push)
```

---

## PHASE 2: ROOT FILES (10 phút)

### Bước 4: Tạo file gốc (.gitignore, requirements.txt, docker-compose.yml)

**4a. .gitignore** (để GitHub không track những file không cần)

File: `Agentic-Personalized-LearningPath/.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment variables
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite3

# LLM / API Keys
.openai_key
.api_keys

# Node
node_modules/
npm-debug.log
dist/
.next/

# Docker
docker-compose.override.yml

# OS
.DS_Store
Thumbs.db
```

**4b. requirements.txt** (Python dependencies)

File: `Agentic-Personalized-LearningPath/requirements.txt`

```
# Core
python-dotenv==1.0.0

# FastAPI
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# LLM & Agents
llama-index==0.9.48
llama-index-core==0.10.1
llama-index-llms-openai==0.1.9
llama-index-vector-stores-chroma==0.1.11
openai==1.13.3

# Knowledge Graph
neo4j==5.15.0

# Vector DB
chromadb==0.4.24

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1

# Data Processing
pandas==2.1.4
numpy==1.26.3

# Testing
pytest==7.4.4
pytest-asyncio==0.23.2
httpx==0.25.2

# Utilities
requests==2.31.0
aiohttp==3.9.1
```

**4c. docker-compose.yml** (Services: FastAPI, PostgreSQL, Neo4j, Redis, Chroma)

File: `Agentic-Personalized-LearningPath/docker-compose.yml`

```yaml
version: '3.8'

services:
  # FastAPI Backend
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: agentic-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/learning_db
      - REDIS_URL=redis://redis:6379
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=testpassword
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - neo4j
      - redis
      - chroma
    volumes:
      - ./backend:/app/backend
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

  # PostgreSQL (State Management)
  postgres:
    image: postgres:16-alpine
    container_name: agentic-postgres
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=learning_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d learning_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Neo4j (Knowledge Graph)
  neo4j:
    image: neo4j:5.15-community
    container_name: agentic-neo4j
    environment:
      - NEO4J_AUTH=neo4j/testpassword
      - NEO4J_apoc_import_file_enabled=true
      - NEO4J_PLUGINS=["apoc"]
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/var/lib/neo4j/data
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:7474"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis (Caching)
  redis:
    image: redis:7-alpine
    container_name: agentic-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Chroma (Vector Database for RAG)
  chroma:
    image: ghcr.io/chroma-core/chroma:latest
    container_name: agentic-chroma
    ports:
      - "8001:8000"
    environment:
      - ANONYMIZED_TELEMETRY=false
    volumes:
      - chroma_data:/chroma/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Next.js Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: agentic-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
    command: npm run dev

volumes:
  postgres_data:
  neo4j_data:
  redis_data:
  chroma_data:
```

**4d. Dockerfile.backend** (Build backend image)

File: `Agentic-Personalized-LearningPath/Dockerfile.backend`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend ./backend

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**4e. README.md** (Project overview)

File: `Agentic-Personalized-LearningPath/README.md`

```markdown
# 🚀 Agentic-Personalized-Learning-Path

A production-ready **Multi-Agent AI system** for adaptive learning path generation using:
- **Knowledge Graphs (Neo4j)** for domain structure
- **Large Language Models (LLM)** for intelligent tutoring
- **Reinforcement Learning** for dynamic path optimization
- **Harvard 2025 Pedagogical Principles** for evidence-based design

## 📊 Architecture

```
Frontend (Next.js 14)
    ↓
API Gateway (FastAPI)
    ↓
6 Specialized Agents (LlamaIndex + AgentWorkflow)
    ↓
Knowledge Systems (Neo4j, Chroma) + Data (PostgreSQL, Redis)
```

## 🎯 Features

✅ Multi-agent architecture (6 specialized agents)  
✅ Knowledge graph-based domain modeling  
✅ RAG (Retrieval-Augmented Generation) with 3-layer grounding  
✅ Reinforcement learning path planning (MOPO-like)  
✅ Zettelkasten knowledge artifact generation  
✅ Harvard 7 pedagogical principles enforcement  
✅ Dual-KG (Course + Personal)  
✅ Production-ready code + Docker support  

## 🏃 Quick Start

```bash
# 1. Clone and enter folder
git clone https://github.com/YOUR_USERNAME/Agentic-Personalized-LearningPath.git
cd Agentic-Personalized-LearningPath

# 2. Set environment
export OPENAI_API_KEY=sk-...

# 3. Start all services
docker-compose up -d

# 4. Check health
curl http://localhost:8000/health
curl http://localhost:3000

# 5. Stop services
docker-compose down
```

## 📁 Folder Structure

```
Agentic-Personalized-LearningPath/
├── backend/
│   ├── agents/           # 6 specialized agents
│   ├── core/             # Core infrastructure
│   ├── models/           # Pydantic models
│   ├── database/         # DB integrations
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI app
├── frontend/
│   ├── app/              # Next.js app router
│   ├── components/       # React components
│   └── package.json
├── docs/
│   ├── QUICK_START.md
│   ├── IMPLEMENTATION_GUIDE.md
│   └── ARCHITECTURE_DECISIONS.md
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 📚 Documentation

- **QUICK_START.md** - Get running in 30 min
- **IMPLEMENTATION_GUIDE.md** - Detailed code structure (12 weeks)
- **ARCHITECTURE_DECISIONS.md** - Why each tech choice

## 🎓 Research Foundation

- Harvard 2025: "AI Tutoring Outperforms In-Class Active Learning"
- Dartmouth 2025: "Precision Education at Scale"
- Google DeepMind 2024: LearnLM (5 principles)

## 📧 Contact

- Advisor: [Your Advisor]
- Author: [Your Name]
- GitHub: [Your GitHub]

---

**Status**: Phase 1 (Setup) ✅  
**Next**: Phase 2 (Core backend) 🔄  
**Timeline**: 12 weeks to MVP
```

---

## PHASE 3: FOLDER STRUCTURE (10 phút)

### Bước 5: Tạo Backend Folder Structure

**5a. Tạo các thư mục**

Trong AntiGravity Explorer, tạo folders sau (right-click → New Folder):

```
backend/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── knowledge_extraction_agent.py
│   ├── profiler_agent.py
│   ├── planner_agent.py
│   ├── tutor_agent.py
│   ├── evaluator_agent.py
│   └── kag_agent.py
├── core/
│   ├── __init__.py
│   ├── state_manager.py
│   ├── event_bus.py
│   ├── grounding_system.py
│   └── rl_planner.py
├── models/
│   ├── __init__.py
│   ├── schemas.py
│   └── enums.py
├── database/
│   ├── __init__.py
│   ├── neo4j_client.py
│   ├── postgres_client.py
│   └── redis_client.py
├── api/
│   ├── __init__.py
│   ├── routes.py
│   └── dependencies.py
├── __init__.py
├── config.py
├── main.py
└── requirements.txt (copy from root)
```

**5b. Tạo Frontend Folder Structure**

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── (auth)/
│   │   ├── login/
│   │   └── signup/
│   └── api/
│       ├── proxy/
│       └── health/
├── components/
│   ├── ChatInterface.tsx
│   ├── LearningPath.tsx
│   ├── Dashboard.tsx
│   └── shared/
├── lib/
│   ├── api.ts
│   └── utils.ts
├── styles/
│   └── globals.css
├── package.json
├── next.config.js
├── tsconfig.json
└── .gitignore
```

**5c. Tạo Docs Folder**

```
docs/
├── QUICK_START.md
├── IMPLEMENTATION_GUIDE.md
├── ARCHITECTURE_DECISIONS.md
└── API_REFERENCE.md
```

### Bước 6: Tạo Main Python Files

**6a. backend/__init__.py** (Empty file to mark as package)

```python
"""
Agentic Personalized Learning Path Backend
"""

__version__ = "0.1.0"
```

**6b. backend/config.py** (Configuration management)

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application configuration"""
    
    # API
    API_TITLE: str = "Agentic Learning Path API"
    API_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/learning_db"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "testpassword"
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    
    # Chroma
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

**6c. backend/main.py** (FastAPI entry point)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.config import get_settings

logger = logging.getLogger(__name__)

# Initialization on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("🚀 Starting Agentic Learning Path API...")
    # Startup code
    yield
    logger.info("🛑 Shutting down...")
    # Cleanup code

# Create FastAPI app
app = FastAPI(
    title="Agentic Learning Path API",
    description="Multi-Agent AI system for personalized learning paths",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "message": "✅ Agentic Learning Path API is running"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "🚀 Welcome to Agentic Learning Path API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## PHASE 4: GIT COMMIT (10 phút)

### Bước 7: First Commit to GitHub

**7a. Trong AntiGravity Terminal**

```bash
# Navigate to project
cd /path/to/Agentic-Personalized-LearningPath

# Check status
git status
# Should show: Untracked files: ...

# Add all files
git add .

# Commit
git commit -m "🎉 Initial commit: Setup project structure, Docker, and base FastAPI

- Initialize project structure with backend/frontend folders
- Add Docker Compose for PostgreSQL, Neo4j, Redis, Chroma
- Create FastAPI application with health check endpoints
- Add Python requirements and dependencies
- Configure environment setup
- Add documentation stubs

Phase: 1/3 (Setup complete)
"

# Push to GitHub
git push -u origin main
# Note: If main branch doesn't exist, might need:
# git push -u origin master
# Then on GitHub, set default branch to main
```

**7b. Verify on GitHub**

Mở browser → https://github.com/YOUR_USERNAME/Agentic-Personalized-LearningPath

✅ Bạn sẽ thấy:
- Tất cả files đã push
- Green checkmark next to commit
- README.md displayed nicely

---

## PHASE 5: LOCAL TESTING (5 phút)

### Bước 8: Test Docker Setup

**8a. Verify Docker Compose**

```bash
# Build images
docker-compose build

# Start services (background)
docker-compose up -d

# Check status
docker-compose ps
# Output should show: 
# STATUS: Up X seconds (all services healthy)

# Check logs
docker-compose logs backend
# Look for: "Uvicorn running on http://0.0.0.0:8000"

# Test API
curl http://localhost:8000/health
# Output:
# {
#   "status": "healthy",
#   "version": "0.1.0",
#   "message": "✅ Agentic Learning Path API is running"
# }

# Stop services
docker-compose down
```

---

## 📋 CHECKLIST - PHASE 1 COMPLETE?

Đánh dấu khi hoàn thành:

- [ ] GitHub repository created (public, blank)
- [ ] Local git initialized (`git init`)
- [ ] Remote connected (`git remote add origin`)
- [ ] .gitignore created
- [ ] requirements.txt created
- [ ] docker-compose.yml created
- [ ] Dockerfile.backend created
- [ ] README.md created
- [ ] backend/ folder structure created
- [ ] frontend/ folder structure created (basic)
- [ ] docs/ folder created
- [ ] backend/__init__.py created
- [ ] backend/config.py created
- [ ] backend/main.py created
- [ ] First commit pushed to GitHub ✅
- [ ] Docker Compose test passed (all services up)

---

## ✅ NEXT STEP

**Khi Phase 1 hoàn thành:**

1. Mở file **QUICK_START.md** (sẽ tạo ở bước sau)
2. Follow Phase 2-4 để build agents
3. Integrate với databases
4. Test full loop

---

## 🎯 SUMMARY

Bạn vừa setup:

✅ **GitHub Repository** - Public, ready for advisor review  
✅ **Project Structure** - Production-ready folders  
✅ **Docker Infrastructure** - All services (FastAPI, PostgreSQL, Neo4j, Redis, Chroma)  
✅ **Base FastAPI** - Health check endpoints working  
✅ **First Commit** - Everything pushed to GitHub  

**Folder size**: ~2-3 MB (mostly docker configs)  
**Ready for**: Phase 2 (Build core agents)

---

**Thời gian hoàn thành Phase 1**: ~45 phút  
**Độ khó**: ⭐⭐ (Moderate - mostly folder creation)  
**Lỗi thường gặp**: 
- Git remote URL sai → Kiểm tra: `git remote -v`
- Docker not installed → Cài từ docker.com
- Port 8000/3000 bị dùng → Đổi trong docker-compose.yml

---

**Bạn ready chưa? Chat lại khi hoàn thành Phase 1!** 🚀
