from app.tools.db_factory import get_db


def get_schema_for_prompt() -> str:
    """
    Fetches live schema from whichever database is configured in .env
    """
    db = get_db()
    schema = db.get_schema()
    return f"DATABASE SCHEMA:\n\n{schema}"