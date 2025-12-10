# 💬 ANTIGRAVITY AGENT PROMPTS - CÁC MESSAGE CẦN CHAT VÀO

**Cách dùng**: Copy-paste từng prompt vào khung chat AntiGravity Agent (bên phải)  
**Thứ tự**: Chạy lần lượt từ trên xuống  

---

## PROMPT SET 1: TẠOE FILE VỚI NOI DUNG

### 1️⃣ Tạo .gitignore

**Chat message:**
```
Create file: .gitignore
Location: /Agentic-Personalized-LearningPath/.gitignore

Content:
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

**Expected result**: ✅ .gitignore created in AntiGravity Explorer

---

### 2️⃣ Tạo requirements.txt

**Chat message:**
```
Create file: requirements.txt
Location: /Agentic-Personalized-LearningPath/requirements.txt

Content (Python dependencies):
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

**Expected result**: ✅ requirements.txt created

---

### 3️⃣ Tạo docker-compose.yml

**Chat message:**
```
Create file: docker-compose.yml
Location: /Agentic-Personalized-LearningPath/docker-compose.yml

Content:
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

**Expected result**: ✅ docker-compose.yml created

---

### 4️⃣ Tạo Dockerfile.backend

**Chat message:**
```
Create file: Dockerfile.backend
Location: /Agentic-Personalized-LearningPath/Dockerfile.backend

Content:
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

**Expected result**: ✅ Dockerfile.backend created

---

### 5️⃣ Tạo backend/__init__.py

**Chat message:**
```
Create file: backend/__init__.py
Location: /Agentic-Personalized-LearningPath/backend/__init__.py

Content:
"""
Agentic Personalized Learning Path Backend
"""

__version__ = "0.1.0"
```

**Expected result**: ✅ backend/__init__.py created (marks folder as package)

---

### 6️⃣ Tạo backend/config.py

**Chat message:**
```
Create file: backend/config.py
Location: /Agentic-Personalized-LearningPath/backend/config.py

Content:
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

**Expected result**: ✅ backend/config.py created

---

### 7️⃣ Tạo backend/main.py

**Chat message:**
```
Create file: backend/main.py
Location: /Agentic-Personalized-LearningPath/backend/main.py

Content:
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

**Expected result**: ✅ backend/main.py created with health endpoints

---

## PROMPT SET 2: FOLDER CREATION

### 8️⃣ Tạo Backend Subfolders

**Chat message:**
```
Create the following folder structure in AntiGravity Explorer:

/Agentic-Personalized-LearningPath/backend/
  ├── agents/
  ├── core/
  ├── models/
  ├── database/
  └── api/

Then create __init__.py files in each subfolder to make them packages.
```

**Expected result**: ✅ All subfolders created with __init__.py in each

---

### 9️⃣ Tạo Frontend Folder Structure

**Chat message:**
```
Create the following folder structure in AntiGravity Explorer:

/Agentic-Personalized-LearningPath/frontend/
  ├── app/
  │   ├── (dashboard)/
  │   ├── (auth)/
  │   └── api/
  ├── components/
  ├── lib/
  ├── styles/
  └── public/

For now, we'll add content later. Just create the empty folders.
```

**Expected result**: ✅ Frontend folder structure ready

---

### 🔟 Tạo Docs Folder

**Chat message:**
```
Create folder: /Agentic-Personalized-LearningPath/docs/

This will hold:
- QUICK_START.md
- IMPLEMENTATION_GUIDE.md
- ARCHITECTURE_DECISIONS.md
```

**Expected result**: ✅ docs/ folder created

---

## PROMPT SET 3: GIT OPERATIONS (VỚI TERMINAL)

### 1️⃣1️⃣ Initialize Git & Connect to GitHub

**Chạy trong Terminal (AntiGravity):**

```bash
# Navigate to project folder
cd /path/to/Agentic-Personalized-LearningPath

# Initialize Git
git init

# Configure user (nếu chưa config)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Connect to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/Agentic-Personalized-LearningPath.git

# Verify connection
git remote -v
# Output should show:
# origin  https://github.com/YOUR_USERNAME/Agentic-Personalized-LearningPath.git (fetch)
# origin  https://github.com/YOUR_USERNAME/Agentic-Personalized-LearningPath.git (push)
```

