# Research Methodology: Privacy-Preserving NLP via Masked LLM Prompting Pipelines

**Project Title:** Privacy-Preserving NLP: Round-Trip Fidelity Evaluation of PII Restoration in Masked LLM Prompting Pipelines  
**Subject:** AI/ML Engineering & Computational Privacy  
**Date:** November 2026  

---

## 1. Introduction & Research Motivation

Large Language Models (LLMs) served as remote cloud APIs (e.g., OpenAI, Anthropic, Google Gemini) process billions of user prompts daily. When users transmit prompts containing Personally Identifiable Information (PII) — such as patient names, contact numbers, street addresses, or government identification numbers — to remote third-party servers, they expose sensitive data to unauthorized retention, logging, and model memorization risks.

While pseudonymization through placeholder tokens is frequently suggested in privacy literature, **no standardized empirical framework evaluates the round-trip restoration fidelity of this approach**. Specifically:

1. Do placeholder tokens survive syntactic rewriting (summarization, paraphrasing, translation, grammatical editing) by LLMs intact?
2. Which placeholder structure provides optimal robustness against token mutation while preventing token collision and semantic leakage?
3. Can downstream restoration achieve zero identity leakage when faced with LLM hallucinations or dropped tokens?

**PIIShield AI** answers these questions through a mathematically formalized, experimentally reproducible evaluation platform.

---

## 2. Research Questions (RQs)

* **RQ1 (Preservation Robustness):** What percentage of PII placeholders survive unmodified across different LLM prompt-processing tasks (Normal, Paraphrase, Summarize, Translate, Edit)?
* **RQ2 (Strategy Efficacy):** How do four distinct placeholder representations (Sequential Basic, Random Typed, Opaque Hash, and Cryptographic Protected) compare in terms of downstream restoration F1 score and collision resistance?
* **RQ3 (Failure Mode Taxonomy):** What is the empirical distribution of failure modes when placeholders are corrupted (Dropped, Inflected, Mistranslated, Hallucinated, Cross-Wired)?
* **RQ4 (Predictive Risk):** Can machine learning models predict placeholder corruption risk a priori based solely on prompt-time features?
* **RQ5 (Detection Decoupling):** How does upstream PII detection accuracy (evaluated on public competition benchmarks) correlate with downstream restoration success?

---

## 3. Mathematical Framework & Metric Formulations

### 3.1 PII Detection Layer Metrics

Evaluated at the character-span level against independent ground truth:

$$\text{Detection Precision } (P_{det}) = \frac{TP_{det}}{TP_{det} + FP_{det}}$$

$$\text{Detection Recall } (R_{det}) = \frac{TP_{det}}{TP_{det} + FN_{det}}$$

$$\text{Detection } F_1 = \frac{2 \cdot P_{det} \cdot R_{det}}{P_{det} + R_{det}}$$

Where a True Positive ($TP_{det}$) requires an **exact character-span match** $[s, e]$ and matching entity type.

### 3.2 Round-Trip Restoration Metrics

Evaluated strictly at the placeholder level upon LLM response delivery:

$$\text{Restoration Precision } (P_{rest}) = \frac{\text{Correct Restorations}}{\text{Total Restoration Attempts}} = \frac{C}{A}$$

$$\text{Restoration Recall } (R_{rest}) = \frac{\text{Correct Restorations}}{\text{Total Expected Placeholders}} = \frac{C}{E}$$

$$\text{Restoration } F_1 = \frac{2 \cdot P_{rest} \cdot R_{rest}}{P_{rest} + R_{rest}} = \frac{2 \cdot C}{A + E}$$

**Denominator Clarifications:**
* $E$ (Expected): Total number of placeholders inserted during masking.
* $A$ (Attempts): All placeholders present in the output that underwent restoration attempts ($C + \text{Failed Attempts}$). If a token was completely dropped ($D$), it is not counted in $A$, but it is counted in $E$, appropriately penalizing Recall while preserving Precision.
* $C$ (Correct): Placeholders successfully verified and restored with their true mapped identity.

### 3.3 Placeholder Preservation Rate

$$\text{Preservation Rate} = \frac{E - D}{E}$$

Where $D$ is the count of completely dropped (omitted) placeholder tokens.

### 3.4 False Restoration Rate (Leakage Indicator)

$$\text{False Restoration Rate } (FRR) = \frac{\text{Cross-Wired Restorations} + \text{Hallucinated Mappings}}{A}$$

Under PIIShield AI's zero-leakage guarantee, $FRR \equiv 0.000$ because unverified tokens are strictly rejected.

---

