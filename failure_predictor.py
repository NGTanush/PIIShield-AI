"""
ML-Based Failure Prediction Module for PIIShield AI.

Trains a classifier to predict the probability that a placeholder will
survive LLM processing (or fail) based on features extractable at masking time.

NOTE: The synthetic dataset used for training is intentionally small (300 prompts,
852 entities). The model is therefore EXPERIMENTAL and labelled accordingly.
Never claim it is production-ready based on this limited data.
"""
import json
import os
import sys
import pickle
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MODEL_DIR = PROJECT_ROOT / "evaluation" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "failure_predictor.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
METADATA_PATH = MODEL_DIR / "predictor_metadata.json"

ENTITY_TYPE_ORDER = [
    "PERSON", "EMAIL", "PHONE", "LOCATION", "DATE",
    "ADDRESS", "IDENTIFICATION_NUMBER", "ORGANIZATION", "OTHER"
]

STRATEGY_ORDER = [
    "strategy_a_basic", "strategy_b_random_typed",
    "strategy_c_opaque", "strategy_d_protected"
]

SCENARIO_ORDER = [
    "normal", "paraphrase", "summarize", "translate",
    "grammar", "placeholder_modification", "placeholder_deletion",
    "placeholder_duplication", "other"
]


def _build_feature_vector(
    entity_type: str,
    placeholder_strategy: str,
    scenario: str,
    num_entities_in_prompt: int,
    entity_index: int,
    pii_density: str,
    language: str,
    prompt_token_count: int,
) -> np.ndarray:
    """
    Build a fixed-length feature vector for one placeholder occurrence.

    Features (12 total):
    - One-hot entity type (9 dims)
    - One-hot strategy (4 dims)
    - One-hot scenario (9 dims)
    - num_entities_in_prompt (normalized)
    - entity_index (normalized, 0-based)
    - pii_density_encoded (0=Low, 1=Medium, 2=High)
    - language_encoded (0=English, 1=Hinglish)
    - prompt_token_count (normalized)
    """
    # Entity type one-hot
    et = [1 if entity_type == e else 0 for e in ENTITY_TYPE_ORDER]
    # Strategy one-hot
    st = [1 if placeholder_strategy == s else 0 for s in STRATEGY_ORDER]
    # Scenario one-hot
    sc = [1 if scenario == s else 0 for s in SCENARIO_ORDER]
    # Numeric features
    n_ents = min(num_entities_in_prompt, 20) / 20.0
    e_idx = min(entity_index, 10) / 10.0
    density_map = {"Low": 0, "Medium": 1, "High": 2, "low": 0, "medium": 1, "high": 2}
    density_enc = density_map.get(pii_density, 1) / 2.0
    lang_enc = 1.0 if language in ("Hinglish", "hinglish", "code-mixed") else 0.0
    tok_count = min(prompt_token_count, 200) / 200.0

    return np.array(et + st + sc + [n_ents, e_idx, density_enc, lang_enc, tok_count], dtype=float)


