from app.tools.mysql_tool import MySQLTool

def get_schema_for_prompt() -> str:
    """Fetch live schema from MySQL for use in LLM prompts."""
    tool = MySQLTool()
    schema = tool.get_schema()
    return f"DATABASE SCHEMA:\n\n{schema}"