## 4. The Four Placeholder Masking Strategies

```
┌────────────────────────────────────────────────────────────────────────┐
│ STRATEGY A: BASIC TYPED                                                │
│ Syntax: [<ENTITY_TYPE>_<INDEX>]                                        │
│ Example: [PERSON_1], [EMAIL_1], [PHONE_1]                              │
│ Theoretical Properties: Sequential, highly interpretable to LLM.       │
│ Vulnerability: Reordering ambiguity, multi-turn collisions.            │
├────────────────────────────────────────────────────────────────────────┤
│ STRATEGY B: RANDOM TYPED                                               │
│ Syntax: [<ENTITY_TYPE>_<5_CHAR_HEX_SALT>]                              │
│ Example: [PERSON_X7K92], [EMAIL_M4N81]                                 │
│ Theoretical Properties: Salted with SHA-256 entropy.                   │
│ Advantage: Prevents token collision across multi-turn sessions.        │
├────────────────────────────────────────────────────────────────────────┤
│ STRATEGY C: OPAQUE RANDOM                                              │
│ Syntax: Z<7_CHAR_HEX_HASH>                                             │
│ Example: ZXQ7K92M, ZD483CFE                                            │
│ Theoretical Properties: Zero semantic category leakage.                │
│ Advantage: Cloud LLM cannot infer what type of PII is being processed. │
├────────────────────────────────────────────────────────────────────────┤
│ STRATEGY D: CRYPTOGRAPHIC PROTECTED                                    │
│ Syntax: [PROT:<ENTITY_TYPE>:P<INDEX>:<4_CHAR_CRC_CHECKSUM>]            │
│ Example: [PROT:PERSON:P1:C4D9], [PROT:EMAIL:P1:9F2A]                   │
│ Checksum: hashlib.md5(original_value.encode())[:4].upper()             │
│ Theoretical Properties: Deterministic cryptographic tamper detection.  │
│ Advantage: Automatic detection of token modification or injection.     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Seven Failure Classification Modes

When an LLM processes masked text, output tokens are categorized into seven mutually exclusive states:

1. **`CORRECT`**: Token preserved identically in format and content; passes cryptographic checksum where applicable.
2. **`MISSED`**: Token omitted and replaced with a generalized noun phrase (e.g., *"the applicant"* instead of `[PERSON_1]`).
3. **`DROPPED`**: Token deleted entirely from output without any substitute.
4. **`INFLECTED`**: Token structure altered (brackets stripped `PERSON_1`, braces `{PERSON_1}`, lowercase `[person_1]`).
5. **`MISTRANSLATED`**: Token identifier translated into another natural language (e.g., `[PERSONNE_1]` in French).
6. **`HALLUCINATED`**: Spurious placeholder synthesized by LLM that was not present in the prompt.
7. **`CROSS_WIRED`**: Multiple placeholders swapped in relative position or entity binding.

---

## 6. Dataset Methodology & Integrity

### 6.1 Synthetic Research Dataset (300 Prompts, 852 Entities)
- **Controlled Environment:** Designed to evaluate restoration without real privacy risks.
- **Entity Balance:**
  - `PERSON`: 280 entities (32.9%)
  - `DATE`: 128 entities (15.0%)
  - `EMAIL`: 120 entities (14.1%)
  - `LOCATION`: 88 entities (10.3%)
  - `IDENTIFICATION_NUMBER`: 84 entities (9.9%)
  - `PHONE`: 84 entities (9.9%)
  - `ADDRESS`: 68 entities (8.0%)
- **Character Offset Invariant:** Every entity verified with `assert prompt[start:end] == value`.
- **Linguistic Mix:** 220 English prompts, 80 Hinglish/code-mixed prompts.

### 6.2 Public Kaggle Benchmark (PII Data Detection)
- **Source:** Kaggle `pii-detection-removal-from-educational-data` competition.
- **Purpose:** Independent evaluation of upstream **PII Detection accuracy** on student essays.
- **Strict Decoupling:** Never mixed with restoration metrics; public essays are never transmitted to external LLMs.

---

## 7. The Zero-Leakage Restoration Invariant

PIIShield AI implements a strict decision rule for restoration:

$$\text{Restore}(\tau) = \begin{cases} 
\mathcal{M}[\tau] & \text{if } \tau \in \text{dom}(\mathcal{M}) \land \text{Category}(\tau) = \text{CORRECT} \land \text{Verify}(\tau) = \text{True} \\
\text{BLOCKED} & \text{otherwise}
\end{cases}$$

This guarantees that unverified, corrupted, or hallucinated tokens are **never** restored with incorrect identities.

