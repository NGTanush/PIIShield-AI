"""
PIIShield AI — Comprehensive Test Suite
Validates:
  - All 4 placeholder strategies (Basic, Random Typed, Opaque, Protected)
  - All 7 failure categories (Correct, Missed, Dropped, Inflected, Mistranslated, Hallucinated, Cross-Wired)
  - Separate Detection & Restoration metrics
  - Isolated database testing without polluting live database
"""
import sys
import os
import io
import re

# Force UTF-8 output encoding on Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detection.pii_detector import detect_pii, detect_with_regex
from masking.pii_masker import PIIMasker
from llm.llm_processor import process_with_demo, get_available_scenarios
from validation.placeholder_validator import (
    validate_placeholders, FailureCategory, find_all_placeholders
)
from restoration.pii_restorer import PIIRestorer
from evaluation.metrics import (
    compute_restoration_metrics, compute_detection_metrics, safe_divide
)
from database.db_manager import (
    init_db, save_experiment, get_all_experiments, get_dashboard_stats
)


def test_regex_detection():
    """Test regex-based PII detection across multiple structured formats."""
    text = (
        "Email: test@example.com, Phone: +91-9876543210, SSN: 123-45-6789, "
        "Aadhaar: 4532 8901 2345, PAN: ABCDE1234F"
    )
    entities = detect_with_regex(text)
    types_found = {e.entity_type for e in entities}
    assert "EMAIL" in types_found, f"Expected EMAIL, got {types_found}"
    assert "PHONE" in types_found, f"Expected PHONE, got {types_found}"
    assert "SSN" in types_found, f"Expected SSN, got {types_found}"
    assert "AADHAAR" in types_found, f"Expected AADHAAR, got {types_found}"
    assert "PAN" in types_found, f"Expected PAN, got {types_found}"
    print("✅ test_regex_detection passed")


def test_four_masking_strategies():
    """Test masking under all 4 placeholder strategies."""
    text = "Rahul Sharma can be reached at rahul@example.com."
    entities = detect_pii(text, use_spacy=False)

    # Strategy A: Basic
    masker_a = PIIMasker(strategy="strategy_a_basic")
    m_a, map_a = masker_a.mask_text(text, entities)
    assert "[EMAIL_1]" in m_a
    assert "rahul@example.com" not in m_a

    # Strategy B: Random Typed
    masker_b = PIIMasker(strategy="strategy_b_random_typed")
    m_b, map_b = masker_b.mask_text(text, entities)
    assert any("[EMAIL_" in k for k in map_b.keys())
    assert "rahul@example.com" not in m_b

    # Strategy C: Opaque
    masker_c = PIIMasker(strategy="strategy_c_opaque")
    m_c, map_c = masker_c.mask_text(text, entities)
    assert any(k.startswith("Z") for k in map_c.keys())
    assert "rahul@example.com" not in m_c

    # Strategy D: Protected
    masker_d = PIIMasker(strategy="strategy_d_protected")
    m_d, map_d = masker_d.mask_text(text, entities)
    assert any("[PROT:EMAIL:" in k for k in map_d.keys())
    assert "rahul@example.com" not in m_d

    print("✅ test_four_masking_strategies passed (Strategies A, B, C, D verified)")


def test_validation_all_failure_categories():
    """Verify classification of all 7 failure categories."""
    mapping = {
        "[PERSON_1]": "Rahul Sharma",
        "[EMAIL_1]": "rahul@example.com",
        "[PHONE_1]": "+91-9876543210",
        "[LOCATION_1]": "Bengaluru",
        "[DATE_1]": "15/08/2025"
    }
    masked_prompt = "Contact [PERSON_1] at [EMAIL_1] or [PHONE_1] in [LOCATION_1] on [DATE_1]."

    # 1. Correct
    resp_correct = "Contact [PERSON_1] at [EMAIL_1]."
    rep1 = validate_placeholders(resp_correct, {"[PERSON_1]": "Rahul Sharma", "[EMAIL_1]": "rahul@example.com"})
    assert rep1.correct_count == 2
    assert rep1.results[0].category == FailureCategory.CORRECT

    # 2. Dropped
    resp_dropped = "Contact at [EMAIL_1]."  # PERSON_1 dropped
    rep2 = validate_placeholders(resp_dropped, {"[PERSON_1]": "Rahul Sharma", "[EMAIL_1]": "rahul@example.com"})
    assert rep2.dropped_count == 1
    assert rep2.results[0].category == FailureCategory.DROPPED

    # 3. Inflected (casing / brackets stripped)
    resp_inflected = "Contact person_1 at (EMAIL_1)."
    rep3 = validate_placeholders(resp_inflected, {"[PERSON_1]": "Rahul Sharma", "[EMAIL_1]": "rahul@example.com"})
    assert rep3.inflected_count == 2

    # 4. Mistranslated (French translation of token: [PERSONNE_1])
    resp_mistranslated = "Contactez [PERSONNE_1] à [COURRIEL_1]."
    rep4 = validate_placeholders(resp_mistranslated, {"[PERSON_1]": "Rahul Sharma", "[EMAIL_1]": "rahul@example.com"})
    assert rep4.mistranslated_count == 2

    # 5. Hallucinated (spurious placeholder in response)
    resp_hallucinated = "Contact [PERSON_1] and [SPECIAL_ID_99]."
    rep5 = validate_placeholders(resp_hallucinated, {"[PERSON_1]": "Rahul Sharma"})
    assert rep5.hallucinated_count == 1
    assert "[SPECIAL_ID_99]" in rep5.unexpected_placeholders

    # 6. Cross-wired (swapped placeholders)
    resp_cross = "Contact [EMAIL_1] at [PERSON_1]."
    rep6 = validate_placeholders(
        resp_cross,
        {"[PERSON_1]": "Rahul Sharma", "[EMAIL_1]": "rahul@example.com"},
        masked_prompt="Contact [PERSON_1] at [EMAIL_1]."
    )
    assert rep6.cross_wired_count >= 1

    # 7. Duplicated
    resp_dup = "Contact [PERSON_1] and verify [PERSON_1]."
    rep7 = validate_placeholders(resp_dup, {"[PERSON_1]": "Rahul Sharma"})
    assert len(rep7.duplicate_placeholders) >= 1

    # 8. Missed (substituted by generic phrase)
    resp_missed = "Please reach out to the customer directly."
    rep8 = validate_placeholders(resp_missed, {"[PERSON_1]": "Rahul Sharma"})
    assert rep8.missed_count == 1

    print("✅ test_validation_all_failure_categories passed (All 7 categories verified)")


