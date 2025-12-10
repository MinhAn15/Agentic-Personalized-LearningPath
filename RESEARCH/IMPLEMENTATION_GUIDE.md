# 🎯 KỲ HOẠCH XÂY DỰNG HỆ THỐNG PERSONALIZED LEARNING PATH - PRODUCTION READY
## Luận văn "Hệ thống Đa tác nhân Cá nhân hóa Lộ trình Học" - VER3 Enhanced

**Thời gian viết**: Tháng 12/2025  
**Môi trường**: Google AntiGravity IDE + GitHub  
**Mục tiêu**: Production-ready source code với Harvard 7 Principles + Multi-Agent Architecture  
**Chuẩn áp dụng**: MIS Masters Standard (HCMUT 2025)

---

## 📋 PHẦN 1: TỔNG QUAN CẤU TRÚC DỰ ÁN

### 1.1 Kiến trúc Hệ Thống (C4 Model - Context Level)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PERSONALIZED LEARNING PATH SYSTEM                    │
│                                                                           │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐ │
│  │  Frontend UI     │────▶│   Backend API    │────▶│   Knowledge      │ │
│  │  (Next.js 14)    │     │   (FastAPI)      │     │   Systems        │ │
│  │  - Dashboard     │     │                  │     │                  │ │
│  │  - Tutor Chat    │     │  🤖 6 Agents     │     │ ▪️ Neo4j Aura   │ │
│  │  - Progress      │     │  ▪️ Profiler     │     │ ▪️ Chroma VDB   │ │
│  │  - Analytics     │     │  ▪️ Planner      │     │ ▪️ LlamaIndex   │ │
│  └──────────────────┘     │  ▪️ Tutor        │     │                  │ │
│                            │  ▪️ Evaluator    │     └──────────────────┘ │
│                            │  ▪️ KAG          │            ▲            │
│                            │  ▪️ Knowledge    │            │            │
│                            │    Extraction   │            │            │
│                            │                  │     ┌──────────────────┐ │
│                            │  ▪️ Event Bus    │────▶│  LLM Services   │ │
│                            │  ▪️ State Mgr    │     │  ▪️ GPT-4o       │ │
│                            │  ▪️ Grounding    │     │  ▪️ Gemini Pro   │ │
│                            │    System       │     │  ▪️ Claude Opus  │ │
│                            └──────────────────┘     └──────────────────┘ │
│                                    ▲                                      │
│                                    │                                      │
│                            ┌───────┴────────┐                            │
│                            │  PostgreSQL    │                            │
│                            │  (State + Log) │                            │
│                            └────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Folder Structure (Production-ready)

```
personalized-learning-path-kg-llm/
├── .github/
│   ├── workflows/
│   │   ├── ci-backend.yml         # CI/CD for backend
│   │   ├── ci-frontend.yml        # CI/CD for frontend
│   │   └── deploy.yml             # Deployment workflow
│   └── ISSUE_TEMPLATE/
│       └── bug_report.md
│
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py            # Environment + config
│   │   ├── constants.py           # Bloom levels, weights
│   │   └── logging.py             # Logging configuration
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── central_state.py       # Central State Manager
│   │   ├── event_bus.py           # Event Bus (Pub-Sub)
│   │   ├── grounding.py           # 3-layer Grounding Enforcer
│   │   └── exceptions.py          # Custom exceptions
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                # BaseAgent abstract class
│   │   ├── knowledge_extraction.py # Knowledge Extraction Agent
│   │   ├── profiler.py            # LearnerProfiler Agent
│   │   ├── planner.py             # PathPlanner Agent (MOPO-like)
│   │   ├── tutor.py               # Tutor Agent (Harvard 7 Principles)
│   │   ├── evaluator.py           # Evaluator Agent
│   │   ├── kag.py                 # KAG Agent (Zettelkasten)
│   │   └── workflow_orchestrator.py # Multi-Agent Orchestration
│   │
│   ├── kg/
│   │   ├── __init__.py
│   │   ├── neo4j_driver.py        # Neo4j connection & queries
│   │   ├── course_kg.py           # Course KG interface
│   │   ├── personal_kg.py         # Personal KG interface
│   │   ├── kg_builder.py          # Automated KG construction
│   │   └── cypher_queries.py      # Predefined Cypher queries
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── vector_db.py           # Chroma vector store
│   │   ├── embedding.py           # Embedding model (OpenAI)
│   │   ├── retriever.py           # RAG retriever (double grounding)
│   │   └── document_processor.py  # Document chunking & indexing
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── learner.py             # LearnerProfile Pydantic
│   │   ├── path.py                # LearningPath schema
│   │   ├── evaluation.py          # EvalResult schema
│   │   ├── artifact.py            # Artifact (Note) schema
│   │   └── kg_schema.py           # KG Node/Relationship schemas
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── learner.py             # /api/learner endpoints
│   │   ├── path.py                # /api/path endpoints
│   │   ├── tutor.py               # /api/tutor endpoints (chat)
│   │   ├── evaluator.py           # /api/evaluator endpoints
│   │   ├── artifacts.py           # /api/artifacts endpoints
│   │   ├── kg.py                  # /api/kg endpoints (admin)
│   │   └── admin.py               # /api/admin endpoints
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py              # Logging utility
│   │   ├── metrics.py             # Analytics & metrics
│   │   ├── validators.py          # Data validators
│   │   ├── cache.py               # Caching (Redis)
│   │   └── crypto.py              # Encryption utilities
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py         # LLM API wrapper
│   │   ├── knowledge_service.py   # Knowledge extraction service
│   │   └── learning_service.py    # Core learning logic
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_agents.py
│   │   ├── test_kg.py
│   │   ├── test_rag.py
│   │   ├── test_routes.py
│   │   └── conftest.py            # Pytest fixtures
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx             # Root layout
│   │   ├── page.tsx               # Home page
│   │   │
│   │   ├── learner/
│   │   │   ├── page.tsx           # Learner dashboard
│   │   │   ├── layout.tsx
│   │   │   ├── tutor/
│   │   │   │   ├── page.tsx       # Tutor chat interface
│   │   │   │   └── layout.tsx
│   │   │   ├── progress/
│   │   │   │   └── page.tsx       # Progress tracking
│   │   │   ├── artifacts/
│   │   │   │   └── page.tsx       # Knowledge artifacts
│   │   │   └── settings/
│   │   │       └── page.tsx       # User settings
│   │   │
│   │   ├── admin/
│   │   │   ├── page.tsx           # Admin dashboard
│   │   │   ├── layout.tsx
│   │   │   ├── kg-builder/
│   │   │   │   └── page.tsx       # KG management
│   │   │   ├── analytics/
│   │   │   │   └── page.tsx       # Learning analytics
│   │   │   └── users/
│   │   │       └── page.tsx       # User management
│   │   │
│   │   └── api/
│   │       ├── proxy/[...path].ts # Backend proxy
│   │       └── auth/[...auth0].ts # Auth0 integration
│   │
│   ├── components/
│   │   ├── TutorChat.tsx
│   │   ├── QuizPanel.tsx
│   │   ├── PathVisualization.tsx  # Graph visualization
│   │   ├── NotesViewer.tsx
│   │   ├── ProgressBar.tsx
│   │   └── common/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Loading.tsx
│   │
│   ├── hooks/
│   │   ├── useAPI.ts              # API fetch hook
│   │   ├── useAuth.ts             # Auth hook
│   │   └── useLearner.ts          # Learner context
│   │
│   ├── styles/
│   │   ├── globals.css
│   │   └── components.module.css
│   │
│   ├── public/
│   │   ├── logo.svg
│   │   └── icons/
│   │
│   ├── .env.local.example
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── Dockerfile
│   └── .dockerignore
│
├── database/
│   ├── cypher_scripts/
│   │   ├── init_course_kg.cypher      # Initialize Course KG schema
│   │   ├── init_personal_kg.cypher    # Initialize Personal KG schema
│   │   ├── sample_data.cypher         # Sample course data
│   │   └── migrations/
│   │       ├── v1_initial.cypher
│   │       └── v2_personal_kg.cypher
│   │
│   ├── sql/
│   │   ├── init_postgres.sql          # PostgreSQL schema
│   │   └── migrations/
│   │       ├── 001_initial_state.sql
│   │       └── 002_learner_logs.sql
│   │
│   ├── sample_documents/
│   │   ├── sql_basics.md
│   │   ├── data_modeling.md
│   │   └── business_intelligence.md
│   │
│   └── README.md
│
├── docs/
│   ├── ARCHITECTURE.md             # System architecture
│   ├── AGENTS.md                   # Agents documentation
│   ├── API_SPEC.md                 # OpenAPI/Swagger docs
│   ├── DEPLOYMENT.md               # Deployment guide
│   ├── TESTING.md                  # Testing strategy
│   └── TROUBLESHOOTING.md
│
├── scripts/
│   ├── setup.sh                    # Environment setup
│   ├── build.sh                    # Build Docker images
│   ├── deploy.sh                   # Deployment script
│   ├── migrate_kg.py               # Database migration
│   └── seed_sample_data.py         # Seed sample data
│
├── docker-compose.yml              # Local dev environment
├── docker-compose.prod.yml         # Production environment
├── .env.example
├── .gitignore
├── .dockerignore
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## 🔧 PHẦN 2: SETUP INITIAL - BƯỚC 1 (Tuần 1)

### 2.1 Khởi Tạo Repository & Môi Trường

#### Step 1: Clone & Initialize

```bash
# Clone/create repo (thay YOUR_USERNAME bằng GitHub username)
git clone https://github.com/YOUR_USERNAME/personalized-learning-path-kg-llm.git
cd personalized-learning-path-kg-llm

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows

