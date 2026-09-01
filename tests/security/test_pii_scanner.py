"""Security unit tests for PIIScanner engine."""

from security.scanners.pii_scanner import PIIScanner


def test_email_detection_and_redaction():
    text = "Please reach out to support.agent@company.org for assistance."
    detections = PIIScanner.scan(text)
    assert len(detections) == 1
    assert detections[0].pii_type == "EMAIL"
    sanitized = PIIScanner.sanitize(text)
    assert "support.agent@company.org" not in sanitized
    assert "[REDACTED_EMAIL]" in sanitized


def test_phone_detection_and_redaction():
    text = "Call direct line at +1 (555) 234-5678 or 555-876-5432."
    detections = PIIScanner.scan(text)
    assert len(detections) >= 1
    sanitized = PIIScanner.sanitize(text)
    assert "[REDACTED_PHONE]" in sanitized


def test_ssn_detection_and_redaction():
    text = "Confidential record SSN: 123-45-6789."
    detections = PIIScanner.scan(text)
    assert len(detections) == 1
    assert detections[0].pii_type == "SSN"
    sanitized = PIIScanner.sanitize(text)
    assert "123-45-6789" not in sanitized
    assert "[REDACTED_SSN]" in sanitized


def test_credit_card_detection_and_redaction():
    text = "Processed transaction with card 4111 2222 3333 4444."
    detections = PIIScanner.scan(text)
    assert len(detections) >= 1
    assert detections[0].pii_type == "CREDIT_CARD"
    sanitized = PIIScanner.sanitize(text)
    assert "4111 2222 3333 4444" not in sanitized
    assert "[REDACTED_CREDIT_CARD]" in sanitized
