"""Unit and Integration Tests for ML Failure Prediction in PIIShield AI."""
import io
import json
import os
import sys
from pathlib import Path

# Safe utf-8 stdout for Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.failure_predictor import (
    predict_failure_probability,
    predict_batch,
    get_model_metadata,
    _build_feature_vector,
    train_model
)


def test_feature_vector_structure():
    """Verify feature vector generates correct dimensions and values."""
    feat = _build_feature_vector(
        entity_type="PERSON",
        placeholder_strategy="strategy_a_basic",
        scenario="normal",
        num_entities_in_prompt=3,
        entity_index=0,
        pii_density="Medium",
        language="English",
        prompt_token_count=50,
    )
    # 9 entity types + 4 strategies + 9 scenarios + 5 numeric = 27 dims
    assert len(feat) == 27, f"Expected 27 features, got {len(feat)}"
    assert feat[0] == 1.0, "PERSON should be active (1.0)"
    assert feat[9] == 1.0, "strategy_a_basic should be active (1.0)"
    print("✅ test_feature_vector_structure passed (27 feature dimensions verified)")


def test_model_metadata():
    """Verify model metadata structure and presence."""
    meta = get_model_metadata()
    assert meta.get("status") in ("trained", "loaded_existing"), f"Unexpected status: {meta.get('status')}"
    assert "best_model" in meta
    assert "best_model_metrics" in meta
    bm = meta["best_model_metrics"]
    assert "accuracy" in bm and "f1" in bm and "precision" in bm and "recall" in bm
    assert 0.0 <= bm["accuracy"] <= 1.0
    print(f"✅ test_model_metadata passed (Best Model: {meta.get('best_model')}, Accuracy: {bm['accuracy']*100:.1f}%)")


def test_prediction_probability_bounds():
    """Verify single prediction outputs probability between 0 and 1 with valid risk level."""
    pred = predict_failure_probability("EMAIL", "strategy_b_random_typed", "paraphrase")
    prob = pred["failure_probability"]
    assert 0.0 <= prob <= 1.0, f"Probability {prob} out of bounds"
    assert pred["risk_level"] in ("LOW", "MODERATE", "HIGH", "VERY HIGH")
    assert pred["prediction"] in ("PASS", "FAIL")
    assert pred["is_experimental"] is True
    print(f"✅ test_prediction_probability_bounds passed (Prob: {prob:.4f}, Risk: {pred['risk_level']})")


def test_scenario_risk_differential():
    """Verify that corruptive scenarios (Modification/Deletion) yield higher risk than Normal."""
    p_normal = predict_failure_probability("PERSON", "strategy_a_basic", "normal")
    p_corrupt = predict_failure_probability("PERSON", "strategy_a_basic", "placeholder_deletion")
    assert p_corrupt["failure_probability"] > p_normal["failure_probability"], (
        f"Corruptive scenario should have higher risk: {p_corrupt['failure_probability']} <= {p_normal['failure_probability']}"
    )
    print(f"✅ test_scenario_risk_differential passed (Normal: {p_normal['failure_probability']:.2f} < Deletion: {p_corrupt['failure_probability']:.2f})")


def test_batch_prediction():
    """Verify batch prediction processes multiple entities consistently."""
    entities = ["PERSON", "EMAIL", "PHONE", "LOCATION"]
    results = predict_batch(
        entity_types=entities,
        placeholder_strategy="strategy_d_protected",
        scenario="summarize",
        num_entities_in_prompt=4,
    )
    assert len(results) == 4, f"Expected 4 predictions, got {len(results)}"
    for idx, r in enumerate(results):
        assert r["entity_type"] == entities[idx]
        assert 0.0 <= r["failure_probability"] <= 1.0
    print("✅ test_batch_prediction passed (4 entities evaluated)")


def run_all_tests():
    print("=" * 60)
    print("PIIShield AI — ML Failure Prediction Test Suite")
    print("=" * 60)
    tests = [
        test_feature_vector_structure,
        test_model_metadata,
        test_prediction_probability_bounds,
        test_scenario_risk_differential,
        test_batch_prediction,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"❌ {t.__name__} FAILED: {e}")
            failed += 1
    print("=" * 60)
    print(f"Failure Prediction Tests: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 60)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()

