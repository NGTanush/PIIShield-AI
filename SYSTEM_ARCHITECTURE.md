# System Architecture Specification: PIIShield AI

**Project:** PIIShield AI — Privacy-Preserving NLP Middleware  
**Architecture Style:** Client-Side Zero-Knowledge Middleware & Empirical Research Framework  
**Date:** November 2026  

---

## 1. High-Level Architectural Overview

PIIShield AI operates as an **isolated, client-side privacy gateway** positioned between the user's application environment and third-party Large Language Model (LLM) APIs.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT / LOCAL BOUNDARY                         │
│                                                                        │
│   [User Input Text] ──────────────────────────────────────────────┐    │
│           │                                                       │    │
│           ▼                                                       │    │
│   ┌───────────────┐                                               │    │
│   │ PII Detector  │ (Regex + spaCy NER)                           │    │
│   └───────┬───────┘                                               │    │
│           ▼                                                       │    │
│   ┌───────────────┐        Isolated Local Mapping                 │    │
│   │  PII Masker   │──────► [Memory-Only Dictionary]               │    │
│   └───────┬───────┘        (NEVER sent to remote host)            │    │
│           │                                                       │    │
│           │ (Masked Prompt ONLY)                                  │    │
│           ▼                                                       │    │
├───────────┼───────────────────────────────────────────────────────┼────┤
│           │                      REMOTE / CLOUD BOUNDARY          │    │
│           │                                                       │    │
│           ▼                                                       │    │
│   ┌───────────────┐                                               │    │
│   │ External LLM  │ (Ollama, OpenAI API, or Mock Scenarios)       │    │
│   └───────┬───────┘ Sees ONLY placeholders: [PERSON_1], etc.      │    │
│           │                                                       │    │
├───────────┼───────────────────────────────────────────────────────┼────┤
│           │ (Raw Output)                                          │    │
│           ▼                                                       │    │
│   ┌────────────────────────┐                                      │    │
│   │ Placeholder Validator  │◄── Audits tokens against Local Map   │    │
│   └───────────┬────────────┘    Checks format, dropped, CRC       │    │
│               ▼                                                   │    │
│   ┌────────────────────────┐                                      │    │
│   │   Safe PII Restorer    │◄── Restores ONLY validated tokens    │    │
│   └───────────┬────────────┘                                      │    │
│               ▼                                                   │    │
│   ┌────────────────────────┐                                      │    │
│   │  Research Evaluation   │──► Sanitized SQLite Database         │    │
│   │   & ML Predictor       │    (No raw PII logged)               │    │
│   └───────────┬────────────┘                                      │    │
│               ▼                                                   │    │
│   [Final Restored Output] ────────────────────────────────────────┘    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory & Module Organization

```
PIIShield-AI/
├── app.py                            # Streamlit Application Entrypoint (10 Pages)
├── requirements.txt                  # Production Dependencies
├── README.md                         # Quickstart & System Overview
├── FINAL_PROJECT_AUDIT.md            # Comprehensive Project Audit
├── RESEARCH_METHODOLOGY.md           # Research Questions & Formulations
├── EXPERIMENTAL_RESULTS.md           # Empirical Evaluation Data
├── SYSTEM_ARCHITECTURE.md            # Architecture Specification (This file)
├── SECURITY_AND_PRIVACY.md           # Threat Model & Security Proof
├── FINAL_DEMONSTRATION_GUIDE.md      # Examiner Demonstration Script
├── PROJECT_COMPLETION_REPORT.md      # Final Deliverable Summary
├── .env.example                      # Template Configuration (No Secrets)
├── .gitignore                        # Git Exclusions
├── piishield.db                      # Sanitized SQLite Experiment Database
│
├── detection/                        # 1. PII Detection Layer
│   └── pii_detector.py              # Hybrid Regex + spaCy NER Detection
│
├── masking/                          # 2. Adaptive Masking Layer
│   └── pii_masker.py                # Strategies A, B, C, D Masking Engine
│
├── llm/                              # 3. LLM Integration Layer
│   └── llm_processor.py             # Ollama, OpenAI API, & 8 Demo Scenarios
│
├── validation/                       # 4. Placeholder Validation Layer
│   └── placeholder_validator.py     # 7 Failure Modes & Checksum Auditing
│
├── restoration/                      # 5. Safe Restoration Layer
│   └── pii_restorer.py              # Zero-Leakage Conditional Restorer
│
├── evaluation/                       # 6. Evaluation & ML Prediction
│   ├── metrics.py                   # P/R/F1 Mathematical Metric Formulations
│   ├── benchmark_detection.py       # Public Kaggle Detection Benchmark
│   ├── failure_predictor.py         # Scikit-Learn ML Failure Predictor
│   └── models/                      # Serialized ML Models & Scalers
│
├── database/                         # 7. Persistence Layer
│   └── db_manager.py                # SQLite Sanitized Run Tracking
│
├── dataset/                          # 8. Research Datasets
│   ├── synthetic_prompts.csv        # 300 Controlled Base Prompts
│   ├── ground_truth.json            # 852 Verified Character-Span Entities
│   ├── experiment_scenarios.csv     # Multi-Scenario Perturbation Matrix
│   ├── placeholder_variants.csv     # 4-Strategy Masking Manifest
│   └── public_benchmark/            # Kaggle Educational PII Benchmark
│
├── dashboard/                        # 9. Multi-Page UI Frontend
│   ├── styles.py                    # Dark Glassmorphic Theme CSS
│   ├── page_overview.py             # 1. Overview Dashboard
│   ├── page_dataset.py              # 2. Research Dataset & Kaggle Tab
│   ├── page_detection.py            # 3. PII Detection & Masking Lab
│   ├── page_llm.py                  # 4. LLM Processing Gateway
│   ├── page_validation.py           # 5. Validation & Restoration
│   ├── page_failure_prediction.py   # 6. ML Failure Prediction Lab
│   ├── page_strategies.py           # 7. Strategy Comparison Lab
│   ├── page_evaluation.py           # 8. Research Evaluation Metrics
│   ├── page_history.py              # 9. Experiment History Log
│   └── page_about.py                # 10. Research Documentation
│
└── tests/                            # 10. Automated Test Suites
    ├── test_pipeline.py             # Pipeline & Failure Category Tests (7/7)
    ├── test_dataset.py              # Dataset & Offset Integrity Tests (6/6)
    ├── test_kaggle_integration.py   # Kaggle Benchmark Tests (6/6)
    └── test_failure_predictor.py    # ML Failure Predictor Tests (5/5)
```

