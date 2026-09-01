"""Sensitivity Classifier for automated data categorization."""

from security.permissions.enums import SensitivityTier
from security.scanners.secret_scanner import SecretScanner
from security.scanners.pii_scanner import PIIScanner


class SensitivityClassifier:
    """Classifies content into sensitivity tiers based on scanner findings and heuristics."""

    @classmethod
    def classify(cls, text: str) -> SensitivityTier:
        """Analyze text and determine its sensitivity tier."""
        if not text:
            return SensitivityTier.PUBLIC

        secret_detections = SecretScanner.scan(text)
        pii_detections = PIIScanner.scan(text)

        # 1. Check for RESTRICTED indicators (Private keys, DB connection credentials)
        for s in secret_detections:
            if s.secret_type in ("PRIVATE_KEY", "DATABASE_CREDENTIALS"):
                return SensitivityTier.RESTRICTED

        # 2. Check for CONFIDENTIAL indicators (API keys, SSN, Credit Cards)
        if secret_detections:
            return SensitivityTier.CONFIDENTIAL

        for p in pii_detections:
            if p.pii_type in ("SSN", "CREDIT_CARD"):
                return SensitivityTier.CONFIDENTIAL

        # 3. Check for INTERNAL indicators (Emails, Phones)
        if pii_detections:
            return SensitivityTier.INTERNAL

        return SensitivityTier.PUBLIC
