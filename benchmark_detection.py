"""PII Detection Benchmark Engine for Public Kaggle Dataset.

Evaluates and compares:
1. Regex-only detection
2. spaCy NER-only detection
3. Hybrid detection (Regex + NER merged)

Calculates entity-level Precision, Recall, F1, and per-category breakdowns
using exact span and entity-type matching against Kaggle ground truth.
"""
import io
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd

# Safe utf-8 stdout
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from detection.pii_detector import (
    detect_with_regex,
    detect_with_spacy,
    detect_pii,
    PIIEntity
)
PROCESSED_FILE = BASE_DIR / "dataset" / "public_benchmark" / "processed" / "kaggle_pii_ground_truth.json"
RESULTS_DIR = BASE_DIR / "dataset" / "public_benchmark" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_method_on_docs(docs: List[Dict[str, Any]], method_name: str) -> Dict[str, Any]:
    """
    Evaluates a specific detection method against preprocessed Kaggle documents.
    Uses exact character span [start:end] and entity_type matching.
    """
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    # Per-category accumulators
    cat_stats: Dict[str, Dict[str, int]] = {}
    
    detailed_matches = []
    
    for doc in docs:
        doc_id = doc["document_id"]
        text = doc["full_text"]
        gt_entities = doc["entities"]
        
        # Run detection method
        if method_name == "regex":
            preds = detect_with_regex(text)
        elif method_name == "spacy":
            preds = detect_with_spacy(text)
        elif method_name == "hybrid":
            preds = detect_pii(text, use_spacy=True)
        else:
            raise ValueError(f"Unknown detection method: {method_name}")
            
        matched_gt_indices = set()
        matched_pred_indices = set()
        
        # Check exact matches: start, end, type
        for p_idx, p in enumerate(preds):
            p_type = p.entity_type
            for g_idx, g in enumerate(gt_entities):
                if g_idx in matched_gt_indices:
                    continue
                # Exact span and standard type match
                if p.start == g["start"] and p.end == g["end"] and p_type == g["standard_type"]:
                    matched_gt_indices.add(g_idx)
                    matched_pred_indices.add(p_idx)
                    
                    if p_type not in cat_stats:
                        cat_stats[p_type] = {"tp": 0, "fp": 0, "fn": 0}
                    cat_stats[p_type]["tp"] += 1
                    
                    detailed_matches.append({
                        "doc_id": doc_id,
                        "type": p_type,
                        "value": p.value,
                        "status": "TP",
                        "method": method_name
                    })
                    break
        
        # Unmatched predictions are False Positives
        for p_idx, p in enumerate(preds):
            if p_idx not in matched_pred_indices:
                p_type = p.entity_type
                if p_type not in cat_stats:
                    cat_stats[p_type] = {"tp": 0, "fp": 0, "fn": 0}
                cat_stats[p_type]["fp"] += 1
                
                detailed_matches.append({
                    "doc_id": doc_id,
                    "type": p_type,
                    "value": p.value,
                    "status": "FP",
                    "method": method_name
                })
        
        # Unmatched ground truth entities are False Negatives
        for g_idx, g in enumerate(gt_entities):
            if g_idx not in matched_gt_indices:
                g_type = g["standard_type"]
                if g_type not in cat_stats:
                    cat_stats[g_type] = {"tp": 0, "fp": 0, "fn": 0}
                cat_stats[g_type]["fn"] += 1
                
                detailed_matches.append({
                    "doc_id": doc_id,
                    "type": g_type,
                    "value": g["value"],
                    "status": "FN",
                    "method": method_name
                })
                
        total_tp += len(matched_gt_indices)
        total_fp += (len(preds) - len(matched_pred_indices))
        total_fn += (len(gt_entities) - len(matched_gt_indices))

    # Calculate overall micro metrics
    prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
    
    # Calculate per-category metrics
    per_category = {}
    f1_list = []
    for cat, counts in cat_stats.items():
        c_tp = counts["tp"]
        c_fp = counts["fp"]
        c_fn = counts["fn"]
        c_p = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 0.0
        c_r = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 0.0
        c_f1 = (2 * c_p * c_r) / (c_p + c_r) if (c_p + c_r) > 0 else 0.0
        per_category[cat] = {
            "tp": c_tp,
            "fp": c_fp,
            "fn": c_fn,
            "precision": round(c_p, 4),
            "recall": round(c_r, 4),
            "f1_score": round(c_f1, 4),
            "support": c_tp + c_fn
        }
        f1_list.append(c_f1)
        
    macro_f1 = sum(f1_list) / len(f1_list) if f1_list else 0.0
    
    return {
        "method": method_name,
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "macro_f1": round(macro_f1, 4),
        "per_category": per_category,
        "detailed_matches": detailed_matches
    }


