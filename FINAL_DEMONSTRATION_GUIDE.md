# Final Demonstration & Viva Examination Guide

**Project:** PIIShield AI — Privacy-Preserving NLP Middleware  
**Target Audience:** Final Year Project Examiners, Professors, and Evaluators  
**Demonstration Time:** 10–12 Minutes  

---

## 1. Quick Launch Instructions

Open PowerShell or Command Prompt in the project folder and launch:

```bash
# Launch Streamlit on dedicated port 8531
streamlit run app.py --server.port 8531
```

Open your browser to: **`http://localhost:8531`**

> **Note:** If port 8531 is occupied, Streamlit will automatically attempt 8532 or launch with `streamlit run app.py`.

---

## 2. 10-Minute Step-by-Step Viva Demonstration Script

### Step 1: Overview Dashboard (`📊 Overview Dashboard`) — 1 Minute
* **What to Show:**
  * Top metric cards: Total Experiments, Micro-Averaged F1 (**87.8%**), Precision (**90.0%**), Recall (**85.7%**).
  * Explain: *"Our dashboard calculates mathematically sound micro-averages over all historical experiment attempts rather than unweighted averages."*
  * Point out the **Zero-Leakage Invariant**: False Restoration Rate ($FRR$) is strictly **0.0%**.

### Step 2: Research Dataset (`📚 Research Dataset`) — 2 Minutes
* **What to Show:**
  * Point out the dataset characteristics: **300 base prompts**, **852 verified PII entities**, 7 PII categories.
  * Use the filter dropdowns to show English and Hinglish/code-mixed prompts.
  * Click on the **🌐 Public Dataset Benchmark** tab:
    * Show the **Kaggle PII Data Detection competition benchmark**.
    * Highlight the model comparison: Regex (high precision on emails/phones) vs. spaCy NER (broad coverage of names) vs. Hybrid (highest recall: 47.2%).
  * Return to the **🔍 Prompt Inspector & Runner** tab, pick prompt `PROMPT_007`, choose **Strategy D (Protected)**, and click:
    👉 **`🚀 Load into Live Pipeline`**

### Step 3: Detection & Masking (`🔍 PII Detection & Masking`) — 2 Minutes
* **What to Show:**
  * Show the loaded prompt (or type a custom text like below):
    ```text
    Patient Priya Sharma (DOB: 12/05/1988, Phone: 9876543210, Email: priya.sharma@medmail.org) visited Dr. Rajesh Gupta at Apollo Hospital, Bengaluru on 15/03/2025 regarding Aadhaar 4321 8765 2109.
    ```
  * Click **`🔍 Detect PII Entities`**:
    * Show the detected entities table with exact character spans $[start:end]$.
  * Select **Strategy D (Protected)** and click **`🔒 Mask PII Entities`**:
    * Show the resulting masked text: `[PROT:PERSON:P1:C4D9]`, `[PROT:EMAIL:P1:9F2A]`, etc.
  * **Key Viva Talking Point:**
    * *"Notice that the reverse translation mapping is stored strictly in client memory. It is never transmitted across the network to the external LLM."*

### Step 4: LLM Processing (`🤖 LLM Processing`) — 2 Minutes
* **What to Show:**
  * Point out the provider selection options: **🎭 Demo / Simulated Scenarios**, **🦙 Ollama Local LLM**, and **🌐 External Cloud API**.
  * Under Demo Mode, select **`Placeholder Modification`** or **`Normal Response`**.
  * Click **`🚀 Process with LLM`**:
    * Show the generated response. Notice that the LLM has operated solely on the masked text.
    * Point out the provenance badge: `SIMULATED` or `REAL_LLM`.

### Step 5: Validation & Restoration (`🔐 Validation & Restoration`) — 2 Minutes
* **What to Show:**
  * Click **`🔎 Validate & Restore`**:
    * Show the **Validation Summary Cards**: Correct, Dropped, Inflected, Hallucinated, Cross-Wired, Mistranslated.
    * Show the per-placeholder audit trail.
  * **The Zero-Leakage Demonstration:**
    * *"If the LLM stripped the brackets or dropped a token, PIIShield refuses to guess the original identity. The restored output safely preserves unverified tokens or alerts the user, guaranteeing zero identity cross-contamination."*

