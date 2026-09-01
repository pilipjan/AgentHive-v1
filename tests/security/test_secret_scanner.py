"""Security unit tests for SecretScanner engine."""

from security.scanners.secret_scanner import SecretScanner


def test_openai_key_detection_and_redaction():
    text = "Use this key sk-1234567890abcdef1234567890 for API calls."
    detections = SecretScanner.scan(text)
    assert len(detections) == 1
    assert detections[0].secret_type == "OPENAI_API_KEY"

    sanitized = SecretScanner.sanitize(text)
    assert "sk-1234567890abcdef1234567890" not in sanitized
    assert "[REDACTED_SECRET:OPENAI_API_KEY]" in sanitized


def test_openai_project_key_detection():
    text = "Project token: sk-proj-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    detections = SecretScanner.scan(text)
    assert len(detections) == 1
    assert detections[0].secret_type == "OPENAI_API_KEY"
    sanitized = SecretScanner.sanitize(text)
    assert "sk-proj-" not in sanitized


def test_anthropic_key_detection():
    text = "Anthropic config: sk-ant-1234567890abcdefghijklmnopqrstuvwx"
    detections = SecretScanner.scan(text)
    assert len(detections) == 1
    assert detections[0].secret_type == "ANTHROPIC_API_KEY"


def test_gemini_key_detection():
    text = "Google studio key: AIzaSyD1234567890abcdef1234567890abc"
    detections = SecretScanner.scan(text)
    assert len(detections) == 1
    assert detections[0].secret_type == "GEMINI_API_KEY"


def test_github_token_detection():
    text = "GitHub PAT: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    detections = SecretScanner.scan(text)
    assert len(detections) == 1
    assert detections[0].secret_type == "GITHUB_TOKEN"


def test_aws_key_detection():
    text = "AWS Key ID: AKIAIOSFODNN7EXAMPLE"
    detections = SecretScanner.scan(text)
    assert len(detections) == 1
    assert detections[0].secret_type == "AWS_ACCESS_KEY"


def test_private_key_detection():
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0Y...\n-----END RSA PRIVATE KEY-----"
    detections = SecretScanner.scan(text)
    assert len(detections) == 1
    assert detections[0].secret_type == "PRIVATE_KEY"
    sanitized = SecretScanner.sanitize(text)
    assert "-----BEGIN" not in sanitized
    assert "[REDACTED_SECRET:PRIVATE_KEY]" in sanitized


def test_database_url_credentials_detection():
    text = "Connect to postgresql://postgres:SuperSecretPassword123@db.prod.internal:5432/agenthive"
    detections = SecretScanner.scan(text)
    assert len(detections) >= 1
    assert detections[0].secret_type == "DATABASE_CREDENTIALS"


def test_clean_text_passes_untouched():
    text = "The quick brown fox jumps over the lazy dog. Python version is 3.10."
    assert not SecretScanner.has_secrets(text)
    assert SecretScanner.sanitize(text) == text
