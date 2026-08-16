from abc import ABC, abstractmethod
import pandas as pd


class BaseDatabase(ABC):
    """
    Abstract base class for all database tools.
    Every database tool must implement these two methods.
    This ensures mysql_tool, sqlite_tool, postgres_tool
    are all interchangeable in the workflow.
    """

    @abstractmethod
    def get_schema(self) -> str:
        """
        Fetch the full database schema as a string.
        Returns CREATE TABLE statements or equivalent.
        """
        pass

    @abstractmethod
    def execute_query(self, sql: str) -> dict:
        """
        Execute a SQL query and return results.
        Returns:
        {
            dataframe: pd.DataFrame,
            row_count: int,
            columns: list,
            execution_time_ms: int
        }
        """
        pass