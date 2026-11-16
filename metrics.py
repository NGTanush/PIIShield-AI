"""
PIIShield AI — Evaluation Metrics Engine
Mathematically rigorous computation of PII Detection Metrics,
Placeholder Preservation Rates, and Round-Trip PII Restoration Fidelity.
"""
from typing import Dict, Any, List, Optional
from validation.placeholder_validator import ValidationReport, FailureCategory


def safe_divide(numerator: float, denominator: float) -> float:
    """Safe division returning 0.0 when denominator is zero."""
    if denominator == 0 or denominator == 0.0:
        return 0.0
    return numerator / denominator


def compute_restoration_metrics(
    validation_report: ValidationReport,
    restoration_attempts: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compute mathematically sound restoration fidelity metrics.

    Definitions:
      - Total Expected Placeholders (E): Ground-truth placeholders sent in masked prompt.
      - Restoration Attempts (A): Total placeholders evaluated for restoration.
        By default, equal to all placeholders detected in the LLM output (correct + corrupted + mistranslated + cross_wired).
      - Correct Restorations (C): Placeholders validated as exact match and correctly restored.
      - Restoration Precision: C / A (0.0 if A == 0)
      - Restoration Recall: C / E (0.0 if E == 0)
      - Restoration F1: 2 * (P * R) / (P + R) (0.0 if P + R == 0)
      - Preservation Rate: (E - Dropped) / E
    """
    total_expected = len(validation_report.results)
    correct = validation_report.correct_count

    # Attempts: candidate placeholders found in response where restoration was evaluated
    if restoration_attempts is None:
        attempts = sum(
            1 for r in validation_report.results
            if r.category in (
                FailureCategory.CORRECT,
                FailureCategory.INFLECTED,
                FailureCategory.MISTRANSLATED,
                FailureCategory.CROSS_WIRED,
                FailureCategory.MISSED
            )
        ) + validation_report.hallucinated_count
        # If no corrupted tokens but correct exist, attempts = correct
        attempts = max(attempts, correct)
    else:
        attempts = restoration_attempts

    precision = safe_divide(float(correct), float(attempts))
    recall = safe_divide(float(correct), float(total_expected))
    f1 = safe_divide(2.0 * precision * recall, precision + recall)

    # Preservation rate: placeholders that survived in any form (not dropped)
    dropped = validation_report.dropped_count
    preserved = max(0, total_expected - dropped)
    preservation_rate = safe_divide(float(preserved), float(total_expected))

    # Per-entity type breakdown
    per_entity: Dict[str, Dict[str, Any]] = {}
    for r in validation_report.results:
        # Extract entity type from placeholder token (supports Strategy A, B, C, D)
        etype = _extract_entity_type(r.placeholder)
        if etype not in per_entity:
            per_entity[etype] = {
                "expected": 0,
                "correct": 0,
                "failed": 0,
                "attempts": 0,
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0
            }
        per_entity[etype]["expected"] += 1
        if r.category == FailureCategory.CORRECT:
            per_entity[etype]["correct"] += 1
            per_entity[etype]["attempts"] += 1
        else:
            per_entity[etype]["failed"] += 1
            if r.category != FailureCategory.DROPPED:
                per_entity[etype]["attempts"] += 1

    # Calculate per-entity P/R/F1
    for etype, data in per_entity.items():
        p = safe_divide(float(data["correct"]), float(data["attempts"]))
        r = safe_divide(float(data["correct"]), float(data["expected"]))
        f = safe_divide(2.0 * p * r, p + r)
        data["precision"] = round(p, 4)
        data["recall"] = round(r, 4)
        data["f1"] = round(f, 4)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "placeholder_preservation_rate": round(preservation_rate, 4),
        "total_expected": total_expected,
        "restoration_attempts": attempts,
        "total_correct": correct,
        "total_failed": total_expected - correct,
        "failure_distribution": validation_report.summary(),
        "per_entity_type": per_entity,
        "num_hallucinated": validation_report.hallucinated_count,
        "num_duplicated": len(validation_report.duplicate_placeholders),
    }


def compute_detection_metrics(
    detected_entities: List[Any],
    ground_truth_entities: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Compute PII Detection layer metrics independently from restoration.
    Compares detected entities against ground-truth annotations by value and type.
    """
    if not ground_truth_entities:
        return {
            "detection_precision": 1.0 if detected_entities else 0.0,
            "detection_recall": 1.0 if not detected_entities else 0.0,
            "detection_f1": 1.0 if not detected_entities else 0.0,
            "true_positives": 0,
            "false_positives": len(detected_entities),
            "false_negatives": 0,
        }

    gt_matches = [False] * len(ground_truth_entities)
    tp = 0
    fp = 0

    for det in detected_entities:
        det_val = getattr(det, "value", str(det))
        det_type = getattr(det, "entity_type", "")

        matched = False
        for idx, gt in enumerate(ground_truth_entities):
            if not gt_matches[idx]:
                gt_val = gt.get("value", "")
                gt_type = gt.get("entity_type", "")
                if det_val.strip().lower() == gt_val.strip().lower():
                    # value matches; if type matches or not specified
                    if not det_type or det_type == gt_type or gt_type in ("OTHER", "IDENTIFICATION_NUMBER"):
                        gt_matches[idx] = True
                        matched = True
                        tp += 1
                        break
        if not matched:
            fp += 1

    fn = len(ground_truth_entities) - tp
    prec = safe_divide(float(tp), float(tp + fp))
    rec = safe_divide(float(tp), float(len(ground_truth_entities)))
    f1 = safe_divide(2.0 * prec * rec, prec + rec)

    return {
        "detection_precision": round(prec, 4),
        "detection_recall": round(rec, 4),
        "detection_f1": round(f1, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
    }


def _extract_entity_type(placeholder: str) -> str:
    """Helper to extract entity type across all 4 placeholder strategies."""
    p = placeholder.strip("[]")
    if p.startswith("PROT:"):
        # Strategy D: PROT:PERSON:P1:C4D9
        parts = p.split(":")
        return parts[1] if len(parts) > 1 else "UNKNOWN"
    elif "_" in p:
        # Strategy A or B: PERSON_1 or PERSON_X7K92
        return p.rsplit("_", 1)[0]
    elif p.startswith("Z") and len(p) == 8:
        # Strategy C: Opaque
        return "OPAQUE"
    return "OTHER"


# Backwards compatibility alias
compute_metrics = compute_restoration_metrics