def _build_training_data() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Build a synthetic training dataset from the experiment scenarios CSV.
    Each row in experiment_scenarios.csv represents a (prompt, scenario) pair.
    We label an experiment as 'failure' (1) if the scenario is known to cause
    placeholder issues, based on the documented research scenarios.

    Label encoding:
    - 0 = placeholder preserved correctly
    - 1 = placeholder failed (dropped / modified / hallucinated)
    """
    scenarios_path = PROJECT_ROOT / "dataset" / "experiment_scenarios.csv"
    prompts_path = PROJECT_ROOT / "dataset" / "synthetic_prompts.csv"
    gt_path = PROJECT_ROOT / "dataset" / "ground_truth.json"

    if not scenarios_path.exists() or not prompts_path.exists():
        raise FileNotFoundError("Synthetic dataset files not found. Run dataset/generate_dataset.py first.")

    df_scenarios = pd.read_csv(scenarios_path)
    df_prompts = pd.read_csv(prompts_path)

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    gt_map = {item["prompt_id"]: item for item in ground_truth}

    # Failure probability by scenario (empirical from research design)
    # Based on documented behaviour in PIIShield research scenarios
    scenario_failure_prob = {
        "Normal": 0.03,          # Very low failure rate
        "Paraphrasing": 0.08,    # Low — LLM rephrases but keeps tokens
        "Summarization": 0.25,   # Medium — tokens may be dropped in summaries
        "Translation": 0.45,     # High — tokens often get translated
        "Grammar Correction": 0.05,
        "Placeholder Modification": 0.70,  # Very high — explicitly modifies tokens
        "Placeholder Deletion": 0.80,       # Very high — explicitly deletes tokens
        "Placeholder Duplication": 0.60,    # High — creates invalid duplicates
    }
    # Strategy failure resistance (from published research design)
    strategy_failure_adjustment = {
        "strategy_a_basic": 0.0,       # Baseline
        "strategy_b_random_typed": -0.03,  # Slightly more resistant
        "strategy_c_opaque": 0.10,     # Slightly more fragile (LLM doesn't understand)
        "strategy_d_protected": -0.05, # Checksum helps detect, counts as handled
    }

    X_rows = []
    y_labels = []
    prompt_ids = []

    rng = np.random.default_rng(42)

    for _, row in df_scenarios.iterrows():
        pid = row.get("prompt_id", "")
        scenario = row.get("scenario", "Normal")
        strategy = row.get("placeholder_strategy", "strategy_a_basic")
        language = row.get("language", "English")
        pii_density = row.get("pii_density", "Medium")

        gt_item = gt_map.get(pid)
        if gt_item is None:
            continue

        annotations = gt_item.get("annotations", [])
        num_entities = len(annotations)
        prompt_text = gt_item.get("original_prompt", "")
        token_count = len(prompt_text.split())

        base_fail_prob = scenario_failure_prob.get(scenario, 0.10)
        strat_adj = strategy_failure_adjustment.get(strategy, 0.0)
        final_fail_prob = max(0.0, min(1.0, base_fail_prob + strat_adj))

        for idx, ann in enumerate(annotations):
            entity_type = ann.get("entity_type", "OTHER")
            feat = _build_feature_vector(
                entity_type=entity_type,
                placeholder_strategy=strategy,
                scenario=scenario.lower().replace(" ", "_"),
                num_entities_in_prompt=num_entities,
                entity_index=idx,
                pii_density=pii_density,
                language=language,
                prompt_token_count=token_count,
            )

            # Deterministic labelling based on scenario probability
            # (This is synthetic ground truth; real labels would come from actual LLM runs)
            label = int(rng.random() < final_fail_prob)

            X_rows.append(feat)
            y_labels.append(label)
            prompt_ids.append(pid)

    if not X_rows:
        raise ValueError("No training samples could be constructed.")

    return np.array(X_rows), np.array(y_labels), prompt_ids


def train_model(force_retrain: bool = False) -> Dict[str, Any]:
    """
    Train and persist the failure prediction model.
    Uses Logistic Regression as baseline and Random Forest as main model.
    Returns evaluation metrics dictionary.
    """
    if MODEL_PATH.exists() and not force_retrain:
        meta = {}
        if METADATA_PATH.exists():
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
        return {"status": "loaded_existing", **meta}

    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import GroupShuffleSplit
        from sklearn.metrics import (
            precision_score, recall_score, f1_score,
            accuracy_score, confusion_matrix, classification_report
        )
    except ImportError:
        return {"status": "error", "message": "scikit-learn not installed. Run: pip install scikit-learn"}

    print("[*] Building training data from synthetic benchmark dataset...")
    X, y, prompt_ids = _build_training_data()

    total_samples = len(X)
    n_positive = int(y.sum())
    n_negative = total_samples - n_positive

    print(f"[*] Training samples: {total_samples} | Positive (failure): {n_positive} | Negative: {n_negative}")

    # Group-aware split: prompts with same ID go entirely into train or test
    # This prevents leakage from similar prompt templates
    unique_ids = list(set(prompt_ids))
    id_arr = np.array(prompt_ids)

    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups=id_arr))

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # Scale features
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc = scaler.transform(X_test)

    # Baseline: Logistic Regression
    lr = LogisticRegression(max_iter=500, random_state=42, class_weight="balanced")
    lr.fit(X_train_sc, y_train)
    lr_pred = lr.predict(X_test_sc)

    lr_metrics = {
        "accuracy": float(accuracy_score(y_test, lr_pred)),
        "precision": float(precision_score(y_test, lr_pred, zero_division=0)),
        "recall": float(recall_score(y_test, lr_pred, zero_division=0)),
        "f1": float(f1_score(y_test, lr_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, lr_pred).tolist(),
    }

    # Main model: Random Forest
    rf = RandomForestClassifier(
        n_estimators=100, max_depth=8, random_state=42, class_weight="balanced"
    )
    rf.fit(X_train_sc, y_train)
    rf_pred = rf.predict(X_test_sc)
    rf_proba = rf.predict_proba(X_test_sc)[:, 1]

    rf_metrics = {
        "accuracy": float(accuracy_score(y_test, rf_pred)),
        "precision": float(precision_score(y_test, rf_pred, zero_division=0)),
        "recall": float(recall_score(y_test, rf_pred, zero_division=0)),
        "f1": float(f1_score(y_test, rf_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, rf_pred).tolist(),
    }

    # Choose best model (by F1)
    best_model = rf if rf_metrics["f1"] >= lr_metrics["f1"] else lr
    best_name = "RandomForest" if rf_metrics["f1"] >= lr_metrics["f1"] else "LogisticRegression"

    # Save model and scaler
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(best_model, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    # Feature importance (RF only)
    feature_names = (
        [f"entity_{e}" for e in ENTITY_TYPE_ORDER]
        + [f"strategy_{s}" for s in STRATEGY_ORDER]
        + [f"scenario_{sc}" for sc in SCENARIO_ORDER]
        + ["num_entities_norm", "entity_idx_norm", "density_enc", "language_enc", "token_count_norm"]
    )
    importance = {}
    if hasattr(best_model, "feature_importances_"):
        for name, imp in zip(feature_names, best_model.feature_importances_):
            importance[name] = round(float(imp), 5)

    metadata = {
        "status": "trained",
        "best_model": best_name,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "total_samples": total_samples,
        "positive_rate": round(float(n_positive / total_samples), 4),
        "logistic_regression": lr_metrics,
        "random_forest": rf_metrics,
        "best_model_metrics": rf_metrics if best_name == "RandomForest" else lr_metrics,
        "feature_names": feature_names,
        "top_features": dict(sorted(importance.items(), key=lambda x: -x[1])[:10]),
        "data_limitation": (
            "EXPERIMENTAL: Trained on synthetic data with scenario-based labels. "
            "Ground-truth failure labels are simulated from documented scenario failure rates, "
            "not from actual LLM outputs. Performance numbers are indicative only."
        ),
        "model_path": str(MODEL_PATH),
        "scaler_path": str(SCALER_PATH),
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n[+] Model trained: {best_name}")
    print(f"    Accuracy: {rf_metrics['accuracy']*100:.1f}%  Precision: {rf_metrics['precision']*100:.1f}%  Recall: {rf_metrics['recall']*100:.1f}%  F1: {rf_metrics['f1']*100:.1f}%")
    print(f"[+] Model saved to: {MODEL_PATH}")

    return metadata


def predict_failure_probability(
    entity_type: str,
    placeholder_strategy: str,
    scenario: str,
    num_entities_in_prompt: int = 1,
    entity_index: int = 0,
    pii_density: str = "Medium",
    language: str = "English",
    prompt_token_count: int = 50,
) -> Dict[str, Any]:
    """
    Predict probability that a placeholder will fail during LLM processing.
    Returns risk level, probability, and confidence.
    """
    if not MODEL_PATH.exists() or not SCALER_PATH.exists():
        # Auto-train if model missing
        result = train_model()
        if result.get("status") == "error":
            return {
                "failure_probability": 0.5,
                "risk_level": "UNKNOWN",
                "prediction": "UNCERTAIN",
                "error": result.get("message", "Model not available"),
                "is_experimental": True
            }

    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)
    except Exception as e:
        return {
            "failure_probability": 0.5,
            "risk_level": "UNKNOWN",
            "prediction": "UNCERTAIN",
            "error": str(e),
            "is_experimental": True
        }

    feat = _build_feature_vector(
        entity_type=entity_type,
        placeholder_strategy=placeholder_strategy,
        scenario=scenario,
        num_entities_in_prompt=num_entities_in_prompt,
        entity_index=entity_index,
        pii_density=pii_density,
        language=language,
        prompt_token_count=prompt_token_count,
    ).reshape(1, -1)

    feat_sc = scaler.transform(feat)
    pred_label = int(model.predict(feat_sc)[0])

    if hasattr(model, "predict_proba"):
        prob = float(model.predict_proba(feat_sc)[0][1])
    else:
        prob = float(pred_label)

    if prob < 0.25:
        risk = "LOW"
    elif prob < 0.50:
        risk = "MODERATE"
    elif prob < 0.75:
        risk = "HIGH"
    else:
        risk = "VERY HIGH"

    return {
        "failure_probability": round(prob, 4),
        "risk_level": risk,
        "prediction": "FAIL" if pred_label == 1 else "PASS",
        "entity_type": entity_type,
        "strategy": placeholder_strategy,
        "scenario": scenario,
        "is_experimental": True,
        "disclaimer": "EXPERIMENTAL: Based on synthetic scenario labels, not real LLM outputs."
    }


def predict_batch(
    entity_types: List[str],
    placeholder_strategy: str,
    scenario: str,
    num_entities_in_prompt: int,
    pii_density: str = "Medium",
    language: str = "English",
    prompt_token_count: int = 50,
) -> List[Dict[str, Any]]:
    """Predict for each entity in a prompt."""
    return [
        predict_failure_probability(
            entity_type=et,
            placeholder_strategy=placeholder_strategy,
            scenario=scenario,
            num_entities_in_prompt=num_entities_in_prompt,
            entity_index=idx,
            pii_density=pii_density,
            language=language,
            prompt_token_count=prompt_token_count,
        )
        for idx, et in enumerate(entity_types)
    ]


def get_model_metadata() -> Dict[str, Any]:
    """Return training metadata if model exists."""
    if METADATA_PATH.exists():
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"status": "not_trained"}


if __name__ == "__main__":
    print("Training failure prediction model...")
    meta = train_model(force_retrain=True)
    print("\nFull Metadata:")
    print(json.dumps({k: v for k, v in meta.items() if k not in ("feature_names",)}, indent=2))

