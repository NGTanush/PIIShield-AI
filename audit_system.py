"""
Phase 1: Comprehensive System Audit Script
Inspects database records, LLM modes, dataset characteristics, and metric calculations.
"""
import sqlite3
import json
import os
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "piishield.db")

print("=" * 60)
print("PHASE 1 AUDIT: SYSTEM & EXPERIMENTAL RECORDS")
print("=" * 60)

# 1. Audit SQLite database
print("\n--- [Audit Item 1 & 6]: SQLite Database & Experiment History ---")
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM experiments ORDER BY id ASC").fetchall()
    print(f"Total rows in piishield.db: {len(rows)}")
    for r in rows:
        d = dict(r)
        print(f"  Experiment #{d['id']}:")
        print(f"    Name: {d['name']}")
        print(f"    Created: {d['created_at']}")
        print(f"    LLM Mode: {d['llm_mode']}, Scenario: {d['llm_scenario']}")
        print(f"    Entities Detected: {d['num_entities_detected']}")
        print(f"    Correct: {d['num_correct']}, Missed: {d['num_missed']}, Dropped: {d['num_dropped']}")
        print(f"    Inflected: {d['num_inflected']}, Mistranslated: {d['num_mistranslated']}, Hallucinated: {d['num_hallucinated']}, Cross-wired: {d['num_cross_wired']}")
        print(f"    Precision: {d['precision_score']}, Recall: {d['recall_score']}, F1: {d['f1_score']}")
        print(f"    Notes: {d['notes']}")
    conn.close()
else:
    print("Database piishield.db does not exist.")

# 2. Audit Dataset
print("\n--- [Audit Item 3 & 4]: Dataset Metadata & Scope ---")
meta_path = os.path.join(BASE_DIR, "dataset", "dataset_metadata.json")
if os.path.exists(meta_path):
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    print(f"Total Prompts: {meta.get('total_prompts')}")
    print(f"Total Entities: {meta.get('total_entities')}")
    print(f"Average Density: {meta.get('avg_entities_per_prompt')}")
    print(f"Entity Categories: {meta.get('entity_category_counts')}")
    print(f"Density Distribution: {meta.get('density_distribution')}")
    print(f"Languages: {meta.get('language_distribution')}")
    print(f"Scenarios: {meta.get('scenario_distribution')}")
else:
    print("dataset_metadata.json not found.")

print("\n" + "=" * 60)
print("AUDIT COMPLETE")
print("=" * 60)