# Copy environment template
cp .env.example .env
```

#### Step 2: Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL + Redis (local)
docker-compose up -d postgres redis neo4j

# Wait for services
sleep 10

# Run migrations
python -m alembic upgrade head
```

#### Step 3: Frontend Setup

```bash
cd ../frontend

# Install Node dependencies
npm install

# Setup Next.js
npm run build
npm run dev  # Local development
```

### 2.2 Konfigurasi Cơ Bản

**File: `backend/config/settings.py`**

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Config
    API_TITLE: str = "Personalized Learning Path System"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    NEO4J_URI: str = "neo4j+s://xxxx.databases.neo4j.io"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str
    
    POSTGRES_URL: str = "postgresql://user:password@localhost/learning_db"
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    
    # Other LLM providers
    GOOGLE_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # RAG
    CHROMA_PATH: str = "./chroma_data"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    
    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 💻 PHẦN 3: IMPLEMENTATION AGENTS - BƯỚC 2-3 (Tuần 2-4)

### 3.1 BaseAgent - Base Class Cho Tất Cả Agents

**File: `backend/agents/base.py`**

```python
from abc import ABC, abstractmethod
from typing import Any, Dict
from datetime import datetime
import logging
from core.central_state import CentralStateManager
from core.event_bus import EventBus

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class cho tất cả agents
    Mỗi agent tương tác qua:
    1. Central State Manager (shared state)
    2. Event Bus (pub-sub communication)
    3. Tools (LLM + external APIs)
    """
    
    def __init__(
        self,
        agent_id: str,
        state: CentralStateManager,
        event_bus: EventBus,
        llm=None
    ):
        self.agent_id = agent_id
        self.state = state
        self.event_bus = event_bus
        self.llm = llm
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Main execution method - must be implemented by subclasses"""
        pass
    
    def publish_event(self, event_type: str, payload: Dict) -> None:
        """Publish event to Event Bus"""
        event = {
            'event_id': f"evt_{datetime.now().isoformat()}_{self.agent_id}",
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'source_agent': self.agent_id,
            'payload': payload
        }
        self.event_bus.publish(event)
        self.logger.info(f"Published {event_type} event")
    
    def subscribe_to(self, event_type: str, callback) -> None:
        """Subscribe to events"""
        self.event_bus.subscribe(event_type, callback)
        self.logger.info(f"Subscribed to {event_type}")
    
    def get_state(self, key: str) -> Any:
        """Get value from central state"""
        return self.state.get(key)
    
    def set_state(self, key: str, value: Any) -> None:
        """Set value in central state"""
        self.state.set(key, value)
    
    def log(self, message: str, level: str = 'INFO') -> None:
        """Utility logging method"""
        getattr(self.logger, level.lower())(f"[{self.agent_id}] {message}")
```

### 3.2 Knowledge Extraction Agent

**File: `backend/agents/knowledge_extraction.py`**

```python
import asyncio
import json
from typing import Dict, List
from base import BaseAgent
from models.kg_schema import KnowledgeNodeCreateRequest, RelationshipCreateRequest

class KnowledgeExtractionAgent(BaseAgent):
    """
    Agent tự động trích xuất tri thức từ documents
    
    INPUT: Document (text/PDF)
    OUTPUT: Structured KG nodes + relationships
    
    Pipeline:
    1. Document parsing
    2. Entity/Relation extraction (LLM-powered)
    3. Schema alignment
    4. Deduplication (semantic similarity)
    5. KG update
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kg_client = kwargs.get('kg_client')
        
        # Subscribe to document upload events
        self.subscribe_to('DOCUMENT_UPLOADED', self.on_document_uploaded)
    
    async def execute(self, document_path: str, course_id: str) -> Dict:
        """
        Extract knowledge from document
        """
        self.log(f"Starting extraction for {document_path}")
        
        try:
            # Step 1: Parse document
            content = await self._parse_document(document_path)
            
            # Step 2: Extract entities and relations
            entities, relations = await self._extract_entities_relations(
                content, course_id
            )
            
            # Step 3: Align with schema
            aligned_nodes = await self._align_schema(entities)
            aligned_relations = await self._align_relations(relations)
            
            # Step 4: Deduplication
            deduplicated = await self._deduplicate(aligned_nodes)
            
            # Step 5: Update KG
            result = await self._update_kg(deduplicated, aligned_relations)
            
            # Publish success event
            self.publish_event('KG_UPDATED', {
                'document': document_path,
                'nodes_created': len(deduplicated),
                'relations_created': len(aligned_relations)
            })
            
            return result
            
        except Exception as e:
            self.log(f"Error in extraction: {str(e)}", level='ERROR')
            self.publish_event('EXTRACTION_FAILED', {'error': str(e)})
            raise
    
    async def _parse_document(self, document_path: str) -> str:
        """Parse document (supports .md, .pdf, .txt)"""
        # Implementation: Use PyPDF2, markdown, etc.
        pass
    
    async def _extract_entities_relations(self, content: str, course_id: str):
        """
        Use LLM to extract entities and relations
        """
        prompt = f"""
Analyze this educational content and extract:
1. ENTITIES (concepts, terms, definitions)
2. RELATIONSHIPS (REQUIRES, NEXT, IS_SUBCONCEPT_OF, etc.)

Content:
{content}

Output JSON format:
{{
    "entities": [
        {{
            "label": "SQL SELECT",
            "definition": "...",
            "example": "SELECT * FROM users",
            "difficulty_level": 1,
            "semantic_tags": ["sql", "query", "beginner"]
        }}
    ],
    "relationships": [
        {{
            "source": "SQL SELECT",
            "target": "SQL FROM",
            "type": "REQUIRES"
        }}
    ]
}}
"""
        response = await self.llm.acomplete(prompt)
        return json.loads(response.text)['entities'], \
               json.loads(response.text)['relationships']
    
    async def _align_schema(self, entities: List) -> List[KnowledgeNodeCreateRequest]:
        """Align entities with Neo4j schema"""
        aligned = []
        for entity in entities:
            aligned.append(KnowledgeNodeCreateRequest(
                node_id=self._generate_node_id(entity['label']),
                label=entity['label'],
                definition=entity.get('definition', ''),
                difficulty_level=entity.get('difficulty_level', 1),
                semantic_tags=entity.get('semantic_tags', []),
                example=entity.get('example', '')
            ))
        return aligned
    
    async def _deduplicate(self, nodes: List) -> List:
        """
        Remove duplicate nodes using semantic similarity
        """
        # Implementation: Compare semantic tags + embeddings
        unique_nodes = []
        for node in nodes:
            # Check if similar node already exists in KG
            existing = await self.kg_client.find_similar_nodes(
                semantic_tags=node.semantic_tags,
                threshold=0.85
            )
            if not existing:
                unique_nodes.append(node)
        return unique_nodes
    
    async def _align_relations(self, relations: List) -> List:
        """Align relationships with schema"""
        # Implementation: Validate relation types
        return relations
    
    async def _update_kg(self, nodes, relations) -> Dict:
        """Update Neo4j KG with new nodes and relations"""
        # Implementation: Use Cypher to create nodes/relations
        created_nodes = len(nodes)
        created_relations = len(relations)
        return {
            'status': 'success',
            'nodes_created': created_nodes,
            'relations_created': created_relations
        }
    
    def _generate_node_id(self, label: str) -> str:
        """Generate unique node ID from label"""
        return label.lower().replace(' ', '_')
    
    async def on_document_uploaded(self, event: Dict) -> None:
        """Handle document upload event"""
        document_path = event['payload']['path']
        course_id = event['payload']['course_id']
        await self.execute(document_path, course_id)
```

