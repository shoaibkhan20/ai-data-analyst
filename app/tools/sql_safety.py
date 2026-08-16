import re

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


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validates that SQL is safe to execute.
    Returns (is_safe, reason)
    """
    stripped = sql.strip()

    # Must start with SELECT or WITH
    if not (stripped.upper().startswith("SELECT") or
            stripped.upper().startswith("WITH")):
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