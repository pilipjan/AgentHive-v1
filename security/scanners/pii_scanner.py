"""PII Protection Scanner for identifying and redacting personal information."""

import re
from dataclasses import dataclass
from typing import List, Pattern, Tuple


@dataclass
class PIIDetection:
    """Individual PII detection finding."""

    pii_type: str
    matched_text: str
    start_pos: int
    end_pos: int


class PIIScanner:
    """Scanner for Personally Identifiable Information (Emails, Phones, SSNs, Credit Cards)."""

    # Pre-compiled PII regex patterns
    PATTERNS: List[Tuple[str, Pattern]] = [
        # Email Addresses (RFC 5322 simplified)
        ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")),
        
        # Credit Card Numbers (13-19 digits, with optional spaces or dashes)
        ("CREDIT_CARD", re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b|\b\d{15,16}\b")),
        
        # Social Security Numbers (US Format: XXX-XX-XXXX)
        ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
        
        # Phone Numbers (International & Domestic formats)
        ("PHONE", re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ]

    @classmethod
    def scan(cls, text: str) -> List[PIIDetection]:
        """Scan input text and return detected PII occurrences."""
        if not text:
            return []

        detections: List[PIIDetection] = []
        for pii_type, pattern in cls.PATTERNS:
            for match in pattern.finditer(text):
                detections.append(
                    PIIDetection(
                        pii_type=pii_type,
                        matched_text=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end(),
                    )
                )
        return detections

    @classmethod
    def has_pii(cls, text: str) -> bool:
        """Check if any PII exists in text."""
        if not text:
            return False
        for _, pattern in cls.PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Replace all detected PII with sanitized redaction placeholders."""
        if not text:
            return text

        sanitized = text
        for pii_type, pattern in cls.PATTERNS:
            def _replace_match(m: re.Match) -> str:
                return f"[REDACTED_{pii_type}]"
            sanitized = pattern.sub(_replace_match, sanitized)

        return sanitized
