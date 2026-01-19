import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Try to find it in .env file in parent directories if not loaded
    print("GOOGLE_API_KEY not found in env. Checking manually...")
    # Add your logic here or just fail if strict
    
if not api_key:
    print("❌ Error: GOOGLE_API_KEY is not set.")
    exit(1)

genai.configure(api_key=api_key)

print("\n🚀 AVAILABLE GEMINI MODELS:")
print("="*40)
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            display_name = getattr(m, 'display_name', m.name)
            print(f"- {m.name} (Display: {display_name})")
except Exception as e:
    print(f"❌ Error listing models: {e}")
print("="*40)
print("\nSuggested for 'flash': gemini-2.0-flash-exp (if available) or gemini-1.5-flash")
