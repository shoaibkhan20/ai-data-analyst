import time
import pandas as pd
import psycopg2
import psycopg2.extras
from app.config import config
from app.tools.base_db import BaseDatabase


class PostgresTool(BaseDatabase):

    def connect(self):
        try:
            connection = psycopg2.connect(
                host=config.POSTGRES_HOST,
                port=config.POSTGRES_PORT,
                dbname=config.POSTGRES_DATABASE,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD,
                connect_timeout=config.QUERY_TIMEOUT,
            )
            return connection
        except Exception as e:
            raise ConnectionError(f"PostgreSQL connection failed: {e}")

    def get_schema(self) -> str:
        connection = self.connect()
        try:
            cursor = connection.cursor()

            # Get all tables in public schema
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE';
            """)
            tables = [row[0] for row in cursor.fetchall()]

            schema_parts = []
            for table in tables:
                # Get columns with types
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """, (table,))
                columns = cursor.fetchall()

                col_defs = ", ".join([
                    f"{col[0]} {col[1].upper()}"
                    for col in columns
                ])
                schema_parts.append(
                    f"CREATE TABLE {table} ({col_defs});"
                )

            cursor.close()
            return "\n\n".join(schema_parts)
        finally:
            connection.close()

    def execute_query(self, sql: str) -> dict:
        connection = self.connect()
        try:
            start = time.time()
            cursor = connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            cursor.execute(sql)
            rows = cursor.fetchmany(config.MAX_ROWS)
            elapsed_ms = round((time.time() - start) * 1000)

            df = pd.DataFrame([dict(row) for row in rows])
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