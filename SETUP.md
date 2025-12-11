# Personalized Learning Path - Development Setup

## 🐍 Python Virtual Environment

### Prerequisites

- Python 3.11+
- pip (Python package manager)
- Git

### Create Virtual Environment

```bash
# Navigate to project root
cd Agentic-Personalized-LearningPath

# Create virtual environment
python -m venv venv

# Activate on Windows
.\venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### Install Dependencies

```bash
# With venv activated
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import langchain; print('LangChain:', langchain.__version__)"
```

### Deactivate Environment

```bash
deactivate
```

---

## 📦 Node.js Environment (Frontend)

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm or yarn

### Setup

```bash
cd frontend

# Install dependencies
npm install

# Verify
npm run dev
```

---

## 🐳 Docker Environment (Recommended for Production)

### Start All Services

```bash
# From project root
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Stop Services

```bash
docker-compose down

# With volumes removed
docker-compose down -v
```

---

## 🔧 Environment Variables

### Backend (.env)

```env
# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/learningpath

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379

# LLM
GOOGLE_API_KEY=your-api-key
LLM_MODEL=gemini-1.5-flash

# Chroma
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 🚀 Quick Start

### Option 1: Docker (Easiest)

```bash
docker-compose up -d
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Neo4j: http://localhost:7474
```

### Option 2: Manual Setup

```bash
# Terminal 1: Backend
cd Agentic-Personalized-LearningPath
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn backend.main:app --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

---

## 📝 Common Issues

### Virtual Environment Not Found

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# If still issues, try:
py -3.11 -m venv venv
```

### Port Already in Use

```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <PID> /F
```

### Module Not Found

```bash
# Ensure venv is activated
pip install -r requirements.txt

# Check Python path
which python  # Unix
where python  # Windows
```

---

## 🧪 Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests (if configured)
cd frontend
npm test
```

---

## 📁 Project Structure

```
Agentic-Personalized-LearningPath/
├── backend/
│   ├── agents/          # 6 AI Agents
│   ├── api/             # FastAPI routes
│   ├── core/            # Base classes, state manager
│   ├── database/        # DB connections
│   ├── models/          # Data models
│   └── main.py          # Entry point
├── frontend/
│   ├── app/             # Next.js pages
│   ├── components/      # React components
│   ├── hooks/           # Custom hooks
│   └── lib/             # API client, utilities
├── venv/                # Python virtual environment
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker configuration
└── README.md
```
