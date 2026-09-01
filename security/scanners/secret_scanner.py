"""Secret Scanner Engine for identifying and redacting credentials and tokens."""

import re
from dataclasses import dataclass
from typing import List, Pattern, Tuple


@dataclass
class SecretDetection:
    """Individual secret detection finding."""

    secret_type: str
    matched_text: str
    start_pos: int
    end_pos: int


class SecretScanner:
    """Comprehensive scanner for credentials, private keys, and API tokens."""

    # Pre-compiled secret patterns (ordered by specificity)
    PATTERNS: List[Tuple[str, Pattern]] = [
        # Anthropic Keys (Must precede general sk- pattern)
        ("ANTHROPIC_API_KEY", re.compile(r"\b(sk-ant-[a-zA-Z0-9_\-]{30,})\b")),

        # OpenAI Keys (Excludes sk-ant)
        ("OPENAI_API_KEY", re.compile(r"\b(sk-(?!ant-)[a-zA-Z0-9_\-]{20,}|sk-proj-[a-zA-Z0-9_\-]{30,})\b")),
        
        # Google AI / Gemini API Keys (AIza + 30-40 chars)
        ("GEMINI_API_KEY", re.compile(r"\b(AIza[0-9A-Za-z\-_]{30,40})\b")),
        
        # GitHub Tokens
        ("GITHUB_TOKEN", re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{60,100})\b")),
        
        # AWS Access Key ID
        ("AWS_ACCESS_KEY", re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
        
        # Private Keys (RSA, EC, OpenSSH, PGP)
        ("PRIVATE_KEY", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
        
        # Database Connection URLs with embedded credentials
        ("DATABASE_CREDENTIALS", re.compile(r"(?:postgresql|postgres|mysql|mongodb(?:\+srv)?)://(?:[^:]+):([^@]+)@")),
        
        # Bearer Tokens
        ("BEARER_TOKEN", re.compile(r"\bBearer\s+([a-zA-Z0-9_\-\.]{25,})\b")),
        
        # Generic Key/Secret assignments (e.g. api_key = "abc...")
        ("GENERIC_API_SECRET", re.compile(r"(?i)\b(?:api[_-]?key|secret[_-]?key|auth[_-]?token|private[_-]?key)\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{16,})['\"]")),
    ]

    @classmethod
    def scan(cls, text: str) -> List[SecretDetection]:
        """Scan input text and return all detected secret occurrences."""
        if not text:
            return []

        detections: List[SecretDetection] = []
        for secret_type, pattern in cls.PATTERNS:
            for match in pattern.finditer(text):
                detections.append(
                    SecretDetection(
                        secret_type=secret_type,
                        matched_text=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end(),
                    )
                )
        return detections

    @classmethod
    def has_secrets(cls, text: str) -> bool:
        """Check if any secret signatures exist in text."""
        if not text:
            return False
        for _, pattern in cls.PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Replace all detected secrets with sanitized placeholders."""
        if not text:
            return text

        sanitized = text
        for secret_type, pattern in cls.PATTERNS:
            def _replace_match(m: re.Match) -> str:
                return f"[REDACTED_SECRET:{secret_type}]"
            sanitized = pattern.sub(_replace_match, sanitized)

        return sanitized
