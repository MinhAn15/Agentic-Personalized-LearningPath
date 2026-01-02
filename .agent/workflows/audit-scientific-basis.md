---
description: Process for identifying and documenting scientific basis for Agents
---

1. **Identify Core Algorithms**
   Review the Agent's `whitebox.md` or source code. Look for:
   -   Decision making logic (e.g., MAB, Thresholds).
   -   Data structures (e.g., Graphs, Vector stores).
   -   Pedagogical rules (e.g., Bloom's Taxonomy, Zettelkasten).

2. **Map to Research/Industry Standards**
   Find the academic or industry source for the algorithm.
   -   *Example*: "Weighted Moving Average" -> Time Series Analysis.
   -   *Example*: "LinUCB" -> Contextual Bandits (Li et al., 2010).

3. **Update Documentation**
   Append the findings to `docs/SCIENTIFIC_BASIS.md` using the format:
   ```markdown
   ### [Algorithm/Concept Name]
   *   **Source**: [Citation/Reference]
   *   **Application**: [How it's used in the code]
   *   **Mechanism**: [Specific implementation detail]
   ```

4. **Verify Implementation**
   Ensure the code actually implements the cited principle (e.g., does the WMA actually use the weights stated?).