**Expected result**: ✅ Local git configured and connected to remote GitHub

---

### 1️⃣2️⃣ First Commit & Push

**Chạy trong Terminal:**

```bash
# Check status
git status

# Add all files
git add .

# Create commit
git commit -m "🎉 Initial commit: Setup project structure

- Initialize project structure with backend/frontend folders
- Add Docker Compose for PostgreSQL, Neo4j, Redis, Chroma
- Create FastAPI application with health check endpoints
- Add Python requirements and dependencies
- Configure environment setup
- Add documentation stubs (to be filled)

Phase: 1/3 (Setup) ✅
Ready for: Backend agents development
"

# Push to GitHub (main branch)
git push -u origin main

# If error 'main' branch not found:
# git push -u origin master
# Then on GitHub, change default branch to main
```

**Expected result**: ✅ All files pushed to GitHub, visible in browser

---

## PROMPT SET 4: VERIFY SETUP

### 1️⃣3️⃣ Verify Docker Compose

**Chạy trong Terminal:**

```bash
# Build all Docker images
docker-compose build

# Start all services in background
docker-compose up -d

# Check status (should all be "Up")
docker-compose ps

# Test FastAPI health endpoint
curl http://localhost:8000/health

# Expected output:
# {
#   "status": "healthy",
#   "version": "0.1.0",
#   "message": "✅ Agentic Learning Path API is running"
# }

# Test Neo4j is running
curl http://localhost:7474

# Stop all services
docker-compose down
```

**Expected result**: ✅ All services start and health checks pass

---

## 🎯 QUICK COMMAND REFERENCE

**Thường dùng nhất:**

```bash
# Start everything
docker-compose up -d

# Check logs
docker-compose logs backend
docker-compose logs neo4j

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/docs   # Swagger UI

# Stop everything
docker-compose down

# Git push changes
git add .
git commit -m "Your message"
git push

# View git history
git log --oneline
```

---

## ⏰ TIMELINE

| # | Action | Time | Tool |
|---|--------|------|------|
| 1-2 | Create .gitignore, requirements.txt | 2 min | AntiGravity Chat |
| 3-4 | Create docker-compose.yml, Dockerfile | 3 min | AntiGravity Chat |
| 5-7 | Create backend files (init, config, main) | 5 min | AntiGravity Chat |
| 8-10 | Create folder structure | 5 min | AntiGravity Explorer |
| 11-12 | Git init, commit, push | 10 min | Terminal |
| 13 | Verify Docker & API | 5 min | Terminal + Browser |
| **TOTAL** | **Phase 1 Complete** | **30-45 min** | |

---

## ✅ COMPLETION CHECKLIST

Sau khi chạy hết tất cả prompts trên:

- [ ] .gitignore created
- [ ] requirements.txt created
- [ ] docker-compose.yml created
- [ ] Dockerfile.backend created
- [ ] backend/__init__.py created
- [ ] backend/config.py created
- [ ] backend/main.py created
- [ ] backend subfolders created (agents, core, models, database, api)
- [ ] frontend folder structure created
- [ ] docs/ folder created
- [ ] Git initialized locally
- [ ] Git connected to GitHub
- [ ] All files committed
- [ ] All files pushed to GitHub
- [ ] Docker Compose verified (all services up)
- [ ] API health check working (✅ response)

**When all checked**: Phase 1 is COMPLETE! 🎉

---

## 💡 TIPS

1. **Copy prompts exactly** - Don't modify content unless needed
2. **One prompt at a time** - Wait for folder/file to appear in AntiGravity before next
3. **Check Terminal output** - Verify no errors
4. **GitHub refresh** - Wait 10-20 sec after push, then refresh browser to see changes
5. **Docker troubleshooting**:
   - Port already in use? Check: `lsof -i :8000`
   - Container won't start? Check: `docker-compose logs [service-name]`
   - Network issue? Try: `docker network prune`

---

**Ready? Start from PROMPT 1 above! 🚀**
