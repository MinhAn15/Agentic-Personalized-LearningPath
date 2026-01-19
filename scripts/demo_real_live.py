import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def print_step(step, msg):
    print(f"\n{'='*60}")
    print(f"STEP {step}: {msg}")
    print(f"{'='*60}")

def print_result(data):
    print("\nResult:")
    print(json.dumps(data, indent=2))

def demo():
    print("Starting Agentic Learning Path DEMO")
    print(f"Target URL: {BASE_URL}")
    
    # Check Health
    try:
        r = requests.get(f"http://localhost:8000/health")
        if r.status_code != 200:
            print("[X] System is not healthy. Please check docker containers and backend.")
            return
        print("[OK] System Health Check Passed")
    except Exception as e:
        print(f"[X] Connection failed: {e}")
        return

    # 1. Ingest Content
    print_step(1, "Knowledge Extraction Agent (Ingest Content)")
    content = """
    # Python Variables and Data Types
    
    A variable is a container for storing data values. In Python, variables are created the moment you assign a value to them.
    
    ## Variable Names
    A variable name must start with a letter or the underscore character. It cannot start with a number.
    
    ## Data Types
    Python has the following data types built-in by default:
    - Text Type: str
    - Numeric Types: int, float, complex
    - Sequence Types: list, tuple, range
    
    Example:
    x = 5
    y = "John"
    print(x)
    print(y)
    """
    
    payload_ingest = {
        "content": content,
        "document_type": "LECTURE",
        "title": "Python Variables Basics"
    }
    
    r = requests.post(f"{BASE_URL}/agents/knowledge-extraction", json=payload_ingest)
    if r.status_code == 200:
        print_result(r.json())
    else:
        print(f"[X] Error {r.status_code}: {r.text}")
    
    print("\n[Waiting 20s for Gemini API Safe-Zone...]")
    time.sleep(20)

    # 2. Profile Learner
    print_step(2, "Profiler Agent (Create Profile)")
    payload_profile = {
        "message": "I am a complete beginner and I want to learn Python for Data Science. I have about 5 hours a week.",
        "learner_name": "DemoUser"
    }
    
    learner_id = None
    r = requests.post(f"{BASE_URL}/agents/profiler", json=payload_profile)
    if r.status_code == 200:
        res = r.json()
        print_result(res)
        if res.get("success"):
            # Extract learner_id from result.profile.learner_id
            # Structure: result -> result -> profile -> learner_id or result -> result -> learner_id
            # Based on previous output: result -> result -> learner_id
            learner_id = res["result"].get("learner_id")
            # If not there, checking result -> result -> profile -> learner_id
            if not learner_id and "profile" in res["result"]:
                 learner_id = res["result"]["profile"].get("learner_id")
    else:
        print(f"[X] Error {r.status_code}: {r.text}")
    
    if not learner_id:
        print("[!] Could not extract learner_id, using fallback 'demo_learner_01'")
        learner_id = "demo_learner_01"
    
    print(f"\nUsing Learner ID: {learner_id}")

    print("\n[Waiting 20s for Gemini API Safe-Zone...]")
    time.sleep(20)

    # 3. Plan Path
    print_step(3, "Path Planner Agent (Generate Path)")
    payload_plan = {
        "learner_id": learner_id,
        "goal": "Master Python Variables"
    }
    
    r = requests.post(f"{BASE_URL}/paths/plan", json=payload_plan)
    if r.status_code == 200:
        print_result(r.json())
    else:
        print(f"[X] Error {r.status_code}: {r.text}")

    print("\n[Waiting 20s for Gemini API Safe-Zone...]")
    time.sleep(20)

    # 4. Tutoring Session
    print_step(4, "Tutor Agent (Ask Question)")
    payload_tutor = {
        "learner_id": learner_id,
        "question": "What is a variable?",
        "concept_id": "concept_python_variables",
        "hint_level": 1
    }
    
    # Correct Endpoint: /tutoring/ask (verified in tutor_routes.py)
    r = requests.post(f"{BASE_URL}/tutoring/ask", json=payload_tutor) 
    
    if r.status_code == 200:
        print_result(r.json())
    else:
        print(f"[X] Error {r.status_code}: {r.text}")

    print("\n[Waiting 20s for Gemini API Safe-Zone...]")
    time.sleep(20)

    # 5. Evaluate
    print_step(5, "Evaluator Agent (Submit Answer)")
    payload_eval = {
        "learner_id": learner_id,
        "concept_id": "concept_python_variables",
        "learner_response": "A variable is like a container that stores data values.",
        "expected_answer": "Container for storing data values",
        "explanation": "Definition of variable"
    }
    
    r = requests.post(f"{BASE_URL}/evaluation/evaluate", json=payload_eval)
    if r.status_code == 200:
        print_result(r.json())
    else:
         print(f"[X] Error {r.status_code}: {r.text}")

if __name__ == "__main__":
    demo()
