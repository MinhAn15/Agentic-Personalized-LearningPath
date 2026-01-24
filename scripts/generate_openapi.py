import sys
import os
import json
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.getcwd())

# Attempt to import app
try:
    from backend.main import app
    print("✅ Successfully imported FastAPI app")
    
    # Generate OpenAPI schema
    openapi_schema = app.openapi()
    
    # Write to file
    with open("appendix_c_openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
        
    print(f"✅ Generated appendix_c_openapi.json ({len(str(openapi_schema))} bytes)")

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Ensure you are running this from the project root.")
except Exception as e:
    print(f"❌ Error: {e}")
    # Print traceback
    import traceback
    traceback.print_exc()
