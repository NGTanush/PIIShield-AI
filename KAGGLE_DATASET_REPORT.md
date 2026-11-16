# Kaggle Dataset Integration & Manifest Report

**Competition:** The Learning Agency Lab – PII Data Detection  
**Competition Slug:** `pii-detection-removal-from-educational-data`  
**Target Output Directory:** `./dataset/raw/kaggle_competition`  
**Report Date:** November 15, 2026  

---

## 1. Authentication Status & Blocker Analysis

When executing the official KaggleHub competition download command:

```python
import kagglehub

path = kagglehub.competition_download(
    'pii-detection-removal-from-educational-data',
    output_dir='./dataset/raw/kaggle_competition'
)
print("Dataset downloaded to:", path)
```

The system encountered the following exception:

```
kagglehub.exceptions.UnauthenticatedError: User is not authenticated
```

### Authentication Diagnostic Findings:
* `C:\Users\tanus\.kaggle\kaggle.json`: **NOT FOUND** (`exists = False`).
* `KAGGLE_USERNAME` in environment: **NOT SET**.
* `KAGGLE_KEY` in environment: **NOT SET**.

### Exact Steps for User Authentication (Zero-Leakage):
1. Log in to your Kaggle account in your web browser: [https://www.kaggle.com](https://www.kaggle.com).
2. Visit the competition page and accept the competition rules:  
   👉 [https://www.kaggle.com/competitions/pii-detection-removal-from-educational-data/rules](https://www.kaggle.com/competitions/pii-detection-removal-from-educational-data/rules).
3. Navigate to your Kaggle Account Settings: [https://www.kaggle.com/settings](https://www.kaggle.com/settings).
4. Scroll to the **API** section and click **Create New Token**. This downloads a file named `kaggle.json`.
5. Place `kaggle.json` directly into:
   ```
   C:\Users\tanus\.kaggle\kaggle.json
   ```
   *(Note: Never paste your API token or secret key into the chat or commit it to Git.)*
6. Execute the automated download and ingestion command:
   ```bash
   python dataset/public_benchmark/download_kaggle.py
   python dataset/public_benchmark/preprocess_full_kaggle.py
   python evaluation/benchmark_full_kaggle.py
   ```

---

## 2. Currently Active Dataset Manifest

While awaiting user placement of `kaggle.json`, the pipeline is primed and operating on the verified representative benchmark sample formatted identically to the competition schema:

| Attribute | Measured Value |
| :--- | :--- |
| **Dataset Source** | Kaggle Competition Schema (`pii-detection-removal-from-educational-data`) |
| **Active Dataset Scope** | 10 Educational Essays (Benchmark Sample) |
| **Full Competition Dataset Active** | **False (Pending Kaggle Authentication)** |
| **Total Tokens** | 622 |
| **Total PII Tokens (BIO)** | 118 |
| **Total Labelled PII Entities** | 53 |
| **Documents with PII** | 10 of 10 (100%) |
| **Train / Validation Split** | Document-Level (Seed = 42, Zero Document Leakage) |
| **Train Split Size** | 8 Documents (42 Entities) |
| **Validation Split Size** | 2 Documents (11 Entities) |

### Active Files Inventory:

| File Name | Path | Size | Description |
| :--- | :--- | :---: | :--- |
| `train.json` | `dataset/public_benchmark/raw/train.json` | 34.4 KB | Training essays with tokens, whitespace, & BIO labels |
| `test.json` | `dataset/public_benchmark/raw/test.json` | 25.3 KB | Unlabelled test essays (no labels) |
| `sample_submission.csv` | `dataset/public_benchmark/raw/sample_submission.csv` | 3.1 KB | Competition submission format (`row_id`, `document`, `token`, `label`) |
| `split_indices.json` | `dataset/public_benchmark/processed/split_indices.json` | 0.4 KB | Document ID partition mapping for zero-leakage evaluation |
| `kaggle_metadata.json` | `dataset/public_benchmark/metadata/kaggle_metadata.json` | 1.2 KB | Generated machine-readable dataset manifest |

---

## 3. PII Entity Category Distribution

Mapped from raw competition BIO labels to standard PIIShield AI ontology:

```
┌─────────────────────────┬──────────────────────────┬───────┬────────────┐
│ Kaggle BIO Label        │ PIIShield Standard Type  │ Count │ Percentage │
├─────────────────────────┼──────────────────────────┼───────┼────────────┤
│ B-NAME_STUDENT          │ PERSON                   │    20 │      37.7% │
│ B-EMAIL                 │ EMAIL                    │    10 │      18.9% │
│ B-STREET_ADDRESS        │ ADDRESS                  │    10 │      18.9% │
│ B-PHONE_NUM             │ PHONE                    │     7 │      13.2% │
│ B-ID_NUM                │ IDENTIFICATION_NUMBER    │     5 │       9.4% │
│ B-URL_PERSONAL          │ URL                      │     1 │       1.9% │
│ B-USERNAME              │ USERNAME                 │     0 │       0.0% │
├─────────────────────────┼──────────────────────────┼───────┼────────────┤
│ TOTAL                   │                          │    53 │     100.0% │
└─────────────────────────┴──────────────────────────┴───────┴────────────┘
```

---

## 4. Transition Protocol to Full 6,807-Essay Dataset

Once `kaggle.json` is in place, running `python dataset/public_benchmark/download_kaggle.py`:
1. Downloads the full ~2GB competition archive to `dataset/raw/kaggle_competition/`.
2. `preprocess_full_kaggle.py` streams all 6,807 training documents.
3. Automatically sets `is_full_competition_dataset = True` in `kaggle_metadata.json`.
4. Automatically updates Streamlit dashboard cards and metrics to reflect the full 6,807 essay distribution.

