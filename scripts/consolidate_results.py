"""
Consolidate Experiment Results
Reads all experiment result JSON files and merges them into a single summary file
optimized for the Visualization Dashboard.
"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data" / "experiments" / "results"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "analysis" / "all_results.json"

def main():
    if not DATA_DIR.exists():
        print(f"Directory not found: {DATA_DIR}")
        return

    all_runs = []
    
    try:
        print(f"Scanning {DATA_DIR}...")
    except UnicodeEncodeError:
        print(f"Scanning directory: {DATA_DIR.name}")
    files = sorted(DATA_DIR.glob("experiment_*.json"))
    
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Extract lightweight summary for the dashboard to avoid loading massive files
                config = data.get("config", {})
                metrics = data.get("metrics", {})
                agents = metrics.get("agents", {})
                
                summary = {
                    "experiment_id": data.get("experiment_id"),
                    "timestamp": data.get("timestamp"),
                    "mode": "REAL" if config.get("use_real_llm") else "MOCK",
                    "type": "BASELINE" if config.get("use_baseline") else "AGENTIC",
                    "learner": config.get("learner_profile", "unknown"),
                    "duration": metrics.get("experiment_duration_seconds", 0),
                    "latencies": {
                        "ke": agents.get("knowledge_extraction", {}).get("avg_latency_ms", 0),
                        "profiler": agents.get("profiler", {}).get("avg_latency_ms", 0),
                        "tutor": agents.get("tutor", {}).get("avg_latency_ms", 0),
                    },
                    "status": "SUCCESS" if "error" not in data else "FAILED"
                }
                
                all_runs.append(summary)
                
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_runs, f, indent=2)
        
    try:
        print(f"Consolidated {len(all_runs)} runs into {OUTPUT_FILE.name}")
    except UnicodeEncodeError:
        print(f"Consolidated {len(all_runs)} runs")

if __name__ == "__main__":
    main()
