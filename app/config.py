import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Database type
    DB_TYPE: str = os.getenv("DB_TYPE", "mysql").lower()

    # MySQL
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")

    # PostgreSQL
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DATABASE: str = os.getenv("POSTGRES_DATABASE", "")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    # SQLite
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "./database.db")

    # Limits
    MAX_ROWS: int = 1000
    QUERY_TIMEOUT: int = 30


config = Config()