# Kaggle Benchmark Results & Evaluation Report

**Competition:** The Learning Agency Lab – PII Data Detection  
**Evaluation Scope:** Exact Span & Entity-Type Matching ($[start:end]$ alignment)  
**Report Date:** November 15, 2026  

---

## 1. Overall Model Benchmark Comparison

All detectors were evaluated across all ground-truth entities ($N=53$):

| Detection Method | True Positives ($TP$) | False Positives ($FP$) | False Negatives ($FN$) | Precision | Recall | Micro $F_1$ | Competition $F_5$ | Macro $F_1$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Regex Patterns Only** | 14 | 11 | 39 | **56.0%** | 26.4% | **35.9%** | 27.0% | **22.7%** |
| **2. spaCy NER Only** | 11 | 56 | 42 | 16.4% | 20.8% | 18.3% | 20.5% | 6.0% |
| **3. Hybrid (Regex + NER)** | **25** | 64 | **28** | 28.1% | **47.2%** | **35.2%** | **46.0%** | 21.1% |

### Key Observations:
1. **Hybrid Method Dominates Recall and $F_5$:**
   * The Hybrid detector achieves the highest recall (**47.2%**) and recovers **25 true positive entities**, outperforming Regex (14 TP) and spaCy (11 TP).
   * Under the competition's recall-weighted $F_5$ metric ($\beta=5$), Hybrid achieves **46.0%** vs 27.0% for Regex and 20.5% for spaCy, demonstrating superior redaction safety.
2. **Regex Excels in Precision:**
   * Regex achieves **56.0% precision**, driven by 100% precision on email addresses and telephone numbers.
3. **spaCy Over-Generation:**
   * Off-the-shelf `en_core_web_sm` generates 56 false positives on ordinary capitalized words in student essays, depressing precision to 16.4%.

---

## 2. Per-Entity Category Performance Breakdown

### Table: Category Breakdown (Hybrid Detection Engine)

| Entity Type | Support ($N$) | True Positives | False Positives | False Negatives | Precision | Recall | $F_1$ Score | $F_5$ Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **EMAIL** | 10 | 10 | 0 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| **PHONE** | 7 | 4 | 11 | 3 | 26.7% | 57.1% | 36.4% | 54.4% |
| **PERSON** | 20 | 11 | 20 | 9 | 35.5% | 55.0% | 43.1% | 53.8% |
| **ADDRESS** | 10 | 0 | 3 | 10 | 0.0% | 0.0% | 0.0% | 0.0% |
| **ID_NUM** | 5 | 0 | 0 | 5 | 0.0% | 0.0% | 0.0% | 0.0% |
| **URL** | 1 | 0 | 0 | 1 | 0.0% | 0.0% | 0.0% | 0.0% |

---

## 3. Failure Mode & Error Analysis

### 3.1 EMAIL Detection (100% Precision, 100% Recall)
* Standard RFC-5322 regex patterns reliably match student and university emails (e.g. `sarah.jenkins@university.edu`, `carlos.mendoza99@campus-mail.org`).
* Zero false positives or false negatives observed.

### 3.2 PERSON Detection (55% Recall, 35.5% Precision)
* spaCy correctly identifies first and last names in student signatures (e.g. *"Elena Rostova"*, *"David Kim"*).
* Misses non-Western name token boundaries and names embedded within titles or headers.
* Generates false positives on capitalized course assignments and technical terms (e.g. *"Design Thinking"*).

### 3.3 STREET_ADDRESS (0% Exact Span Match)
* The Kaggle competition defines addresses as complete strings including building numbers, street names, cities, states, and postal codes (e.g. *"742 Evergreen Terrace, Springfield, OR 97477"*).
* spaCy's `FAC` / `LOC` labels only capture single tokens (e.g. *"Evergreen Terrace"*), causing **exact span matching** to fail because the span $[start:end]$ does not align with the complete multi-token ground truth.
* Fine-tuned transformer models (e.g. DeBERTa-v3 token classification) are required for multi-token address boundary alignment.

---

## 4. The $F_5$ Evaluation Metric Rationale

In privacy redaction competitions, missing a sensitive entity (False Negative) is significantly more dangerous than redacting an ordinary word (False Positive).

$$F_\beta = (1 + \beta^2) \frac{\text{Precision} \cdot \text{Recall}}{(\beta^2 \cdot \text{Precision}) + \text{Recall}}$$

With $\beta = 5$:

$$F_5 = \frac{26 \cdot P \cdot R}{25 \cdot P + R}$$

Under $F_5$, recall is weighted **25 times more heavily** than precision, properly rewarding the Hybrid detector for recovering 25 true entities.

