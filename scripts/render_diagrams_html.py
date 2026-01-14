import re
import os

MARKDOWN_FILE = "docs/DEMO_WORKFLOWS.md"
OUTPUT_DIR = "docs/presentation"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "demo_dashboard.html")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Agentic System - Demo Flows</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({ startOnLoad: true, theme: 'neutral' });
    </script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin-bottom: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; }
        h2 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .mermaid { text-align: center; margin-top: 20px; }
        .description { color: #666; font-style: italic; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Agentic System Flows</h1>
        <p style="text-align:center">Scientific Refinement (2025)</p>
        
        <!-- CONTENT_PLACEHOLDER -->
    </div>
</body>
</html>
"""

def parse_markdown(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by H2 headers (Agents)
    sections = re.split(r'^##\s+', content, flags=re.MULTILINE)[1:] # Skip preamble
    
    diagrams = []
    
    for section in sections:
        lines = section.split('\n')
        title = lines[0].strip()
        
        # Find Mermaid blocks
        mermaid_pattern = r'```mermaid\n(.*?)\n```'
        matches = re.findall(mermaid_pattern, section, re.DOTALL)
        
        for i, code in enumerate(matches):
            diagrams.append({
                "title": title,
                "code": code.strip()
            })
            
    return diagrams

def generate_html(diagrams):
    cards_html = ""
    for d in diagrams:
        cards_html += f"""
        <div class="card">
            <h2>{d['title']}</h2>
            <div class="description">Visual Flow</div>
            <div class="mermaid">
{d['code']}
            </div>
        </div>
        """
    
    final_html = HTML_TEMPLATE.replace("<!-- CONTENT_PLACEHOLDER -->", cards_html)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print(f"[OK] Dashboard generated: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    diagrams = parse_markdown(MARKDOWN_FILE)
    generate_html(diagrams)