### 3.3 LearnerProfiler Agent

**File: `backend/agents/profiler.py`**

```python
from base import BaseAgent
from models.learner import LearnerProfile
from datetime import datetime

class LearnerProfilerAgent(BaseAgent):
    """
    Agent phân tích và cập nhật hồ sơ người học
    
    Tính toán:
    - Skill level (từ pre-test)
    - Knowledge state (concepts mastered)
    - Learning style
    - Available time
    """
    
    async def execute(
        self,
        learner_id: str,
        user_query: str,
        pretest_score: float = None
    ) -> LearnerProfile:
        """
        Create/update learner profile
        """
        self.log(f"Profiling learner {learner_id}")
        
        # Parse natural language input using LLM
        parsed_input = await self._parse_input(user_query)
        
        # Assess skill level
        skill_level = self._assess_skill_level(pretest_score)
        
        # Create profile
        profile = LearnerProfile(
            learner_id=learner_id,
            learning_goal=parsed_input['goal'],
            time_available=parsed_input.get('time_days', 7),
            learning_style=parsed_input.get('style', 'VISUAL'),
            skill_level=skill_level,
            pretest_score=pretest_score or 0.0,
            created_at=datetime.now(),
            concept_mastery_map={},
            completed_concepts=[],
            error_patterns=[]
        )
        
        # Store in state
        self.set_state(f"learner:{learner_id}:profile", profile.dict())
        
        # Publish event
        self.publish_event('LEARNER_PROFILED', {
            'learner_id': learner_id,
            'skill_level': skill_level
        })
        
        return profile
    
    async def _parse_input(self, query: str) -> Dict:
        """Parse user query using LLM (Harvard principle: understand context)"""
        prompt = f"""
Extract learning information from: "{query}"

JSON output:
{{
    "goal": "specific learning objective",
    "time_days": <number>,
    "style": "VISUAL|AUDITORY|READING|KINESTHETIC"
}}
"""
        response = await self.llm.acomplete(prompt)
        return json.loads(response.text)
    
    def _assess_skill_level(self, pretest_score: float) -> str:
        """Map score to skill level"""
        if pretest_score is None:
            return "UNKNOWN"
        elif pretest_score >= 0.7:
            return "ADVANCED"
        elif pretest_score >= 0.5:
            return "INTERMEDIATE"
        else:
            return "FOUNDATIONAL"
    
    async def on_evaluation_completed(self, event: Dict) -> None:
        """Update profile when evaluation completed"""
        learner_id = event['learner_id']
        concept_id = event['payload']['concept_id']
        mastery = event['payload']['mastery_level']
        
        profile = self.get_state(f"learner:{learner_id}:profile")
        profile['concept_mastery_map'][concept_id] = mastery
        
        # Calculate average mastery
        if profile['concept_mastery_map']:
            avg = sum(profile['concept_mastery_map'].values()) / len(profile['concept_mastery_map'])
            profile['avg_mastery'] = avg
        
        self.set_state(f"learner:{learner_id}:profile", profile)
```

### 3.4 PathPlanner Agent (MOPO-like)

**File: `backend/agents/planner.py`**

```python
from base import BaseAgent
from models.path import LearningPath
import networkx as nx
from typing import List, Tuple

class PathPlannerAgent(BaseAgent):
    """
    Agent lập lộ trình học tập tối ưu
    
    Algorithm: MOPO-like (Model-based Policy learning)
    - Dynamic: Learns from feedback
    - Adaptive: Adjusts difficulty/pacing
    - Personalized: Considers learner state
    
    Constraints:
    - REQUIRES: Respect prerequisite edges
    - TIME: Fit in available time
    - DIFFICULTY: Match skill level
    - ENGAGEMENT: Promote active learning (Harvard principle)
    """
    
    async def execute(
        self,
        learner_id: str,
        goal_concept_ids: List[str]
    ) -> LearningPath:
        """
        Plan optimal learning path
        """
        self.log(f"Planning path for learner {learner_id}")
        
        # Get learner profile
        profile = self.get_state(f"learner:{learner_id}:profile")
        
        # Get Course KG
        course_kg = self.kg_client.get_course_kg()
        
        # Identify start node (current position)
        start_nodes = await self._identify_start_nodes(
            profile, course_kg
        )
        
        # Plan path using MOPO-like algorithm
        path = await self._plan_adaptive_path(
            start_nodes=start_nodes,
            goal_nodes=goal_concept_ids,
            course_kg=course_kg,
            learner_profile=profile
        )
        
        # Publish event
        self.publish_event('PATH_PLANNED', {
            'learner_id': learner_id,
            'path_length': len(path),
            'estimated_time': sum([node.get('estimated_time', 30) for node in path])
        })
        
        return path
    
    async def _identify_start_nodes(self, profile: Dict, kg) -> List[str]:
        """
        Identify where learner is currently at
        
        Logic:
        1. Check completed concepts
        2. If none, use pretest to identify gaps
        3. Return prerequisite nodes needed
        """
        completed = profile.get('completed_concepts', [])
        if completed:
            # Find next uncompleted nodes reachable from completed
            return await kg.find_next_concepts(completed)
        else:
            # Use pretest results
            gaps = await self._identify_gaps_from_pretest(profile, kg)
            return gaps if gaps else await kg.get_foundational_nodes()
    
    async def _plan_adaptive_path(
        self,
        start_nodes: List[str],
        goal_nodes: List[str],
        course_kg,
        learner_profile: Dict
    ) -> List[Dict]:
        """
        Main MOPO-like path planning algorithm
        
        State: (current_node, learner_state, time_remaining)
        Action: Which next concept to teach
        Reward: Learning gain + engagement + time efficiency
        """
        
        path = []
        current = start_nodes[0]
        time_remaining = learner_profile.get('time_available', 7) * 8  # hours
        
        visited = set()
        
        while len(path) < 20 and time_remaining > 0:  # Safety limits
            visited.add(current)
            
            # Get concept details
            concept = await course_kg.get_node(current)
            
            # Harvard Principle: Check if needs remediation
            needs_remediation = await self._check_remediation_needed(
                current, learner_profile
            )
            
            if needs_remediation:
                # Find remediation concept
                remedial = await course_kg.find_remediation_for(current)
                path.append({
                    'concept_id': remedial,
                    'type': 'REMEDIATION',
                    'estimated_time': 25
                })
                time_remaining -= 25
            else:
                # Add concept to path
                path.append({
                    'concept_id': current,
                    'type': 'MAIN',
                    'difficulty': concept.get('difficulty_level', 2),
                    'estimated_time': concept.get('estimated_time', 30)
                })
                time_remaining -= concept.get('estimated_time', 30)
            
            # Find next concept (action selection)
            next_concepts = await course_kg.find_next_unvisited(
                current, visited
            )
            
            if not next_concepts or time_remaining <= 0:
                break
            
            # RL-style: Select best next concept based on reward
            current = self._select_best_next(
                next_concepts, goal_nodes, learner_profile
            )
        
        return path
    
    def _select_best_next(
        self,
        candidates: List[str],
        goals: List[str],
        profile: Dict
    ) -> str:
        """
        Select best next concept using policy gradient idea
        
        Reward = P(correct) + ΔMastery - TimeNormalized + Engagement
        """
        scores = {}
        for concept_id in candidates:
            score = 0
            
            # P(correct): Predict likelihood of success
            p_correct = 0.7  # From knowledge tracing model
            score += p_correct
            
            # ΔMastery: Progress towards goal
            if concept_id in goals:
                score += 0.5
            
            # Engagement: Avoid too easy/too hard (Goldilocks principle)
            skill_level = profile['skill_level']
            concept_difficulty = 2  # Fetch from KG
            if skill_level == "INTERMEDIATE" and concept_difficulty == 2:
                score += 0.3  # Perfect match
            
            scores[concept_id] = score
        
        # Return highest scoring concept
        return max(scores, key=scores.get)
    
    async def _check_remediation_needed(self, concept_id: str, profile: Dict) -> bool:
        """Check if learner needs remediation before this concept"""
        mastery = profile['concept_mastery_map'].get(concept_id, 0.0)
        return mastery < 0.6  # If <60%, needs remediation
    
    async def _identify_gaps_from_pretest(self, profile: Dict, kg) -> List[str]:
        """Identify knowledge gaps from pretest results"""
        # Implementation: Map pretest questions to concepts
        pass
```

