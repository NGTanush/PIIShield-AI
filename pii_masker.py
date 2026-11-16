"""
PII Masking module — Supports 4 distinct placeholder strategies:
  - Strategy A: Basic Typed ([PERSON_1])
  - Strategy B: Random Typed ([PERSON_X7K92])
  - Strategy C: Opaque Random (ZXQ7K92M)
  - Strategy D: Protected Cryptographic Checksum ([PROT:PERSON:P1:C4D9])
"""
import hashlib
import random
from typing import List, Dict, Tuple, Optional
from detection.pii_detector import PIIEntity


class PIIMasker:
    """Masks PII entities with configurable placeholder strategies."""

    def __init__(self, strategy: str = "strategy_a_basic"):
        """
        Initialize masker with chosen strategy.
        Args:
            strategy: 'strategy_a_basic', 'strategy_b_random_typed',
                      'strategy_c_opaque', or 'strategy_d_protected'
        """
        self.strategy = strategy
        self.placeholder_map: Dict[str, str] = {}  # placeholder -> original value
        self.reverse_map: Dict[str, str] = {}      # original value -> placeholder
        self.type_counters: Dict[str, int] = {}
        self.integrity_metadata: Dict[str, Dict] = {}  # metadata for Strategy D

    def _generate_placeholder(self, entity_type: str, value: str) -> str:
        """Generate placeholder according to active strategy."""
        count = self.type_counters.get(entity_type, 0) + 1
        self.type_counters[entity_type] = count

        if self.strategy in ("strategy_b_random_typed", "random_typed"):
            # Strategy B: Typed with 5-char alphanumeric salt
            salt = hashlib.sha256(f"{entity_type}:{count}:{value}".encode()).hexdigest()[:5].upper()
            return f"[{entity_type}_{salt}]"

        elif self.strategy in ("strategy_c_opaque", "opaque"):
            # Strategy C: 8-char opaque token (starts with Z for clean word boundary)
            token = hashlib.sha256(f"{entity_type}:{count}:{value}".encode()).hexdigest()[:7].upper()
            return f"Z{token}"

        elif self.strategy in ("strategy_d_protected", "protected"):
            # Strategy D: Protected with 4-char CRC/MD5 checksum
            checksum = hashlib.md5(value.encode("utf-8")).hexdigest()[:4].upper()
            ph = f"[PROT:{entity_type}:P{count}:{checksum}]"
            self.integrity_metadata[ph] = {
                "entity_type": entity_type,
                "index": count,
                "checksum": checksum,
                "length": len(value)
            }
            return ph

        else:
            # Strategy A (Default): Basic typed sequential
            return f"[{entity_type}_{count}]"

    def mask_text(
        self,
        text: str,
        entities: List[PIIEntity],
        strategy: Optional[str] = None
    ) -> Tuple[str, Dict[str, str]]:
        """
        Replace detected PII entities with placeholders.

        Args:
            text: Original text containing PII.
            entities: Detected PII entities.
            strategy: Optional override for placeholder strategy.

        Returns:
            Tuple of (masked_text, placeholder_mapping).
        """
        if strategy:
            self.strategy = strategy

        self.placeholder_map = {}
        self.reverse_map = {}
        self.type_counters = {}
        self.integrity_metadata = {}

        # Sort entities by start position in reverse so replacements don't shift offsets
        sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)

        masked = text
        for entity in sorted_entities:
            value = entity.value

            # Reuse placeholder if exact same value appears multiple times
            if value in self.reverse_map:
                placeholder = self.reverse_map[value]
            else:
                placeholder = self._generate_placeholder(entity.entity_type, value)
                self.placeholder_map[placeholder] = value
                self.reverse_map[value] = placeholder

            masked = masked[:entity.start] + placeholder + masked[entity.end:]

        return masked, self.placeholder_map

    def get_mapping(self) -> Dict[str, str]:
        """Return the current placeholder mapping."""
        return dict(self.placeholder_map)

    def get_metadata(self) -> Dict[str, Dict]:
        """Return integrity metadata for Strategy D."""
        return dict(self.integrity_metadata)
