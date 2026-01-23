"""
Test Data Generator for Full-Scale Experiments
Generates:
- 10 synthetic PDF course materials
- 5 synthetic learner profiles with varying skill levels
"""

import json
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models.schemas import LearnerProfile
from backend.models.enums import SkillLevel, LearningStyle

# =============================================
# CONFIGURATION
# =============================================

DATA_DIR = Path(__file__).parent.parent / "data" / "experiments"
PDF_DIR = DATA_DIR / "pdfs"
PROFILES_DIR = DATA_DIR / "learner_profiles"

# Course content topics for synthetic PDFs
COURSE_TOPICS = [
    ("1_sql_basics", "SQL Basics: SELECT, FROM, WHERE"),
    ("2_sql_joins", "SQL JOINs: INNER, LEFT, RIGHT, FULL"),
    ("3_sql_aggregation", "SQL Aggregation: GROUP BY, HAVING, COUNT, SUM"),
    ("4_sql_subqueries", "SQL Subqueries and CTEs"),
    ("5_sql_optimization", "SQL Query Optimization and Indexing"),
    ("6_python_basics", "Python Basics: Variables, Data Types, Control Flow"),
    ("7_python_functions", "Python Functions and Modules"),
    ("8_python_oop", "Python Object-Oriented Programming"),
    ("9_data_analysis", "Data Analysis with Pandas"),
    ("10_machine_learning", "Introduction to Machine Learning with Scikit-Learn"),
    ("11_quantum_physics", "Quantum Physics: Wave-Particle Duality"),
    ("12_european_history", "European History: The Renaissance"),
]

# Learner personas for synthetic profiles
LEARNER_PERSONAS = [
    {
        "name": "Alice Nguyen",
        "skill_level": SkillLevel.BEGINNER,
        "learning_style": LearningStyle.VISUAL,
        "available_time": 60,
        "goal": ["sql_basics", "sql_joins"],
        "age": 22,
    },
    {
        "name": "Bob Tran",
        "skill_level": SkillLevel.INTERMEDIATE,
        "learning_style": LearningStyle.READING,
        "available_time": 120,
        "goal": ["sql_optimization", "python_oop"],
        "age": 28,
    },
    {
        "name": "Carol Le",
        "skill_level": SkillLevel.BEGINNER,
        "learning_style": LearningStyle.KINESTHETIC,
        "available_time": 45,
        "goal": ["python_basics", "python_functions"],
        "age": 19,
    },
    {
        "name": "David Pham",
        "skill_level": SkillLevel.ADVANCED,
        "learning_style": LearningStyle.AUDITORY,
        "available_time": 90,
        "goal": ["data_analysis", "machine_learning"],
        "age": 35,
    },
    {
        "name": "Eva Hoang",
        "skill_level": SkillLevel.INTERMEDIATE,
        "learning_style": LearningStyle.VISUAL,
        "available_time": 75,
        "goal": ["sql_subqueries", "sql_aggregation", "python_basics"],
        "age": 25,
    },
]


# =============================================
# PDF CONTENT TEMPLATES
# =============================================

