
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

print("Checking imports...")


try:
    from backend.core.dual_kg_manager import DualKGManager
    print("[OK] DualKGManager imported")
except ImportError as e:
    print(f"[FAIL] DualKGManager failed: {e}")

try:
    from backend.core.harvard_enforcer import Harvard7Enforcer
    print("[OK] Harvard7Enforcer imported")
except ImportError as e:
    print(f"[FAIL] Harvard7Enforcer failed: {e}")

try:
    from backend.core.state_manager import CentralStateManager
    print("[OK] CentralStateManager imported")
except ImportError as e:
    print(f"[FAIL] CentralStateManager failed: {e}")

try:
    from backend.agents.tutor_agent import TutorAgent
    print("[OK] TutorAgent imported")
except ImportError as e:
    print(f"[FAIL] TutorAgent failed: {e}")

try:
    from backend.agents.path_planner_agent import PathPlannerAgent, MOPOValidator
    print("[OK] PathPlannerAgent & MOPOValidator imported")
except ImportError as e:
    print(f"[FAIL] PathPlannerAgent failed: {e}")

print("Syntax check complete.")