---

## 3. Database Schema Specification

SQLite database stored at `piishield.db`:

```sql
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    original_text_length INTEGER,
    masked_text TEXT NOT NULL,
    num_entities_detected INTEGER NOT NULL,
    entity_types_json TEXT,
    llm_mode TEXT NOT NULL,
    llm_scenario TEXT NOT NULL,
    raw_llm_response TEXT NOT NULL,
    restored_response TEXT NOT NULL,
    num_correct INTEGER NOT NULL,
    num_missed INTEGER NOT NULL,
    num_dropped INTEGER NOT NULL,
    num_inflected INTEGER NOT NULL,
    num_mistranslated INTEGER NOT NULL,
    num_hallucinated INTEGER NOT NULL,
    num_cross_wired INTEGER NOT NULL,
    precision_score REAL NOT NULL,
    recall_score REAL NOT NULL,
    f1_score REAL NOT NULL,
    placeholder_preservation_rate REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    notes TEXT,
    data_provenance TEXT NOT NULL DEFAULT 'simulated',
    placeholder_strategy TEXT NOT NULL DEFAULT 'strategy_a_basic',
    num_restoration_attempts INTEGER DEFAULT 0,
    detection_precision REAL DEFAULT 1.0,
    detection_recall REAL DEFAULT 1.0,
    detection_f1 REAL DEFAULT 1.0
);
```

**Privacy Guarantee:** Notice that the `experiments` table contains `original_text_length`, `masked_text`, and `restored_response` (which contains restored text created on the local client), but **never stores the raw local PII mapping dictionary**.

---

## 4. Streamlit Session State Dataflow

To ensure seamless multi-page workflow without cross-contamination:

| State Key | Producer Page | Consumer Pages | Description |
| :--- | :--- | :--- | :--- |
| `original_text` | Detection, Dataset | Masking, LLM, Validation | Current prompt plaintext |
| `entities` | Detection, Dataset | Masking, Evaluation | List of detected `PIIEntity` objects |
| `masked_text` | Detection, Dataset | LLM, Validation, DB | Sanitized text containing placeholders |
| `placeholder_mapping` | Detection, Dataset | Validation, Restorer | Isolated in-memory `{placeholder: plaintext}` |
| `placeholder_strategy`| Detection, Dataset | Masking, Validation, DB | Active strategy (A, B, C, or D) |
| `llm_response` | LLM Processing | Validation, Restorer, DB | Raw string returned by LLM |
| `validation_report` | Validation | Restorer, Evaluation | Audit instance with categorized results |
| `restored_text` | Validation | Evaluation, DB | Final post-processed client text |
| `data_provenance` | Dataset, LLM | Evaluation, DB | Tag (`benchmark`, `real_llm`, `simulated`) |

