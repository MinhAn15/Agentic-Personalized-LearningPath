# 🏗️ ARCHITECTURE DECISION RECORDS (ADR)

## Document: Architecture Decisions for Personalized Learning Path System VER3 Enhanced

**Status**: Approved  
**Date**: December 2025  
**Authors**: Thesis Team + AI Consultant  
**Version**: 3.0 with Agentic AI Enhancement

---

## ADR-1: Multi-Agent Architecture over Traditional Monolithic System

### Context
Traditional single-agent systems (one LLM endpoint) struggle with:
- Separation of concerns (profiling vs tutoring vs evaluation)
- Scalability (one LLM for all tasks = bottleneck)
- State management complexity
- Error recovery and resilience

### Decision
**✅ APPROVED**: Use Multi-Agent Architecture with 6 specialized agents

### Rationale
1. **Separation of Concerns**: Each agent has single responsibility
   - ProfilerAgent: Understand learner
   - PlannerAgent: Design optimal path
   - TutorAgent: Interactive teaching
   - EvaluatorAgent: Assessment & decisions
   - KAGAgent: Knowledge management
   - KnowledgeExtractionAgent: KG construction

2. **Scalability**: Can deploy agents independently
   - Each agent can run on separate container/serverless function
   - Independent rate limits and API quota management
   - Easier to add new agents (e.g., MotivationAgent, MetacognitionAgent)

3. **Fault Tolerance**: Agent failure doesn't crash system
   - Event-driven architecture = loose coupling
   - If TutorAgent fails, Evaluator can handle gracefully
   - Circuit breaker patterns can be added per agent

4. **LlamaIndex AgentWorkflow Support**
   - LlamaIndex 0.10.0+ has native multi-agent support
   - Handoff mechanism: agents can transfer tasks
   - Built-in state management

### Trade-offs
- **Complexity**: More moving parts to manage
  - Mitigation: Central State Manager + Event Bus abstracts complexity
- **Latency**: Agent handoffs add milliseconds
  - Mitigation: Async/await + event streaming minimize impact
- **Debugging**: Harder to trace cross-agent issues
  - Mitigation: Comprehensive logging + event history

### References
- Microsoft Research: "Communicative Agents for Software Development" (2024)
- AutoGen framework documentation (Microsoft)
- LlamaIndex AgentWorkflow release notes (2025)

---

## ADR-2: Knowledge Graph (Neo4j) over Traditional Relational Database

