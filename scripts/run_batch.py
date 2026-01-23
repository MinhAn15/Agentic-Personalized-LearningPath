"""
Batch Experiment Runner for Thesis Data Collection
Automates the execution of multiple experiment runs to generate statistical data.

Features:
- Alternates between Control (Baseline) and Treatment (Agentic) groups.
- Handles Rate Limiting (Sleep intervals).
- Resilient to individual run failures.
- Progress tracking.

Usage:
    python scripts/run_batch.py --n 100 --real
    python scripts/run_batch.py --n 10 --mock
"""

import argparse
import subprocess
import time
import sys
import random
from pathlib import Path
from datetime import datetime

# Configuration
PYTHON_EXE = sys.executable
SCRIPT_PATH = Path(__file__).parent / "run_experiment.py"
LOG_DIR = Path(__file__).parent.parent / "data" / "experiments" / "logs"

def run_single_experiment(is_baseline: bool, use_real: bool, run_id: int):
    """Execute a single run of run_experiment.py"""
    
    cmd = [PYTHON_EXE, str(SCRIPT_PATH)]
    
    if use_real:
        cmd.append("--real")
        
    if is_baseline:
        cmd.append("--baseline")
        
    # Alternate learners if needed, or random
    learners = ["alice", "bob", "charlie", "david", "eve"]
    learner = random.choice(learners) 
    cmd.extend(["--learner", learner])
    
    mode = "BASELINE" if is_baseline else "AGENTIC"
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting Run {run_id}: {mode} ({learner})...")
    
    start = time.time()
    try:
        # Run subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False # Don't raise exception on non-zero exit
        )
        
        duration = time.time() - start
        
        # Log Output
        log_file = LOG_DIR / f"run_{run_id}_{mode.lower()}.log"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(result.stdout)
            f.write("\n=== STDERR ===\n")
            f.write(result.stderr)
            
        if result.returncode == 0:
            print(f"Run {run_id} Success ({duration:.1f}s)")
            return True
        else:
            print(f"Run {run_id} Failed (Exit Code {result.returncode}) - See {log_file}")
            return False
            
    except Exception as e:
        print(f"Run {run_id} Exception: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Batch Experiment Runner")
    parser.add_argument("--n", type=int, default=10, help="Total number of runs")
    parser.add_argument("--real", action="store_true", help="Use Real LLM")
    parser.add_argument("--delay", type=int, default=10, help="Delay between runs (seconds)")
    args = parser.parse_args()
    
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting Batch: {args.n} runs | Mode: {'REAL' if args.real else 'MOCK'}")
    try:
        print(f"Logs: {LOG_DIR}")
    except UnicodeEncodeError:
        print(f"Logs stored in: {LOG_DIR.name}")
    
    successful_runs = 0
    failed_runs = 0
    
    for i in range(1, args.n + 1):
        # Alternate between Baseline and Agentic
        # Odd runs = Agentic, Even runs = Baseline (or vice versa)
        is_baseline = (i % 2 == 0)
        
        success = run_single_experiment(is_baseline, args.real, i)
        
        if success:
            successful_runs += 1
        else:
            failed_runs += 1
            
        # Progress
        print(f"Progress: {i}/{args.n} | Success: {successful_runs} | Fail: {failed_runs}")
        
        # Sleep to be nice to APIs
        if i < args.n:
            print(f"Sleeping {args.delay}s...")
            time.sleep(args.delay)
            
    print("\n" + "="*50)
    print("BATCH COMPLETE")
    print(f"Total: {args.n}")
    print(f"Success: {successful_runs}")
    print(f"Failed: {failed_runs}")
    print("="*50)

if __name__ == "__main__":
    main()
