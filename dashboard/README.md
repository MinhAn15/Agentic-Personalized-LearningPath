# Thesis Experiment Dashboard

Visualize real-time metrics for the Agentic Learning Path experiments.

## Setup

1. **Consolidate Data**:

   Ensure you have run the consolidation script to generate `data/analysis/all_results.json`.

   ```bash
   python scripts/consolidate_results.py
   ```

2. **Serve Dashboard**:

   Because of browser security (CORS), you cannot open `index.html` directly. You must serve it via HTTP.
   
   Run this command from the project root:

   ```bash
   python -m http.server 8000
   ```

3. **View**:

   Open browser to: [http://localhost:8000/dashboard/](http://localhost:8000/dashboard/)


## Features
- **Latency Comparison**: Agentic vs Baseline Bar Chart.
- **Success Rate**: Global pipeline health.
- **Recent Runs**: Table of last 10 executions.
