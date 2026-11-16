"""PII Detection module using regex patterns, spaCy NER, and context-aware rules.

Supports categories:
  - PERSON
  - EMAIL
  - PHONE
  - ADDRESS
  - DATE / DATE_OF_BIRTH
  - LOCATION
  - ORGANIZATION
  - IDENTIFICATION_NUMBER (SSN, Aadhaar, PAN, Passport, Student/Employee ID)
  - FINANCIAL (Credit Card, IBAN, Bank Account)
  - USERNAME
  - URL
  - IP_ADDRESS
"""
import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

# Module-level singleton for spaCy model to prevent reloading bottleneck
_CACHED_NLP = None


def get_spacy_nlp():
    """Retrieve or initialize the cached spaCy NLP model."""
    global _CACHED_NLP
    if _CACHED_NLP is None:
        try:
            import spacy
            # Disable parser and lemmatizer for speed (NER requires only tok2vec/tagger + ner)
            _CACHED_NLP = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
        except Exception:
            _CACHED_NLP = False
    return _CACHED_NLP if _CACHED_NLP is not False else None


@dataclass
class PIIEntity:
    """Represents a detected PII entity."""
    entity_type: str
    value: str
    start: int
    end: int
    score: float = 1.0
    source: str = "regex"  # "regex", "spacy", "context", or "hybrid"


# Regex patterns for structured and semi-structured PII
PII_PATTERNS = {
    "EMAIL": r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b',
    "PHONE": r'\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b',
    "DATE": r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s*\d{2,4})\b',
    "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
    "CREDIT_CARD": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "IP_ADDRESS": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    "AADHAAR": r'\b\d{4}\s?\d{4}\s?\d{4}\b',
    "PAN": r'\b[A-Z]{5}\d{4}[A-Z]\b',
    "URL": r'\b(?:https?://|www\.)[A-Za-z0-9.\-]+(?:\.[A-Za-z]{2,})+(?:/[^\s]*)?\b',
    "ADDRESS": r'\b\d{1,5}\s+(?:[A-Za-z0-9.\-]+\s+){1,4}(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct|Way|Square|Sq|Trail|Trl|Highway|Hwy|Parkway|Pkwy)\b|\bP\.?O\.?\s*Box\s+\d+\b',
}

# Context-aware patterns for complex identifiers
CONTEXT_PATTERNS = [
    # Username: e.g. @username or username: john_doe
    (r'(?i)\b(?:username|user id|handle|login)\s*[:#\-]?\s*([A-Za-z0-9_\.\-]{3,30})\b', "USERNAME", 1, 0.90),
    (r'(?<!\w)@([A-Za-z0-9_]{3,30})\b', "USERNAME", 1, 0.85),
    # Student / Employee ID
    (r'(?i)\b(?:student\s*id|student\s*#|id\s*num(?:ber)?|employee\s*id|emp\s*#|badge\s*#)\s*[:#\-]?\s*([A-Z0-9\-_]{4,20})\b', "IDENTIFICATION_NUMBER", 1, 0.92),
    # Passport Number
    (r'(?i)\b(?:passport\s*(?:no|num|number)?)\s*[:#\-]?\s*([A-Z0-9]{7,10})\b', "IDENTIFICATION_NUMBER", 1, 0.92),
    # Date of Birth
    (r'(?i)\b(?:dob|date\s*of\s*birth|born\s*(?:on)?)\s*[:#\-]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s*\d{2,4})\b', "DATE_OF_BIRTH", 1, 0.95),
    # Financial: IBAN / Account Number
    (r'(?i)\b(?:iban|account\s*num(?:ber)?|acc\s*#)\s*[:#\-]?\s*([A-Z0-9]{8,34})\b', "FINANCIAL", 1, 0.90),
]


def detect_with_regex(text: str) -> List[PIIEntity]:
    """Detect PII entities using regular expressions."""
    entities = []
    for entity_type, pattern in PII_PATTERNS.items():
        for match in re.finditer(pattern, text):
            # Skip if it looks like a generic short number for phone
            if entity_type == "PHONE" and len(re.sub(r'\D', '', match.group())) < 7:
                continue
            entities.append(PIIEntity(
                entity_type=entity_type,
                value=match.group(),
                start=match.start(),
                end=match.end(),
                score=0.95,
                source="regex"
            ))
    return entities


