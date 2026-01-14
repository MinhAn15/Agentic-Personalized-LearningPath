---
description: Generate visual assets (HTML Dashboard) for the thesis presentation.
---

# Visualization Procedure

This workflow generates detailed HTML whitebox visualizations for each Agent.

---

## 1. Whitebox HTML Structure

Each `agent_N_whitebox.html` must include:

### Header Section
- Agent name and role description (Vietnamese)
- Scientific basis badges (paper references)
- Tech stack badges (Neo4j, Redis, etc.)
- "Vai trò" explanation: What this agent does in the system
- "Tại sao cần thiết" explanation: Why this agent is necessary

### Sequence Diagram
- Mermaid `sequenceDiagram` showing end-to-end flow
- `section-intro` explaining what the diagram shows
- Key Insight box after diagram

### Phase Cards (one per major phase)
Each phase card includes:
1. **Phase Header**: Color-coded, title + step number
2. **Phase Explanation** (yellow box): 
   - "Mục đích" (purpose)
   - "Tại sao quan trọng" (why important)
   - Technical details in Vietnamese
3. **Steps** with:
   - Step name + method call badge
   - `step-description`: Vietnamese explanation of logic
   - **IO Grid**: INPUT → MECHANISM → OUTPUT boxes
   - `scientific-note`: Paper reference or technical note

### Constants Summary Table
- All constants used in this agent
- Values, file locations, purposes

---

## 2. CSS Design Guidelines

```css
/* Color scheme */
--primary: #2563eb;     /* Blue - for inputs */
--secondary: #7c3aed;   /* Purple - for mechanisms */
--success: #059669;     /* Green - for outputs */
--warning: #d97706;     /* Orange - for phase explanations */
--danger: #dc2626;      /* Red - for Phase 5 */

/* Explanation boxes */
.phase-explanation: yellow gradient, left border orange
.scientific-note: blue gradient, left border primary
.key-insight: green border, green background
```

---

## 3. File Locations

| Agent | HTML Path |
|-------|-----------|
| Agent 1 | `docs/presentation/agent_1_whitebox.html` |
| Agent 2 | `docs/presentation/agent_2_whitebox.html` |
| Agent 3 | `docs/presentation/agent_3_whitebox.html` |
| Agent 4 | `docs/presentation/agent_4_whitebox.html` |
| Agent 5 | `docs/presentation/agent_5_whitebox.html` |
| Agent 6 | `docs/presentation/agent_6_whitebox.html` |

---

## 4. Content Sources

For each agent, reference:
- `backend/agents/{agent}_agent.py` - Implementation
- `docs/AGENT_N_WHITEBOX.md` - Technical documentation
- `docs/SCIENTIFIC_BASIS.md` - Paper references
- `backend/core/constants.py` - Constants values

---

## 5. Generation Commands

### Simple Dashboard (from DEMO_WORKFLOWS.md)
```bash
python scripts/render_diagrams_html.py
```

### View Individual Whitebox
Open `docs/presentation/agent_N_whitebox.html` in browser

---

## 6. Required Elements Checklist

- [ ] Header with role description (Vietnamese)
- [ ] Scientific basis badges
- [ ] Mermaid sequence diagram with explanation
- [ ] Key Insight box
- [ ] Phase cards with color-coded headers
- [ ] Phase explanation (yellow box) for each phase
- [ ] Step descriptions (Vietnamese)
- [ ] IO Grid (Input/Mechanism/Output)
- [ ] Scientific notes with paper citations
- [ ] Constants summary table
- [ ] Footer with generation date

---

## 7. Language Guidelines

- **Phase explanations**: Vietnamese
- **Code references**: English (method names, constants)
- **Scientific notes**: English with Vietnamese context
- **Step descriptions**: Vietnamese, technical but accessible
