"""
PIIShield AI — Placeholder Validation Module
Performs deep structural and semantic integrity verification of PII placeholders.
Classifies all failure categories:
  - CORRECT
  - MISSED
  - DROPPED
  - INFLECTED (Modified format / casing / brackets)
  - MISTRANSLATED (Multilingual translation of token)
  - HALLUCINATED (New unexpected placeholder)
  - CROSS_WIRED (Placeholders swapped or bound to wrong context)
Supports all 4 Placeholder Strategies (Basic, Random Typed, Opaque, Protected).
"""
import re
import hashlib
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class FailureCategory(Enum):
    """Categories of placeholder preservation and restoration failures."""
    CORRECT = "correct"
    MISSED = "missed"                   # Placeholder replaced by generic noun phrase
    DROPPED = "dropped"                 # Completely omitted from response
    INFLECTED = "inflected"             # Modified casing, brackets, or syntax
    MISTRANSLATED = "mistranslated"     # Token translated to another language
    HALLUCINATED = "hallucinated"       # Spurious placeholder not in original prompt
    CROSS_WIRED = "cross_wired"         # Placeholders swapped / bound to wrong entity


# Translation dictionary for multilingual mistranslation detection
TRANSLATED_TOKENS = {
    "PERSON": ["PERSONNE", "PERSONA", "INDIVIDU", "SUJETO"],
    "EMAIL": ["COURRIEL", "CORREO", "EMAIL_ADRESSE", "MEL"],
    "PHONE": ["TELEPHONE", "TELEFONO", "NUMERO_TEL", "PORTABLE"],
    "LOCATION": ["LIEU", "UBICACION", "ENDROIT", "STANDORT", "LOCALITE"],
    "DATE": ["FECHA", "DATUM"],
    "ADDRESS": ["ADRESSE", "DIRECCION", "INDIRIZZO", "ANSCHRIFT"],
    "IDENTIFICATION_NUMBER": ["NUMERO_IDENTITE", "NUMERO_ID", "NUMERO_FISCAL"],
}

# Generic noun replacements indicating MISSED placeholders
GENERIC_SUBSTITUTES = [
    r"\bthe (?:user|person|client|customer|individual|patient|employee)\b",
    r"\bthe (?:email|contact address|mailbox)\b",
    r"\bthe (?:phone number|telephone|hotline|mobile)\b",
    r"\bthe (?:address|residence|location|city)\b",
    r"\bthe (?:identification|id number|tax number)\b",
]


@dataclass
class ValidationResult:
    """Result of validating an individual placeholder."""
    placeholder: str
    original_value: str
    category: FailureCategory
    found_text: str = ""
    notes: str = ""
    checksum_valid: Optional[bool] = None


@dataclass
class ValidationReport:
    """Comprehensive validation report for an LLM response."""
    results: List[ValidationResult] = field(default_factory=list)
    unexpected_placeholders: List[str] = field(default_factory=list)  # Hallucinated
    duplicate_placeholders: List[str] = field(default_factory=list)
    strategy_detected: str = "strategy_a_basic"

    @property
    def correct_count(self) -> int:
        return sum(1 for r in self.results if r.category == FailureCategory.CORRECT)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.category != FailureCategory.CORRECT)

    @property
    def dropped_count(self) -> int:
        return sum(1 for r in self.results if r.category == FailureCategory.DROPPED)

    @property
    def inflected_count(self) -> int:
        return sum(1 for r in self.results if r.category == FailureCategory.INFLECTED)

    @property
    def mistranslated_count(self) -> int:
        return sum(1 for r in self.results if r.category == FailureCategory.MISTRANSLATED)

    @property
    def hallucinated_count(self) -> int:
        return len(self.unexpected_placeholders)

    @property
    def cross_wired_count(self) -> int:
        return sum(1 for r in self.results if r.category == FailureCategory.CROSS_WIRED)

    @property
    def missed_count(self) -> int:
        return sum(1 for r in self.results if r.category == FailureCategory.MISSED)

    def summary(self) -> Dict[str, int]:
        return {
            "correct": self.correct_count,
            "missed": self.missed_count,
            "dropped": self.dropped_count,
            "inflected": self.inflected_count,
            "mistranslated": self.mistranslated_count,
            "hallucinated": self.hallucinated_count,
            "cross_wired": self.cross_wired_count,
            "duplicated": len(self.duplicate_placeholders),
        }


