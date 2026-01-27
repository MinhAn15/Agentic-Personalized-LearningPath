import re
import os

MARKDOWN_FILE = r"c:\Users\an.ly\.gemini\antigravity\brain\0a1d4978-dd5f-4bc4-bbf8-b700b59eb0d5\DEFENSE_SLIDES_CONTENT.md"
OUTPUT_FILE = r"c:\Users\an.ly\OneDrive - Orient\2026\LUẬN VĂN THẠC SĨ\Agentic-Personalized-LearningPath\docs\defense_slides.html"

# Theme - Modern Minimalist (Light Professional)
COLORS = {
    "primary": "#708090",   # Slate Gray
    "highlight": "#2c3e50", # Dark Slate / Charcoal
    "bg": "#ffffff",        # White
    "text": "#36454f"       # Charcoal
}

def parse_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    slides = []
    # Split by Slide headers (assuming format "### Slide X:")
    # First, separate sections if needed, but the structure is mainly headers
    
    # Simple regex to find slides. 
    # Logic: Content between "### Slide" and the next "### Slide" or end of file
    
    parts = re.split(r"(### Slide \d+: .*?)\n", content)
    
    # parts[0] is intro before first slide (if any)
    # parts[1] is Header, parts[2] is Content, parts[3] is Header...
    
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        body = parts[i+1].strip()
        
        # Clean up Markdown syntax for HTML
        # Bold **text** -> <b>text</b>
        body = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", body)
        # Italic *text* -> <i>text</i>
        body = re.sub(r"\*(.*?)\*", r"<i>\1</i>", body)
        # Lists - -> <li>
        lines = body.split('\n')
        html_body = ""
        in_list = False
        
        for line in lines:
            if line.strip().startswith("- "):
                if not in_list:
                    html_body += "<ul>\n"
                    in_list = True
                html_body += f"<li>{line.strip()[2:]}</li>\n"
            elif re.match(r"^\d+\.", line.strip()):
                 # Order list logic simplified for now, treating as list items
                if not in_list:
                    html_body += "<ul>\n"
                    in_list = True
                html_body += f"<li>{line.strip().split('.', 1)[1].strip()}</li>\n"
            else:
                if in_list:
                    html_body += "</ul>\n"
                    in_list = False
                if line.strip():
                     html_body += f"<p>{line}</p>\n"
        
        if in_list:
            html_body += "</ul>\n"

        # Parse Header Title
        title = header.split(":", 1)[1].strip() if ":" in header else header
        
        slides.append({
            "title": title,
            "content": html_body
        })
        
    return slides

def generate_html(slides):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APLO Thesis Defense</title>
    <style>
        body {{
            background-color: {COLORS['bg']};
            color: {COLORS['text']};
            font-family: 'DejaVu Sans', sans-serif;
            margin: 0;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }}
        .slide-container {{
            flex: 1;
            display: flex;
            align_items: center;
            justify_content: center;
            position: relative;
        }}
        .slide {{
            display: none;
            width: 80%;
            max-width: 1000px;
            padding: 40px;
            text-align: left;
            border: 2px solid {COLORS['primary']};
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
            background: rgba(0, 0, 0, 0.02);
            border-radius: 10px;
            animation: fadeIn 0.5s ease-in-out;
        }}
        .slide.active {{
            display: block;
        }}
        h2 {{
            color: {COLORS['highlight']};
            font-family: 'DejaVu Sans Bold', sans-serif;
            border-bottom: 2px solid {COLORS['primary']};
            padding-bottom: 10px;
            margin-top: 0;
        }}
        p {{
            font-size: 1.2em;
            line-height: 1.6;
        }}
        li {{
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        strong, b {{
            color: {COLORS['highlight']};
        }}
        .controls {{
            height: 60px;
            display: flex;
            justify-content: center;
            align-items: center;
            background: rgba(0,0,0,0.5);
            gap: 20px;
        }}
        button {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
            font-family: 'DejaVu Sans Bold', sans-serif;
        }}
        button:hover {{
            background-color: {COLORS['highlight']};
            color: {COLORS['bg']};
        }}
        button:disabled {{
            background-color: gray;
            cursor: not-allowed;
        }}
        .progress-bar {{
            position: absolute;
            bottom: 60px;
            left: 0;
            height: 5px;
            background-color: {COLORS['highlight']};
            width: 0%;
            transition: width 0.3s;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body>

<div class="slide-container">
"""
    for i, slide in enumerate(slides):
        active_class = " active" if i == 0 else ""
        html += f"""
    <div class="slide{active_class}" id="slide-{i}">
        <h2>{slide['title']}</h2>
        <div class="content">{slide['content']}</div>
        <div style="position: absolute; bottom: 10px; right: 20px; font-size: 0.8em; color: gray;">
            Slide {i+1} / {len(slides)}
        </div>
    </div>
"""

    html += f"""
    <div class="progress-bar" id="progress"></div>
</div>

<div class="controls">
    <button id="prevBtn" onclick="changeSlide(-1)">Previous</button>
    <button id="nextBtn" onclick="changeSlide(1)">Next</button>
</div>

<script>
    let currentSlide = 0;
    const totalSlides = {len(slides)};
    
    function updateSlide() {{
        document.querySelectorAll('.slide').forEach((s, index) => {{
            s.classList.remove('active');
            if (index === currentSlide) {{
                s.classList.add('active');
            }}
        }});
        
        const progress = ((currentSlide + 1) / totalSlides) * 100;
        document.getElementById('progress').style.width = progress + '%';
        
        document.getElementById('prevBtn').disabled = currentSlide === 0;
        document.getElementById('nextBtn').disabled = currentSlide === totalSlides - 1;
    }}

    function changeSlide(direction) {{
        const next = currentSlide + direction;
        if (next >= 0 && next < totalSlides) {{
            currentSlide = next;
            updateSlide();
        }}
    }}
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {{
        if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'Enter') {{
            changeSlide(1);
        }} else if (e.key === 'ArrowLeft') {{
            changeSlide(-1);
        }}
    }});

    updateSlide();
</script>

</body>
</html>
"""
    return html

def main():
    if not os.path.exists(MARKDOWN_FILE):
        print(f"Error: Markdown file not found at {MARKDOWN_FILE}")
        return

    slides = parse_markdown(MARKDOWN_FILE)
    print(f"Parsed {len(slides)} slides.")
    
    html_content = generate_html(slides)
    
    # Ensure docs directory
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Slides generated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
