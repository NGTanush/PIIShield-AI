"""Comprehensive Detection Benchmark Module for Kaggle PII Data Detection.

Evaluates Regex, spaCy NER, and Hybrid detectors across Kaggle documents
using exact span matching, per-category breakdown, Macro/Micro F1,
and competition-standard F-beta (beta=5, F5) recall-weighted metric.
"""
import io
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from detection.pii_detector import (
    detect_with_regex,
    detect_with_spacy,
    detect_pii,
    PIIEntity
)

PUBLIC_BENCHMARK_DIR = PROJECT_ROOT / "dataset" / "public_benchmark"
PROCESSED_DIR = PUBLIC_BENCHMARK_DIR / "processed"
RESULTS_DIR = PUBLIC_BENCHMARK_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def compute_f_beta(precision: float, recall: float, beta: float = 5.0) -> float:
    """Computes F-beta score. With beta=5, recall is weighted 5x higher than precision."""
    b2 = beta ** 2
    denom = (b2 * precision) + recall
    if denom == 0:
        return 0.0
    return ((1.0 + b2) * precision * recall) / denom


def evaluate_method(docs: List[Dict[str, Any]], method_name: str) -> Dict[str, Any]:
    """
    Evaluates detection method on preprocessed documents using exact span and type matching.
    """
    total_tp = 0
    total_fp = 0
    total_fn = 0
    cat_stats: Dict[str, Dict[str, int]] = {}

    for doc in docs:
        text = doc["full_text"]
        gt_entities = doc["entities"]

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

        for p_idx, p in enumerate(preds):
            p_type = p.entity_type
            for g_idx, g in enumerate(gt_entities):
                if g_idx in matched_gt_indices:
                    continue
                if p.start == g["start"] and p.end == g["end"] and p_type == g["standard_type"]:
                    matched_gt_indices.add(g_idx)
                    matched_pred_indices.add(p_idx)
                    if p_type not in cat_stats:
                        cat_stats[p_type] = {"tp": 0, "fp": 0, "fn": 0}
                    cat_stats[p_type]["tp"] += 1
                    break

        for p_idx, p in enumerate(preds):
            if p_idx not in matched_pred_indices:
                p_type = p.entity_type
                if p_type not in cat_stats:
                    cat_stats[p_type] = {"tp": 0, "fp": 0, "fn": 0}
                cat_stats[p_type]["fp"] += 1

        for g_idx, g in enumerate(gt_entities):
            if g_idx not in matched_gt_indices:
                g_type = g["standard_type"]
                if g_type not in cat_stats:
                    cat_stats[g_type] = {"tp": 0, "fp": 0, "fn": 0}
                cat_stats[g_type]["fn"] += 1

        total_tp += len(matched_gt_indices)
        total_fp += (len(preds) - len(matched_pred_indices))
        total_fn += (len(gt_entities) - len(matched_gt_indices))

    prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
    f5 = compute_f_beta(prec, rec, beta=5.0)

    per_category = {}
    f1_list = []
    for cat, counts in cat_stats.items():
        c_tp = counts["tp"]
        c_fp = counts["fp"]
        c_fn = counts["fn"]
        c_p = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 0.0
        c_r = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 0.0
        c_f1 = (2 * c_p * c_r) / (c_p + c_r) if (c_p + c_r) > 0 else 0.0
        c_f5 = compute_f_beta(c_p, c_r, beta=5.0)
        per_category[cat] = {
            "tp": c_tp, "fp": c_fp, "fn": c_fn,
            "precision": round(c_p, 4),
            "recall": round(c_r, 4),
            "f1_score": round(c_f1, 4),
            "f5_score": round(c_f5, 4),
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
        "f5_score": round(f5, 4),
        "macro_f1": round(macro_f1, 4),
        "per_category": per_category
    }


def run_full_benchmark(use_validation_split: bool = False) -> Dict[str, Any]:
    """
    Runs benchmark on either the validation split or all processed documents.
    """
    file_to_load = PROCESSED_DIR / ("kaggle_val_ground_truth.json" if use_validation_split else "kaggle_pii_ground_truth.json")
    if not file_to_load.exists():
        file_to_load = PROCESSED_DIR / "kaggle_pii_ground_truth.json"
        
    if not file_to_load.exists():
        raise FileNotFoundError(f"Processed ground truth file not found at {file_to_load}. Run preprocess_full_kaggle.py first.")

    with open(file_to_load, "r", encoding="utf-8") as f:
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

    print(f"\n{'='*70}")
    print(f"   KAGGLE PII BENCHMARK EVALUATION (Dataset: {file_to_load.name}, {len(docs)} Docs)")
    print(f"{'='*70}")

    for m in methods:
        eval_res = evaluate_method(docs, m)
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
            "F5_Score": eval_res["f5_score"],
            "Macro_F1": eval_res["macro_f1"]
        })

        for cat, cdata in eval_res["per_category"].items():
            cat_rows.append({
                "Method": lbl,
                "Entity_Type": cat,
                "Precision": cdata["precision"],
                "Recall": cdata["recall"],
                "F1_Score": cdata["f1_score"],
                "F5_Score": cdata["f5_score"],
                "Support": cdata["support"]
            })

        print(f"[{lbl}]")
        print(f"  Precision: {eval_res['precision']*100:.1f}% | Recall: {eval_res['recall']*100:.1f}% | Micro F1: {eval_res['f1_score']*100:.1f}% | F5: {eval_res['f5_score']*100:.1f}% | Macro F1: {eval_res['macro_f1']*100:.1f}%")
        print(f"  TP: {eval_res['true_positives']} | FP: {eval_res['false_positives']} | FN: {eval_res['false_negatives']}")
        print(f"{'-'*70}")

    json_path = RESULTS_DIR / "detection_benchmark_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(RESULTS_DIR / "detection_benchmark_summary.csv", index=False)

    df_cat = pd.DataFrame(cat_rows)
    df_cat.to_csv(RESULTS_DIR / "per_category_comparison.csv", index=False)

    print(f"\n[+] Full Benchmark Results saved to:")
    print(f"    - {json_path}")
    print(f"    - {RESULTS_DIR / 'detection_benchmark_summary.csv'}")
    print(f"    - {RESULTS_DIR / 'per_category_comparison.csv'}")

    return {
        "summary": summary_rows,
        "results": results,
        "documents_evaluated": len(docs)
    }


if __name__ == "__main__":
    run_full_benchmark(use_validation_split=False)