def find_all_placeholders(text: str, expected_mapping: Optional[Dict[str, str]] = None) -> List[str]:
    """
    Extract all placeholder tokens in text across Strategies A, B, C, and D in order of appearance.
    Preserves multiple occurrences so duplicates can be detected.
    """
    ordered: List[str] = []

    # Combined regex pattern matching Strategy D, Strategy A/B, and Strategy C
    pattern = re.compile(
        r'(\[PROT:[A-Z_]+:[A-Za-z0-9]+:[A-Za-z0-9]+\]|\[[A-Z_]+_[A-Za-z0-9]+\]|\bZ[A-F0-9]{7}\b)'
    )
    for m in pattern.finditer(text):
        ordered.append(m.group())

    # If an expected mapping is provided with custom tokens, also scan for any missed
    if expected_mapping:
        for ph in expected_mapping.keys():
            if ph not in ordered and ph in text:
                # Find all occurrences of this custom token in text
                for _ in re.finditer(re.escape(ph), text):
                    ordered.append(ph)

    return ordered


def find_near_matches(text: str, placeholder: str) -> List[Tuple[str, str]]:
    """
    Find near matches for a placeholder (casing shifts, bracket stripping, braces, parentheses).
    Returns list of (matched_string, failure_type).
    """
    near: List[Tuple[str, str]] = []
    inner = placeholder.strip("[]")

    # 1. Check lowercase with brackets e.g. [person_1]
    lower_ph = placeholder.lower()
    if lower_ph in text and placeholder not in text:
        near.append((lower_ph, "inflected"))

    # 2. Check inner without brackets (e.g. PERSON_1 or person_1)
    pattern = re.compile(r'\b' + re.escape(inner) + r'\b', re.IGNORECASE)
    m = pattern.search(text)
    if m and placeholder not in text:
        near.append((m.group(), "inflected"))

    # 3. Check bracket mutations: (TOKEN), {TOKEN}, <TOKEN>
    for op, cl in [("(", ")"), ("{", "}"), ("<", ">")]:
        wrapped = f"{op}{inner}{cl}"
        if wrapped in text:
            near.append((wrapped, "inflected"))

    # 4. Check for mistranslation of the entity type (e.g. [PERSONNE_1])
    base_type = inner.split("_")[0] if "_" in inner else ""
    if base_type in TRANSLATED_TOKENS:
        for trans_type in TRANSLATED_TOKENS[base_type]:
            trans_inner = inner.replace(base_type, trans_type, 1)
            trans_ph = f"[{trans_inner}]"
            if trans_ph in text or trans_inner in text or f"({trans_inner})" in text:
                near.append((trans_ph, "mistranslated"))

    # 5. Check Strategy D protected placeholder with tampered/corrupted checksum
    if placeholder.startswith("[PROT:"):
        prefix_part = ":".join(placeholder.split(":")[:3]) + ":"  # e.g. [PROT:PERSON:P1:
        prot_match = re.search(re.escape(prefix_part) + r'[A-Za-z0-9]+\]', text)
        if prot_match and prot_match.group() != placeholder:
            near.append((prot_match.group(), "inflected"))

    return near


def _detect_cross_wiring(
    found_order: List[str],
    expected_order: List[str],
    original_mapping: Dict[str, str]
) -> Set[str]:
    """
    Detect if multiple placeholders swapped relative positions (cross-wiring).
    """
    cross_wired: Set[str] = set()
    # Filter to only expected placeholders that appeared in response
    common_found = [ph for ph in found_order if ph in expected_order]
    common_expected = [ph for ph in expected_order if ph in found_order]

    if len(common_found) >= 2 and len(common_expected) >= 2:
        # If order differs from expected relative order, flag swapped tokens
        if common_found != common_expected:
            for i, ph in enumerate(common_found):
                if i < len(common_expected) and ph != common_expected[i]:
                    cross_wired.add(ph)
                    cross_wired.add(common_expected[i])

    return cross_wired


