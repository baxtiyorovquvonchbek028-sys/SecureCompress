"""
scanner.py — Sensitive data detection using regex patterns
"""

import re
from typing import List


# ─── Patterns ────────────────────────────────────────────────────────────────

PATTERNS = {
    'Email manzil': re.compile(
        r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
        re.IGNORECASE
    ),
    'Telefon raqami': re.compile(
        r'\+?\d[\d\s\-().]{7,14}\d',
    ),
    'Kredit karta raqami': re.compile(
        r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|[0-9]{16})\b'
    ),
    'IBAN / bank raqami': re.compile(
        r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b'
    ),
    'IP manzil': re.compile(
        r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
    ),
    'JWT Token': re.compile(
        r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]+'
    ),
    'API kalit': re.compile(
        r'(?:api[_\-]?key|apikey|access[_\-]?token)\s*[=:]\s*["\']?[\w\-]{16,}["\']?',
        re.IGNORECASE
    ),
    'SSH private key': re.compile(
        r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'
    ),
}

SENSITIVE_KEYWORDS = [
    'password', 'parol', 'login', 'username', 'secret',
    'private_key', 'passwd', 'pwd', 'token', 'auth',
    'credential', 'ssn', 'social_security', 'passcode'
]

KEYWORD_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in SENSITIVE_KEYWORDS) + r')\b',
    re.IGNORECASE
)


def scan_sensitive_data(text: str) -> List[str]:
    """
    Scan text for sensitive data patterns.
    Returns list of warning messages.
    """
    if not text or not text.strip():
        return []

    warnings = []
    seen = set()

    # Pattern-based detection
    for label, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        if matches and label not in seen:
            count = len(matches)
            warnings.append(f"⚠️ {label} aniqlandi ({count} ta)")
            seen.add(label)

    # Keyword detection
    kw_matches = KEYWORD_PATTERN.findall(text)
    if kw_matches:
        unique_kw = list(set(m.lower() for m in kw_matches))[:5]
        kw_str = ', '.join(unique_kw)
        warnings.append(f"🔑 Maxfiy kalit so'zlar topildi: {kw_str}")

    return warnings


def get_risk_level(warnings: List[str]) -> str:
    """Determine risk level based on warnings."""
    n = len(warnings)
    if n == 0:
        return 'safe'
    elif n <= 2:
        return 'low'
    elif n <= 4:
        return 'medium'
    return 'high'
