"""Memory Firewall Pipeline for inspecting, sanitizing, and filtering agent memory and communication."""

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union
from security.permissions.enums import (
    AgentPermissionEnum,
    PolicyVerdict,
    SensitivityTier,
    VisibilityScope,
)
from security.permissions.authorizer import PermissionAuthorizer
from security.scanners.secret_scanner import SecretScanner
from security.scanners.pii_scanner import PIIScanner
from security.firewall.classifier import SensitivityClassifier


@dataclass
class FirewallResult:
    """Output verdict and sanitized payload resulting from Memory Firewall execution."""

    verdict: PolicyVerdict
    original_text_hash: str
    sanitized_text: str
    sensitivity: SensitivityTier
    detected_secrets: List[str] = field(default_factory=list)
    detected_pii: List[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None
    audit_payload: Dict[str, Any] = field(default_factory=dict)


class MemoryFirewall:
    """6-stage Memory Firewall enforcing data boundaries, secret blocking, and PII protection."""

    @classmethod
    def process_message(
        cls,
        content: str,
        sender_id: str,
        sender_permissions: Union[List[str], Set[str]],
        is_same_hive: bool = True,
        strict_mode: bool = True,
    ) -> FirewallResult:
        """Process a collaborative message through the Memory Firewall."""
        raw_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Stage 1: Permission Check
        if not PermissionAuthorizer.can_message_agents(sender_permissions, is_same_hive):
            return FirewallResult(
                verdict=PolicyVerdict.BLOCKED,
                original_text_hash=raw_hash,
                sanitized_text="",
                sensitivity=SensitivityTier.RESTRICTED,
                rejection_reason="Agent lacks MESSAGE_AGENTS permission or target is outside assigned Hive.",
                audit_payload={"actor": sender_id, "action": "MESSAGE_BLOCKED_UNAUTHORIZED"},
            )

        # Stage 2: Sensitivity Classification
        sensitivity = SensitivityClassifier.classify(content)

        # Stage 3 & 4: Secret and PII Scanners
        secret_detections = SecretScanner.scan(content)
        pii_detections = PIIScanner.scan(content)
        secret_types = [s.secret_type for s in secret_detections]
        pii_types = [p.pii_type for p in pii_detections]

        # Stage 5: Hard block check for critical restricted items
        if any(st in ("PRIVATE_KEY", "DATABASE_CREDENTIALS") for st in secret_types):
            return FirewallResult(
                verdict=PolicyVerdict.BLOCKED,
                original_text_hash=raw_hash,
                sanitized_text="",
                sensitivity=SensitivityTier.RESTRICTED,
                detected_secrets=secret_types,
                detected_pii=pii_types,
                rejection_reason="Message contained forbidden RESTRICTED credentials (private key or DB connection).",
                audit_payload={"actor": sender_id, "action": "MESSAGE_BLOCKED_RESTRICTED_SECRET"},
            )

        # Stage 6: Policy Verdict - Redaction for general secrets and PII
        if secret_detections or pii_detections:
            sanitized = SecretScanner.sanitize(content)
            sanitized = PIIScanner.sanitize(sanitized)
            return FirewallResult(
                verdict=PolicyVerdict.REDACTED,
                original_text_hash=raw_hash,
                sanitized_text=sanitized,
                sensitivity=sensitivity,
                detected_secrets=secret_types,
                detected_pii=pii_types,
                audit_payload={
                    "actor": sender_id,
                    "action": "MESSAGE_SANITIZED",
                    "secrets_redacted": secret_types,
                    "pii_redacted": pii_types,
                },
            )

        # Allowed Clean Message
        return FirewallResult(
            verdict=PolicyVerdict.ALLOWED,
            original_text_hash=raw_hash,
            sanitized_text=content,
            sensitivity=sensitivity,
            audit_payload={"actor": sender_id, "action": "MESSAGE_DELIVERED"},
        )

    @classmethod
    def process_knowledge(
        cls,
        content: str,
        summary: str,
        source_agent_id: str,
        source_permissions: Union[List[str], Set[str]],
        target_visibility: VisibilityScope,
    ) -> FirewallResult:
        """Process candidate knowledge submission before entering shared memory."""
        combined_text = f"{summary}\n{content}"
        raw_hash = hashlib.sha256(combined_text.encode("utf-8")).hexdigest()

        # 1. Permission Check
        if not PermissionAuthorizer.can_write_knowledge(source_permissions, target_visibility):
            return FirewallResult(
                verdict=PolicyVerdict.BLOCKED,
                original_text_hash=raw_hash,
                sanitized_text="",
                sensitivity=SensitivityTier.RESTRICTED,
                rejection_reason=f"Agent lacks WRITE_KNOWLEDGE permission for target visibility {target_visibility.value}.",
                audit_payload={"actor": source_agent_id, "action": "KNOWLEDGE_BLOCKED_UNAUTHORIZED"},
            )

        # 2. Sensitivity Classification
        sensitivity = SensitivityClassifier.classify(combined_text)

        # 3 & 4. Secret & PII Scanning
        secret_detections = SecretScanner.scan(combined_text)
        pii_detections = PIIScanner.scan(combined_text)
        secret_types = [s.secret_type for s in secret_detections]
        pii_types = [p.pii_type for p in pii_detections]

        # 5. Public / Project visibility cannot contain unredacted secrets
        if secret_detections and target_visibility in (VisibilityScope.PUBLIC, VisibilityScope.PROJECT):
            return FirewallResult(
                verdict=PolicyVerdict.BLOCKED,
                original_text_hash=raw_hash,
                sanitized_text="",
                sensitivity=SensitivityTier.RESTRICTED,
                detected_secrets=secret_types,
                detected_pii=pii_types,
                rejection_reason="Public or Project shared knowledge submissions cannot contain raw credentials.",
                audit_payload={"actor": source_agent_id, "action": "KNOWLEDGE_BLOCKED_PUBLIC_SECRET"},
            )

        # 6. Apply Redaction if internal/hive
        if secret_detections or pii_detections:
            sanitized = SecretScanner.sanitize(content)
            sanitized = PIIScanner.sanitize(sanitized)
            return FirewallResult(
                verdict=PolicyVerdict.REDACTED,
                original_text_hash=raw_hash,
                sanitized_text=sanitized,
                sensitivity=sensitivity,
                detected_secrets=secret_types,
                detected_pii=pii_types,
                audit_payload={
                    "actor": source_agent_id,
                    "action": "KNOWLEDGE_SANITIZED",
                    "secrets_redacted": secret_types,
                    "pii_redacted": pii_types,
                },
            )

        return FirewallResult(
            verdict=PolicyVerdict.ALLOWED,
            original_text_hash=raw_hash,
            sanitized_text=content,
            sensitivity=sensitivity,
            audit_payload={"actor": source_agent_id, "action": "KNOWLEDGE_STORED"},
        )