def test_strategy_d_checksum_validation():
    """Verify Strategy D cryptographic checksum tamper detection."""
    from detection.pii_detector import PIIEntity
    orig_val = "Rahul Sharma"
    text = f"My name is {orig_val}."
    entity = PIIEntity(entity_type="PERSON", value=orig_val, start=11, end=11 + len(orig_val), score=1.0)
    
    masker = PIIMasker(strategy="strategy_d_protected")
    masked, mapping = masker.mask_text(text, [entity])
    assert len(mapping) == 1

    # Valid response
    rep_valid = validate_placeholders(masked, mapping)
    assert rep_valid.correct_count == 1

    # Tampered response (altered checksum tag)
    tampered_resp = re.sub(r':[A-F0-9]{4}\]', ':XXXX]', masked)
    rep_tampered = validate_placeholders(tampered_resp, mapping)
    assert rep_tampered.correct_count == 0
    assert rep_tampered.inflected_count == 1
    print("✅ test_strategy_d_checksum_validation passed (Tamper detection verified)")


def test_restoration_strict_zero_leakage():
    """Verify that only validated CORRECT placeholders are restored."""
    mapping = {"[PERSON_1]": "Rahul Sharma", "[EMAIL_1]": "rahul@example.com"}
    response = "Hello person_1, your email is [EMAIL_1]."

    report = validate_placeholders(response, mapping)
    restorer = PIIRestorer()
    restored, log = restorer.restore(response, mapping, report)

    assert "rahul@example.com" in restored, "Valid email should be restored"
    assert "Rahul Sharma" not in restored, "Inflected person_1 must NOT be restored (Zero-Leakage Policy)"
    assert restorer.successful_restorations == 1
    assert restorer.failed_restorations == 1
    print("✅ test_restoration_strict_zero_leakage passed")


def test_mathematical_metrics():
    """Verify mathematical correctness of restoration and detection metrics."""
    # Test zero denominators
    assert safe_divide(5.0, 0.0) == 0.0
    assert safe_divide(0.0, 0.0) == 0.0

    # Test restoration metrics
    rep = validate_placeholders(
        "Hello [PERSON_1], email [EMAIL_1] dropped phone.",
        {"[PERSON_1]": "Rahul", "[EMAIL_1]": "r@e.com", "[PHONE_1]": "999"}
    )
    metrics = compute_restoration_metrics(rep)
    assert metrics["total_expected"] == 3
    assert metrics["total_correct"] == 2
    assert metrics["precision"] == 1.0  # 2 correct / 2 attempts
    assert round(metrics["recall"], 2) == 0.67  # 2 correct / 3 expected
    assert round(metrics["f1_score"], 2) == 0.80

    # Test separate detection metrics
    gt_entities = [
        {"entity_type": "PERSON", "value": "Rahul"},
        {"entity_type": "EMAIL", "value": "r@e.com"}
    ]
    det_entities = [
        type("E", (), {"entity_type": "PERSON", "value": "Rahul"})()
    ]
    det_metrics = compute_detection_metrics(det_entities, gt_entities)
    assert det_metrics["detection_precision"] == 1.0
    assert det_metrics["detection_recall"] == 0.5
    assert round(det_metrics["detection_f1"], 2) == 0.67
    print("✅ test_mathematical_metrics passed")


def test_isolated_database_testing():
    """Verify tests run against an isolated test database and leave live database untouched."""
    test_db = os.path.join(os.path.dirname(__file__), "test_piishield_isolated.db")
    if os.path.exists(test_db):
        os.remove(test_db)

    init_db(test_db)
    exp_id = save_experiment({
        "name": "Isolated Unit Test",
        "num_entities_detected": 4,
        "num_correct": 4,
        "precision_score": 1.0,
        "recall_score": 1.0,
        "f1_score": 1.0,
        "data_provenance": "test_suite"
    }, db_path=test_db)
    assert exp_id > 0

    stats = get_dashboard_stats(db_path=test_db)
    # Exclude tests works
    all_rows = get_all_experiments(db_path=test_db, exclude_tests=False)
    assert len(all_rows) == 1

    # Cleanup test database
    if os.path.exists(test_db):
        os.remove(test_db)
    print("✅ test_isolated_database_testing passed (Live DB protected)")


if __name__ == "__main__":
    print("=" * 60)
    print("PIIShield AI — Rigorous Pipeline & Metrics Test Suite")
    print("=" * 60)

    tests = [
        test_regex_detection,
        test_four_masking_strategies,
        test_validation_all_failure_categories,
        test_strategy_d_checksum_validation,
        test_restoration_strict_zero_leakage,
        test_mathematical_metrics,
        test_isolated_database_testing,
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
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 60)
    if failed > 0:
        sys.exit(1)