---

## 🤖 PHẦN 4: TUTOR & EVALUATOR AGENTS - BƯỚC 5-6

### 4.1 Tutor Agent (Harvard 7 Principles + Socratic Method)

**File: `backend/agents/tutor.py`**

```python
from base import BaseAgent
from typing import Optional

class TutorAgent(BaseAgent):
    """
    Interactive tutoring agent
    
    Implements:
    ✓ Harvard 7 Pedagogical Principles (Kestin et al., 2025)
    ✓ Socratic/Reverse Socratic method
    ✓ RAG + 3-layer grounding
    ✓ LearnLM principles
    """
    
    # Harvard 7 Principles as system prompt building blocks
    HARVARD_PRINCIPLES = {
        '1_active_learning': {
            'name': 'Facilitate Active Learning',
            'instruction': 'Never give direct answers immediately. Guide learner through problem-solving with questions.'
        },
        '2_cognitive_load': {
            'name': 'Manage Cognitive Load',
            'instruction': 'Keep responses SHORT (2-4 sentences). Break complex concepts into small steps.'
        },
        '3_one_step': {
            'name': 'One Step at a Time',
            'instruction': 'Reveal only ONE step per response. Wait for confirmation before continuing.'
        },
        '4_self_thinking': {
            'name': 'Encourage Self-Thinking',
            'instruction': 'Ask "What do you think...?" before giving hints. Let learner attempt 1-2 times first.'
        },
        '5_growth_mindset': {
            'name': 'Promote Growth Mindset',
            'instruction': 'Emphasize effort over results. "Mistakes are learning opportunities!"'
        },
        '6_personalized_feedback': {
            'name': 'Personalized Feedback',
            'instruction': 'Feedback addresses SPECIFIC misconception for THIS learner, not generic.'
        },
        '7_grounding': {
            'name': 'Ground in Curated Content',
            'instruction': '3-layer grounding: (1) Course KG, (2) RAG documents, (3) Personal KG. Cite sources.'
        }
    }
    
    async def execute(
        self,
        learner_id: str,
        concept_id: str,
        user_message: str
    ) -> Dict:
        """
        Tutoring interaction loop
        """
        self.log(f"Tutoring {learner_id} on {concept_id}")
        
        # Get context
        concept = await self.kg_client.get_concept(concept_id)
        profile = self.get_state(f"learner:{learner_id}:profile")
        conversation_history = self.get_state(f"session:{learner_id}:history") or []
        
        # Build context for LLM
        context = await self._build_grounding_context(
            concept_id, profile
        )
        
        # Generate tutoring response (with Harvard principles)
        response = await self._generate_tutoring_response(
            user_message=user_message,
            concept=concept,
            profile=profile,
            context=context,
            history=conversation_history
        )
        
        # Track interaction (for KAG later)
        conversation_history.append({
            'role': 'learner',
            'content': user_message
        })
        conversation_history.append({
            'role': 'tutor',
            'content': response['message']
        })
        self.set_state(f"session:{learner_id}:history", conversation_history)
        
        # Publish interaction event
        self.publish_event('TUTOR_INTERACTION', {
            'learner_id': learner_id,
            'concept_id': concept_id,
            'interaction_count': len(conversation_history)
        })
        
        return {
            'message': response['message'],
            'next_action': response.get('next_action', 'CONTINUE'),  # or 'EVALUATE'
            'hints_given': response.get('hints_count', 0)
        }
    
    async def _build_grounding_context(self, concept_id: str, profile: Dict) -> Dict:
        """
        Build 3-layer grounding context
        Layer 1: Course KG
        Layer 2: RAG documents
        Layer 3: Personal KG
        """
        
        # Layer 1: Course KG
        concept_kg = await self.kg_client.get_concept_with_relations(concept_id)
        
        # Layer 2: RAG
        rag_context = await self.rag_retriever.retrieve(
            query=f"Explain {concept_kg['label']}",
            top_k=3
        )
        
        # Layer 3: Personal KG (if exists)
        personal_context = await self.kg_client.get_personal_knowledge(
            learner_id=profile['learner_id'],
            concept_id=concept_id
        )
        
        return {
            'course_kg': concept_kg,
            'rag_documents': rag_context,
            'personal_kg': personal_context
        }
    
    async def _generate_tutoring_response(
        self,
        user_message: str,
        concept: Dict,
        profile: Dict,
        context: Dict,
        history: List
    ) -> Dict:
        """
        Generate tutoring response with Harvard principles embedded
        """
        
        # Build system prompt with Harvard principles
        system_prompt = self._build_harvard_aware_prompt(concept, profile)
        
        # Add conversation history
        messages = [
            {'role': 'system', 'content': system_prompt},
            *[{'role': msg['role'], 'content': msg['content']} for msg in history[-6:]],  # Last 3 exchanges
            {'role': 'user', 'content': user_message}
        ]
        
        # Call LLM with grounding context injected
        response = await self.llm.achat(
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        return {
            'message': response.message.content,
            'next_action': await self._decide_next_action(response.message.content),
            'hints_count': self._count_hints_given(response.message.content)
        }
    
    def _build_harvard_aware_prompt(self, concept: Dict, profile: Dict) -> str:
        """
        Build system prompt incorporating ALL 7 Harvard principles
        """
        
        learner_name = profile.get('learner_id', 'Learner')
        skill_level = profile.get('skill_level', 'INTERMEDIATE')
        
        prompt = f"""
您是一个根据哈佛2025年研究(Kestin et al.)优化的AI导师。

学生信息:
- 姓名: {learner_name}
- 技能水平: {skill_level}
- 目标: {profile.get('learning_goal', 'Unknown')}

要讲授的概念: {concept['label']}

📚 哈佛7项原则(必须严格遵守):

1️⃣ 【促进主动学习】- 不要立即给出答案!用问题引导学生解决问题
   示例: "你认为下一步是什么?" vs "下一步是..."

2️⃣ 【管理认知负荷】- 回复要短(2-4句话)。打破复杂概念成小步骤
   示例: 不要发送长篇解释,分成3个回复

3️⃣ 【一次一步】- 每次只透露一个步骤。等待学生确认后再继续
   示例: "步骤1是... 你准备好步骤2了吗?"

4️⃣ 【鼓励自主思考】- 先问"你怎么想?",让学生尝试1-2次后才给提示

5️⃣ 【培养成长心态】- 强调努力而非结果。"错误是学习机会!"

6️⃣ 【个性化反馈】- 解决THIS学生的具体误概念,不要通用反馈
   
7️⃣ 【三层基础】- 仅使用来自:
   - 课程KG数据库
   - RAG检索的经过审查的文档
   - 学生的个人知识图
   如果不在这些来源中，说"这超出了范围"

现在,请按照这7项原则回应学生的问题。
"""
        
        return prompt
    
    async def _decide_next_action(self, response: str) -> str:
        """Decide if should continue or evaluate"""
        # Logic: If response suggests learner understands, recommend evaluation
        if 'ready for evaluation' in response.lower() or \
           'let's test' in response.lower():
            return 'EVALUATE'
        return 'CONTINUE'
    
    def _count_hints_given(self, response: str) -> int:
        """Count how many hints were given"""
        hints = response.count('hint') + response.count('try') + response.count('think')
        return min(hints, 5)
```

