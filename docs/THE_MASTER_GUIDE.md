# The Creator's Guide to the Personalized Learning Agent System

> "Don't Panic. It's just a Graph."

## 1. Introduction: The Elevator Pitch
Imagine a tutor that doesn't just "know things" (like a textbook) but "understands you" (like a mentor).
Most AI tutors are just **Reactive Answering Machines**. You ask, they answer. If you don't know what to ask, you're stuck.
**This System** is different. It is **Proactive**. It builds a map of your mind (Knowledge State), plans a path through the wilderness of information (Knowledge Graph), and holds your hand (Scaffolding) until you reach mastery.

## 2. System Overview: The 6 Agents
The system is a "Society of Mind" composed of 6 specialized agents working in concert:

1.  **Agent 1 (Reader):** The eyes. It reads PDFs and extracts not just text, but *logic* (triples).
2.  **Agent 2 (Profiler):** The memory. It tracks your frustration, boredom, and mastery of every concept.
3.  **Agent 3 (Planner):** The strategist. It uses "Tree of Thoughts" to simulate futures and pick the best teaching path.
4.  **Agent 4 (Tutor):** The voice. It uses the Socratic Method to guide you, never giving the answer away cheaply.
5.  **Agent 5 (Evaluator):** The judge. It strictly grades your understanding against a ground truth.
6.  **Agent 6 (Librarian/KAG):** The scholar. It holds the map (Neo4j Graph) and the books (Vector DB).

## 3. The Story of a Request
*User clicks "Start Learning"*

1.  **Profiler:** "User is new. Mood is Neutral. Mastery is 0."
2.  **Planner:** "I see 3 possible starting points. Path A is too hard. Path B is boring. Path C (Introduction) is perfect. Selecting Path C. Target: 'Neural Networks'."
3.  **Librarian:** "Fetching 'Neural Networks'. I found 3 definitions in the Vector DB. But wait—the Graph says 'Neural Networks' require 'Linear Algebra'. Improving context..."
4.  **Tutor:** "Hello! Before we dive into Neural Networks, tell me: what do you know about a Dot Product?" (Socratic Question inspired by Graph Prerequisite).
5.  **User:** "It multiplies numbers?"
6.  **Evaluator:** "Correctness: Partial. Quality: 0.4. Feedback: Missing the summation aspect."
7.  **Profiler:** "Updating State: Linear Algebra Mastery = 0.3."
8.  **Tutor:** "Close! It sums the products. Think of it as alignment..."

## 4. Key Innovations

### The Vector Blind Spot
Standard RAG systems are blind to logic using only semantic similarity. They find text *about* X, but miss the *prerequisites* of X.
**Our Solution:** We use **Neo4j** to explicitly model `(Concept)-[:REQUIRES]->(Prerequisite)`. We don't guess dependencies; we *know* them.

### Mental Simulation
Before the AI says anything, Agent 3 "hallucinates" the future. "If I teach X, will the user be bored?" It scores these simulated futures and picks the path that maximizes **Long-Term Retention**, even if it means slowing down today.

## 5. Operating Manual

### How to Run
```bash
# 1. Start the Infrastructure (Neo4j, Postgres, Redis, VectorDB)
docker-compose up -d

# 2. Start the Backend API
uvicorn backend.main:app --reload
```

### How to Demo
1.  Navigate to `http://localhost:3000`.
2.  Login as `student_1`.
3.  Ask: *"Teach me about Transformers."*
4.  Watch the **Whitebox Dashboard** to see Agent 3 rejecting the direct path and proposing a prerequisite bridge instead.

### Debugging
*   **Logs:** `tail -f backend/logs/agent.log`
*   **Graph View:** Open `http://localhost:7474` (Neo4j Browser) and run `MATCH (n) RETURN n LIMIT 25`.