def detect_context_aware_pii(text: str) -> List[PIIEntity]:
    """Detect PII entities requiring linguistic context clues."""
    entities = []
    for pattern, entity_type, group_idx, score in CONTEXT_PATTERNS:
        for match in re.finditer(pattern, text):
            val = match.group(group_idx)
            start = match.start(group_idx)
            end = match.end(group_idx)
            if val and len(val.strip()) > 0:
                entities.append(PIIEntity(
                    entity_type=entity_type,
                    value=val,
                    start=start,
                    end=end,
                    score=score,
                    source="context"
                ))
    return entities


def detect_with_spacy(text: str) -> List[PIIEntity]:
    """Detect PII entities using cached spaCy NER."""
    nlp = get_spacy_nlp()
    if nlp is None:
        return []

    doc = nlp(text)
    entities = []

    # Map spaCy labels to PIIShield ontology
    label_map = {
        "PERSON": "PERSON",
        "GPE": "LOCATION",
        "LOC": "LOCATION",
        "ORG": "ORGANIZATION",
        "DATE": "DATE",
        "FAC": "ADDRESS",
    }

    for ent in doc.ents:
        if ent.label_ in label_map:
            entities.append(PIIEntity(
                entity_type=label_map[ent.label_],
                value=ent.text,
                start=ent.start_char,
                end=ent.end_char,
                score=0.85,
                source="spacy"
            ))
    return entities


def detect_batch_spacy(texts: List[str], batch_size: int = 64) -> List[List[PIIEntity]]:
    """Fast batch PII detection using spaCy nlp.pipe with cached model."""
    nlp = get_spacy_nlp()
    if nlp is None:
        return [[] for _ in texts]

    label_map = {
        "PERSON": "PERSON",
        "GPE": "LOCATION",
        "LOC": "LOCATION",
        "ORG": "ORGANIZATION",
        "DATE": "DATE",
        "FAC": "ADDRESS",
    }

    results = []
    for doc in nlp.pipe(texts, batch_size=batch_size):
        doc_entities = []
        for ent in doc.ents:
            if ent.label_ in label_map:
                doc_entities.append(PIIEntity(
                    entity_type=label_map[ent.label_],
                    value=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    score=0.85,
                    source="spacy"
                ))
        results.append(doc_entities)
    return results


def merge_entities(entities: List[PIIEntity]) -> List[PIIEntity]:
    """Merge overlapping entities, prioritizing higher-confidence detections."""
    if not entities:
        return []

    # Sort by start position, then descending score
    sorted_ents = sorted(entities, key=lambda e: (e.start, -e.score, -(e.end - e.start)))
    merged = [sorted_ents[0]]

    for ent in sorted_ents[1:]:
        last = merged[-1]
        # Check for overlap
        if ent.start < last.end:
            # If current entity has higher score or longer match with equal score, replace
            if ent.score > last.score or (ent.score == last.score and (ent.end - ent.start) > (last.end - last.start)):
                merged[-1] = ent
        else:
            merged.append(ent)

    return merged


def detect_pii(text: str, use_spacy: bool = True, use_context: bool = True) -> List[PIIEntity]:
    """
    Main PII detection function combining regex, context rules, and spaCy.

    Args:
        text: Input text to scan for PII.
        use_spacy: Whether to also use spaCy NER.
        use_context: Whether to use context-aware patterns.

    Returns:
        List of detected PII entities, merged and deduplicated.
    """
    all_entities = []

    # 1. Regex detection
    all_entities.extend(detect_with_regex(text))

    # 2. Context-aware detection
    if use_context:
        all_entities.extend(detect_context_aware_pii(text))

    # 3. spaCy NER detection
    if use_spacy:
        all_entities.extend(detect_with_spacy(text))

    # 4. Merge overlapping detections
    return merge_entities(all_entities)


def detect_batch_pii(
    texts: List[str],
    use_spacy: bool = True,
    use_context: bool = True,
    batch_size: int = 64
) -> List[List[PIIEntity]]:
    """Batch PII detection combining regex, context, and batched spaCy processing."""
    # Run batched spaCy if requested
    spacy_batch = detect_batch_spacy(texts, batch_size=batch_size) if use_spacy else [[] for _ in texts]

    batch_results = []
    for idx, text in enumerate(texts):
        ents = []
        ents.extend(detect_with_regex(text))
        if use_context:
            ents.extend(detect_context_aware_pii(text))
        ents.extend(spacy_batch[idx])
        batch_results.append(merge_entities(ents))

    return batch_results
