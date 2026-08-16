import time
import sqlite3
import pandas as pd
from app.config import config
from app.tools.base_db import BaseDatabase


class SQLiteTool(BaseDatabase):

    def connect(self):
        try:
            connection = sqlite3.connect(config.SQLITE_PATH)
            connection.row_factory = sqlite3.Row
            return connection
        except Exception as e:
            raise ConnectionError(f"SQLite connection failed: {e}")

    def get_schema(self) -> str:
        connection = self.connect()
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%';
            """)
            tables = [row[0] for row in cursor.fetchall()]

            schema_parts = []
            for table in tables:
                cursor.execute("""
                    SELECT sql FROM sqlite_master
                    WHERE type='table' AND name=?;
                """, (table,))
                row = cursor.fetchone()
                if row:
                    schema_parts.append(row[0])

            return "\n\n".join(schema_parts)
        finally:
            connection.close()

    def execute_query(self, sql: str) -> dict:
        connection = self.connect()
        try:
            start = time.time()
            cursor = connection.cursor()
            cursor.execute(sql)

            # fetchall then slice — SQLite has no buffered mode
            all_rows = cursor.fetchall()
            rows = all_rows[:config.MAX_ROWS]

            elapsed_ms = round((time.time() - start) * 1000)

            if rows:
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(
                    [dict(zip(columns, row)) for row in rows]
                )
            else:
                df = pd.DataFrame()

            cursor.close()

            return {
                "dataframe": df,
                "row_count": len(df),
                "columns": list(df.columns) if not df.empty else [],
                "execution_time_ms": elapsed_ms,
            }
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")
        finally:
            connection.close()