def generate_pdf_content(topic_id: str, topic_title: str) -> str:
    """Generate synthetic course material content for a topic."""
    
    templates = {
        "1_sql_basics": """
# SQL Basics: SELECT, FROM, WHERE

## Learning Objectives
By the end of this module, you will be able to:
- Write basic SQL SELECT statements
- Filter data using WHERE clauses
- Understand data types in SQL

## 1. Introduction to SQL
SQL (Structured Query Language) is the standard language for interacting with relational databases.

### Key Concepts
- **Tables**: Data is stored in tables with rows and columns
- **Columns**: Each column has a specific data type (INT, VARCHAR, DATE, etc.)
- **Rows**: Each row represents a single record

## 2. The SELECT Statement
```sql
SELECT column1, column2
FROM table_name;
```

### Example
```sql
SELECT first_name, last_name, email
FROM employees;
```

## 3. The WHERE Clause
```sql
SELECT column1, column2
FROM table_name
WHERE condition;
```

### Comparison Operators
| Operator | Description |
|----------|-------------|
| = | Equal |
| <> | Not equal |
| > | Greater than |
| < | Less than |
| >= | Greater than or equal |
| <= | Less than or equal |

## Practice Exercises
1. Write a query to select all columns from the `customers` table
2. Write a query to select customers where `country = 'Vietnam'`
3. Write a query to select products with `price > 100`

## Summary
- SELECT retrieves data from tables
- FROM specifies the table
- WHERE filters the results
""",
        "2_sql_joins": """
# SQL JOINs: INNER, LEFT, RIGHT, FULL

## Learning Objectives
- Understand the concept of table relationships
- Write INNER JOIN queries
- Differentiate between LEFT, RIGHT, and FULL JOINs

## 1. Why JOINs?
In relational databases, data is often split across multiple tables. JOINs allow us to combine related data.

## 2. INNER JOIN
Returns only rows with matching values in both tables.

```sql
SELECT orders.order_id, customers.customer_name
FROM orders
INNER JOIN customers ON orders.customer_id = customers.id;
```

## 3. LEFT JOIN
Returns all rows from the left table, and matching rows from the right table.

```sql
SELECT customers.customer_name, orders.order_id
FROM customers
LEFT JOIN orders ON customers.id = orders.customer_id;
```

## 4. RIGHT JOIN
Returns all rows from the right table, and matching rows from the left table.

## 5. FULL OUTER JOIN
Returns all rows when there is a match in either table.

## Practice Exercises
1. Write an INNER JOIN between `employees` and `departments`
2. Write a LEFT JOIN to find all customers, including those without orders
3. Explain when you would use a RIGHT JOIN vs LEFT JOIN

## Summary
- JOINs combine data from multiple tables
- INNER JOIN: Only matching rows
- LEFT/RIGHT JOIN: All rows from one side, matching from other
- FULL JOIN: All rows from both sides
""",
    }
    
    # 11. Quantum Physics Template
    templates["11_quantum_physics"] = """
# Quantum Physics: Wave-Particle Duality

## Learning Objectives
- Understand the concept of Wave-Particle Duality
- Explain the Double-Slit Experiment
- Define the Heisenberg Uncertainty Principle

## 1. Introduction
Classical physics treats particles and waves as distinct entities. Quantum mechanics reveals that matter and light exhibit properties of both.

## 2. The Double-Slit Experiment
When light shines through two slits, it creates an interference pattern (wave behavior), even if photons are sent one at a time. However, if observed, they behave like particles.

## 3. Key Principles
- **Superposition**: A system exists in all possible states until measured.
- **Entanglement**: Particles can be correlated instantly across distances.

## Summary
Matter behaves as both a wave and a particle depending on observation.
"""

    # 12. European History Template
    templates["12_european_history"] = """
# European History: The Renaissance

## Learning Objectives
- Identify key figures of the Renaissance (Da Vinci, Michelangelo)
- Understand the shift from Medieval to Modern thought
- Explain Humanism

## 1. Context (14th - 17th Century)
The Renaissance was a fervent period of European cultural, artistic, political and economic "rebirth" following the Middle Ages.

## 2. Humanism
An intellectual movement focusing on human potential and achievements, moving away from divine-centric views.

## 3. Key Figures
- **Leonardo da Vinci**: The "Renaissance Man" (Mona Lisa, Last Supper).
- **Michelangelo**: The Sistine Chapel, David.

## Summary
The Renaissance bridged the gap between the Middle Ages and modern-day civilization.
"""
    
    # Return specific template if available, otherwise generate generic content
    if topic_id in templates:
        return templates[topic_id]
    
    # Generic template for other topics
    return f"""
# {topic_title}

## Learning Objectives
By the end of this module, you will be able to:
- Understand the core concepts of {topic_title.split(':')[0]}
- Apply these concepts in practical scenarios
- Identify common pitfalls and best practices

## 1. Introduction
This module covers essential concepts related to {topic_title}.

### Key Concepts
- Concept 1: Foundational understanding
- Concept 2: Practical application
- Concept 3: Advanced techniques

## 2. Core Content
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

### 2.1 Subtopic A
Detailed explanation of the first subtopic with examples.

```
# Example code or syntax
example_variable = "Hello, World!"
```

### 2.2 Subtopic B
Detailed explanation of the second subtopic.

## 3. Practice Exercises
1. Exercise 1: Basic application
2. Exercise 2: Intermediate challenge
3. Exercise 3: Advanced problem

## 4. Summary
- Key takeaway 1
- Key takeaway 2
- Key takeaway 3

## References
- Reference 1
- Reference 2
"""


def generate_learner_profile(persona: dict) -> LearnerProfile:
    """Generate a synthetic LearnerProfile from a persona definition."""
    
    learner_id = str(uuid.uuid4())
    
    # Initialize with some pre-existing mastery for intermediate/advanced learners
    initial_mastery = {}
    if persona["skill_level"] == SkillLevel.INTERMEDIATE:
        initial_mastery = {
            "sql_basics": random.uniform(0.6, 0.8),
            "python_basics": random.uniform(0.5, 0.7),
        }
    elif persona["skill_level"] == SkillLevel.ADVANCED:
        initial_mastery = {
            "sql_basics": random.uniform(0.8, 0.95),
            "sql_joins": random.uniform(0.7, 0.9),
            "python_basics": random.uniform(0.8, 0.95),
            "python_functions": random.uniform(0.7, 0.85),
        }
    
    profile = LearnerProfile(
        learner_id=learner_id,
        name=persona["name"],
        demographic={
            "age": persona["age"],
            "language": "vi",
            "timezone": "Asia/Ho_Chi_Minh",
        },
        learning_goal=persona["goal"],
        learning_style=persona["learning_style"],
        skill_level=persona["skill_level"],
        available_time=persona["available_time"],
        concept_mastery_map=initial_mastery,
        preferences={
            "pace": "medium",
            "verbosity": "normal",
            "hint_level": 2,
            "difficulty_next": "MEDIUM" if persona["skill_level"] == SkillLevel.BEGINNER else "HARD",
        },
        goal=", ".join(persona["goal"]),
        time_available=persona["available_time"],
        current_skill_level=persona["skill_level"],
        preferred_learning_style=persona["learning_style"],
    )
    
    profile.recalculate_avg_mastery()
    return profile


