import os
import datetime

OUTPUT_DIR = "docs/presentation"

# CSS & Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{agent_name} - Deep Dive Whitebox</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'neutral', securityLevel: 'loose' }});
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #0f172a;     /* Slate 900 */
            --accent: #3b82f6;      /* Blue 500 */
            --success: #10b981;     /* Emerald 500 */
            --warning: #f59e0b;     /* Amber 500 */
            --danger: #ef4444;      /* Red 500 */
            --bg: #f8fafc;
            --code-bg: #1e293b;
            --code-text: #e2e8f0;
        }}
        
        body {{ font-family: 'Inter', sans-serif; padding: 40px; background: var(--bg); color: #334155; line-height: 1.6; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        
        /* Header */
        .header {{ background: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 40px; border-top: 6px solid var(--accent); }}
        .header h1 {{ margin: 0; color: var(--primary); font-size: 2.8em; letter-spacing: -0.02em; }}
        .role-title {{ font-size: 1.4em; color: #64748b; margin-top: 10px; font-weight: 500; }}
        
        .badges {{ margin-top: 25px; display: flex; gap: 12px; flex-wrap: wrap; }}
        .badge {{ padding: 6px 14px; border-radius: 24px; font-weight: 600; font-size: 0.9em; }}
        .badge-science {{ background: #eff6ff; color: var(--accent); border: 1px solid #bfdbfe; }}
        .badge-tech {{ background: #f0fdf4; color: var(--success); border: 1px solid #bbf7d0; }}
        
        /* Diagram */
        .card {{ background: white; padding: 30px; border-radius: 16px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
        .key-insight {{ 
            margin-top: 20px; padding: 20px; 
            border-left: 4px solid var(--warning); 
            background: #fffbeb; color: #92400e;
            font-size: 1.1em;
        }}
        
        /* Phase Steps */
        .phase-section h2 {{ color: var(--primary); border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-top: 0; }}
        
        .step {{ margin-bottom: 40px; background: white; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }}
        .step-header {{ 
            padding: 15px 25px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;
            display: flex; justify-content: space-between; align-items: center;
        }}
        .step-title {{ font-weight: 700; color: var(--primary); font-size: 1.1em; }}
        .method-code {{ font-family: 'Fira Code', monospace; background: #e2e8f0; color: #475569; padding: 4px 8px; border-radius: 6px; font-size: 0.9em; }}
        
        .step-body {{ padding: 25px; }}
        .step-desc {{ font-size: 1.05em; margin-bottom: 20px; color: #1e293b; }}
        
        /* IO Grid */
        .io-grid {{ display: grid; grid-template-columns: 1fr 1.5fr 1fr; gap: 20px; margin-bottom: 20px; }}
        .io-box {{ padding: 15px; border-radius: 8px; font-size: 0.95em; }}
        .io-label {{ text-transform: uppercase; font-size: 0.75em; font-weight: 700; margin-bottom: 8px; letter-spacing: 0.05em; }}
        
        .io-input {{ background: #f1f5f9; border: 1px solid #cbd5e1; }}
        .io-mech {{ background: #eef2ff; border: 1px solid #c7d2fe; }}
        .io-output {{ background: #f0fdf4; border: 1px solid #bbf7d0; }}
        
        /* Deep Dive collapsible */
        details.deep-dive {{ margin-top: 15px; border: 1px solid #e2e8f0; border-radius: 8px; }}
        details.deep-dive summary {{ 
            padding: 12px 20px; background: #f8fafc; cursor: pointer; font-weight: 600; color: var(--accent);
            list-style: none; display: flex; align-items: center; gap: 8px;
        }}
        details.deep-dive summary::before {{ content: "⚙️"; }}
        details.deep-dive[open] summary {{ border-bottom: 1px solid #e2e8f0; }}
        
        .dive-content {{ padding: 20px; background: #ffffff; }}
        
        pre {{ margin: 0; background: var(--code-bg); padding: 15px; border-radius: 8px; overflow-x: auto; }}
        code {{ font-family: 'Fira Code', monospace; color: var(--code-text); font-size: 0.9em; }}
        
        .formula-box {{ 
            background: #fff; border-left: 4px solid var(--secondary); padding: 15px; margin: 15px 0; font-family: 'Times New Roman', serif; font-style: italic; font-size: 1.1em; 
        }}

        /* Complexity Card */
        .complexity-card {{ background: #1e293b; color: white; padding: 30px; border-radius: 16px; margin-top: 40px; }}
        .complexity-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 30px; margin-top: 20px; }}
        .metric {{ text-align: center; }}
        .metric-val {{ font-size: 2em; font-weight: 700; color: var(--accent); }}
        .metric-label {{ font-size: 0.9em; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}

        /* Detail Panel */
        .backdrop {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); opacity: 0; pointer-events: none; transition: opacity 0.3s; z-index: 90; }}
        .backdrop.active {{ opacity: 1; pointer-events: all; }}
        
        .detail-panel {{ 
            position: fixed; top: 0; right: -500px; width: 450px; height: 100%; 
            background: white; box-shadow: -5px 0 15px rgba(0,0,0,0.1); 
            transition: right 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            z-index: 100; overflow-y: auto;
        }}
        .detail-panel.active {{ right: 0; }}
        
        .panel-header {{ background: var(--primary); color: white; padding: 25px; display: flex; justify-content: space-between; align-items: center; }}
        .panel-header h2 {{ margin: 0; font-size: 1.3em; }}
        
        .panel-body {{ padding: 25px; }}
        .panel-section {{ margin-bottom: 25px; font-size: 1em; color: #475569; }}
        .panel-label {{ text-transform: uppercase; font-size: 0.75em; font-weight: 700; color: #94a3b8; margin-bottom: 8px; letter-spacing: 0.05em; }}
        .panel-code {{ background: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid #cbd5e1; font-family: 'Fira Code', monospace; font-size: 0.85em; color: var(--primary); white-space: pre-wrap; }}

    </style>
</head>
<body>
    <div class="container">
        
        <div class="header">
            <div style="text-transform: uppercase; color: var(--accent); font-weight: 700; font-size: 0.9em; letter-spacing: 0.1em; margin-bottom: 10px;">Detailed Technical Specification</div>
            <h1>{agent_name}</h1>
            <div class="role-title">{agent_role_vn}</div>
            
            <p style="font-size: 1.1em; max-width: 800px; margin-top: 20px;">{why_needed}</p>
            
            <div class="badges">
                {science_badges}
                {tech_badges}
            </div>
        </div>

        <div class="card">
            <h2>Process Architecture</h2>
            <div class="mermaid">
{mermaid_sequence}
            </div>
            <div class="key-insight">
                <strong>💡 Core Deviation / Innovation:</strong> {key_insight}
            </div>
        </div>

        {phase_html}
        
        <div class="complexity-card">
            <h2>Complexity & Performance Analysis</h2>
            <div class="complexity-grid">
                {complexity_metrics}
            </div>
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #334155;">
                <h3>Performance Bottleneck</h3>
                <p>{bottleneck}</p>
            </div>
        </div>

        <div style="text-align: center; color: #94a3b8; margin-top: 60px; font-size: 0.9em;">
             Thesis Defense System • Generated by Antigravity • {gen_date}
        </div>
    </div>

    <!-- Detail Panel -->
    <div id="backdrop" class="backdrop" onclick="closeDetails()"></div>
    <div id="detail-panel" class="detail-panel">
        <div class="panel-header">
            <h2 id="panel-title">Component Details</h2>
            <button onclick="closeDetails()" style="background:none; border:none; color:white; font-size:1.5em; cursor:pointer;">×</button>
        </div>
        <div class="panel-body">
            <div id="panel-desc" class="panel-section"></div>
            
            <div class="panel-section" style="display:none; background: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid var(--accent); margin-bottom: 25px;">
                <div class="panel-label" style="color: var(--accent);">Internal Logic</div>
                <div id="panel-logic" style="color: #334155; font-size: 0.95em;"></div>
            </div>

            <div class="panel-label">Technical Specs</div>
            <pre id="panel-specs" class="panel-code"></pre>
            
            <div class="panel-label">Source Reference</div>
            <div id="panel-source" style="font-family: 'Fira Code', monospace; color: var(--accent); font-size: 0.9em;"></div>
        </div>
    </div>

    <script>
        const NODE_DETAILS = {node_details_json};

        function showDetails(nodeId) {{
            const data = NODE_DETAILS[nodeId];
            if (!data) return;

            document.getElementById('panel-title').innerText = data.title;
            document.getElementById('panel-desc').innerHTML = data.desc;
            
            // Logic Section (New)
            const logicEl = document.getElementById('panel-logic');
            if (data.logic) {{
                logicEl.innerText = data.logic;
                logicEl.parentElement.style.display = 'block';
            }} else {{
                logicEl.parentElement.style.display = 'none';
            }}

            document.getElementById('panel-specs').innerText = data.specs || "No specific configuration.";
            document.getElementById('panel-source').innerText = data.source || "System Component";
            
            document.getElementById('backdrop').classList.add('active');
            document.getElementById('detail-panel').classList.add('active');
        }}

        function closeDetails() {{
            document.getElementById('backdrop').classList.remove('active');
            document.getElementById('detail-panel').classList.remove('active');
        }}

        // Auto-attach clicks after Mermaid renders
        // Note: We use the native mermaid click directive in the graph definition
    </script>
</body>
</html>
"""

AGENTS = [
    {
        "id": 1,
        "name": "Agent 1: Knowledge Extraction",
        "role_vn": "The Librarian (Thủ thư)",
        "why_needed": "Chuyển đổi tài liệu phi cấu trúc thành Knowledge Graph 3 lớp (Concept-Relationship-Metadata) để khắc phục điểm yếu mất ngữ cảnh của RAG truyền thống.",
        "science_badges": ["LightRAG (Guo 2024)", "MultiDocFusion (2025)", "Dual-Graph Adaptation"],
        "tech_badges": ["Neo4j", "Gemini 1.5", "Redis Semaphores", "AsyncIO"],
        "key_insight": "Sử dụng 'Global Theme Injection' để định hướng trích xuất ngay từ bước chunking, và thuật toán 3-Way Similarity (Semantic+Structural+Lexical) để giải quyết xung đột thực thể.",
        "mermaid_sequence": """
graph TD
    subgraph P1[Phase 1: Ingestion]
        Doc[PDF Document] -->|Hash SHA256| Registry{Exists in Redis?}
        Registry -- No --> Chunk[MultiDocFusion Chunking]
    end
    
    subgraph P2[Phase 2: Parallel Extraction]
        Chunk -->|Semaphore=5| LLM[Gemini 1.5]
        LLM -->|Layer 1| Concepts[Concepts w/ Global Theme]
        LLM -->|Layer 2| Rels[Relationships w/ Edge Keywords]
        LLM -->|Layer 3| Meta[Metadata & Bloom Level]
    end
    
    subgraph P3[Phase 3: Resolution]
        Concepts --> ER[3-Way Entity Resolution]
        ER -->|Merge| UniqueNodes
    end
    
    subgraph P4[Phase 4: Persistence]
        UniqueNodes --> Neo4j[(Neo4j Graph)]
    end
    
    click Doc showDetails
    click Registry showDetails
    click Chunk showDetails
    click LLM showDetails
    click Concepts showDetails
    click Rels showDetails
    click Meta showDetails
    click ER showDetails
    click UniqueNodes showDetails
    click Neo4j showDetails
        """,
        "node_details": {
            "Doc": {
                "title": "Document Stream",
                "desc": "Input handler for PDF/Image/Text files. Converts binary streams to normalized text using `PyMuPDF` or `GeminiVision`.",
                "logic": "1. Validate MIME type & Magic Numbers.\n2. If PDF, use PyMuPDF to extract text layer.\n3. If Image, use Gemini Vision to OCR.\n4. Normalize to UTF-8 stream.",
                "specs": "Max Size: 50MB\nFormats: .pdf, .docx, .md, .png\nValidation: Magic Numbers check",
                "source": "backend/api/router.py"
            },
            "Registry": {
                "title": "Document Registry",
                "desc": "Idempotency layer to prevent re-processing identical documents. Uses SHA-256 hash of file content.",
                "logic": "1. Calculate SHA-256 of raw file bytes.\n2. Check Redis Set `doc_hash:{hash}`.\n3. If exists -> Reject/Return Cache.\n4. If new -> Add to Set & Proceed.",
                "specs": "Storage: Redis Set\nKey: `doc_hash:{sha256}`\nTTL: Permanent",
                "source": "backend/models/document_registry.py"
            },
            "Chunk": {
                "title": "SemanticChunker",
                "desc": "Intelligent splitter that preserves hierarchical context (MultiDocFusion). Does NOT use fixed character windows.",
                "logic": "1. Split by Paragraphs (\\n\\n).\n2. Build Tree Structure based on Headers (#, ##).\n3. Traverse Tree (DFS) to group related sections.\n4. Merge until token limit (4000) reached.",
                "specs": "Algorithm: MultiDocFusion\nMax Token: 10,000\nOverlap: Context-based (not fixed)",
                "source": "backend/utils/semantic_chunker.py"
            },
            "LLM": {
                "title": "Gemini 1.5 Pro/Flash",
                "desc": "Multimodal LLM used for extraction. Flash is used for high-volume extraction, Pro for complex reasoning.",
                "logic": "1. Construct Prompt with 'Global Theme'.\n2. Call API with Temperature=0.0.\n3. Parse JSON output.\n4. Retry on JSONDecodeError (Exponential Backoff).",
                "specs": "Model: `gemini-1.5-flash-latest`\nTemp: 0.0 (Deterministic)\nRetries: 3 (Exponential Backoff)",
                "source": "backend/core/llm_provider.py"
            },
            "Concepts": {
                "title": "Concept Extractor",
                "desc": "Extracts entities using Pydantic validation. Enforces 'Global Theme' constraint.",
                "logic": "1. Filter terms NOT related to Domain (e.g. 'SQL').\n2. Classify Bloom's Level (Remember -> Create).\n3. Validate against `ConceptNode` schema.",
                "specs": "Output: `List[ConceptNode]`\nStrict JSON Mode: True\nField: `bloom_level` (1-6)",
                "source": "backend/agents/knowledge_extraction_agent.py"
            },
            "Rels": {
                "title": "Relationship Extractor",
                "desc": "Identifies connections between concepts. Generates 'Edge Keywords' for LightRAG indexing.",
                "logic": "1. Analyze co-occurrence in chunk.\n2. Determine Relationship Type (Prerequisite vs Related).\n3. Extract 3-5 keywords summarizing the edge.\n4. Assign Weight (0.0-1.0).",
                "specs": "Output: `List[Relationship]`\nTypes: [REQUIRES, RELATED_TO...]\nEdge Attr: `keywords`",
                "source": "backend/prompts.py"
            },
            "Meta": {
                "title": "Metadata Extractor",
                "desc": "Classifies document metadata (Domain, Difficulty, Target Audience) for filtering.",
                "logic": "1. Analyze first 1000 tokens.\n2. Extract 'Target Audience' (Beginner/Adv).\n3. Identify Top-5 semantic topics.",
                "specs": "Fields: [domain, difficulty, audience]\nAuto-Tagging: Top-5 Topics",
                "source": "backend/agents/knowledge_extraction_agent.py"
            },
            "ER": {
                "title": "Entity Resolver",
                "desc": "Merges duplicate concepts (e.g., 'Loop' vs 'Loops') using 3-Way Similarity.",
                "logic": "1. Semantic Sim (Cosine of Embeddings).\n2. Structural Sim (Jaccard of Neighbors).\n3. Lexical Sim (Levenshtein).\n4. Weighted Sum > 0.85 -> Merge.",
                "specs": "Threshold: 0.85\nWeights: Semantic(0.6) + Struct(0.3) + Lexical(0.1)\nVector: 768-dim (Gemini)",
                "source": "backend/utils/entity_resolver.py"
            },
            "UniqueNodes": {
                "title": "Merged Entity Set",
                "desc": "Final clean set of nodes after resolution. Represents the canonical knowledge.",
                "logic": "1. Deduplicate by Name (Case-insensitive).\n2. Merge Attributes (Description, Tags).\n3. Re-link Relationships to Canonical ID.",
                "specs": "Structure: `Dict[ConceptID, ConceptNode]`\nConstraint: Unique IDs",
                "source": "Memory (Runtime)"
            },
            "Neo4j": {
                "title": "Neo4j Graph DB",
                "desc": "Persistent storage for the Knowledge Graph. Stores Nodes and relationships with vector index.",
                "logic": "1. Batch Upsert (UNWIND logic).\n2. Update Vector Index.\n3. Create constraints (Unique IDs).",
                "specs": "Index: Vector (Cosine)\nConstraints: Unique(ConceptID)\nBatch Size: 500 nodes",
                "source": "backend/utils/neo4j_batch_upsert.py"
            }
        },
        "phases": [
            {
                "title": "Phase 1: Semantic Chunking",
                "steps": [
                    {
                        "name": "Multi-Document Fusion",
                        "method": "_multidocfusion_pipeline()",
                        "desc": "Phân rã tài liệu giữ lại cấu trúc phân cấp (Header heirarchy) sử dụng Pipeline 4 bước: Paragraph Split -> DSHP-LLM Tree -> DFS Grouping -> Refiner.",
                        "input": "Raw Document Stream",
                        "mech": "Hierarchical Recursive Splitter",
                        "output": "Rich Chunks (Text + Path Context)",
                        "deep_dive": {
                            "summary": "Algorithm Logic (MultiDocFusion)",
                            "code": """
async def _multidocfusion_pipeline(document):
    # Stage 1: Pre-split by paragraphs
    paragraphs = _paragraph_split(document)
    
    # Stage 2: DSHP-LLM - Build Hierarchical Tree
    tree = await _dshp_llm_build_tree(paragraphs)
    
    # Stage 3: DFS Grouping (Tree Traversal)
    grouped_sections = _dfs_group_tree(tree, paragraphs)
    
    # Stage 4: Refiner (Self-Correction)
    refined = await _refiner_phase(grouped_sections)
    
    return refined
# Implementation: backend/utils/semantic_chunker.py
                            """
                        }
                    }
                ]
            },
            {
                "title": "Phase 2: 3-Layer Extraction",
                "steps": [
                    {
                        "name": "Global Theme Injection",
                        "method": "_extract_concepts_from_chunk()",
                        "desc": "Trích xuất khái niệm nhưng bắt buộc LLM nhìn qua lăng kính của Domain (chủ đề toàn cục).",
                        "input": "Chunk + Domain (e.g., 'SQL')",
                        "mech": "Prompt Engineering (Global Context)",
                        "output": "List[ConceptNode]",
                        "deep_dive": {
                            "summary": "Prompt Template",
                            "code": """
SYSTEM: You are an expert Knowledge Engineer.
GLOBAL THEME: {domain}  <-- Injected here

TASK: Extract learning concepts from the text below.
Constraints:
1. Ignore generic terms not related to {domain}.
2. For each concept, determine Bloom's Taxonomy level.

INPUT TEXT:
{chunk_text}
                            """
                        }
                    },
                    {
                        "name": "Relationship Extraction",
                        "method": "_extract_relationships_from_chunk()",
                        "desc": "Xác định cạnh nối và từ khóa cạnh (Edge Keywords) theo nguyên lý LightRAG.",
                        "input": "Concepts + Chunk",
                        "mech": "LLM Reasoning (Gemini 1.5)",
                        "output": "Edges (PREREQUISITE, RELATED...)",
                        "deep_dive": {
                            "summary": "LightRAG Edge Prompt",
                            "code": """
# actual implementation from backend/prompts.py
Identify relationships between these concepts:
{concept_list}

For each relationship, specify:
1. source: Source concept_id
2. target: Target concept_id
3. relationship_type: [REQUIRES, IS_PREREQUISITE_OF, ...]
4. weight: 0.0-1.0
5. dependency: STRONG, MODERATE, WEAK
6. keywords: **CRITICAL** - High-level themes summarizing the nature of the relationship (e.g., "Data Integrity").
7. summary: A concise sentence explaining why they are related.

Return ONLY valid JSON array.
                            """
                        }
                    }
                ]
            },
            {
                "title": "Phase 3: Entity Resolution",
                "steps": [
                    {
                        "name": "3-Way Resolution Algorithm",
                        "method": "_entity_resolution()",
                        "desc": "Tính điểm trùng lặp dựa trên công thức có trọng số.",
                        "input": "Candidate Pairs",
                        "mech": "Weighted Similarity Aggregation",
                        "output": "Merge Decision (Boolean)",
                        "deep_dive": {
                            "summary": "Similarity Formula",
                            "code": """
# 3-Way Similarity Calculation (backend/utils/entity_resolver.py)
Score = (0.60 * S_semantic) + (0.30 * S_structural) + (0.10 * S_contextual)

Where:
- S_semantic: Cosine similarity of Embeddings ("Name | Context | Desc | Tags")
- S_structural: Jaccard similarity of Prerequisites maps
- S_contextual: Jaccard similarity of Tags (semantic_tags)

threshold = 0.85 (Configured in Agent)
IF Score > threshold:
    Execute Merge(Node A, Node B)
    # Conflict Resolution: Weighted Average for attributes
                            """
                        }
                    }
                ]
            }
        ],
        "complexity": {
            "metrics": [
                ("Time", "blocks", "O(N) + O(C×3)"),
                ("Latency (20k)", "seconds", "~15s"),
                ("Concurrency", "threads", "5"),
                ("Memory", "MB", "~150")
            ],
            "bottleneck": "LLM Latency per chunk (Phase 2). Mitigated by Semaphore=5 parallel execution."
        }
    },
    {
        "id": 2,
        "name": "Agent 2: Profiler",
        "role_vn": "The State Manager (Quản lý trạng thái)",
        "why_needed": "Giải quyết vấn đề 'Cold Start' (người dùng mới) và mô hình hóa năng lực người học thành Vector toán học để các Agent khác sử dụng.",
        "science_badges": ["Semantic LKT (Lee 2024)", "VARK Model", "Vector Space Model"],
        "tech_badges": ["PostgreSQL", "Redis", "Gemini Embeddings", "RedLock"],
        "key_insight": "Thay thế Bayesian Knowledge Tracing (BKT) cũ bằng Zero-Shot LKT dựa trên LLM, cho phép suy luận trạng thái mastery ngay cả khi chưa có lịch sử log.",
        "mermaid_sequence": """
sequenceDiagram
    participant User
    participant A2 as Agent 2
    participant Neo4j
    participant DB as Postgres
    participant Redis
    
    User->>A2: "Teach me SQL Joins"
    A2->>A2: Intent Parsing (Few-Shot)
    A2->>Neo4j: Hybrid Retrieval (Keyword+Vector)
    
    alt Cold Start
        A2->>User: Diagnostic Test (3 Questions)
        User-->>A2: Answers
        A2->>DB: Fetch Learner Profile
        A2->>A2: Zero-Shot LKT Inference (LLM)
    end
    
    A2->>A2: Vectorize Profile (10-dim Array)
    
    par Dual-Write
        A2->>DB: ACID Save (Source of Truth)
        A2->>Redis: Cache Component State
    end
    
    click User showDetails
    click A2 showDetails
    click Neo4j showDetails
    click DB showDetails
    click Redis showDetails
        """,
        "node_details": {
            "User": {
                "title": "Learner Actor",
                "desc": "End-user interacting via Chat Interface. Goals are parsed by Intent Extraction.",
                "logic": "1. Sends message ('Teach me SQL').\n2. Authenticated via JWT.\n3. Receives Streamed Response.",
                "specs": "Input: Natural Language\nAuth: Bearer Token",
                "source": "Frontend/Client"
            },
            "A2": {
                "title": "ProfilerAgent",
                "desc": "Orchestrates Cold Start diagnosis, State updates, and Profile Vectorization.",
                "logic": "1. Check Redis for Session.\n2. If New -> Trigger Cold Start (3-Q Diagnostic).\n3. If Returning -> Update Dynamic State (Velocity, Mood).\n4. Vectorize Profile.",
                "specs": "Model: Zero-Shot LKT (Gemini)\nVector Dim: 10\nTTL: 3600s",
                "source": "backend/agents/profiler_agent.py"
            },
            "Neo4j": {
                "title": "Neo4j Graph Store",
                "desc": "Hybrid Retriever (Vector + Graph) for Diagnostic Concepts.",
                "logic": "1. Embed User Goal (Vector).\n2. Graph Traversal (Centrality).\n3. Return weighted concepts for Diagnosis.",
                "specs": "Index: PropertyGraphIndex\nRerank: Centrality",
                "source": "backend/agents/profiler_agent.py"
            },
            "DB": {
                "title": "LearnerProfile (Postgres)",
                "desc": "Comprehensive 17-dimension profile (Static, Dynamic, Episodic).",
                "logic": "1. ACID Transaction for Profile Save.\n2. Stores History (Sessions, Errors).\n3. Source of Truth for Rehydration.",
                "specs": "Schema: LearnerProfile\nDims: 17 (Thesis Tab 3.8)",
                "source": "backend/models/schemas.py"
            },
            "Redis": {
                "title": "Redis Cache",
                "desc": "High-speed state cache for Session and Profile data.",
                "logic": "1. Store `profile:{id}` as JSON.\n2. Use RedLock for distributed updates.\n3. Expire after 1 hour (Slide on Activity).",
                "specs": "Key: `profile:{id}`\nTTL: 3600s\nLock: RedLock",
                "source": "backend/database/redis_client.py"
            }
        },
        "phases": [
            {
                "title": "Phase 1: Cold Start Resolution",
                "steps": [
                    {
                        "name": "Zero-Shot LKT Inference",
                        "method": "_predict_mastery_lkt()",
                        "desc": "Suy luận mức độ thành thạo mastery chỉ dựa trên bài test ngắn, không cần train model BKT.",
                        "input": "DiagnosticQA + Concept Desc",
                        "mech": "LLM Reasoning (Lee 2024)",
                        "output": "Mastery Probability (0.0 - 1.0)",
                        "deep_dive": {
                            "summary": "LKT Prompt Logic",
                            "code": """
Human: The student answered 'Inner Join' to question 1 (Correct).
Answered 'Left Join' to question 2 (Incorrect - Conceptual Error).
Concept: SQL Joins.

Task: Estimate mastery probability p(m).
Reasoning:
1. Student identified basic syntax correctly.
2. Failed to distinguish Left/Inner logic.
3. Conclusion: Partial mastery, high procedural, low conceptual.

Output: 0.45
                            """
                        }
                    }
                ]
            },
            {
                "title": "Phase 2: Profile Vectorization",
                "steps": [
                    {
                        "name": "10-Dimensional Embedding",
                        "method": "_vectorize_profile()",
                        "desc": "Biến đổi toàn bộ hồ sơ phi cấu trúc thành vector cố định để Agent 3 (Planner) sử dụng.",
                        "input": "JSON Profile",
                        "mech": "Normalization & One-Hot",
                        "output": "Float32 Array [10]",
                        "deep_dive": {
                            "summary": "Vector Components",
                            "code": """
Vector Structure V = [v1, v2, ..., v10]

v1: Current Global Mastery (0-1)
v2: Velocity (Concepts/Hour)
v3: Visual Preference (VARK)
v4: Auditory Preference (VARK)
v5: Textual Preference (VARK)
v6: Kinesthetic Preference (VARK)
v7: Time Availability (Normalized 0-1)
v8: Goal Difficulty
v9: Frustration Level (Recent Failures)
v10: Bloom Capability
                            """
                        }
                    }
                ]
            }
        ],
        "complexity": {
            "metrics": [
                ("Time", "blocks", "O(1)"),
                ("Latency", "ms", "~200ms"),
                ("Storage", "KB/user", "20"),
                ("Vector Dim", "d", "10")
            ],
            "bottleneck": "I/O bound (DB writes). Mitigated by Async Dual-Write."
        }
    },
    {
        "id": 3,
        "name": "Agent 3: Path Planner",
        "role_vn": "The Navigator (Điều hướng)",
        "why_needed": "Cân bằng giữa kế hoạch chiến lược dài hạn (System 2) và phản ứng thích nghi nhanh (System 1) để tạo lộ trình học tối ưu.",
        "science_badges": ["Tree of Thoughts (ToT)", "LinUCB (Bandit)", "Mental Simulation"],
        "tech_badges": ["Neo4j", "Gemini 1.5", "Redis MAB State", "Beam Search"],
        "key_insight": "Kiến trúc Hybrid: Sử dụng ToT (Beam Search) cho lần lập kế hoạch đầu tiên để tránh Local Optima, sau đó chuyển sang LinUCB (Contextual Bandit) để điều chỉnh siêu tốc từng bước.",
        "mermaid_sequence": """
graph TD
    Input[Profile Vector V] --> Check{Is First Plan?}
    
    subgraph System2[System 2: Strategic ToT]
        Check -- Yes --> Gen[Thought Generator]
        Gen -->|Expand b=3| Candidates
        Candidates --> Eval[State Evaluator]
        Eval -->|Simulate| Scores
        Scores --> Prune[Beam Pruning]
        Prune --> Path[Optimal Sequence]
    end
    
    subgraph System1[System 1: Adaptive LinUCB]
        Check -- No --> Bandit[LinUCB Algorithm]
        Bandit -->|Disjoint Models| Select[Select Next Concept]
    end
    
    Gate -->|Pass| Adaptive[Adaptive Chaining]
    Gate -->|Fail| Review[Forced Review Mode]
    
    click Input showDetails
    click Check showDetails
    click Gen showDetails
    click Candidates showDetails
    click Eval showDetails
    click Scores showDetails
    click Prune showDetails
    click Path showDetails
    click Bandit showDetails
    click Select showDetails
    click Gate showDetails
        """,
        "node_details": {
            "Input": {
                "title": "Profile Vector",
                "desc": "10-dimensional numpy array representing Learner State.",
                "logic": "Normalized Input: [Mastery, Velocity, V, A, R, K, Time, Difficulty, Frustration, Bloom]",
                "specs": "Dim: 10\nSource: `Agent2.vectorize`",
                "source": "backend/agents/profiler_agent.py"
            },
            "Check": {
                "title": "Strategy Switch",
                "desc": "Decides between expensive Planning (System 2) vs fast Adaptation (System 1).",
                "logic": "IF (New Session OR Concept Drift > 0.3) -> System 2 (ToT)\nELSE -> System 1 (LinUCB)",
                "specs": "Trigger: Cold Start OR Drift > Threshold",
                "source": "backend/agents/path_planner_agent.py"
            },
            "Gen": {
                "title": "Thought Generator",
                "desc": "LLM proposes k=3 candidate next steps (Review, Scaffold, Challenge).",
                "logic": "1. Prompt LLM with current Concept + Goal.\n2. Ask for 3 distinct strategies (Review, Scaffold, Challenge).\n3. Return JSON candidates.",
                "specs": "Method: `_thought_generator`\nk: 3",
                "source": "backend/agents/path_planner_agent.py"
            },
            "Eval": {
                "title": "State Evaluator",
                "desc": "Simulates learner's mental state to score path viability.",
                "logic": "1. 'Simulate student learning x'.\n2. Check Prerequisites.\n3. Predict Frustration.\n4. Score 0.0-1.0.",
                "specs": "Method: `_evaluate_path_viability`\nScore: 0.0-1.0",
                "source": "backend/agents/path_planner_agent.py"
            },
            "Prune": {
                "title": "Beam Search Pruning",
                "desc": "Keeps top-k best paths, discards rest.",
                "logic": "1. Sort candidates by Score.\n2. Keep top-3 (Beam Width).\n3. Repeat for Depth=3.",
                "specs": "Beam Width (b): 3\nMax Depth (d): 3",
                "source": "backend/agents/path_planner_agent.py"
            },
            "Bandit": {
                "title": "LinUCB Engine",
                "desc": "Contextual Multi-Armed Bandit for fast O(1) decision making.",
                "logic": "1. Calculate p_ta for each arm (concept).\n2. p_ta = Theta*x + Alpha*sqrt(Variance).\n3. Select argmax(p_ta).",
                "specs": "Alpha: 1.0\nFeatures: 10",
                "source": "backend/core/rl_engine.py"
            },
            "Gate": {
                "title": "Probabilistic Mastery Gate",
                "desc": "Soft gate that allows exploration based on mastery probability.",
                "logic": "Prob = min(1.0, Score / 0.8).\nIf Random() > Prob -> Force Review.\nElse -> Pass.",
                "specs": "Formula: `min(1.0, score / 0.8)`\nFull Pass: 0.8",
                "source": "backend/agents/path_planner_agent.py"
            }
        },
        "phases": [
            {
                "title": "Phase 1: Strategic Planning (ToT)",
                "steps": [
                    {
                        "name": "Beam Search (b=3, d=3)",
                        "method": "_beam_search()",
                        "desc": "Tìm kiếm trên cây không gian trạng thái với độ rộng 3 và độ sâu 3.",
                        "input": "Start Node + Goal Node",
                        "mech": "Tree Search + LLM Evaluator",
                        "output": "Best Path Sequence",
                        "deep_dive": {
                            "summary": "Complexity Cost",
                            "code": """
Cost Analysis for ToT (b=3, d=3):

Step 1: Generate 3 candidate thoughts (1 LLM Call)
Step 2: Evaluate 3 candidates (3 LLM Calls)
Step 3: Branch 3x3 = 9 next thoughts (3 LLM Calls)
Step 4: Evaluate 9 candidates (9 LLM Calls)
...
Total LLM Calls approx: 1 + b + b*b ...
Current Implementation Limit: Exactly 18 calls per plan.
Latency: ~9-12 seconds.
                            """
                        }
                    }
                ]
            },
            {
                "title": "Phase 2: Real-time Adaptation (LinUCB)",
                "steps": [
                    {
                        "name": "Contextual Bandit Decision",
                        "method": "rl_engine.select()",
                        "desc": "Chọn concept tiếp theo dựa trên vector đặc trưng người học và ma trận phần thưởng lịch sử.",
                        "input": "Context Vector (10-dim)",
                        "mech": "LinUCB Disjoint Algorithm",
                        "output": "Next Concept ID",
                        "deep_dive": {
                            "summary": "LinUCB Formula",
                            "code": """
For each arm (concept) 'a':

p_at = (theta_a_transpose * x_t) + alpha * sqrt(x_t_transpose * A_inv_a * x_t)

Where:
- x_t: Current user context vector
- theta_a: Feature weights for arm a (learned benefit)
- alpha: Exploration parameter (0.5)
- term 2: Uncertainty (Exploration bonus)

We select: argmax(p_at)
                            """
                        }
                    }
                ]
            }
        ],
        "complexity": {
            "metrics": [
                ("ToT Cost", "calls", "18"),
                ("LinUCB Latency", "ms", "50"),
                ("Space", "b×d", "3×3"),
                ("Exploration", "alpha", "0.5")
            ],
            "bottleneck": "ToT Planning Latency (~10s). Only runs on first session or major drift."
        }
    },
    {
        "id": 4,
        "name": "Agent 4: Tutor",
        "role_vn": "The Socratic Guide (Gia sư Socratic)",
        "why_needed": "Ngăn chặn việc học vẹt (passive learning) bằng cách không bao giờ đưa ra đáp án trực tiếp, mà sử dụng gợi ý tích cực (scaffolding).",
        "science_badges": ["Dynamic CoT", "Scaffolding Theory", "Harvard 7 Principles"],
        "tech_badges": ["Gemini 1.5", "Regex Guards", "Vector Retrieval"],
        "key_insight": "Sử dụng 'Hidden Chain-of-Thought': Agent giải bài toán ngầm bên trong (CoT) để hiểu sâu vấn đề, nhưng chỉ xuất ra các gợi ý từng bước (Scaffolding) cho người học.",
        "mermaid_sequence": """
sequenceDiagram
    participant User
    participant A4 as Agent 4
    
    User->>A4: "I'm stuck on this SQL error"
    
    box rgb(240, 240, 240) Internal "Sub-conscious"
        A4->>A4: Retrieve Context (RAG)
        A4->>A4: Generate CoT Trace (The Solution)
        A4->>A4: Slicing: Break Solution into 5 Steps
    end
    
    loop Scaffolding
        A4->>A4: Leakage Check (Regex)
        A4-->>User: Hint 1 (Broad Concept)
        User->>A4: Still stuck
        A4-->>User: Hint 2 (Specific Syntax)
    end

    click User showDetails
    click A4 showDetails
    click RAG showDetails
    click KG showDetails
    click Personal showDetails
    click CoT showDetails
    click Scaffold showDetails
        """,
        "node_details": {
            "User": {
                "title": "Learner Actor",
                "desc": "End-user asking for help via Chat.",
                "logic": "1. Asks question.\n2. Receives Socratic guidance (not answers).",
                "specs": "Input: Natural Language",
                "source": "Frontend"
            },
            "A4": {
                "title": "TutorAgent",
                "desc": "Socratic Guide enforcing Harvard 7 Principles.",
                "logic": "1. Receive Question.\n2. Determine Phase (Intro/Probing/Scaffold).\n3. Grounding (3-Layer).\n4. Generate Response.",
                "specs": "Model: Gemini 1.5\nEnforcer: Harvard7Enforcer",
                "source": "backend/agents/tutor_agent.py"
            },
            "RAG": {
                "title": "Doc Grounding (Layer 1)",
                "desc": "Retrieves context from ChromaDB (PDFs/Slides).",
                "logic": "Query Vector Store -> Top-k Chunks -> Context Window.",
                "specs": "Source: ChromaDB\nEmbedding: Gemini-001",
                "source": "backend/agents/tutor_agent.py"
            },
            "KG": {
                "title": "Course Grounding (Layer 2)",
                "desc": "Retrieves structured concepts from Neo4j.",
                "logic": "Cypher Query -> Concept + Prereqs + Misconceptions.",
                "specs": "Source: Neo4j",
                "source": "backend/agents/tutor_agent.py"
            },
            "Personal": {
                "title": "Personal Grounding (Layer 3)",
                "desc": "Retrieves learner's past mastery and errors.",
                "logic": "Cypher Query -> Learner Node -> History/Notes.",
                "specs": "Source: Neo4j (LearnerProfile)",
                "source": "backend/agents/tutor_agent.py"
            },
            "CoT": {
                "title": "Dynamic Chain-of-Thought",
                "desc": "Generates internal reasoning traces (Hidden Manual).",
                "logic": "1. Prompt with Exemplars (Wei 2022).\n2. Generate n=3 traces.\n3. Self-Consistency Check.",
                "specs": "Traces: 3\nMethod: `_generate_cot_traces`",
                "source": "backend/agents/tutor_agent.py"
            },
            "Scaffold": {
                "title": "Scaffolding Slicer",
                "desc": "Breaks the solution into small, digestible hints.",
                "logic": "1. Take Best Trace.\n2. Slice into steps.\n3. Regex Guard (Leakage Check).\n4. Deliver one by one.",
                "specs": "Max Steps: 5\nGuard: Regex",
                "source": "backend/agents/tutor_agent.py"
            }
        },
        "phases": [
            {
                "title": "Phase 1: Hidden Reasoning",
                "steps": [
                    {
                        "name": "Generate Hidden CoT",
                        "method": "_generate_cot_traces()",
                        "desc": "Sinh chuỗi suy luận đầy đủ để giải quyết vấn đề của học sinh.",
                        "input": "Problem + Context",
                        "mech": "Self-Consistency CoT",
                        "output": "Solution Trace",
                        "deep_dive": {
                            "summary": "CoT Prompt Template",
                            "code": """
INSTRUCTION: You are a tutor. Solve this problem step-by-step.
IMPORTANT: Enclose your reasoning in <thinking> tags.

Problem: {student_question}

Response:
<thinking>
1. The user is asking about 'Group By'.
2. The error is likely omitting the non-aggregated column.
3. Solution: Add the column to the GROUP BY clause.
</thinking>
...
                            """
                        }
                    }
                ]
            },
            {
                "title": "Phase 2: Pedagogical Guardrails",
                "steps": [
                    {
                        "name": "Leakage Guard",
                        "method": "_extract_scaffold()",
                        "desc": "Đảm bảo không tiết lộ code đáp án trong lời giải thích.",
                        "input": "Draft Response",
                        "mech": "Regex Pattern Matching",
                        "output": "Safe Response or Fallback",
                        "deep_dive": {
                            "summary": "Guard Patterns",
                            "code": """
Patterns = [
  r"```sql.*```",          # No code blocks
  r"(SELECT|FROM|WHERE).*", # No raw SQL segments
  r"Answer is .*",          # No direct answers
]

If match found:
   Rewrite response to be more abstract.
                            """
                        }
                    }
                ]
            }
        ],
        "complexity": {
            "metrics": [
                ("Prompt Size", "tokens", "~2k"),
                ("Safety Checks", "rules", "15+"),
                ("Reasoning", "CoT", "n=3"),
                ("Latency", "sec", "2-3")
            ],
            "bottleneck": "Text generation Speed. Mitigated by streaming responses (future)."
        }
    },
    {
        "id": 5,
        "name": "Agent 5: Evaluator",
        "role_vn": "The Judge (Thẩm phán)",
        "why_needed": "Đánh giá không chỉ Đúng/Sai (Binary) mà còn đánh giá quy trình tư duy, phân loại lỗi sai (Error Taxonomy) để đưa ra hướng xử lý sư phạm.",
        "science_badges": ["JudgeLM (Zhu 2023)", "Bloom's Ref-as-Prior", "Bayesian KT"],
        "tech_badges": ["Gemini 1.5", "WMA Smoothing", "Postgres"],
        "key_insight": "Kết hợp JudgeLM (với kỹ thuật Reference-as-Prior) và Cây quyết định sư phạm (5 nhánh) để điều hướng học viên: Mastered, Proceed, Alternate, Remediate, Retry.",
        "mermaid_sequence": """
graph LR
    Input[Student Answer] --> Judge[JudgeLM Scoring]
    Ref[Golden Answer] --> Judge
    
    Judge -->|Score 0-10| Classify[Error Classifier]
    Classify -->|Taxonomy| Decision{5-Path Tree}
    
    Decision -->|Score > 8| Mastered[Mark Mastered]
    Decision -->|Score 5-8| Proceed[Proceed with Caution]
    Decision -->|Score < 5| Remediate[Trigger Remediation]
    
    Mastered --> Update[WMA Update]
    Proceed --> Update
    Remediate --> Update

    click Input showDetails
    click Ref showDetails
    click Judge showDetails
    click Classify showDetails
    click Decision showDetails
    click Mastered showDetails
    click Proceed showDetails
    click Remediate showDetails
    click Update showDetails
        """,
        "node_details": {
            "Judge": {
                "title": "JudgeLM Scoring",
                "desc": "Evaluates answer quality using 'Reference-as-Prior' technique.",
                "logic": "1. Compare Student vs Golden Answer.\n2. Score on Rubric (Correctness 60%, Completeness 20%, Clarity 20%).",
                "specs": "Model: Gemini 1.5 Zero-shot\nOutput: 0.0 - 10.0",
                "source": "backend/agents/evaluator_agent.py"
            },
            "Classify": {
                "title": "Error Classifier",
                "desc": "Categorizes the type of error for pedagogical response.",
                "logic": "Matches inputs to 4 categories:\n- Conceptual (Deep misunderstanding)\n- Procedural (Wrong steps)\n- Incomplete (Missing info)\n- Careless (Typo/Calc)",
                "specs": "Taxonomy: 4 Classes",
                "source": "backend/agents/evaluator_agent.py"
            },
            "Decision": {
                "title": "5-Path Decision Engine",
                "desc": "Determines the next learning action based on Score + Error.",
                "logic": "- Mastered (>9.0)\n- Proceed (>8.0)\n- Alternate (>6.0)\n- Remediate (<6.0 + Conceptual)\n- Retry (<6.0 + Other)",
                "specs": "Paths: 5 Branch Logic",
                "source": "backend/agents/evaluator_agent.py"
            },
            "Update": {
                "title": "Mastery Update (WMA)",
                "desc": "Updates the learner's knowledge state.",
                "logic": "Hybrid Update:\nNew = (Current * 0.4) + (Score * 0.6)\nUpdates Personal Knowledge Graph.",
                "specs": "Algorithm: Weighted Moving Average",
                "source": "backend/agents/evaluator_agent.py"
            },
            "Input": {
                "title": "Student Input",
                "desc": "The raw answer provided by the learner.",
                "logic": "Input text stream.",
                "specs": "Type: String",
                "source": "Frontend"
            },
            "Ref": {
                "title": "Golden Answer",
                "desc": "The ground truth answer from the curriculum.",
                "logic": "Retrieved from Vector Store or Concept Node.",
                "specs": "Source: RAG/KG",
                "source": "backend/agents/evaluator_agent.py"
            },
            "Mastered": {
                 "title": "Path: Mastered",
                 "desc": "Outcome when score is high (>8-9).",
                 "logic": "Confidence High -> Mark Concept as Learned.",
                 "specs": "Threshold: > 0.8",
                 "source": "backend/agents/evaluator_agent.py"
            },
            "Proceed": {
                 "title": "Path: Proceed",
                 "desc": "Outcome when score is passing (5-8).",
                 "logic": "Good enough to move on, but maybe review later.",
                 "specs": "Threshold: 0.5 - 0.8",
                 "source": "backend/agents/evaluator_agent.py"
            },
            "Remediate": {
                 "title": "Path: Remediate",
                 "desc": "Outcome when score is low (<5).",
                 "logic": "Needs review or alternative material.",
                 "specs": "Threshold: < 0.5",
                 "source": "backend/agents/evaluator_agent.py"
            }
        },
        "phases": [
            {
                "title": "Phase 1: Advanced Evaluation",
                "steps": [
                    {
                        "name": "JudgeLM Logic",
                        "method": "_score_response()",
                        "desc": "So khớp câu trả lời với Đáp án chuẩn dựa trên Rubric.",
                        "input": "Ans + Ref + Rubric",
                        "mech": "LLM-as-a-Judge",
                        "output": "Score + Rationale",
                        "deep_dive": {
                            "summary": "Rubric Criteria",
                            "code": """
Evaluation Rubric:
1. Correctness (40%): Is the logic sound?
2. Completeness (30%): Are all constraints met?
3. Clarity (20%): Is it well explained?
4. Efficiency (10%): Is the solution optimal?

Input Format:
[Student Answer] vs [Reference Answer]
                            """
                        }
                    }
                ]
            },
            {
                "title": "Phase 2: Decision Engine",
                "steps": [
                    {
                        "name": "5-Path Decision Tree",
                        "method": "_make_path_decision()",
                        "desc": "Mapping điểm số và loại lỗi sang hành động tiếp theo.",
                        "input": "Score + ErrorType",
                        "mech": "Deterministic Rules",
                        "output": "Action Enum",
                        "deep_dive": {
                            "summary": "Logic Tree",
                            "code": """
IF Score >= 0.8:
    RETURN "MASTERED"
ELIF Score >= 0.6:
    RETURN "PROCEED"
ELIF ErrorType == "MISCONCEPTION":
    RETURN "REMEDIATE" (Concept Review)
ELIF ErrorType == "CARELESS":
    RETURN "RETRY" (Same Problem)
ELSE:
    RETURN "ALTERNATE" (Easier Problem)
                            """
                        }
                    }
                ]
            }
        ],
        "complexity": {
            "metrics": [
                ("Rubric Dims", "count", "4"),
                ("Taxonomy", "types", "5"),
                ("Paths", "outcomes", "5"),
                ("Cost/Eval", "tokens", "~500")
            ],
            "bottleneck": "None. Very lightweight execution."
        }
    },
    {
        "id": 6,
        "name": "Agent 6: KAG (MemGPT)",
        "role_vn": "Personal OS (Hệ điều hành cá nhân)",
        "why_needed": "Giải quyết giới hạn Context Window của LLM trong các lộ trình học kéo dài hàng tuần/tháng bằng cơ chế bộ nhớ phân tầng.",
        "science_badges": ["MemGPT", "Zettelkasten", "Dual-Code Theory"],
        "tech_badges": ["Neo4j Archival", "Redis WorkingMem", "Mermaid Gen"],
        "key_insight": "Cơ chế 'Memory Pressure': Tự động tính toán áp lực bộ nhớ. Khi vượt ngưỡng 70%, kích hoạt quy trình Auto-Archive để tóm tắt và cất giữ kiến thức cũ vào Graph (Zettelkasten).",
        "mermaid_sequence": """
sequenceDiagram
    participant User
    participant A6 as Agent 6 (OS)
    participant RAM as Working Context
    participant Disk as Neo4j Graph
    
    User->>A6: "Recall lesson from last week"
    
    loop Heartbeat
        A6->>RAM: Check Pressure
        opt Pressure > 70% (Overflow Warning)
            A6->>A6: Summarize Oldest Turns
            A6->>Disk: Archive (Zettelkasten Note)
            A6->>RAM: Evict Raw Tokens
        end
        
        A6->>A6: Retrieval Function Call
        A6->>Disk: Search(Query)
        Disk-->>A6: Retrievals
    end
    
    A6-->>User: Synthisized Answer

    click User showDetails
    click A6 showDetails
    click RAM showDetails
    click Disk showDetails
        """,
        "node_details": {
            "User": {
                "title": "User Request",
                "desc": "The learner's input or query.",
                "logic": "Initiates the session.",
                "specs": "Type: String",
                "source": "Frontend"
            },
            "A6": {
                "title": "KAG Agent (OS Kernel)",
                "desc": "Orchestrates the Memory OS and Heartbeat Loop during thinking process.",
                "logic": "1. Monitor Pressure.\n2. Compile Context.\n3. Think (LLM).\n4. Act (Tools).\n5. Loop.",
                "specs": "Model: Gemini 1.5 Flash\nMax Steps: 5",
                "source": "backend/agents/kag_agent.py"
            },
            "RAM": {
                "title": "Working Context (RAM)",
                "desc": "Short-term memory including System Prompt, Core Memory, and FIFO Queue.",
                "logic": "Managed by `WorkingMemory` class. Maintains fixed token window.",
                "specs": "Limit: 8192 tokens\nEviction: FIFO",
                "source": "backend/memory/working_memory.py"
            },
            "Disk": {
                "title": "Archival Memory (Disk)",
                "desc": "Long-term storage in Neo4j (Graph + Vector).",
                "logic": "Stores Zettelkasten notes and raw summaries.\nSupports Vector Search & Cypher Queries.",
                "specs": "Storage: Neo4j\nIndex: Vector",
                "source": "backend/memory/archival_storage.py"
            }
        },
        "phases": [
            {
                "title": "Phase 1: Memory Management",
                "steps": [
                    {
                        "name": "Pressure Monitor",
                        "method": "is_pressure_high()",
                        "desc": "Tính toán tỷ lệ token sử dụng so với giới hạn cửa sổ.",
                        "input": "TokenCount",
                        "mech": "Thresholding",
                        "output": "Boolean (IsOverflow)",
                        "deep_dive": {
                            "summary": "Pressure Formula",
                            "code": """
# Memory Pressure Calculation
current_tokens = count_tokens(system_prompt + conversation_history)
max_tokens = 8192 (Gemini 1.5 Flash Window Safe Limit)

pressure_ratio = current_tokens / max_tokens

IF pressure_ratio > 0.7:
    TRIGGER Auto-Archival
ELSE:
    CONTINUE
                            """
                        }
                    }
                ]
            },
            {
                "title": "Phase 2: Knowledge Artifacts",
                "steps": [
                    {
                        "name": "Note Generation (Dual-Code)",
                        "method": "_generate_artifact()",
                        "desc": "Tạo ghi chú Zettelkasten (Text) + Biểu đồ tư duy (Visual) cùng lúc.",
                        "input": "Context",
                        "mech": "Multi-modal Output",
                        "output": "Markdown + Mermaid",
                        "deep_dive": {
                            "summary": "Dual-Code Prompt",
                            "code": """
Task: Create a Zettelkasten Note (Atomic).
Requirement: Apply Dual-Code Theory (Paivio).

Output Format:
# [Concept Name]
[Concise textual explanation...]

## Visual Map
```mermaid
graph TD
   ... (Visual representation of concept)
```

Tags: #tag1 #tag2
                            """
                        }
                    }
                ]
            }
        ],
        "complexity": {
            "metrics": [
                ("Window", "tokens", "8192"),
                ("Threshold", "ratio", "0.7"),
                ("Heartbeats", "max", "5"),
                ("Archive", "ops", "O(N)")
            ],
            "bottleneck": "Recursive Function Calling loop (Heartbeat) can stall if not capped."
        }
    }
]

def render_html():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for agent in AGENTS:
        # 1. Badges
        s_badges = "".join([f'<span class="badge badge-science">{b}</span>' for b in agent['science_badges']])
        t_badges = "".join([f'<span class="badge badge-tech">{b}</span>' for b in agent['tech_badges']])
        
        # 2. Phases
        phases_html = ""
        for p in agent['phases']:
            steps_html = ""
            for s in p['steps']:
                deep_html = ""
                if 'deep_dive' in s:
                    deep_html = f"""
                    <details class="deep-dive">
                        <summary>Deep Dive: {s['deep_dive']['summary']}</summary>
                        <div class="dive-content">
                            <pre><code>{s['deep_dive']['code'].strip()}</code></pre>
                        </div>
                    </details>
                    """
                
                steps_html += f"""
                <div class="step">
                    <div class="step-header">
                        <span class="step-title">{s['name']}</span>
                        <span class="method-code">{s['method']}</span>
                    </div>
                    <div class="step-body">
                        <p class="step-desc">{s['desc']}</p>
                        
                        <div class="io-grid">
                            <div class="io-box io-input">
                                <div class="io-label">Input</div>
                                {s['input']}
                            </div>
                            <div class="io-box io-mech">
                                <div class="io-label">Mechanism</div>
                                {s['mech']}
                            </div>
                            <div class="io-box io-output">
                                <div class="io-label">Output</div>
                                {s['output']}
                            </div>
                        </div>
                        
                        {deep_html}
                    </div>
                </div>
                """
            
            phases_html += f"""
            <div class="phase-section">
                <h2>{p['title']}</h2>
                {steps_html}
            </div>
            """
            
        # 3. Complexity
        comp = agent['complexity']
        comp_html = "".join([f"""
            <div class="metric">
                <div class="metric-val">{m[2]}</div>
                <div class="metric-label">{m[0]} ({m[1]})</div>
            </div>
        """ for m in comp['metrics']])
        
        # 4. Interaction Data
        import json
        node_details = agent.get("node_details", {})
        node_details_json = json.dumps(node_details)
        
        # Append Click Events
        mermaid_clicks = "\n".join([f"click {nid} showDetails" for nid in node_details.keys()])
        full_mermaid = agent["mermaid_sequence"] + "\n" + mermaid_clicks

        # 5. Render
        html = HTML_TEMPLATE.format(
            agent_name=agent['name'],
            agent_role_vn=agent['role_vn'],
            why_needed=agent['why_needed'],
            science_badges=s_badges,
            tech_badges=t_badges,
            key_insight=agent['key_insight'],
            mermaid_sequence=full_mermaid,
            phase_html=phases_html,
            complexity_metrics=comp_html,
            bottleneck=comp['bottleneck'],
            gen_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            node_details_json=node_details_json
        )
        
        filename = f"agent_{agent['id']}_whitebox.html"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Generated: {filepath}")

if __name__ == "__main__":
    render_html()
