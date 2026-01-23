"""
Generate Figures for Thesis Analysis
Reads .json experiment results and generates visualization plots.

Metrics Visualized:
1. Latency (Knowledge Extraction, Profiling, Tutoring)
2. Success Rates
3. Agent Comparison (Baseline vs Agentic)
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
from typing import List, Dict

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data" / "experiments" / "results"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "analysis" / "figures"

def load_results() -> List[Dict]:
    """Load all experiment result JSONs."""
    results = []
    if not DATA_DIR.exists():
        print(f"Warning: {DATA_DIR} does not exist.")
        return []
        
    for file_path in DATA_DIR.glob("experiment_*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                results.append(data)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            
    print(f"Loaded {len(results)} experiment files.")
    return results

def extract_metrics(results: List[Dict]) -> pd.DataFrame:
    """Extract key metrics into a DataFrame."""
    rows = []
    
    for r in results:
        config = r.get("config", {})
        metrics = r.get("metrics", {})
        agents = metrics.get("agents", {})
        
        # Determine strict mode (Real vs Mock)
        mode = "Real" if config.get("use_real_llm") else "Mock"
        
        # Determine Agent Type (Baseline vs Agentic)
        # Baseline runs have use_baseline=True in config
        is_baseline = config.get("use_baseline", False)
        system_type = "Baseline (RAG)" if is_baseline else "Agentic System"
        
        # Extract Latencies
        ke_latency = agents.get("knowledge_extraction", {}).get("avg_latency_ms", 0) / 1000
        profiler_latency = agents.get("profiler", {}).get("avg_latency_ms", 0) / 1000
        tutor_latency = agents.get("tutor", {}).get("avg_latency_ms", 0) / 1000
        
        rows.append({
            "Experiment ID": r.get("experiment_id")[:8],
            "Mode": mode,
            "System": system_type,
            "KE Latency (s)": ke_latency,
            "Profiler Latency (s)": profiler_latency,
            "Tutor Latency (s)": tutor_latency,
            "Total Duration (s)": metrics.get("experiment_duration_seconds", 0)
        })
        
    return pd.DataFrame(rows)

def plot_latency_comparison(df: pd.DataFrame):
    """Generate Latency Comparison Chart."""
    if df.empty:
        print("No data to plot.")
        return

    # Filter for Real execution if possible, else plot all
    real_df = df[df["Mode"] == "Real"]
    if real_df.empty:
        print("No REAL run data found. plotting MOCK data instead.")
        plot_data = df
    else:
        plot_data = real_df

    plt.figure(figsize=(10, 6))
    sns.barplot(data=plot_data, x="System", y="Tutor Latency (s)", hue="System", palette="viridis")
    plt.title("Tutor Response Latency: Baseline vs Agentic")
    plt.ylabel("Latency (seconds)")
    plt.xlabel("System Architecture")
    
    output_path = OUTPUT_DIR / "latency_comparison.png"
    plt.savefig(output_path)
    try:
        print(f"Saved figure to {output_path}")
    except UnicodeEncodeError:
        print(f"Saved figure to {output_path.name}")
    plt.close()

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    results = load_results()
    if not results:
        print("No results found. Run experiments first.")
        return
        
    df = extract_metrics(results)
    print("\nMetrics Summary:")
    print(df.groupby(["System", "Mode"]).mean(numeric_only=True))
    
    plot_latency_comparison(df)

if __name__ == "__main__":
    main()