# =============================================
# MAIN GENERATION FUNCTIONS
# =============================================

def generate_pdfs():
    """Generate synthetic PDF course materials as markdown files."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    for topic_id, topic_title in COURSE_TOPICS:
        content = generate_pdf_content(topic_id, topic_title)
        filename = PDF_DIR / f"{topic_id}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        generated_files.append(str(filename))
        print(f"Generated: {filename.name}")
    
    return generated_files


def generate_profiles():
    """Generate synthetic learner profiles as JSON files."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    for persona in LEARNER_PERSONAS:
        profile = generate_learner_profile(persona)
        
        # Create filename from name
        safe_name = persona["name"].lower().replace(" ", "_")
        filename = PROFILES_DIR / f"{safe_name}.json"
        
        # Serialize to JSON (handle datetime and enums)
        profile_dict = profile.model_dump()
        profile_dict["created_at"] = profile_dict["created_at"].isoformat()
        profile_dict["last_updated"] = profile_dict["last_updated"].isoformat()
        profile_dict["skill_level"] = profile_dict["skill_level"].value
        profile_dict["learning_style"] = profile_dict["learning_style"].value
        profile_dict["current_skill_level"] = profile_dict["current_skill_level"].value
        profile_dict["preferred_learning_style"] = profile_dict["preferred_learning_style"].value
        
        # Handle MasteryMap items
        for item in profile_dict.get("current_mastery", []):
            if "last_updated" in item and isinstance(item["last_updated"], datetime):
                item["last_updated"] = item["last_updated"].isoformat()
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(profile_dict, f, indent=2, default=str)
        
        generated_files.append(str(filename))
        print(f"Generated: {filename.name}")
    
    return generated_files


def generate_experiment_config():
    """Generate experiment configuration file."""
    config = {
        "experiment_id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(),
        "settings": {
            "llm_provider": "gemini",
            "api_calls_budget_per_agent": 50,
            "mock_fallback": True,
        },
        "pdfs": [f"{topic_id}.md" for topic_id, _ in COURSE_TOPICS],
        "learner_profiles": [p["name"].lower().replace(" ", "_") + ".json" for p in LEARNER_PERSONAS],
        "phases": {
            "1_knowledge_extraction": {
                "input": "pdfs/",
                "output": "kg_nodes.json",
            },
            "2_profiling": {
                "input": "learner_profiles/",
                "output": "updated_profiles.json",
            },
            "3_path_planning": {
                "paths_per_learner": 3,
                "output": "learning_paths.json",
            },
            "4_tutoring": {
                "sessions_per_path": 10,
                "output": "tutor_sessions.json",
            },
            "5_evaluation": {
                "output": "evaluation_results.json",
            },
            "6_kag_archival": {
                "output": "memory_states.json",
            },
        },
        "metrics": [
            "learning_gain",
            "path_efficiency",
            "tutor_accuracy",
            "evaluator_consistency",
            "latency_per_agent",
            "throughput",
        ],
    }
    
    config_file = DATA_DIR / "experiment_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    print(f"Generated: {config_file.name}")
    return str(config_file)


# =============================================
# MAIN ENTRY POINT
# =============================================

def main():
    """Generate all test data for full-scale experiments."""
    print("=" * 60)
    print("Full-Scale Experiment Data Generator")
    print("=" * 60)
    
    # Ensure base directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate PDFs
    print("\nGenerating Course Materials (PDFs)...")
    pdf_files = generate_pdfs()
    
    # Generate Learner Profiles
    print("\nGenerating Learner Profiles...")
    profile_files = generate_profiles()
    
    # Generate Experiment Config
    print("\nGenerating Experiment Configuration...")
    config_file = generate_experiment_config()
    
    # Summary
    print("\n" + "=" * 60)
    print("Data Generation Complete!")
    print("=" * 60)
    try:
        print(f"Output Directory: {DATA_DIR}")
    except UnicodeEncodeError:
        print(f"Output Directory: {DATA_DIR.name}")
    print(f"PDFs Generated: {len(pdf_files)}")
    print(f"Profiles Generated: {len(profile_files)}")
    print(f"Config File: {config_file}")
    print("\nNext Steps:")
    print("1. Run `python scripts/run_experiment.py` to execute the experiment")
    print("2. Check `data/experiments/` for generated outputs")


if __name__ == "__main__":
    main()