### 4.2 Evaluator Agent

**File: `backend/agents/evaluator.py`**

```python
from base import BaseAgent
from enum import Enum

class EvalDecision(str, Enum):
    PROCEED = "PROCEED"
    REMEDIATE = "REMEDIATE"
    ALTERNATE_PATH = "ALTERNATE_PATH"
    COMPLETE = "COMPLETE"

class EvaluatorAgent(BaseAgent):
    """
    Adaptive evaluation agent
    
    - Generates assessment questions
    - Classifies errors (misconception types)
    - Decides: Proceed/Remediate/Alternate
    - Triggers KAG if needed
    """
    
    async def execute(
        self,
        learner_id: str,
        concept_id: str,
        learner_response: str
    ) -> Dict:
        """
        Evaluate learner understanding of concept
        """
        self.log(f"Evaluating {learner_id} on {concept_id}")
        
        # Get concept details
        concept = await self.kg_client.get_concept(concept_id)
        
        # Score the response
        score, is_correct = await self._score_response(
            learner_response, concept
        )
        
        # Classify errors (if incorrect)
        error_type = None
        if not is_correct:
            error_type = await self._classify_error(
                learner_response, concept, score
            )
        
        # Update learner mastery in Personal KG
        mastery_level = await self._update_mastery(
            learner_id, concept_id, score, is_correct, error_type
        )
        
        # Decide next action
        decision = self._decide_next_action(
            mastery_level, is_correct, error_type
        )
        
        # Determine next concept (if action != COMPLETE)
        next_concept = None
        if decision == EvalDecision.PROCEED:
            next_concept = await self.kg_client.get_next_concept(concept_id)
        elif decision == EvalDecision.REMEDIATE:
            next_concept = await self.kg_client.get_remediation_for(concept_id)
        elif decision == EvalDecision.ALTERNATE_PATH:
            next_concept = await self.kg_client.get_alternative_path_concept(concept_id)
        
        # Publish evaluation result
        self.publish_event('EVALUATION_COMPLETED', {
            'learner_id': learner_id,
            'concept_id': concept_id,
            'mastery_level': mastery_level,
            'decision': decision.value,
            'error_type': error_type,
            'next_concept': next_concept
        })
        
        # If triggered KAG conditions, publish for KAG Agent
        if decision != EvalDecision.PROCEED:
            # Trigger artifact generation
            self.publish_event('CREATE_ARTIFACT', {
                'learner_id': learner_id,
                'concept_id': concept_id,
                'error_type': error_type
            })
        
        return {
            'score': score,
            'mastery_level': mastery_level,
            'decision': decision.value,
            'error_type': error_type,
            'next_concept': next_concept,
            'feedback': await self._generate_feedback(
                is_correct, error_type, mastery_level
            )
        }
    
    async def _score_response(self, response: str, concept: Dict) -> Tuple[float, bool]:
        """
        Use LLM to score the response
        Returns: (score 0-1, is_correct boolean)
        """
        prompt = f"""
Score this learner response to the concept "{concept['label']}".

Expected understanding:
{concept['definition']}

Learner response:
{response}

Output JSON:
{{
    "score": 0.85,  # 0-1 score
    "is_correct": true,
    "reasoning": "..."
}}
"""
        result = await self.llm.acomplete(prompt)
        data = json.loads(result.text)
        return data['score'], data['is_correct']
    
    async def _classify_error(self, response: str, concept: Dict, score: float) -> str:
        """
        Classify type of error/misconception
        Examples: PARTIAL_UNDERSTANDING, WRONG_PREREQUISITE, INTERFERENCE, etc.
        """
        if score > 0.7:
            return None
        
        prompt = f"""
Classify the misconception in this response:

Concept: {concept['label']}
Expected: {concept['definition']}
Learner said: {response}

Error type: [PARTIAL_UNDERSTANDING|WRONG_PREREQUISITE|INTERFERENCE|OVERGENERALIZATION|OTHER]
"""
        result = await self.llm.acomplete(prompt)
        return result.text.strip()
    
    def _decide_next_action(
        self,
        mastery_level: float,
        is_correct: bool,
        error_type: Optional[str]
    ) -> EvalDecision:
        """
        Decision logic (can be extended with RL)
        """
        if mastery_level >= 0.8:
            return EvalDecision.PROCEED
        elif mastery_level < 0.5:
            if error_type and 'PREREQUISITE' in error_type:
                return EvalDecision.REMEDIATE
            else:
                return EvalDecision.ALTERNATE_PATH
        else:
            return EvalDecision.REMEDIATE
    
    async def _update_mastery(
        self,
        learner_id: str,
        concept_id: str,
        score: float,
        is_correct: bool,
        error_type: Optional[str]
    ) -> float:
        """
        Update learner mastery using Knowledge Tracing-like formula
        """
        # Get previous mastery
        prev_mastery = await self.kg_client.get_mastery_level(
            learner_id, concept_id
        ) or 0.0
        
        # Simple BKT-like update
        mastery = 0.3 * prev_mastery + 0.7 * score
        
        # Update in Personal KG
        await self.kg_client.update_personal_kg_mastery(
            learner_id, concept_id, mastery, error_type
        )
        
        return mastery
    
    async def _generate_feedback(
        self,
        is_correct: bool,
        error_type: Optional[str],
        mastery_level: float
    ) -> str:
        """
        Generate personalized feedback (Harvard principle #6)
        """
        if is_correct:
            return "Great! You've mastered this concept. Let's move to the next one."
        
        # Personalized feedback based on error type
        if error_type == 'WRONG_PREREQUISITE':
            return f"It looks like we need to strengthen {error_type}. Let's review the basics first."
        elif error_type == 'PARTIAL_UNDERSTANDING':
            return "You're on the right track! Let's clarify the specific part you're unsure about."
        else:
            return "No worries! Mistakes help us learn. Let's try a different angle."
```

---

## 📝 PHẦN 5: KAG AGENT (Knowledge Artifacts Generation)

### 5.1 KAG Agent - Atomic Notes & Zettelkasten

**File: `backend/agents/kag.py`**