def validate_placeholders(
    llm_response: str,
    original_mapping: Dict[str, str],
    masked_prompt: str = ""
) -> ValidationReport:
    """
    Comprehensive placeholder validation across all 7 failure categories.

    Args:
        llm_response: Raw text returned by the LLM.
        original_mapping: Dict mapping placeholder -> original PII value.
        masked_prompt: The masked prompt sent to LLM (used for cross-wiring checks).

    Returns:
        ValidationReport with per-placeholder category and audit log.
    """
    report = ValidationReport()
    expected_placeholders = list(original_mapping.keys())

    # Detect active placeholder strategy
    sample_key = expected_placeholders[0] if expected_placeholders else ""
    if sample_key.startswith("[PROT:"):
        report.strategy_detected = "strategy_d_protected"
    elif sample_key.startswith("Z") and len(sample_key) == 8 and "[" not in sample_key:
        report.strategy_detected = "strategy_c_opaque"
    elif "_" in sample_key and len(sample_key.strip("[]").rsplit("_", 1)[-1]) > 2:
        report.strategy_detected = "strategy_b_random_typed"
    else:
        report.strategy_detected = "strategy_a_basic"

    # Extract all placeholders from response
    found_in_response = find_all_placeholders(llm_response, original_mapping)
    found_set = set(found_in_response)

    # 1. Check for duplicates in response
    seen_counts: Dict[str, int] = {}
    for ph in found_in_response:
        seen_counts[ph] = seen_counts.get(ph, 0) + 1
        if seen_counts[ph] == 2 and ph in original_mapping:
            report.duplicate_placeholders.append(ph)

    # 2. Check for Hallucinated placeholders (appeared in response but not in prompt)
    for ph in found_set:
        if ph not in original_mapping:
            report.unexpected_placeholders.append(ph)

    # 3. Detect cross-wiring (swapped positions relative to masked prompt)
    expected_order = [ph for ph in expected_placeholders if ph in masked_prompt]
    cross_wired_set = _detect_cross_wiring(found_in_response, expected_order, original_mapping)

    # 4. Validate each expected placeholder
    for placeholder, original_value in original_mapping.items():
        if placeholder in found_set:
            if placeholder in cross_wired_set:
                result = ValidationResult(
                    placeholder=placeholder,
                    original_value=original_value,
                    category=FailureCategory.CROSS_WIRED,
                    found_text=placeholder,
                    notes="Cross-wired: Placeholder swapped relative positions with another entity token."
                )
            else:
                # For Strategy D, verify cryptographic checksum
                checksum_ok = True
                if report.strategy_detected == "strategy_d_protected":
                    expected_chk = hashlib.md5(original_value.encode("utf-8")).hexdigest()[:4].upper()
                    # Checksum is the last segment: [PROT:TYPE:ID:CHK]
                    parts = placeholder.strip("[]").split(":")
                    if len(parts) >= 4 and parts[3] != expected_chk:
                        checksum_ok = False

                if not checksum_ok:
                    result = ValidationResult(
                        placeholder=placeholder,
                        original_value=original_value,
                        category=FailureCategory.INFLECTED,
                        found_text=placeholder,
                        notes="Checksum failure: Integrity tag altered.",
                        checksum_valid=False
                    )
                else:
                    result = ValidationResult(
                        placeholder=placeholder,
                        original_value=original_value,
                        category=FailureCategory.CORRECT,
                        found_text=placeholder,
                        notes="Placeholder preserved exactly with valid integrity.",
                        checksum_valid=True
                    )

        else:
            # Check near matches (inflected, bracket mutations, mistranslated)
            near_matches = find_near_matches(llm_response, placeholder)

            if near_matches:
                matched_str, failure_type = near_matches[0]
                if failure_type == "mistranslated":
                    result = ValidationResult(
                        placeholder=placeholder,
                        original_value=original_value,
                        category=FailureCategory.MISTRANSLATED,
                        found_text=matched_str,
                        notes=f"Mistranslated: Token translated to '{matched_str}' in target language."
                    )
                else:
                    result = ValidationResult(
                        placeholder=placeholder,
                        original_value=original_value,
                        category=FailureCategory.INFLECTED,
                        found_text=matched_str,
                        notes=f"Inflected/Modified: Formatted as '{matched_str}' instead of exact placeholder."
                    )
            else:
                # Check if it was replaced with a generic noun phrase (MISSED)
                is_missed = False
                for pattern in GENERIC_SUBSTITUTES:
                    if re.search(pattern, llm_response, re.IGNORECASE):
                        is_missed = True
                        break

                if is_missed and len(original_mapping) == 1:
                    result = ValidationResult(
                        placeholder=placeholder,
                        original_value=original_value,
                        category=FailureCategory.MISSED,
                        found_text="",
                        notes="Missed: Placeholder replaced by generic noun phrase in response."
                    )
                else:
                    result = ValidationResult(
                        placeholder=placeholder,
                        original_value=original_value,
                        category=FailureCategory.DROPPED,
                        found_text="",
                        notes="Dropped: Token completely omitted from output text."
                    )

        report.results.append(result)

    return report