### Context
Learning path recommendation requires:
- Prerequisite chains (A requires B requires C)
- Alternative paths (if A fails, go to B')
- Semantic relationships (similar_to, is_subconcept_of)
- Shortest path queries with multiple constraints

### Decision
**✅ APPROVED**: Use Neo4j Aura (managed service) for Course KG + Personal KG (Dual-KG Architecture)

### Rationale

#### Why Graph Database?
1. **Natural for Learning Domains**: Concepts are inherently networked
   - SQL SELECT depends on SQL FROM and SQL WHERE
   - Graph structure mirrors prerequisite dependencies
   - Queries like "find all prerequisites for X" = simple Cypher

2. **Flexible Relationships**
   ```cypher
   // Impossible in SQL, simple in Cypher:
   MATCH (concept1)-[:REQUIRES*1..3]->(concept2)
   WHERE concept1.label = "Machine Learning"
   AND concept2.difficulty_level <= 2
   RETURN concept2
   ```

3. **Performance**: Graph queries faster than SQL JOINs for deep relationships
   - Cypher native path-finding
   - Index on relationships (not just nodes)
   - Specialized query optimization for graph patterns

#### Why Neo4j specifically?
1. **ACID guarantees**: Transactions matter in learning state
2. **Property Graph model**: Node/relationship properties = rich metadata
3. **Cypher language**: More intuitive for domain experts than SQL
4. **Aura cloud**: No infrastructure management needed
5. **APOC library**: 450+ utility functions (deduplication, similarity scoring)
6. **LlamaIndex integration**: Property Graph Index directly supported

#### Why Dual-KG (Course KG + Personal KG)?
- **Course KG**: Static, curated, shared across all learners
  - Query: "What are prerequisites for SQL Joins?"
  - Update: Weekly when new content added
  
- **Personal KG**: Dynamic, per-learner, updated in real-time
  - Stores: mastery levels, learning history, error patterns
  - Query: "What concepts has student X mastered?"
  - Update: After each evaluation
  - Supports Zettelkasten artifact linking

This separation ensures:
- Course KG stays clean and uncorrupted
- Personal KG can be archived/deleted per GDPR
- Different backup/replication strategies

### Trade-offs
- **Learning curve**: Team must learn Cypher
  - Mitigation: LLM can generate Cypher from natural language
- **Schema changes**: More rigid than NoSQL, less flexible than SQL
  - Mitigation: Use Neo4j schema constraints for data quality
- **Cost**: Neo4j Aura not free (but MongoDB/Firebase not free either)
  - Mitigation: Free tier supports 200k nodes = sufficient for thesis

### References
- Neo4j white paper: "Knowledge Graphs for Learning" (2024)
- Dartmouth study: "RAG + Knowledge Graph for Educational Trust" (2025)
- https://neo4j.com/developer/graph-algorithms-optimization/

---

## ADR-3: LlamaIndex over LangChain for LLM Framework

### Context
Need framework to:
- Integrate LLM with Knowledge Graph
- Support RAG (Retrieval-Augmented Generation)
- Manage prompt templates and chains
- Handle agent orchestration

### Decision
**✅ APPROVED**: Use LlamaIndex (specifically Property Graph Index + AgentWorkflow)

### Rationale

| Feature | LlamaIndex | LangChain | LLaMA-Factory |
|---------|-----------|----------|--------------|
| **KG Integration** | Native Property Graph Index | Requires custom wrapper | Not applicable |
| **Agent Support** | AgentWorkflow (2025) | LLMChain-based | Not applicable |
| **RAG** | VectorStoreIndex + KG fusion | Basic RAG | Not applicable |
| **Documentation** | Excellent (2025) | Comprehensive | Limited |
| **Learning curve** | Moderate | Steep | Steep |
| **Production use** | Yes (Databricks, ServiceTitan) | Yes (major companies) | Limited |

### Key Decision Factors
1. **Property Graph Index**: Unique to LlamaIndex
   - Connects LLM directly to Neo4j
   - Automatic prompt generation for graph queries
   - No manual Cypher writing needed

2. **AgentWorkflow (New 2025)**: Better than AutoGen for education domain
   - Built-in state management across interactions
   - Handoff mechanism (one agent to another)
   - Event streaming for real-time monitoring

3. **RAG Integration**: Cleanest fusion of multiple sources
   - VectorStoreIndex for document retrieval
   - Property Graph Index for KG queries
   - Ranked aggregation of both

4. **Ecosystem**: Better integration with evaluation/monitoring
   - LlamaIndex llamatrace for debugging
   - Native support for grounding validation

### Trade-offs
- **Not as established as LangChain** for production use
  - Mitigation: LlamaIndex team is experienced (ex-Llama team)
  - Mitigation: Already used by 10k+ projects
  
- **Fewer LLM provider integrations**
  - Mitigation: Supports all major providers (OpenAI, Gemini, Claude, Ollama)

### References
- LlamaIndex blog: "Introducing AgentWorkflow" (2025)
- https://docs.llamaindex.ai/en/stable/modules/agents/

---

## ADR-4: Retrieval-Augmented Generation (RAG) + 3-Layer Grounding

### Context
LLMs hallucinate. In education, this is CRITICAL:
- Telling student "SELECT is a type of loop" = learning damage
- Need to ground every statement in verified sources

Harvard 2025 research + Dartmouth 2025 research show:
- RAG alone reduces hallucinations ~40%
- Learners trust AI more when grounded in curated materials

### Decision
**✅ APPROVED**: Implement 3-Layer Grounding System:
1. **Layer 1**: Course KG (structured knowledge)
2. **Layer 2**: RAG documents (lecture materials)
3. **Layer 3**: Personal KG (learner's own notes)

### Implementation Architecture

```
Tutor Agent Query: "How do SQL JOINs work?"
    ↓
┌─────────────────────────────────────────┐
│  Grounding Enforcer System              │
├─────────────────────────────────────────┤
│ Layer 1: Query Course KG                │
│  - Find SQL_JOIN concept node           │
│  - Get definition, prerequisites        │
│                                         │
│ Layer 2: Retrieve RAG documents         │
│  - Search: "SQL JOINS tutorial"         │
│  - Top 3 chunks from lectures           │
│                                         │
│ Layer 3: Fetch Personal KG              │
│  - Student's previous notes on JOINS    │
│  - Student's misconceptions log         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Synthesize Response with LLM           │
│  "Based on Lecture 5 (Layer 2),         │
│   SQL JOIN is... (Layer 1)              │
│   You previously struggled with... (L3)"│
└─────────────────────────────────────────┘
```

### RAG Implementation Details

**Vector Database**: Chroma (not Pinecone)
- Why: Open-source, embeddings stored locally
- Compatible with: All embedding models
- Cost: Free
- Scalability: Fine for 500+ documents

**Embedding Model**: OpenAI `text-embedding-3-small`
- Dimensions: 1536 (best for education domain)
- Cost: $0.02 per 1M tokens (negligible)
- Quality: Superior to free alternatives

**Chunking Strategy**:
```
Document: SQL_Basics.md
    ↓
Chunk by H2 sections (400-600 tokens each)
    ↓
Each chunk tagged with:
- source_section
- difficulty_level
- concepts_covered
    ↓
Stored in Chroma with metadata
```

### Why Not Fine-tuning?
- **Too expensive**: $1000+ to fine-tune even smaller models
- **Slow to update**: Can't dynamically add new documents
- **Overkill for domain**: Standard LLMs already good at explanation
- **RAG + prompt engineering** = 80% of fine-tuning benefit at 1% cost

### Validation Strategy

Every response checked:
```python
@dataclass
class GroundingValidation:
    grounding_layers_used: int  # 1, 2, or 3
    confidence_score: float     # 0-1
    sources_cited: List[str]   # ["Lecture 5", "KG", "Your notes"]
    
    def is_valid(self) -> bool:
        return self.grounding_layers_used >= 2 and \
               self.confidence_score >= 0.8
```

If `is_valid() == False`: Return "I don't have enough information"

### References
- Dartmouth Study 2025: "RAG increases educational trust" 
- ArXiv: "Retrieval Augmented Generation for Large Language Models" (2023)
- LlamaIndex RAG documentation

---

## ADR-5: Reinforcement Learning (not A*) for Path Planning

### Context
Traditional path planning uses A* algorithm:
```
A* features:
✓ Optimal solution guaranteed
✓ Efficient exploration
✗ Static heuristic function
✗ Cannot learn from feedback
✗ Assumes deterministic transitions
```

Learning is non-deterministic:
- Same concept taught twice = different outcomes based on mood, previous knowledge, etc.
- Optimal path changes as learner progresses
- Dynamic difficulty adjustment impossible with A*

### Decision
**✅ APPROVED**: Use RL-based path planning (policy gradient method)

### Algorithm Choice: MOPO-like (Model-based Policy Optimization)

```
State: (current_concept, learner_state, time_remaining)
Action: next_concept_to_teach
Reward: 
  R(s,a) = α·P_correct 
         + β·ΔMastery 
         - γ·T_normalized 
         + δ·E_engagement

Transition Model: Knowledge Tracing (predict outcome of action)
Policy: π(a|s) = probability of selecting action given state
```

### Why RL over A*?

| Metric | A* | RL |
|--------|-----|-----|
| **Learns from feedback** | ✗ | ✓ |
| **Adapts to learner** | ✗ | ✓ |
| **Handles uncertainty** | ✗ | ✓ |
| **Update path mid-learning** | ✗ | ✓ |
| **Proven in education** | ✓ | ✓ (Nature 2025) |

### Hyperparameter Tuning
```python
ALPHA = 0.4    # Weight learning correctness (P_correct)
BETA = 0.3     # Weight mastery improvement (ΔMastery)
GAMMA = 0.2    # Penalize time overage (T_normalized)
DELTA = 0.1    # Encourage engagement (E_engagement)

# These can be tuned based on learner preferences
```

### Exploration vs Exploitation
- **Exploitation**: Follow best path so far (70% of time)
- **Exploration**: Try alternative path to learn (30% of time)
- Ratio adjustable based on learner's time budget

### References
- Nature 2025: "Reinforcement Learning for Knowledge Tracing" (deep RL-DKT model)
- Sutton & Barto: "Reinforcement Learning: An Introduction" (2nd ed, 2018)
- Educational ML: "Personalized Learning via Reinforcement Learning" (2023)

---

## ADR-6: Harvard 7 Pedagogical Principles Integration

### Context
Harvard 2025 study (Kestin et al.) published definitive evidence:
- 7 principles integrated into AI tutor = effect size 0.73-1.3 SD
- Traditional AI tutor = no effect
- In-class teaching = baseline

### Decision
**✅ APPROVED**: Hard-code Harvard 7 principles into TutorAgent prompts

### Principles → Implementation

| # | Principle | Implementation | LLM Instruction |
|---|-----------|----------------|-----------------|
| 1 | **Active Learning** | Guide, don't answer | "Ask questions first, never direct answers" |
| 2 | **Cognitive Load** | Keep short (2-4 sentences) | "Limit responses to 3 sentences max" |
| 3 | **One Step** | Reveal one at a time | "Reveal only step 1 initially, ask if ready for step 2" |
| 4 | **Self-Thinking** | Ask "What do you think?" | "Ask 'What do you think...?' before helping" |
| 5 | **Growth Mindset** | Praise effort | "Emphasize: 'You tried hard, that's great!'" |
| 6 | **Personal Feedback** | Address misconceptions | "Address THIS student's specific error, not generic" |
| 7 | **Grounding** | Use 3-layer system | "Only cite: Course KG, RAG, Personal KG" |

### System Prompt Integration

```python
HARVARD_SYSTEM_PROMPT = """
You are an AI Tutor trained on Harvard 2025 Pedagogical Research.

MUST FOLLOW these 7 principles from Kestin et al., 2025:

1. NEVER give direct answers immediately
   Instead: Guide learner through problem-solving
   Example: "What happens when we remove the WHERE clause?"
   NOT: "When you remove WHERE, all rows are returned"

2. Keep responses SHORT (2-4 sentences max)
   Why: Manage cognitive load (from LearnLM principles)
   NOT: Long explanations - break into multiple turns

3. Reveal ONE STEP AT A TIME
   Say: "Step 1 is... Are you ready for step 2?"
   NOT: "Steps 1, 2, and 3 are..."

4. Ask "What do you think?" BEFORE helping
   Let learner attempt 1-2 times first
   Only then provide hints

5. Praise EFFORT, not intelligence
   "Your effort to try multiple approaches is great!"
   NOT: "You're smart for getting this"

6. Personalized feedback (address THEIR specific misconception)
   "I see you're confusing JOIN with UNION"
   NOT: Generic "Good job" or generic error messages

7. Ground in verified sources ONLY
   From: Course KG, RAG lectures, Personal KG
   Never: "I think..." or unverified claims

Paradigm: "Productive Struggle" not "Content Delivery"
"""
```

### Measurement Strategy
- **Intervention**: Students taught with Harvard principles vs without
- **Metrics**: Learning gain, time-on-task, misconceptions resolved
- **Expected effect**: 0.7-1.3 SD improvement (from Harvard study)

### References
- Kestin, G., Miller, K., et al. (2025). AI tutoring outperforms in-class active learning. Scientific Reports, Nature.
- Google LearnLM: Five Learning Science Principles (2024)
- Cognitive Load Theory: Sweller (2011)

---

## ADR-7: PostgreSQL for State Management (not Redis-only)

### Context
Need to store:
- Learner profiles (static)
- Learning sessions (events)
- Evaluation results (historical)
- Event log (audit trail)

### Decision
**✅ APPROVED**: PostgreSQL for persistent state + Redis for cache

### Architecture
```
┌─────────────────────┐
│   Application       │
└──────────┬──────────┘
           ↓
┌─────────────────────────────────────┐
│  Central State Manager               │
├─────────────────────────────────────┤
│  1. Check Redis cache (fast)         │
│  2. If miss, query PostgreSQL        │
│  3. Update Redis from PostgreSQL     │
└──────┬────────────────────────────┬──┘
       ↓                            ↓
   ┌────────┐              ┌──────────────┐
   │ Redis  │              │ PostgreSQL   │
   │ (hot)  │              │ (persistent) │
   └────────┘              └──────────────┘
```

### Why PostgreSQL not MongoDB/DynamoDB?
- **ACID guarantee**: Learning state can't afford inconsistency
- **Transactions**: Atomic updates across learner profile + evaluation
- **Cost**: PostgreSQL free tier (Render/Railway) fine for thesis
- **Audit trail**: Historical queries built-in

### Why Redis cache?
- **Latency**: Reduce PostgreSQL query from 50ms to 1ms
- **Throughput**: Handle 100+ concurrent learners without db bottleneck
- **Cost**: Free tier (Upstash) $5/month reasonable

### Trade-offs
- **Eventual consistency**: Cache might be slightly stale
  - Mitigation: TTL = 5 minutes (acceptable for education)
  - Mitigation: Critical updates write-through (cache + db)

### References
- PostgreSQL documentation: ACID guarantees
- Redis best practices: Cache-aside pattern

---

## ADR-8: Next.js 14 Frontend (not React SPA + separate backend)

### Context
Could build:
- Option A: React SPA + FastAPI backend (traditional separation)
- Option B: Next.js (App Router) + FastAPI + API proxy routes
- Option C: Next.js full-stack (App Router + API routes = no separate backend)

### Decision
**✅ APPROVED**: Option B - Next.js 14 App Router as proxy, FastAPI as backend

### Rationale
1. **Best of both worlds**
   - Separate backend (FastAPI) = can scale independently, easier testing
   - Next.js proxy routes = no CORS complexity, unified deployment
   
2. **Server-side rendering benefits**
   - Learning paths visualized server-side = SEO friendly
   - Faster initial load (important for learner experience)
   - Metadata dynamic per learner
   
3. **Next.js 14 advantages**
   - App Router = better file-based routing
   - React Server Components = reduce client-side JS
   - Built-in optimization (images, fonts, code splitting)
   - Streaming responses supported

4. **Gradual migration path**
   - Start with Next.js as proxy
   - Can move API routes into Next.js later if needed
   - Can keep FastAPI if team prefers Python

### API Proxy Example
```typescript
// frontend/app/api/[...path].ts
export async function POST(req: Request) {
  const path = req.nextUrl.pathname.replace(/^\/api\//, '');
  const body = await req.json();
  
  const response = await fetch(
    `${process.env.BACKEND_URL}/api/${path}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }
  );
  
  return response;
}
```

### Trade-offs
- **Single point of failure**: If Next.js proxy fails, frontend down
  - Mitigation: Deploy Next.js + FastAPI separately
  - Mitigation: Use API routes as backup

### References
- Vercel Next.js 14 documentation
- API Routes best practices

---

## ADR-9: Docker + Docker Compose for Development Environment

### Decision
**✅ APPROVED**: Docker Compose for local development (all services)

### Services Stack
```yaml
Services:
- FastAPI backend (port 8000)
- Next.js frontend (port 3000)
- PostgreSQL (port 5432)
- Neo4j (ports 7474, 7687)
- Redis (port 6379)
- Chroma vector DB (port 8001)
```

### Why Docker?
1. **Consistency**: "Works on my machine" problem solved
2. **Isolation**: Services don't conflict with system dependencies
3. **Reproducibility**: Exact same environment in production
4. **Easy reset**: `docker-compose down; docker-compose up`

### Production Deployment
- Backend → Cloud Run (Google) or Vercel Serverless
- Frontend → Vercel (next.js optimized)
- Neo4j → Neo4j Aura (managed)
- PostgreSQL → Cloud SQL (Google) or Neon
- Redis → Upstash (serverless)

### References
- Docker best practices for microservices
- 12-Factor app methodology

---

## ADR-10: Testing Strategy (Pytest + Integration Tests)

### Decision
**✅ APPROVED**: 
- **Unit tests**: pytest for agents + utilities
- **Integration tests**: Full workflow (profiler → planner → tutor → evaluator)
- **E2E tests**: Frontend + backend (Playwright)

### Test Coverage Target: 80%

```
Core layers (must test):
✓ Agents (unit): 90% coverage
✓ Knowledge Graph (integration): 85% coverage
✓ RAG system (integration): 80% coverage
✓ API routes (integration): 75% coverage
✓ Frontend components (unit + e2e): 70% coverage
```

### Testing Pyramid
```
       🧪 E2E (slow, expensive)      10%
      🔄 Integration (moderate)       30%
     📦 Unit (fast, cheap)            60%