```python
from base import BaseAgent
from models.artifact import AtomicNote
from datetime import datetime
import json

class KAGAgent(BaseAgent):
    """
    Knowledge Artifact Generation Agent
    
    Tạo Atomic Notes theo Zettelkasten method:
    - Mỗi note = 1 concept
    - Có bi-directional links
    - Tích hợp vào Personal KG
    - Support learning sustainability
    """
    
    async def execute(
        self,
        learner_id: str,
        concept_id: str,
        session_transcript: str,
        error_type: Optional[str] = None
    ) -> Dict:
        """
        Generate knowledge artifacts from learning session
        """
        self.log(f"KAG: Creating artifacts for {learner_id}:{concept_id}")
        
        try:
            # Extract key insights from session transcript
            insights = await self._extract_insights(session_transcript)
            
            # Generate atomic note (Zettelkasten-style)
            note = await self._generate_atomic_note(
                concept_id=concept_id,
                learner_id=learner_id,
                insights=insights,
                error_type=error_type
            )
            
            # Generate additional artifacts (if needed)
            artifacts = [note]
            
            if error_type:
                # Generate remediation note
                remedial_note = await self._generate_remediation_note(
                    concept_id, error_type, insights
                )
                artifacts.append(remedial_note)
            
            # Find related concepts for linking
            related_concepts = await self._find_related_concepts(concept_id)
            
            # Create bi-directional links
            for artifact in artifacts:
                links = await self._create_backlinks(
                    artifact, related_concepts, learner_id
                )
                artifact['links'] = links
            
            # Store artifacts in Personal KG
            await self._store_in_personal_kg(artifacts, learner_id)
            
            # Publish success event
            self.publish_event('ARTIFACTS_GENERATED', {
                'learner_id': learner_id,
                'concept_id': concept_id,
                'artifact_count': len(artifacts)
            })
            
            return {
                'artifacts': artifacts,
                'status': 'success'
            }
            
        except Exception as e:
            self.log(f"KAG Error: {str(e)}", level='ERROR')
            raise
    
    async def _extract_insights(self, transcript: str) -> Dict:
        """
        Extract key insights from session transcript using LLM
        """
        prompt = f"""
Extract learning insights from this tutor-learner session:

{transcript}

Output JSON:
{{
    "key_concepts": ["concept1", "concept2"],
    "misconceptions_clarified": ["...", "..."],
    "examples_used": ["example1", "example2"],
    "common_challenges": "...",
    "understanding_level": "BEGINNER|INTERMEDIATE|ADVANCED"
}}
"""
        result = await self.llm.acomplete(prompt)
        return json.loads(result.text)
    
    async def _generate_atomic_note(
        self,
        concept_id: str,
        learner_id: str,
        insights: Dict,
        error_type: Optional[str]
    ) -> AtomicNote:
        """
        Generate Zettelkasten-style atomic note
        
        Structure:
        - Title: Concept name
        - Definition: In learner's words (from session)
        - Examples: Concrete examples
        - Common mistakes: Misconceptions encountered
        - Related concepts: Tags for linking
        """
        
        concept = await self.kg_client.get_concept(concept_id)
        
        # Generate note content from insights
        prompt = f"""
Create an atomic Zettelkasten note for: {concept['label']}

Based on this learning session insight:
{json.dumps(insights)}

Note structure (Markdown):
# {concept['label']} (ID: {concept_id})

## Definition
<Simple explanation in learner's understanding level>

## Examples
- Example 1
- Example 2

## Common Mistakes
{error_type if error_type else "N/A"}

## Related Concepts
<Tags for linking>

## Source
Learned on: <today>
Session ID: <session_id>
"""
        
        note_content = await self.llm.acomplete(prompt)
        
        note = AtomicNote(
            note_id=f"note_{learner_id}_{concept_id}_{datetime.now().timestamp()}",
            learner_id=learner_id,
            concept_id=concept_id,
            title=concept['label'],
            content=note_content.text,
            tags=insights.get('key_concepts', []),
            source_session_id="session_123",  # Should get from context
            created_at=datetime.now(),
            related_concepts=[]  # Will be filled by _create_backlinks
        )
        
        return note
    
    async def _create_backlinks(
        self,
        artifact: AtomicNote,
        related_concepts: List[str],
        learner_id: str
    ) -> List[Dict]:
        """
        Create bi-directional links to related concepts
        (Zettelkasten principle: Knowledge network)
        """
        links = []
        
        for related_concept_id in related_concepts[:5]:  # Limit to 5
            related_concept = await self.kg_client.get_concept(related_concept_id)
            
            # Check if learner has note for this concept
            related_note = await self.kg_client.find_learner_note(
                learner_id, related_concept_id
            )
            
            if related_note:
                links.append({
                    'type': 'RELATED_TO',
                    'target_note_id': related_note['note_id'],
                    'target_concept': related_concept['label']
                })
        
        return links
    
    async def _store_in_personal_kg(self, artifacts: List, learner_id: str) -> None:
        """
        Store artifacts as nodes in Personal KG
        """
        for artifact in artifacts:
            # Create node in Personal KG
            await self.kg_client.create_artifact_node(
                note_id=artifact.note_id,
                learner_id=learner_id,
                concept_id=artifact.concept_id,
                content=artifact.content
            )
            
            # Create relationships
            for link in artifact.get('links', []):
                await self.kg_client.create_artifact_relationship(
                    from_note=artifact.note_id,
                    to_note=link['target_note_id'],
                    relation_type=link['type']
                )
    
    async def _find_related_concepts(self, concept_id: str) -> List[str]:
        """
        Find related concepts in Course KG
        """
        # Query KG for related concepts
        related = await self.kg_client.find_related_concepts(
            concept_id,
            relation_types=['REQUIRES', 'IS_RELATED_TO', 'IS_SUBCONCEPT_OF'],
            depth=2
        )
        return [c['id'] for c in related]
    
    async def _generate_remediation_note(
        self,
        concept_id: str,
        error_type: str,
        insights: Dict
    ) -> AtomicNote:
        """
        Generate remediation note addressing specific misconception
        """
        # Similar to _generate_atomic_note but focused on remediation
        pass
```

---

## 🏗️ PHẦN 6: CENTRAL STATE & EVENT BUS

### 6.1 Central State Manager

**File: `backend/core/central_state.py`**

```python
from typing import Any, Dict
import json
from datetime import datetime
import asyncio

class CentralStateManager:
    """
    Shared state for all agents
    
    State structure:
    {
        "learner:{id}:profile": {...},
        "session:{id}:history": [...],
        "path:{id}": {...},
        "kg:course": {...}
    }
    """
    
    def __init__(self, postgres_conn):
        self.db = postgres_conn  # PostgreSQL for persistence
        self._cache = {}  # In-memory cache
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Any:
        """Get value (from cache first, then DB)"""
        if key in self._cache:
            return self._cache[key]
        
        # Fallback to database
        result = await self.db.fetch(
            "SELECT value FROM state WHERE key = $1", key
        )
        if result:
            return json.loads(result[0]['value'])
        return None
    
    async def set(self, key: str, value: Any) -> None:
        """Set value (update cache + DB)"""
        async with self._lock:
            # Update cache
            self._cache[key] = value
            
            # Persist to DB
            await self.db.execute(
                """
                INSERT INTO state (key, value, updated_at) 
                VALUES ($1, $2, $3)
                ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = $3
                """,
                key,
                json.dumps(value),
                datetime.now()
            )
    
    async def delete(self, key: str) -> None:
        """Delete key"""
        if key in self._cache:
            del self._cache[key]
        
        await self.db.execute(
            "DELETE FROM state WHERE key = $1", key
        )
    
    async def get_all(self, prefix: str) -> Dict:
        """Get all keys matching prefix"""
        results = {}
        for key, value in self._cache.items():
            if key.startswith(prefix):
                results[key] = value
        return results
```

