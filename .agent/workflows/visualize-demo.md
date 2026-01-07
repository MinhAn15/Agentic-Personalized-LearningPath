---
description: Generate visual assets (HTML Dashboard) for the thesis presentation.
---
# Visualization Procedure

This workflow generates a local HTML dashboard containing all the visual diagrams for the Agents.

## 1. Requirement
Ensure `docs/DEMO_WORKFLOWS.md` exists and contains Mermaid diagrams.

## 2. Generate Dashboard
Run the following script to parse the markdown and generate the HTML.

```bash
python scripts/render_diagrams_html.py
```

## 3. View & Capture
1.  Open `docs/presentation/demo_dashboard.html` in your browser.
2.  Use a screenshot tool (like Snipping Tool) to capture the rendered diagrams.
3.  Paste them into your PowerPoint.
