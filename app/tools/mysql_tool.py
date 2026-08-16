import time
import pandas as pd
import mysql.connector
from mysql.connector import Error
from app.config import config
from app.tools.base_db import BaseDatabase


class MySQLTool(BaseDatabase):

    def connect(self):
        try:
            connection = mysql.connector.connect(
                host=config.MYSQL_HOST,
                port=config.MYSQL_PORT,
                database=config.MYSQL_DATABASE,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                connection_timeout=config.QUERY_TIMEOUT,
            )
            return connection
        except Error as e:
            raise ConnectionError(f"MySQL connection failed: {e}")

    def get_schema(self) -> str:
        connection = self.connect()
        try:
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES;")
            tables = [row[0] for row in cursor.fetchall()]

            schema_parts = []
            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table}`;")
                row = cursor.fetchone()
                schema_parts.append(row[1])

            cursor.close()
            return "\n\n".join(schema_parts)
        finally:
            connection.close()

    def execute_query(self, sql: str) -> dict:
        connection = self.connect()
        try:
            start = time.time()

            # buffered=True fixes "Unread result found" error
            # it reads ALL results into memory immediately
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute(sql)

            # fetchall with limit applied in Python
            all_rows = cursor.fetchall()
            rows = all_rows[:config.MAX_ROWS]

            elapsed_ms = round((time.time() - start) * 1000)

            df = pd.DataFrame(rows)
            cursor.close()

            return {
                "dataframe": df,
                "row_count": len(df),
                "columns": list(df.columns) if not df.empty else [],
                "execution_time_ms": elapsed_ms,
            }
        except Error as e:
            raise RuntimeError(f"Query execution failed: {e}")
        finally:
            connection.close()