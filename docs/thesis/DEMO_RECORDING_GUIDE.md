# 🎥 Thesis Demo Recording Guide

This guide ensures you capture a professional, high-quality technical demonstration of the **Agentic Personalized Learning Path** system.

## 1. Preparation Checklist 📋

### Environment
- [ ] **Dual Screen Setup** (Recommended):
    - **Screen 1 (Left)**: VS Code Terminal (for running scripts).
    - **Screen 2 (Right)**: Web Browser (Chrome/Edge) showing the **Demo Dashboard**.
- [ ] **Clean Desktop**: Close irrelevant apps/notifications.
- [ ] **Recording Software**: OBS Studio, Camtasia, or Zoom (Local Record).

### System State
1.  **Ensure Backend is Running**:
    ```powershell
    docker ps --filter name=agentic-backend
    # Status should be "Up (healthy)"
    ```
2.  **Open Dashboard**:
    - Open `docs/presentation/demo_dashboard.html` in browser.
    - Confirm "🟢 System Online" badge is green.

### Assets
- [ ] **Target PDF**: Have a sample PDF ready (e.g., `Course.pdf` or verify valid path).

## 2. Recording Script 🎬

Follow this sequence for the video:

| Time | Action | Screen Focus | Narration Key Points |
| :--- | :--- | :--- | :--- |
| **0:00** | **Intro** | **Dashboard** (Top Card) | "This is the 'Gravity' Agentic System. It enables personalized learning via a Multi-Agent architecture." |
| **0:15** | **The Goal** | **Dashboard** (Agent 1 Card) | "First, we ingest raw knowledge. Instead of static text, we use an intelligent Agent to build a Knowledge Graph." |
| **0:30** | **Trigger** | **Terminal** | "I will now feed a real PDF university lecture into the system."<br>`python scripts/demo_pdf_ingestion.py "path/to/my.pdf"` |
| **0:45** | **Processing** | **Terminal** (Logs) | "The System analyzes the document... You can see it Chunking, Extracting Entities, and Validating against the schema." |
| **1:00** | **Visualization** | **Dashboard** (End-to-End Card) | "As the data flows, Agent 1 (Knowledge) hands off to Agent 2 (Profiler)..." (Point to the flow diagram). |
| **1:15** | **Personalization** | **Terminal** (Output) | "Here we see the system simulated a 'Visual Beginner' learner and generated a tailored Learning Path." |
| **1:30** | **Conclusion** | **Dashboard** (Full View) | "This demonstrates the complete loop from Raw Data to Personalized Instruction." |

## 3. Execution Commands ⌨️

**Terminal A (Backend Logs - Optional background visual):**
```powershell
docker logs -f agentic-backend
```

**Terminal B (The Driver):**
```powershell
# Run the demo script using your specific Python path
c:\Users\an.ly\AppData\Local\Programs\Python\Python312\python.exe scripts/demo_pdf_ingestion.py "path/to/your/document.pdf"
```

## 4. Pro Tips 🌟

*   **Pause & Explain**: Don't rush code execution. Let the logs scroll a bit, then pause to highlight a specific JSON output (like "concepts_extracted: 25").
*   **Zoom In**: Ensure VS Code font size and Browser zoom are large enough for a projector (125-150%).
*   **Mouse Movement**: Move mouse deliberately. Avoid jittery movements.
*   **Backup**: If live demo fails, you have this recording!

**Good luck!** 🚀