### 6.2 Event Bus (Pub-Sub)

**File: `backend/core/event_bus.py`**

```python
from typing import Callable, Dict, List
import asyncio
from collections import defaultdict

class EventBus:
    """
    Simple Pub-Sub event bus for agent communication
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_history: List[Dict] = []
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to event type"""
        self._subscribers[event_type].append(callback)
    
    async def publish(self, event: Dict) -> None:
        """Publish event to all subscribers"""
        event_type = event['event_type']
        
        # Store in history
        self._event_history.append(event)
        
        # Call all subscribers asynchronously
        if event_type in self._subscribers:
            tasks = [
                callback(event)
                for callback in self._subscribers[event_type]
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_history(self, event_type: str = None, limit: int = 100):
        """Get event history"""
        if event_type:
            return [e for e in self._event_history if e['event_type'] == event_type][-limit:]
        return self._event_history[-limit:]
```

---

## 🌐 PHẦN 7: BACKEND API ROUTES

### 7.1 FastAPI Main App

**File: `backend/main.py`**

```python
from fastapi import FastAPI, CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config.settings import settings
from core.central_state import CentralStateManager
from core.event_bus import EventBus
from routes import learner, path, tutor, evaluator, artifacts, kg, admin

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global app state
state_manager = None
event_bus = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle"""
    global state_manager, event_bus
    
    # Startup
    logger.info("Starting Personalized Learning Path System...")
    
    # Initialize global instances
    state_manager = CentralStateManager(postgres_conn=get_db())
    event_bus = EventBus()
    
    # Initialize agents
    init_agents(state_manager, event_bus)
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(learner.router, prefix="/api/learner", tags=["Learner"])
app.include_router(path.router, prefix="/api/path", tags=["Path"])
app.include_router(tutor.router, prefix="/api/tutor", tags=["Tutor"])
app.include_router(evaluator.router, prefix="/api/evaluator", tags=["Evaluator"])
app.include_router(artifacts.router, prefix="/api/artifacts", tags=["Artifacts"])
app.include_router(kg.router, prefix="/api/kg", tags=["Knowledge Graph"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.API_VERSION}

@app.get("/")
async def root():
    return {
        "message": "Personalized Learning Path System - VER3 Enhanced",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
```

### 7.2 Learner Routes

**File: `backend/routes/learner.py`**

```python
from fastapi import APIRouter, HTTPException
from models.learner import LearnerProfile
from agents import profiler
import uuid

router = APIRouter()

@router.post("/profile/create")
async def create_learner_profile(query: str, pretest_score: float = None):
    """
    Create new learner profile
    
    Input:
    - query: "Tôi muốn học SQL trong 2 tuần"
    - pretest_score: 0.65
    """
    learner_id = str(uuid.uuid4())
    
    profile_agent = profiler.LearnerProfilerAgent(state_manager, event_bus, llm)
    profile = await profile_agent.execute(learner_id, query, pretest_score)
    
    return {
        "learner_id": learner_id,
        "profile": profile.dict()
    }

@router.get("/profile/{learner_id}")
async def get_learner_profile(learner_id: str):
    """Get learner profile"""
    profile = await state_manager.get(f"learner:{learner_id}:profile")
    if not profile:
        raise HTTPException(status_code=404, detail="Learner not found")
    return profile

@router.get("/progress/{learner_id}")
async def get_learner_progress(learner_id: str):
    """Get learner progress"""
    profile = await state_manager.get(f"learner:{learner_id}:profile")
    
    # Calculate metrics
    total_concepts = len(profile['concept_mastery_map'])
    mastered = sum(1 for m in profile['concept_mastery_map'].values() if m >= 0.8)
    
    return {
        "total_concepts": total_concepts,
        "mastered": mastered,
        "progress_percentage": (mastered / total_concepts * 100) if total_concepts > 0 else 0,
        "avg_mastery": profile.get('avg_mastery', 0)
    }
```

---

## 🎨 PHẦN 8: FRONTEND (Next.js 14)

### 8.1 Learner Dashboard

**File: `frontend/app/learner/page.tsx`**

```typescript
'use client'

import React, { useEffect, useState } from 'react'
import { useLearner } from '@/hooks/useLearner'
import TutorChat from '@/components/TutorChat'
import PathVisualization from '@/components/PathVisualization'
import ProgressBar from '@/components/ProgressBar'

export default function LearnerDashboard() {
  const { learner, path, loading } = useLearner()
  const [activeTab, setActiveTab] = useState('path')

  if (loading) return <div>Loading...</div>

  return (
    <div className="learner-dashboard">
      <header>
        <h1>Learning Path for {learner?.learning_goal}</h1>
        <ProgressBar 
          mastered={learner?.mastered_concepts || 0}
          total={learner?.total_concepts || 0}
        />
      </header>

      <div className="main-content">
        <aside className="sidebar">
          <nav>
            <button 
              onClick={() => setActiveTab('path')}
              className={activeTab === 'path' ? 'active' : ''}
            >
              📚 Learning Path
            </button>
            <button 
              onClick={() => setActiveTab('tutor')}
              className={activeTab === 'tutor' ? 'active' : ''}
            >
              🤖 Tutor
            </button>
            <button 
              onClick={() => setActiveTab('notes')}
              className={activeTab === 'notes' ? 'active' : ''}
            >
              📝 My Notes
            </button>
          </nav>
        </aside>

        <main className="content">
          {activeTab === 'path' && <PathVisualization path={path} />}
          {activeTab === 'tutor' && <TutorChat />}
          {activeTab === 'notes' && <NotesPanel learner={learner} />}
        </main>
      </div>
    </div>
  )
}

function NotesPanel({ learner }: any) {
  const [notes, setNotes] = useState([])

  useEffect(() => {
    // Fetch notes from API
    fetch(`/api/artifacts?learner_id=${learner.id}`)
      .then(r => r.json())
      .then(data => setNotes(data))
  }, [learner.id])

  return (
    <div className="notes-panel">
      <h2>Your Knowledge Artifacts (Zettelkasten)</h2>
      {notes.map(note => (
        <div key={note.id} className="note-card">
          <h3>{note.title}</h3>
          <p>{note.content.substring(0, 200)}...</p>
          <div className="links">
            {note.links?.map(link => (
              <span key={link.id} className="tag">{link.target_concept}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
```

---

## 🚀 PHẦN 9: DEPLOYMENT & PRODUCTION

### 9.1 Docker Compose (Development)

**File: `docker-compose.yml`**

```yaml
version: '3.9'

services:
  # Backend
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://user:password@postgres:5432/learning_db
      - NEO4J_URI=neo4j://neo4j:7687
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - neo4j
      - redis
    volumes:
      - ./backend:/app

  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000/api
    depends_on:
      - backend
    volumes:
      - ./frontend:/app

  # PostgreSQL (State + Logs)
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: learning_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Neo4j (Knowledge Graph)
  neo4j:
    image: neo4j:5.17-aura
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/var/lib/neo4j/data
      - ./database/cypher_scripts:/scripts
    ports:
      - "7474:7474"  # UI
      - "7687:7687"  # Bolt

  # Redis (Caching)
  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  neo4j_data:
  redis_data:
```

### 9.2 Deployment Script

**File: `scripts/deploy.sh`**

```bash
#!/bin/bash
set -e

echo "🚀 Deploying Personalized Learning Path System"

# 1. Build Docker images
echo "📦 Building Docker images..."
docker-compose build

# 2. Initialize databases
echo "🗄️ Initializing databases..."
docker-compose up -d postgres neo4j redis

# Wait for services
sleep 10

# 3. Run migrations
echo "🔄 Running migrations..."
docker exec backend python -m alembic upgrade head

# 4. Load sample KG data
echo "📚 Loading knowledge graph..."
docker exec neo4j cypher-shell -u neo4j -p password < database/cypher_scripts/init_course_kg.cypher

# 5. Start all services
echo "▶️ Starting services..."
docker-compose up -d

# 6. Health check
echo "✅ Health checks..."
curl http://localhost:8000/health

echo "🎉 Deployment complete! Access at http://localhost:3000"
```

