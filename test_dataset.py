"""
Unit and Integration Tests for PIIShield AI Research Dataset
"""
import sys
import os
import io
import json
import csv

# Force UTF-8 output encoding on Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset")


def test_dataset_files_exist():
    """Verify all 5 required dataset files and visualizations exist."""
    required = [
        "synthetic_prompts.csv",
        "ground_truth.json",
        "experiment_scenarios.csv",
        "placeholder_variants.csv",
        "dataset_metadata.json",
        "dataset_summary.json",
        "dataset_distribution.png"
    ]
    for fname in required:
        fpath = os.path.join(DATASET_DIR, fname)
        assert os.path.exists(fpath), f"Missing required file: {fname}"
        assert os.path.getsize(fpath) > 0, f"File is empty: {fname}"
    print("✅ test_dataset_files_exist passed")


def test_synthetic_prompts_csv():
    """Verify CSV formatting, row count, and unique IDs."""
    csv_path = os.path.join(DATASET_DIR, "synthetic_prompts.csv")
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 300, f"Expected >= 300 prompts, got {len(rows)}"
    ids = [r["prompt_id"] for r in rows]
    assert len(ids) == len(set(ids)), "Found duplicate prompt IDs in CSV!"
    
    # Check mandatory headers
    expected_headers = {
        "prompt_id", "original_prompt", "masked_prompt_basic",
        "num_entities", "pii_types", "pii_density", "language", "scenario"
    }
    for r in rows:
        for h in expected_headers:
            assert h in r and r[h], f"Missing or empty field '{h}' in row {r.get('prompt_id')}"
    print(f"✅ test_synthetic_prompts_csv passed ({len(rows)} prompts validated)")


def test_ground_truth_character_offsets():
    """Verify strict character offset integrity on every entity annotation."""
    gt_path = os.path.join(DATASET_DIR, "ground_truth.json")
    with open(gt_path, "r", encoding="utf-8") as f:
        gt_list = json.load(f)

    assert len(gt_list) >= 300
    total_annotations = 0

    for item in gt_list:
        orig = item["original_prompt"]
        annotations = item["annotations"]
        for ann in annotations:
            val = ann["value"]
            s = ann["start_char"]
            e = ann["end_char"]
            assert orig[s:e] == val, (
                f"Character offset mismatch in {item['prompt_id']}: expected '{val}', got '{orig[s:e]}'"
            )
            total_annotations += 1

    print(f"✅ test_ground_truth_character_offsets passed ({total_annotations} annotations verified)")


def test_four_placeholder_strategies():
    """Verify that all 4 placeholder strategies are represented in variants."""
    csv_path = os.path.join(DATASET_DIR, "placeholder_variants.csv")
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 300
    for r in rows:
        assert "strategy_a_basic_masked" in r
        assert "strategy_b_random_typed_masked" in r
        assert "strategy_c_opaque_masked" in r
        assert "strategy_d_protected_masked" in r
        
        # Verify Strategy D contains PROT prefix
        if int(r["num_entities"]) > 0:
            assert "PROT:" in r["strategy_d_protected_masked"], "Strategy D format missing PROT tag"
    print("✅ test_four_placeholder_strategies passed")


def test_privacy_segregation():
    """Verify ground-truth original PII is segregated and does not appear in masked prompts."""
    gt_path = os.path.join(DATASET_DIR, "ground_truth.json")
    with open(gt_path, "r", encoding="utf-8") as f:
        gt_list = json.load(f)

    csv_path = os.path.join(DATASET_DIR, "synthetic_prompts.csv")
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        rows = {r["prompt_id"]: r["masked_prompt_basic"] for r in csv.DictReader(f)}

    for item in gt_list:
        pid = item["prompt_id"]
        masked = rows[pid]
        for ann in item["annotations"]:
            # Sensitive structured PII should never be inside the masked prompt
            if ann["entity_type"] in ("EMAIL", "PHONE", "IDENTIFICATION_NUMBER"):
                assert ann["value"] not in masked, (
                    f"Privacy leak! '{ann['value']}' found in masked prompt of {pid}"
                )
    print("✅ test_privacy_segregation passed (Zero leakage verified)")


def test_scenarios_coverage():
    """Verify that all 10 scenario categories are covered in experiment_scenarios.csv."""
    csv_path = os.path.join(DATASET_DIR, "experiment_scenarios.csv")
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    scenarios = {r["scenario"] for r in rows}
    expected_scenarios = {
        "Normal", "Paraphrasing", "Summarization", "Translation",
        "Grammar Correction", "Placeholder Modification", "Placeholder Deletion",
        "Placeholder Duplication", "Multiple Placeholder Confusion", "Multi-Entity Processing"
    }
    assert expected_scenarios.issubset(scenarios), f"Missing scenarios: {expected_scenarios - scenarios}"
    print(f"✅ test_scenarios_coverage passed ({len(scenarios)} distinct scenarios)")


if __name__ == "__main__":
    print("=" * 60)
    print("PIIShield AI — Research Dataset Test Suite")
    print("=" * 60)

    tests = [
        test_dataset_files_exist,
        test_synthetic_prompts_csv,
        test_ground_truth_character_offsets,
        test_four_placeholder_strategies,
        test_privacy_segregation,
        test_scenarios_coverage,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"❌ {test_fn.__name__} FAILED: {e}")
            failed += 1

    print("=" * 60)
    print(f"Dataset Tests: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 60)
    if failed > 0:
        sys.exit(1)

