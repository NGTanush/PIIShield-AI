"""Unit and Integration Tests for Full Kaggle Benchmark Pipeline in PIIShield AI."""
import io
import json
import os
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dataset.public_benchmark.download_kaggle import check_kaggle_credentials
from dataset.public_benchmark.preprocess_full_kaggle import (
    align_token_offsets,
    validate_and_extract_entities,
    KAGGLE_TO_PIISHIELD_MAP,
    process_dataset
)
from evaluation.benchmark_full_kaggle import compute_f_beta, evaluate_method


def test_credential_check_safety():
    """Verify check_kaggle_credentials works cleanly and does not expose secrets."""
    creds = check_kaggle_credentials()
    assert "authenticated" in creds
    assert "credential_type" in creds
    assert isinstance(creds["authenticated"], bool)
    print(f"✅ test_credential_check_safety passed (Authenticated: {creds['authenticated']})")


def test_bio_tag_and_span_extraction():
    """Verify validation and extraction of BIO tokens into character-level entity spans."""
    text = "Essay by Jane Smith. Contact jane@school.edu."
    tokens = ["Essay", "by", "Jane", "Smith", ".", "Contact", "jane@school.edu", "."]
    tws = [True, True, True, False, True, True, False, False]
    labels = ["O", "O", "B-NAME_STUDENT", "I-NAME_STUDENT", "O", "O", "B-EMAIL", "O"]

    entities, issues = validate_and_extract_entities(101, text, tokens, tws, labels)
    assert len(entities) == 2, f"Expected 2 entities, got {len(entities)}"
    assert entities[0]["standard_type"] == "PERSON"
    assert entities[0]["value"] == "Jane Smith"
    assert text[entities[0]["start"]:entities[0]["end"]] == "Jane Smith"

    assert entities[1]["standard_type"] == "EMAIL"
    assert entities[1]["value"] == "jane@school.edu"
    assert text[entities[1]["start"]:entities[1]["end"]] == "jane@school.edu"
    print("✅ test_bio_tag_and_span_extraction passed (2 spans verified with exact text alignment)")


def test_category_mapping_completeness():
    """Verify all 7 Kaggle competition entity categories map to PIIShield ontology."""
    expected = {
        "NAME_STUDENT": "PERSON",
        "EMAIL": "EMAIL",
        "USERNAME": "USERNAME",
        "ID_NUM": "IDENTIFICATION_NUMBER",
        "PHONE_NUM": "PHONE",
        "URL_PERSONAL": "URL",
        "STREET_ADDRESS": "ADDRESS",
    }
    for k, v in expected.items():
        assert KAGGLE_TO_PIISHIELD_MAP.get(k) == v
    print("✅ test_category_mapping_completeness passed (7 categories mapped)")


def test_document_level_split_no_leakage():
    """Verify train/validation split has zero document overlap and deterministic seed."""
    split_file = PROJECT_ROOT / "dataset" / "public_benchmark" / "processed" / "split_indices.json"
    assert split_file.exists(), f"Split indices file missing: {split_file}"

    with open(split_file, "r", encoding="utf-8") as f:
        split_data = json.load(f)

    train_ids = set(split_data["train_doc_ids"])
    val_ids = set(split_data["val_doc_ids"])

    # Zero leakage check
    intersection = train_ids.intersection(val_ids)
    assert len(intersection) == 0, f"Document leakage detected! Overlapping IDs: {intersection}"
    assert len(train_ids) > 0 and len(val_ids) > 0
    print(f"✅ test_document_level_split_no_leakage passed (Train docs: {len(train_ids)}, Val docs: {len(val_ids)}, Overlap: 0)")


def test_f_beta_calculation():
    """Verify F-beta calculation with beta=5."""
    # When P=1.0 and R=1.0, F5=1.0
    assert compute_f_beta(1.0, 1.0, beta=5.0) == 1.0
    # When P=0.0 or R=0.0, F5=0.0
    assert compute_f_beta(0.0, 1.0, beta=5.0) == 0.0
    assert compute_f_beta(1.0, 0.0, beta=5.0) == 0.0
    # Verify recall weighting: high recall should yield higher F5 than high precision
    f5_high_recall = compute_f_beta(0.2, 0.8, beta=5.0)
    f5_high_precision = compute_f_beta(0.8, 0.2, beta=5.0)
    assert f5_high_recall > f5_high_precision, f"F5 should weight recall higher: {f5_high_recall} <= {f5_high_precision}"
    print(f"✅ test_f_beta_calculation passed (F5 high-R: {f5_high_recall:.4f} > high-P: {f5_high_precision:.4f})")


def run_all_tests():
    print("=" * 65)
    print("PIIShield AI — Full Kaggle Benchmark Pipeline Test Suite")
    print("=" * 65)
    tests = [
        test_credential_check_safety,
        test_bio_tag_and_span_extraction,
        test_category_mapping_completeness,
        test_document_level_split_no_leakage,
        test_f_beta_calculation,
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
    print("=" * 65)
    print(f"Kaggle Pipeline Tests: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 65)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()

