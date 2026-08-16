import re

# ─────────────────────────────────────────
# BLOCKED SQL KEYWORDS
# Dangerous operations that should never run
# ─────────────────────────────────────────
BLOCKED_KEYWORDS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bRENAME\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bCALL\b",
    r"\bLOAD\b",
    r"\bOUTFILE\b",
    r"\bINFILE\b",
]

# ─────────────────────────────────────────
# SENSITIVE COLUMN NAMES
# These columns are filtered from results
# even if SQL selects them
# ─────────────────────────────────────────
SENSITIVE_COLUMNS = [
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "api_secret",
    "private_key",
    "auth_token",
    "session_token",
    "ssn",
    "social_security",
    "credit_card",
    "card_number",
    "cvv",
    "pin",
    "salary",
    "wage",
    "bank_account",
    "account_number",
    "routing_number",
    "passport",
    "license_number",
    "date_of_birth",
    "dob",
]


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validates that SQL is safe to execute.
    Returns (is_safe, reason)
    """
    stripped = sql.strip()

    # Must start with SELECT or WITH
    if not (
        stripped.upper().startswith("SELECT") or
        stripped.upper().startswith("WITH")
    ):
        return False, "Only SELECT and WITH (CTE) queries are allowed."

    # Check for blocked keywords
    for pattern in BLOCKED_KEYWORDS:
        if re.search(pattern, stripped.upper()):
            keyword = pattern.replace(r"\b", "").replace("\\b", "")
            return False, f"Blocked keyword detected: {keyword}"

    # Block multiple statements
    without_trailing = stripped.rstrip(";")
    if ";" in without_trailing:
        return False, "Multiple SQL statements are not allowed."

    return True, "OK"


def filter_sensitive_columns(data: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Removes sensitive columns from query results.
    Returns (cleaned_data, list of removed column names)

    Works on the result rows AFTER execution —
    so even if SQL selects a sensitive column it never reaches the user.
    """
    if not data:
        return data, []

    # Find which sensitive columns are present in results
    result_columns = set(data[0].keys())
    removed = []

    for col in result_columns:
        col_lower = col.lower()
        for sensitive in SENSITIVE_COLUMNS:
            if sensitive in col_lower:
                removed.append(col)
                break

    if not removed:
        return data, []

    # Strip sensitive columns from every row
    cleaned = [
        {k: v for k, v in row.items() if k not in removed}
        for row in data
    ]

    return cleaned, removed