def run_benchmark(ground_truth_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Executes benchmark across all detection methods and exports summary CSV and JSON.
    """
    if ground_truth_file is None:
        ground_truth_file = PROCESSED_FILE
        
    if not ground_truth_file.exists():
        raise FileNotFoundError(f"Processed benchmark data not found at {ground_truth_file}. Run preprocess_kaggle.py first.")

    with open(ground_truth_file, "r", encoding="utf-8") as f:
        docs = json.load(f)

    methods = ["regex", "spacy", "hybrid"]
    method_labels = {
        "regex": "1. Regex Patterns Only",
        "spacy": "2. spaCy NER Only",
        "hybrid": "3. Hybrid (Regex + spaCy NER)"
    }
    
    results = {}
    summary_rows = []
    cat_rows = []
    
    print("\n" + "=" * 65)
    print("      PUBLIC BENCHMARK: PII DETECTION EVALUATION RESULTS")
    print("=" * 65)
    
    for m in methods:
        eval_res = evaluate_method_on_docs(docs, m)
        results[m] = eval_res
        
        lbl = method_labels[m]
        summary_rows.append({
            "Method": lbl,
            "TP": eval_res["true_positives"],
            "FP": eval_res["false_positives"],
            "FN": eval_res["false_negatives"],
            "Precision": eval_res["precision"],
            "Recall": eval_res["recall"],
            "F1_Score": eval_res["f1_score"],
            "Macro_F1": eval_res["macro_f1"]
        })
        
        for cat, cdata in eval_res["per_category"].items():
            cat_rows.append({
                "Method": lbl,
                "Entity_Type": cat,
                "Precision": cdata["precision"],
                "Recall": cdata["recall"],
                "F1_Score": cdata["f1_score"],
                "Support": cdata["support"]
            })
            
        print(f"[{lbl}]")
        print(f"  Micro Precision: {eval_res['precision']*100:.1f}% | Recall: {eval_res['recall']*100:.1f}% | F1: {eval_res['f1_score']*100:.1f}% | Macro F1: {eval_res['macro_f1']*100:.1f}%")
        print(f"  TP: {eval_res['true_positives']} | FP: {eval_res['false_positives']} | FN: {eval_res['false_negatives']}")
        print("-" * 65)

    # Export to JSON
    json_path = RESULTS_DIR / "detection_benchmark_results.json"
    clean_results = {m: {k: v for k, v in res.items() if k != "detailed_matches"} for m, res in results.items()}
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(clean_results, f, indent=2)

    # Export Summary CSV
    summary_csv_path = RESULTS_DIR / "detection_benchmark_summary.csv"
    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(summary_csv_path, index=False)

    # Export Per-Category CSV
    cat_csv_path = RESULTS_DIR / "per_category_comparison.csv"
    df_cat = pd.DataFrame(cat_rows)
    df_cat.to_csv(cat_csv_path, index=False)

    print(f"\n[+] Benchmark Results saved successfully:")
    print(f"    - {json_path}")
    print(f"    - {summary_csv_path}")
    print(f"    - {cat_csv_path}")
    
    return {
        "summary": summary_rows,
        "results": clean_results,
        "files": {
            "json": str(json_path),
            "summary_csv": str(summary_csv_path),
            "per_category_csv": str(cat_csv_path)
        }
    }


if __name__ == "__main__":
    run_benchmark()
