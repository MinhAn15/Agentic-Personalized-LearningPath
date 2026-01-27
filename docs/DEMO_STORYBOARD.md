# APLO Demo Storyboard: "The Gap Analysis" Flow

**Context**: This visual sequence demonstrates the core value proposition of APLO: Identifying a specific knowledge gap and dynamically remediating it.

---

## Phase 1: Registration & Baseline

**Scene**: User signs up. Note that the interface is clean and minimal.
![Signup](assets/demo_01_signup_empty.png)

**Action**: User fills in details.
![Signup Filled](assets/demo_02_signup_filled.png)

**Result**: Immediate access to the Dashboard.
![Dashboard](assets/demo_03_dashboard_initial.png)

---

## Phase 2: The Assessment (Pre-test)

**Constraint**: The user is asked about SQL. We intentionally answer "Basics" correctly but fail "Advanced/Connections".

**Scene**: Quiz Interface.
![Quiz Start](assets/demo_04_quiz_start.png)

**Action**: User answers correct for `WHERE` and `SELECT` clauses.
**Failure**: User misunderstands `INNER JOIN` (The Gap).

**Result**: The System detects the "Concept Gap" in SQL Joins.
![Quiz Result Gap](assets/demo_05_quiz_results_gap.png)
> *Note: The system classifies the error as "CONCEPTUAL" and recommends "REMEDIATE".*

---

## Phase 3: Adaptive Remediation

**Scene**: The "Planner" Agent redirects the user to the Intelligent Tutor.
**Guidance**: Instead of a generic lecture, the Tutor asks a Socratic question based on the user's specific misconception.

![Tutor Start](assets/demo_07_tutor_start.png)

**Action**: User attempts to explain their understanding.
**Feedback**: The Tutor validates the partial correctness but corrects the specific misunderstanding about "matching keys".

![Tutor Feedback](assets/demo_08_tutor_feedback.png)

---

## Conclusion
This flow proves the **Agentic** capability:
1.  **Profiler**: Detected the specific gap (Join keys).
2.  **Planner**: Routed to immediate remediation.
3.  **Tutor**: Provided context-aware feedback (not just "Wrong").