```

### Example Test
```python
@pytest.mark.asyncio
async def test_tutor_agent_respects_harvard_principles():
    """Verify Tutor follows Harvard 7 principles"""
    agent = TutorAgent("tutor", mock_state, mock_bus, mock_llm)
    
    response = await agent.execute(
        learner_id="test_001",
        concept_id="sql_select",
        user_message="What is SELECT?"
    )
    
    # Principle 1: Not direct answer
    assert not response['message'].startswith("SELECT is")
    
    # Principle 2: Not too long
    assert len(response['message'].split()) < 50
    
    # Principle 4: Contains question
    assert '?' in response['message']
```

---

## ADR-11: LLM Provider Selection (Multi-provider support)

### Context
Which LLM to use?
- OpenAI GPT-4o
- Google Gemini 2.5 Pro
- Anthropic Claude Opus

### Decision
**✅ APPROVED**: Support all three (flexible, no vendor lock-in)

### Implementation
```python
class LLMService:
    @classmethod
    def create(provider: str) -> BaseLanguageModel:
        if provider == "openai":
            return OpenAI(model="gpt-4o")
        elif provider == "google":
            return Gemini(model="gemini-2.5-pro")
        elif provider == "anthropic":
            return Claude(model="claude-opus-4.1")
```

### Recommendation for Thesis
1. **Primary**: OpenAI GPT-4o
   - Best overall performance
   - Most stable API
   - Largest context window (128k)

2. **Secondary**: Google Gemini 2.5 Pro with LearnLM
   - Has learning science fine-tuning (2025)
   - Slightly cheaper
   - Native multimodal (good for future video integration)

3. **Tertiary**: Claude Opus
   - Best reasoning (for complex path planning)
   - Longest context (200k)
   - Great for open-ended questions

### Cost Analysis
```
Assuming 1000 learners, 5 interactions/learner/day:
- OpenAI GPT-4o: ~$50/day = $1500/month
- Gemini Pro: ~$30/day = $900/month
- Claude Opus: ~$70/day = $2100/month

