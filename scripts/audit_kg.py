"""
Knowledge Graph Audit Script (The "Brain Scan")
Validates the semantic integrity and quality of the Neo4j Knowledge Graph.

Metrics:
1. Node Density: Total nodes / types
2. Orphan Concepts: Nodes with zero outgoing relationships
3. Relationship Variety: Distribution of relationship types
4. Health Score: Composite metric (0-100)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.neo4j_client import Neo4jClient
from backend.config import get_settings

async def run_audit():
    print("="*60)
    print("KNOWLEDGE GRAPH AUDIT (Brain Scan)")
    print("="*60)
    
    settings = get_settings()
    
    # Connect to Neo4j
    client = Neo4jClient(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD
    )
    
    connected = await client.connect()
    if not connected:
        print("ERROR: Could not connect to Neo4j. Check your .env and Docker container.")
        return
        
    print(f"Connected to: {settings.NEO4J_URI}")
    
    # ============================================
    # METRIC 1: Node Count by Label
    # ============================================
    print("\n--- 1. NODE INVENTORY ---")
    node_query = """
    CALL db.labels() YIELD label
    CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) as count', {}) YIELD value
    RETURN label, value.count as count
    ORDER BY value.count DESC
    """
    # Fallback if APOC is not installed
    node_query_fallback = """
    MATCH (n)
    RETURN labels(n)[0] as label, count(n) as count
    ORDER BY count DESC
    """
    try:
        nodes = await client.run_query(node_query)
    except Exception:
        nodes = await client.run_query(node_query_fallback)
        
    total_nodes = sum([n.get('count', 0) for n in nodes])
    print(f"Total Nodes: {total_nodes}")
    for n in nodes:
        print(f"  - {n.get('label', 'Unknown')}: {n.get('count', 0)}")
    
    # ============================================
    # METRIC 2: Relationship Count by Type
    # ============================================
    print("\n--- 2. RELATIONSHIP INVENTORY ---")
    rel_query = """
    MATCH ()-[r]->()
    RETURN type(r) as type, count(r) as count
    ORDER BY count DESC
    """
    rels = await client.run_query(rel_query)
    total_rels = sum([r.get('count', 0) for r in rels])
    print(f"Total Relationships: {total_rels}")
    for r in rels:
        print(f"  - {r.get('type', 'Unknown')}: {r.get('count', 0)}")
    
    # ============================================
    # METRIC 3: Orphan Nodes (No Outgoing Rels)
    # ============================================
    print("\n--- 3. ORPHAN DETECTION ---")
    orphan_query = """
    MATCH (n)
    WHERE NOT (n)-->() AND NOT (n)<--()
    RETURN labels(n)[0] as label, count(n) as count
    """
    orphans = await client.run_query(orphan_query)
    total_orphans = sum([o.get('count', 0) for o in orphans])
    print(f"Total Orphan Nodes: {total_orphans}")
    if orphans:
        for o in orphans:
            print(f"  - {o.get('label', 'Unknown')}: {o.get('count', 0)}")
    else:
        print("  (No orphans - Good!)")
    
    # ============================================
    # METRIC 4: Graph Density
    # ============================================
    print("\n--- 4. GRAPH DENSITY ---")
    if total_nodes > 0:
        avg_degree = (total_rels * 2) / total_nodes  # Each rel connects 2 nodes
        print(f"Average Degree (rels/node): {avg_degree:.2f}")
    else:
        avg_degree = 0
        print("Average Degree: N/A (No nodes)")
    
    # ============================================
    # HEALTH SCORECARD
    # ============================================
    print("\n" + "="*60)
    print("HEALTH SCORECARD")
    print("="*60)
    
    # Scoring Logic:
    # - Node Count: 20 pts if > 10 nodes
    # - Relationship Variety: 20 pts if > 2 types
    # - No Orphans: 30 pts if orphan_ratio < 10%
    # - Density: 30 pts if avg_degree > 1.5
    
    score = 0
    
    # Node Count
    if total_nodes >= 10:
        score += 20
        print("[+20] Node Count: PASS (>= 10 nodes)")
    else:
        print("[ 0] Node Count: FAIL (< 10 nodes)")
    
    # Relationship Variety
    if len(rels) >= 2:
        score += 20
        print(f"[+20] Relationship Variety: PASS ({len(rels)} types)")
    else:
        print(f"[ 0] Relationship Variety: FAIL ({len(rels)} types)")
        
    # Orphan Ratio
    orphan_ratio = (total_orphans / total_nodes * 100) if total_nodes > 0 else 100
    if orphan_ratio < 10:
        score += 30
        print(f"[+30] Orphan Ratio: PASS ({orphan_ratio:.1f}%)")
    else:
        print(f"[ 0] Orphan Ratio: FAIL ({orphan_ratio:.1f}%)")
        
    # Density
    if avg_degree >= 1.5:
        score += 30
        print(f"[+30] Graph Density: PASS (Avg Degree {avg_degree:.2f})")
    else:
        print(f"[ 0] Graph Density: FAIL (Avg Degree {avg_degree:.2f})")
    
    print("-"*60)
    print(f"TOTAL HEALTH SCORE: {score}/100")
    
    if score >= 80:
        print("STATUS: EXCELLENT - Graph is well-formed.")
    elif score >= 50:
        print("STATUS: FAIR - Some improvements needed.")
    else:
        print("STATUS: CRITICAL - Graph requires significant work.")
    
    print("="*60)
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(run_audit())