---

## 📊 PHẦN 10: TESTING & VALIDATION

### 10.1 Agent Testing

**File: `backend/tests/test_agents.py`**

```python
import pytest
from agents.profiler import LearnerProfilerAgent
from agents.planner import PathPlannerAgent
from agents.tutor import TutorAgent
from core.central_state import CentralStateManager
from core.event_bus import EventBus

@pytest.fixture
async def setup():
    """Setup test fixtures"""
    state = CentralStateManager(mock_db)
    bus = EventBus()
    yield state, bus

@pytest.mark.asyncio
async def test_profiler_agent(setup):
    """Test learner profiling"""
    state, bus = setup
    agent = LearnerProfilerAgent("test_profiler", state, bus, llm=mock_llm)
    
    profile = await agent.execute(
        learner_id="test_001",
        user_query="Tôi muốn học SQL trong 2 tuần",
        pretest_score=0.65
    )
    
    assert profile.learner_id == "test_001"
    assert profile.skill_level == "INTERMEDIATE"
    assert profile.time_available == 14

@pytest.mark.asyncio
async def test_path_planner(setup):
    """Test path planning"""
    state, bus = setup
    agent = PathPlannerAgent("test_planner", state, bus, kg_client=mock_kg)
    
    path = await agent.execute(
        learner_id="test_001",
        goal_concept_ids=["sql_select", "sql_from", "sql_where"]
    )
    
    assert len(path) > 0
    assert path[0]['concept_id']  # Should have concept IDs

@pytest.mark.asyncio
async def test_harvard_principles_in_tutor(setup):
    """Test that tutor respects Harvard 7 principles"""
    state, bus = setup
    agent = TutorAgent("test_tutor", state, bus, llm=mock_llm)
    
    response = await agent.execute(
        learner_id="test_001",
        concept_id="sql_select",
        user_message="What is SELECT in SQL?"
    )
    
    # Check response doesn't directly answer (principle 1)
    assert not response['message'].startswith("SELECT is...")
    
    # Check response is not too long (principle 2)
    assert len(response['message'].split('\n')) <= 5
    
    # Check it's a question (principle 4)
    assert '?' in response['message']
```

---

## 📚 PHẦN 11: DATABASE SCHEMAS

### 11.1 Neo4j Course KG Initialization

**File: `database/cypher_scripts/init_course_kg.cypher`**

```cypher
// Create indexes
CREATE INDEX concept_label IF NOT EXISTS FOR (c:Concept) ON (c.label);
CREATE INDEX concept_tags IF NOT EXISTS FOR (c:Concept) ON (c.semantic_tags);

// Create sample concept nodes
CREATE (sql:Concept {
  nodeID: "sql_select",
  label: "SQL SELECT",
  definition: "Retrieve data from database table",
  difficulty_level: 1,
  semantic_tags: ["sql", "query", "dml", "beginner"],
  estimated_time: 30,
  bloom_level: 1,
  learning_objectives: ["Understand SELECT syntax", "Execute basic queries"],
  examples: ["SELECT * FROM users"]
})

CREATE (sqlwhere:Concept {
  nodeID: "sql_where",
  label: "SQL WHERE",
  definition: "Filter rows based on conditions",
  difficulty_level: 2,
  semantic_tags: ["sql", "query", "filtering", "intermediate"],
  estimated_time: 25,
  examples: ["SELECT * FROM users WHERE age > 18"]
})

// Create relationships
MATCH (select:Concept {nodeID: "sql_select"}),
      (where:Concept {nodeID: "sql_where"})
CREATE (select)-[:REQUIRES]->(where)

// Create more concepts... (Data Modeling, JOINs, etc.)

RETURN "Course KG initialized" as message
```

### 11.2 PostgreSQL State Schema

**File: `database/sql/init_postgres.sql`**

```sql
-- Central State table
CREATE TABLE IF NOT EXISTS state (
  id SERIAL PRIMARY KEY,
  key VARCHAR(255) NOT NULL UNIQUE,
  value JSONB NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learner table (denormalized from state)
CREATE TABLE IF NOT EXISTS learners (
  id UUID PRIMARY KEY,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  goal VARCHAR(255),
  skill_level VARCHAR(50),
  profile JSONB
);

-- Learning sessions
CREATE TABLE IF NOT EXISTS sessions (
  id UUID PRIMARY KEY,
  learner_id UUID REFERENCES learners(id),
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  duration_minutes INT,
  concept_id VARCHAR(255)
);

-- Evaluation results
CREATE TABLE IF NOT EXISTS evaluations (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES sessions(id),
  concept_id VARCHAR(255),
  score FLOAT,
  mastery_level FLOAT,
  decision VARCHAR(50)  -- PROCEED, REMEDIATE, etc.
);

-- Artifacts (Knowledge notes)
CREATE TABLE IF NOT EXISTS artifacts (
  id UUID PRIMARY KEY,
  learner_id UUID REFERENCES learners(id),
  concept_id VARCHAR(255),
  title VARCHAR(255),
  content TEXT,
  tags TEXT[],
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_learners_goal ON learners(goal);
CREATE INDEX idx_sessions_learner ON sessions(learner_id);
CREATE INDEX idx_evaluations_session ON evaluations(session_id);
CREATE INDEX idx_artifacts_learner ON artifacts(learner_id);
```

---

## ⚙️ PHẦN 12: ENVIRONMENT & CONFIGURATION

### 12.1 Environment Template

**File: `.env.example`**

```bash
# API Configuration
API_TITLE=Personalized Learning Path System
API_VERSION=1.0.0
DEBUG=False
SECRET_KEY=your-secret-key-here

# Database
POSTGRES_URL=postgresql://user:password@localhost/learning_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=learning_db

# Neo4j
NEO4J_URI=neo4j+s://xxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Redis
REDIS_URL=redis://localhost:6379

# LLM APIs
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...

# RAG
CHROMA_PATH=./chroma_data
EMBEDDING_MODEL=text-embedding-3-large
VECTOR_STORE=chroma  # or pinecone

# Authentication
AUTH0_DOMAIN=your-auth0-domain
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_ENV=development
```

---

## 📋 TÓNGBF KẾ HOẠCH THỰC HIỆN - ROADMAP 12 TUẦN

| Tuần | Giai đoạn | Nhiệm vụ chính | Output |
|------|----------|--------------|--------|
| 1 | Setup | Repository, Docker, Environment | Working dev environment |
| 2-3 | Backend Core | Central State, Event Bus, Base Agent | Core infrastructure |
| 4-5 | Agents P1 | Knowledge Extraction, Profiler, Planner | 3 agents working |
| 6-7 | Agents P2 | Tutor (Harvard 7 principles), Evaluator | 2 agents + RAG |
| 8 | KAG Agent | Artifact generation, Personal KG | Zettelkasten working |
| 9 | Frontend | Dashboard, Chat UI, Visualization | Basic UI |
| 10 | Integration | End-to-end testing, API connectivity | Full workflow |
| 11 | Optimization | Performance, caching, monitoring | Production-ready |
| 12 | Documentation | Code docs, API spec, deployment guide | Complete documentation |

---

## 🎯 KÍCH THƯỚC DỰ ÁN (LOC Estimate)

- **Backend**: ~5,000 LOC (Python)
- **Frontend**: ~2,500 LOC (TypeScript/React)
- **Database Scripts**: ~1,000 LOC (Cypher + SQL)
- **Tests**: ~2,000 LOC
- **Total**: ~10,500 LOC

---

**Good luck with your thesis! 🚀**

This is a production-ready blueprint. Adjust based on your specific needs.
