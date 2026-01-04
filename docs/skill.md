# Skill: Semantic Knowledge Tracing Upgrade (LKT/DKT Hybrid)

## 1. Context & Objective
Upgrade the Learner Profiler from **Bayesian Knowledge Tracing (BKT)** (scalar, discrete) to a **LLM-based Semantic Tracing** architecture.
*   **Primary Source:** *Language Model Can Do Knowledge Tracing (LKT)* [Lee et al.].
*   **Foundational Logic:** *Deep Knowledge Tracing (DKT)* [Piech et al.].
*   **Goal:** Leverage pre-trained semantic understanding to solve the "Cold Start" problem and capture latent dependencies between concepts that BKT misses.

## 2. Data Engineering: The LKT Input Format

Unlike DKT which uses numerical IDs ($q_t, a_t$), the system must transform interactions into a **textual sequence** to utilize the PLM's semantic power.

### 2.1. Tokenization Strategy
*   **Input Sequence Construction:** Concatenate Knowledge Concepts (KCs), Question Texts, and Responses into a single stream.
*   **Special Tokens:** Use `[CLS]` for start, `[EOS]` for end. Use specific tokens `[CORRECT]` and `[INCORRECT]` for outcomes.
*   **Masking Logic:** To train the model to predict mastery, replace 15% of the response tokens with `[MASK]`.

### 2.2. Prompt Template (Strict Construction)
*Reference: LKT Paper, Section 3.2 & Figure 1,*

The AI must format the history buffer ($H_t$) into the following string structure before tokenization:

```text
[CLS] KC_Content_1 \n Question_Text_1 [Response_Token_1] KC_Content_2 \n Question_Text_2 [Response_Token_2] ... KC_Target \n Question_Target [MASK] [EOS]
```

**Variables:**
*   `KC_Content`: Text description of the concept (e.g., "Calculating area").
*   `Question_Text`: The actual problem text (e.g., "A rectangular room measures 12 by 15...").
*   `Response_Token`: Either `[CORRECT]` or `[INCORRECT]`.
*   `Target`: The next step we want to predict probability for.

**Example Data Block:**
```text
KCs : Calculating area Questions : A rectangular room measures 12 feet by 15 feet. What is the area? Responses : [CORRECT]
KCs : Finding perimeter Questions : What is the perimeter... Responses : [MASK]
```

## 3. Model Architecture & Training

### 3.1. Backbone Selection
*   **Model:** Use **DeBERTa-v3** or **RoBERTa** (proven to outperform standard BERT in LKT benchmarks).
*   **Mechanism:** Encoder-based PLM. The model does *not* generate text; it classifies the token at the `[MASK]` position.

### 3.2. Prediction Head (Mathematical Logic)
Instead of a simple classification, we extract the logit for the `[MASK]` token at position $m$.

*   **Equation:** $\hat{y}_{m} = \sigma(h_m)$.
    *   $h_m$: Hidden state vector at mask position.
    *   $\sigma$: Sigmoid function mapping to probability $(0, 1)$.
    *   **Output:** The probability that the student will answer `[CORRECT]`.

### 3.3. Loss Function
Use **Binary Cross-Entropy (BCE)** loss between predicted probability $\hat{y}$ and actual correctness $y$ (0 or 1).
*   **Formula:** $L = - \sum [y \log(\hat{y}) + (1-y) \log(1-\hat{y})]$.

## 4. Solving Specific Problems

### 4.1. The "Cold Start" Problem
*   **Challenge:** New students or new questions have no history $H_t$. BKT fails here.
*   **LKT Solution:** Do *not* initialize with random weights. Rely on the **Pre-trained Knowledge** of the LLM. The model understands from the text "Calculating area" that it is related to "Multiplication", even with zero interaction history.
*   **Heuristic:** For a cold-start student, feed the `Question_Text` with an empty history. The model will output a probability based purely on the semantic difficulty of the text.

### 4.2. Curriculum Optimization (Next Step Recommendation)
*   **DKT Logic:** Use the trained model to simulate future states.
*   **Algorithm:** **Expectimax / Greedy Lookahead**,.
    1.  Candidate Generation: Select $k$ potential next questions ($q_{next}$).
    2.  Simulation: Append each $q_{next}$ to the student's current history string with a `[MASK]` token.
    3.  Evaluation: Query the LKT model to get $P(Correct | History, q_{next})$.
    4.  Selection: Choose the question that yields the optimal probability (e.g., closest to 0.5 for ZPD or highest for mastery confirmation).

## 5. Interpretability & "Whitebox" Analysis

To prevent "Hallucinated Competence" and ensure the model isn't guessing, implement **Attention Analysis**.

### 5.1. Attention Map Extraction
*   **Action:** Extract attention weights from the last layer for the `[MASK]` token.
*   **Verification:** Check which tokens have the highest weights.
    *   *Good Signal:* High attention on domain-specific terms (e.g., "integers", "odd positive").
    *   *Bad Signal:* High attention on stop words ("the", "is") or irrelevant context.

### 5.2. LIME Integration (Optional)
If computational resources allow, run LIME (Local Interpretable Model-agnostic Explanations) to identify which words contributed most to a "Pass" prediction.

## 6. Implementation Checklist for AI Agent

1.  [ ] **Tokenizer Update:** Add special tokens `[CORRECT]`, `[INCORRECT]` to the PLM tokenizer.
2.  [ ] **Data Pipeline:** Create a function `format_interaction_history(user_log) -> string` following the LKT template.
3.  [ ] **Model Registry:** Load `deberta-v3-base`. Replace the head with a binary classification layer on top of the hidden state.
4.  [ ] **Inference Function:**
    ```python
    def predict_mastery(history_str):
        tokenized = tokenizer(history_str + " [MASK]", return_tensors='pt')
        logits = model(**tokenized).last_hidden_state
        mask_idx = (tokenized.input_ids == tokenizer.mask_token_id).nonzero()
        return sigmoid(linear_layer(logits[mask_idx]))
    ```
5.  [ ] **Safety Check:** If history is empty, ensure the prompt includes the full text of the incoming question to leverage Zero-shot capabilities.
