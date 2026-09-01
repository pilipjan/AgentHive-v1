# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

Security is a primary pillar of AgentHive. If you discover a security vulnerability, please do NOT create a public issue on GitHub.

Instead, please report vulnerabilities by contacting the security maintainers:
- **Email:** `security@agenthive.local` (or file a private GitHub security advisory)

Please include:
1. Description of the vulnerability and potential impact.
2. Steps to reproduce or proof-of-concept payload.
3. Affected components (e.g., Memory Firewall, Secret Scanner, Permission Authorizer).

We commit to acknowledging reports within 48 hours and providing a remediation timeline.

## Zero-Trust Architecture Notice

AgentHive operates under the assumption that agents, external models, and inbound task payloads may be adversarial. Secret scanning and PII sanitization are defense-in-depth measures. Operators are advised to follow least-privilege deployment practices.
