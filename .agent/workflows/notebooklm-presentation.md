# NotebookLM Presentation Workflow

This workflow provides a structured approach to using **Google NotebookLM** for creating thesis presentation slides from the Agentic Personalized Learning Path documentation.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NOTEBOOKLM FEEDBACK LOOP                             │
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ UPLOAD   │───►│ PROMPT   │───►│ REVIEW   │───►│ REFINE   │──┐       │
│  │ Context  │    │ Generate │    │ Output   │    │ Iterate  │  │       │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │       │
│       ▲                                                          │       │
│       └──────────────────────────────────────────────────────────┘       │
│                         (Until Quality Achieved)                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Upload Context Files to NotebookLM

### Essential Files (MUST UPLOAD):

| Priority | File | Purpose | Location |
|----------|------|---------|----------|
| 1️⃣ | `NOTEBOOKLM_CONTEXT.md` | Master context document | `docs/NOTEBOOKLM_CONTEXT.md` |
| 2️⃣ | `SCIENTIFIC_BASIS.md` | Theoretical foundation | `docs/SCIENTIFIC_BASIS.md` |
| 3️⃣ | `AGENT_1_WHITEBOX.md` | Agent 1 details | `docs/AGENT_1_WHITEBOX.md` |
| 3️⃣ | `AGENT_2_WHITEBOX.md` | Agent 2 details | `docs/AGENT_2_WHITEBOX.md` |
| 3️⃣ | `AGENT_3_WHITEBOX.md` | Agent 3 details | `docs/AGENT_3_WHITEBOX.md` |
| 3️⃣ | `AGENT_4_WHITEBOX.md` | Agent 4 details | `docs/AGENT_4_WHITEBOX.md` |
| 3️⃣ | `AGENT_5_WHITEBOX.md` | Agent 5 details | `docs/AGENT_5_WHITEBOX.md` |
| 3️⃣ | `AGENT_6_WHITEBOX.md` | Agent 6 details | `docs/AGENT_6_WHITEBOX.md` |

### Optional Supporting Files:

| File | Purpose |
|------|---------|
| `projectbrief.md` | High-level overview |
| `systemPatterns.md` | Architectural patterns |
| SOTA PDFs (LightRAG, ToT, etc.) | Original papers for validation |

---

## Step 2: Set NotebookLM Notebook Instructions

Copy this into NotebookLM's "Notebook Instructions" field:

```
You are helping me create a Master's Thesis presentation about an Agentic AI system for Personalized Learning.

Context:
- This is a 6-Agent Multi-Agent System for adaptive learning
- Each agent implements a SOTA paper (LightRAG, LKT, ToT, CoT, JudgeLM, MemGPT)
- The thesis is in Vietnamese but technical terms should remain in English
- The presentation should be academic but accessible

When I ask for slides:
1. Use clear structure (Title, Key Points, Diagram Ideas)
2. Include the SOTA paper reference with proper citation
3. Highlight the CONTRIBUTION (what's new vs the paper)
4. Keep bullet points concise (max 3 lines each)
5. Suggest Mermaid diagrams where appropriate

Output format per slide:
---
## Slide N: [Title]

**Key Message**: [One sentence summary]

**Bullet Points**:
• Point 1
• Point 2
• Point 3

**Diagram Suggestion**: [Description]

**Speaker Notes**: [What to say]
---
```

---

## Step 3: Prompt Templates for Slide Generation

### 3.1 System Overview Slide
```
Create a slide introducing the 6-Agent architecture.
Include: Purpose, High-level flow, Key differentiation from traditional LMS.
```

### 3.2 Per-Agent Slides (Repeat for each)
```
Create a presentation slide for Agent N ([Agent Name]).

Include:
1. Role in the system
2. SOTA paper implemented (name, year, key insight)
3. Key mechanism (ONE core innovation)
4. Input → Output flow
5. Evaluation metrics (from Whitebox Section 5)

Format: Vietnamese title, English technical terms.
```

### 3.3 Integration Slide
```
Create a slide showing how all 6 agents work together.
Show the data flow and event-driven communication.
Reference the "System Patterns" document.
```

### 3.4 Contribution Slide
```
Create a thesis contribution slide summarizing:
1. What's new in this implementation vs baseline
2. Key innovations per agent
3. Academic contributions for defense
```

---

## Step 4: Review & Iterate

### Quality Checklist:
- [ ] Accurate technical details?
- [ ] Proper SOTA paper citations?
- [ ] Clear contribution claim?
- [ ] Not overclaiming (honest about limitations)?
- [ ] Diagrams make sense?

### Refinement Prompts:

**If too generic:**
```
This is too generic. Reference specific details from AGENT_X_WHITEBOX.md:
- The exact algorithm names (e.g., _predict_mastery_lkt)
- The specific thresholds (e.g., 0.7, 0.85)
- The data structures (e.g., 10-dim vector, WorkingMemory class)
```

**If missing evaluation:**
```
Add the evaluation methodology from Section 5 of the Whitebox.
Include the target metrics and baseline comparisons.
```

**If too long:**
```
This is too long for a slide. Condense to:
- Max 3 bullet points
- Max 2 lines per bullet
- One key takeaway per slide
```

---

## Step 5: Export & Finalize

1. Copy NotebookLM output to a markdown file
2. Use a Markdown-to-PPT tool (e.g., Marp, reveal.js)
3. Or manually create slides in PowerPoint/Google Slides

---

## Quick Reference: Agent → SOTA Mapping

| Agent | Role | SOTA Paper | Key Mechanism |
|-------|------|------------|---------------|
| 1 | Knowledge Extraction | LightRAG (Guo 2024) | Edge-Attribute Thematic Indexing |
| 2 | Learner Profiler | LKT (Lee 2024) | Semantic Mastery Prediction |
| 3 | Path Planner | ToT (Yao 2023) | Beam Search Curriculum |
| 4 | Tutor | CoT (Wei 2022) | Hidden CoT + Slicing |
| 5 | Evaluator | JudgeLM (Zhu 2023) | Reference-as-Prior Scoring |
| 6 | Memory (KAG) | MemGPT (Packer 2023) | Tiered Memory + Heartbeat |