→ Gemini is cheapest but OpenAI more stable
→ For thesis: Use free tier / small scale OK
```

---

## Summary Table: All Key Decisions

| ADR | Component | Choice | Rationale | Risk |
|-----|-----------|--------|-----------|------|
| 1 | Architecture | Multi-Agent | Separation of concerns, scalability | Complexity |
| 2 | Knowledge Store | Neo4j KG | Natural for learning domain | Learning curve |
| 3 | LLM Framework | LlamaIndex | Property Graph Index + AgentWorkflow | Newer technology |
| 4 | Grounding | 3-Layer RAG | Reduce hallucinations, increase trust | Slightly slower |
| 5 | Path Planning | RL-MOPO | Adaptive, learns from feedback | Complex to tune |
| 6 | Pedagogy | Harvard 7 | Evidence-based, proven effective | Constrains design |
| 7 | State Storage | PostgreSQL | ACID transactions, audit trail | Relational overhead |
| 8 | Frontend | Next.js 14 | Server rendering + proxy routes | Single point of failure |
| 9 | Dev Ops | Docker Compose | Consistency, isolation, reproducibility | Overhead in setup |
| 10 | Testing | Pytest + E2E | Fast feedback, good coverage | Time to write tests |
| 11 | LLM Provider | Multi (OpenAI primary) | Flexibility, no lock-in | API key management |

---

## Future ADRs (Post-thesis)

1. **ADR-12**: Mobile app support (React Native?)
2. **ADR-13**: Real-time collaboration (WebSockets for group learning)
3. **ADR-14**: Video generation (from transcripts)
4. **ADR-15**: Offline mode (PWA + local storage)
5. **ADR-16**: Privacy-first storage (encryption at rest, GDPR compliance)

---

**Document Version**: 3.0  
**Last Updated**: December 2025  
**Next Review**: June 2026 (post-deployment)
