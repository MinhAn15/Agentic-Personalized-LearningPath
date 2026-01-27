# MASTER TRACKING PLAN: Agentic Personalized Learning Path
<!-- 
  WHAT: This is the consolidated roadmap for the entire thesis project.
  WHY: To track progress across all 5 phases, ensure alignment with MIS/AI goals, and facilitate future updates.
  WHEN: Updated on 2026-01-27.
-->

## Goal
Successfully build, evaluate, pilot, document, and defend the "Agentic Personalized Learning Path" system, demonstrating scientific rigor and practical application in AI Education.

## Current Phase
**Phase 5: Defense Materials** (Active) & **Phase 3: Real Learner Pilot** (Running)

## Phases

### Phase 1: Core System Architecture
<!-- 
  WHAT: Build the foundation: Multi-Agent System, Dual-KG, and Backend Infrastructure.
  STATUS: Completed
-->
- [x] **Multi-Agent Architecture**: Implemented 6 Agents (Knowledge, Profiler, Planner, Tutor, Evaluator, KAG).
- [x] **Dual-Knowledge Graph**: Setup Neo4j (Graph Structure) + Vector Store (PDF Content) with sync.
- [x] **Pedagogical Engine**: Implemented Harvard 7 Principles & Socratic Enforcer.
- [x] **Infrastructure**: Dockerized Backend, Neo4j, and Python environment.
- **Status:** complete

### Phase 2: Scientific Evaluation
<!-- 
  WHAT: Validate the system using scientific methods (Ablation Study) and define metrics.
  STATUS: Completed
-->
- [x] **Metrics Definitions**: Defined PAS (Pedagogical Alignment Score) and Learning Gain methods.
- [x] **Ablation Study**: Conducted simulation with 125 virtual learners.
- [x] **Results**: Achieved Cohen's d > 0.8 (Large Effect Size) vs Baseline.
- [x] **Tools**: Validated `scripts/run_ablation_study.py`.
- **Status:** complete

### Phase 3: Real Learner Pilot
<!-- 
  WHAT: Conduct real-world testing with human learners to gather empirical evidence.
  STATUS: In Progress (40%)
-->
- [x] **Data Ingestion**: Ingested "Modern MIS", "BI", "Project Management" content (Vector + Neo4j Verified).
- [x] **Infrastructure Readiness**: Fixed Neo4j connection issues; system ready for users.
- [ ] **Recruitment**: Recruit 5-10 Pilot Users (MIS students).
- [ ] **Tracking**: Verify `experiment_schema.sql` properly logs Pilot data.
- [ ] **Admin Dashboard**: Build simple dashboard to monitor Pilot progress.
- **Status:** in_progress

### Phase 4: Documentation (Thesis & Paper)
<!-- 
  WHAT: Document the research for academic submission (Thesis & Q1 Journal).
  STATUS: In Progress (70%)
-->
- [x] **Thesis Draft**: Version 3 completed (Structure & Main Content).
- [x] **Q1 Paper Draft**: IMRAD structure drafted.
- [x] **Whitebox Docs**: Detailed documentation for Agents 1-6.
- [ ] **Update Results**: Integrate real data from Phase 3 into Chapter Results (currently simulated).
- [ ] **Final Polish**: Review against Q1 Journal standards.
- **Status:** in_progress

### Phase 5: Defense Materials
<!-- 
  WHAT: Prepare presentation assets, slides, and demo for the Thesis Defense using the 8-step MIS Strategy.
  STATUS: Active / Just Started (15%)
-->
- [ ] **Defense Slides**: Create interactive `defense_slides.html` (Reveal.js).
- [ ] **Demo Script**: Finalize detailed "Happy Path" & "Edge Case" scripts.
- [ ] **Demo Video**: Record backup video of the system in action.
- [ ] **Rehearsal**: Run GRAVITY Check on presentation flow.
- [ ] **Visual Assets**: Generate high-quality diagrams for slides.
- **Status:** in_progress

## Key Questions & Decisions
1.  **Pilot Group Size**: Small (5-10) vs Large? -> Decision: Small first to ensure stability.
2.  **Demo Risk**: Live Demo vs Video? -> Decision: Prepare Video as Primary Backup, attempt Live if stable.
3.  **Data Sync**: How to ensure Thesis matches Code? -> Decision: Use "Whitebox" docs as source of truth.

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| **Dual-KG Architecture** | Decouples structure (Neo4j) from content (Vector) for better scalability and cleaner RAG. |
| **Local LLM/Embeddings** | Used `BAAI/bge-small-en-v1.5` to avoid API costs during heavy digestion. |
| **SQL for Experiments** | Separated experimental logs from Neo4j to ensure strict governance and easy SQL analytics (MIS standard). |
| **HTML Slides** | Used Reveal.js for slides to allow interactive embedding of Neo4j graphs directly in presentation. |

## Errors Encountered (Log)
| Error | Attempt | Resolution |
|-------|---------|------------|
| Neo4j Connection Refused | 1-4 | Fixed corrupted Docker volume/pid file by full restart & volume wipe. |
| Vector Store Lock | 1 | Waited for ingestion process to release lock before verification. |

## Next Actions (Immediate)
1.  **Defense**: Complete `defense_slides.html` content.
2.  **Defense**: Write detailed Demo Script for recording.
3.  **Pilot**: Open system for first 2-3 "Alpha" users.
