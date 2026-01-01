---
description: Verify that the codebase aligns with the defined specs.
---

# Spec Check Workflow

This workflow acts as a "Spec Guardian" to ensure that implementation matches requirements.

// turbo-all

1. Read the Functional Requirements
   `view_file specs/requirements.md`

2. Read the Architecture Specs
   `view_file specs/architecture.md`

3. (Instructions to Agent)
   - Compare the current task/code against these requirements.
   - If there is a deviation (e.g., coding a feature not in requirements), flagged it.
   - If the code implements a requirement, mark it as checked.
