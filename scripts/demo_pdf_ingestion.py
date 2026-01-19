import requests
import json
import time
import sys
import os
from pypdf import PdfReader

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
DEMO_LEARNER_ID = "demo_learner_01"
SLEEP_INTERVAL = 5  # Reduced sleep for local demo

def print_step(step_name):
    print("\n" + "="*60)
    print(f"STEP: {step_name}")
    print("="*60)

def extract_text_from_pdf(pdf_path):
    print(f"[*] Reading PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"[!] Error: File not found: {pdf_path}")
        return None
    
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        print(f"[*] Extracted {len(text)} characters.")
        return text
    except Exception as e:
        print(f"[!] Error reading PDF: {e}")
        return None

def run_real_ingestion(pdf_path):
    print(f"[*] Target URL: {BASE_URL}")

    # 1. Read PDF
    content = extract_text_from_pdf(pdf_path)
    if not content:
        return

    # 2. Knowledge Extraction (REAL)
    print_step(f"Knowledge Extraction (REAL INGESTION)")
    payload = {
        "content": content,
        "document_type": "LECTURE",
        "title": os.path.basename(pdf_path),
        "force_real": True  # <--- OVERRIDE MOCK
    }
    
    try:
        response = requests.post(f"{BASE_URL}/agents/knowledge-extraction", json=payload)
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"[X] Error {response.status_code}: {response.text}")
            return
    except Exception as e:
        print(f"[!] Connection Error: {e}")
        return

    time.sleep(SLEEP_INTERVAL)

    # 3. Profiler (Mock)
    print_step("Profiler Agent (Mock)")
    payload_profiler = {
        "message": "I want to learn about the concepts in this document.",
        "learner_name": "DemoUser"
    }
    try:
        response = requests.post(f"{BASE_URL}/agents/profiler", json=payload_profiler)
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"[!] Error: {e}")

    time.sleep(SLEEP_INTERVAL)

    # 4. Path Planner (Mock)
    print_step("Path Planner Agent (Mock)")
    payload_path = {
        "learner_id": DEMO_LEARNER_ID,
        "goal": "Master concepts"
    }
    try:
        response = requests.post(f"{BASE_URL}/paths/plan", json=payload_path)
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/demo_pdf_ingestion.py <path_to_pdf>")
        # Create a dummy PDF if none provided? 
        # For now just exit
        print("Creating dummy PDF for testing...")
        from reportlab.pdfgen import canvas
        dummy_path = "dummy_course.pdf"
        c = canvas.Canvas(dummy_path)
        c.drawString(100, 750, "Introduction to Python Variables")
        c.drawString(100, 730, "A variable is a created storage location for data.")
        c.drawString(100, 710, "In Python, variables are created when you assign a value to it.")
        c.save()
        run_real_ingestion(dummy_path)
    else:
        run_real_ingestion(sys.argv[1])
