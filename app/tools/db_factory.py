from app.config import config
from app.tools.base_db import BaseDatabase


def get_db() -> BaseDatabase:
    """
    Returns the correct database tool based on DB_TYPE in .env
    """
    db_type = config.DB_TYPE

    if db_type == "mysql":
        from app.tools.mysql_tool import MySQLTool
        return MySQLTool()

    elif db_type == "sqlite":
        from app.tools.sqlite_tool import SQLiteTool
        return SQLiteTool()

    elif db_type == "postgres":
        from app.tools.postgres_tool import PostgresTool
        return PostgresTool()

    else:
        raise ValueError(
            f"Unsupported DB_TYPE: '{db_type}'. "
            f"Supported types: mysql, postgres, sqlite"
        )