---
description: Workflow to add "Click-to-Explain" interactivity to Agent Whitebox visualizations.
---

# Whitebox Interactivity Upgrade Workflow

This workflow guides the process of upgrading a static Agent Whitebox HTML into an interactive one with Deep Dive panels.

## 1. Select Target Agent
Identify the Agent ID (2-6) you want to upgrade.
- Agent 2: Profiler
- Agent 3: Path Planner
- Agent 4: Tutor
- Agent 5: Evaluator
- Agent 6: KAG (Memory)

## 2. Identify Mermaid Nodes
Read `scripts/render_whitebox_html.py` and locate the `mermaid_sequence` for your target agent.
Extract all Node IDs (e.g., `User`, `A2`, `Neo4j`, `DB`).

## 3. Deep Dive Research (The "Truth")
For each Node ID, locate the actual implementation in the codebase.
**Goal**: Find exact Class names, Constants, and Logic.

- **Check Code**: Use `find_by_name` or `file_search` to find relevant files in `backend/`.
- **Check Specs**: Read `docs/technical_specs/AGENT_X_FULL_SPEC.md`.

**Data to Gather:**
- **Title**: Actual Class/Module Name (e.g., `SemanticChunker`).
- **Description**: 1-2 sentences technical summary.
- **Specs**: Key Configuration (e.g., `Threshold=0.85`, `Vector Dim=10`).
- **Source**: Relative path to the file (e.g., `backend/agents/profiler_agent.py`).

## 4. Construct `node_details` Dictionary
Format the gathered data into a Python dictionary structure:

```python
"node_details": {
    "NODE_ID": {
        "title": "Class Name",
        "desc": "Technical Description",
        "specs": "Config A: Val\nConfig B: Val",
        "source": "backend/path/to/file.py"
    },
    # Repeat for all nodes
}
```

## 5. Update Render Script
1. Open `scripts/render_whitebox_html.py`.
2. Locate the `AGENTS` list entry for your Agent.
3. Insert the `node_details` dictionary into the Agent's dictionary (usually after `mermaid_sequence`).

## 6. Regenerate HTML
Run the generation script:
```powershell
python scripts/render_whitebox_html.py
```

## 7. Verify
Open `docs/presentation/agent_X_whitebox.html` and verify:
- Clicking nodes opens the side panel.
- Data in the panel matches the codebase.