### Step 6: ML Failure Prediction Lab (`🧠 Failure Prediction`) — 1 Minute
* **What to Show:**
  * Show the trained machine-learning model: **Logistic Regression & Random Forest** trained on 852 entity samples with GroupShuffleSplit (no leakage).
  * Enter a test scenario and click **`🔮 Predict Failure Risk`**:
    * Show the predicted failure probability (e.g., 96% failure risk under Deletion vs. 1% under Normal).
  * Show the **Scenario × Strategy Risk Heatmap**.

### Step 7: Strategy Comparison Lab (`🛡️ Placeholder Strategies`) — 1 Minute
* **What to Show:**
  * Show the 4-way side-by-side comparison (A: Basic, B: Random, C: Opaque, D: Protected).
  * Point out the **Cryptographic Integrity Verification Demo**:
    * Show how authentic checksum `C4D9` passes, while tampered token `FFFF` is blocked.

### Step 8: Research Evaluation & Audit Log (`📈 Research Evaluation` & `📜 History`) — 1 Minute
* **What to Show:**
  * Show the calculated mathematically rigorous metrics ($P_{rest}, R_{rest}, F_1$).
  * Click **`💾 Commit Experiment`** to persist the run to `piishield.db`.
  * Navigate to **`📜 Experiment History`**:
    * Show the searchable audit log.
    * Click **`📥 Export Full Experiment Audit Log (CSV)`** to download the CSV for research paper tables.

---

## 3. Frequently Asked Examiner Questions & Model Answers

### Q1: "Why not simply use regex or find-and-replace for PII masking?"
> **Answer:** *"Pure regex only works on structured formats with fixed grammars like emails and phone numbers. It completely fails on unstructured person names, physical street addresses, and context-dependent titles. PIIShield AI combines high-precision regex with transformer/spaCy NER for unstructured entities, resolving overlapping spans using confidence ranking. Furthermore, simple find-and-replace does not address downstream LLM token corruption or safe restoration."*

### Q2: "What happens if an LLM hallucinates a new placeholder like `[PERSON_99]`?"
> **Answer:** *"Our validation engine audits every token against the local mapping dictionary. An unknown token like `[PERSON_99]` is classified as `FailureCategory.HALLUCINATED`. It is strictly rejected and never restored, preventing arbitrary strings from entering local databases."*

### Q3: "How does Strategy D detect prompt injection or token tampering?"
> **Answer:** *"Strategy D embeds a 4-character deterministic checksum: `MD5(original_value)[:4]`. When the response returns from the LLM, the restorer recomputes the checksum against the locally mapped value. If an adversary or model hallucination altered the entity index or checksum, the validation check fails and blocks restoration."*

### Q4: "Does this system guarantee Differential Privacy?"
> **Answer:** *"No, and we explicitly document this limitation in our research methodology. PIIShield AI provides client-side syntactic pseudonymization and integrity verification. While it eliminates direct identifier transmission to cloud LLMs, it does not prevent contextual re-identification if the surrounding prose contains unique quasi-identifiers."*

### Q5: "How does your system prevent experiment data pollution?"
> **Answer:** *"We enforce strict test isolation. Automated test suites write to temporary in-memory or sandboxed databases (`test_piishield_isolated.db`), leaving the primary research database `piishield.db` clean. Additionally, our database only records masked tokens, never raw personal information."*

---

## 4. Emergency Backup Commands

```bash
# 1. Verify all 24 automated tests in terminal:
python tests/test_pipeline.py
python tests/test_dataset.py
python tests/test_kaggle_integration.py
python tests/test_failure_predictor.py

# 2. Re-train ML model if needed:
python evaluation/failure_predictor.py

# 3. Check database contents:
python -c "from database.db_manager import get_dashboard_stats; import json; print(json.dumps(get_dashboard_stats(), indent=2))"
```

