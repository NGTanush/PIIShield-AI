# Dataset Methodology & Provenance Architecture

**Project:** PIIShield AI — Privacy-Preserving NLP Middleware  
**Date:** November 2026  

---

## 1. Dual-Dataset Research Architecture

PIIShield AI enforces a strict, scientifically motivated architectural separation between its two datasets:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PIIShield AI DATA ARCHITECTURE                  │
├───────────────────────────────────┬────────────────────────────────────┤
│ 1. SYNTHETIC BENCHMARK DATASET    │ 2. PUBLIC KAGGLE BENCHMARK DATASET │
│ (300 Prompts, 852 Entities)       │ (Educational Student Essays)       │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Evaluates: Downstream Round-    │ • Evaluates: Upstream PII          │
│   Trip Placeholder Restoration    │   Detection Model Accuracy         │
│ • Evaluates: 4 Placeholder Masking│ • Evaluates: Exact Span Matching & │
│   Strategies (A, B, C, D)         │   Recall-Weighted F5 Score         │
│ • Evaluates: 7 Failure Categories │ • Source: The Learning Agency Lab  │
│   Under LLM Perturbations         │   (Kaggle Competition)             │
│ • Zero privacy risk (Fictional)   │ • Strictly isolated from external  │
│ • Full character offset checks    │   cloud LLM transmissions          │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## 2. Why the Datasets Must Remain Decoupled

1. **Non-Equivalence of Evaluation Goals:**
   * The Kaggle competition evaluates **PII Detection** (finding named entities in static student essays).
   * PIIShield AI investigates **Round-Trip Placeholder Restoration** (measuring whether placeholders survive complex LLM prompt processing without corruption).
2. **Privacy Transmission Safety:**
   * Sending student essays containing real or semi-synthetic personal names and emails to commercial third-party LLMs would defeat the core purpose of a privacy gateway.
   * Only controlled synthetic prompts are transmitted through live external LLMs.
3. **Reproducibility of Failure Perturbations:**
   * Systematic evaluation of inflected, mistranslated, or deleted tokens requires controlled scenario design (e.g. translation to French, token bracket stripping) which cannot be inferred from unperturbed static essays alone.

---

## 3. Strict Data Provenance Labels

Every experiment recorded in PIIShield AI carries an immutable provenance tag in `piishield.db`:

* **`synthetic`**: Controlled experiments using the 300-prompt benchmark dataset.
* **`kaggle_train`**: Upstream detection evaluation on training partition essays.
* **`kaggle_validation`**: Upstream detection evaluation on held-out validation essays ($N_{seed}=42$).
* **`real_llm`**: Live prompt executions processed via local Ollama or cloud OpenAI-compatible APIs.
* **`simulated`**: Live interactive demonstrations executed via the 8-scenario deterministic simulator.

---

## 4. Tokenization & BIO Tag Alignment Methodology

### 4.1 BIO Token Grouping
Kaggle essays are tokenized into discrete words and annotated with BIO (Beginning, Inside, Outside) tags:
* `B-<TYPE>` initiates an entity span.
* `I-<TYPE>` continues the entity span.
* `O` designates non-PII tokens.

The preprocessing algorithm merges adjacent $B$ and $I$ tokens into unified entity spans:

$$\text{Span}(\tau_i \dots \tau_j) = [start(\tau_i), end(\tau_j)] \quad \text{where } \forall k \in [i+1, j], \, label(\tau_k) = \text{I-TYPE}$$

### 4.2 Document-Level Partitioning
To eliminate data leakage, document splitting is conducted strictly at the essay level:
* A fixed random seed ($seed = 42$) randomly assigns 80% of documents to training and 20% to validation.
* No individual document has tokens spanning both splits:
  $$\mathcal{D}_{\text{train}} \cap \mathcal{D}_{\text{val}} = \emptyset$$
* Split indices are permanently recorded in `dataset/public_benchmark/processed/split_indices.json`.

