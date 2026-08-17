import sys
import json
from app.workflow.analyst_workflow import stream


def print_step(data: dict):
    """Print each step in a readable format."""
    if data["type"] == "step":
        status = data["status"].upper()
        name = data["name"]
        step = data["step"]

        # Status colors using ANSI codes
        colors = {
            "RUNNING": "\033[93m",   # yellow
            "DONE": "\033[92m",      # green
            "ERROR": "\033[91m",     # red
            "BLOCKED": "\033[91m",   # red
            "RETRYING": "\033[94m",  # blue
        }
        reset = "\033[0m"
        color = colors.get(status, "")

        print(f"  {color}[{status}]{reset} Step {step} — {name}")

        # Print extra info if available
        if data.get("sql"):
            print(f"           SQL: {data['sql'][:120]}...")
        if data.get("rows_returned") is not None:
            print(f"           Rows returned: {data['rows_returned']}")
        if data.get("attempts") and data["attempts"] > 1:
            print(f"           Attempts: {data['attempts']}")
        if data.get("reason"):
            print(f"           Reason: {data['reason']}")
        if data.get("chart_type"):
            print(f"           Chart type: {data['chart_type']}")
        if data.get("stats"):
            for col, stat in data["stats"].items():
                print(f"           {col}: total={stat['total']}, avg={stat['average']}, max={stat['max']}")

    elif data["type"] == "final":
        print("\n" + "─" * 60)
        print("  RESULT")
        print("─" * 60)

        if data.get("error"):
            print(f"\n  Error: {data['error']}")
            return

        print(f"\n  Answer:\n  {data.get('answer', 'No answer generated')}")
        print(f"\n  Rows returned: {data.get('row_count', 0)}")
        print(f"  Execution time: {data.get('execution_time_ms', 0)}ms")
        print(f"  SQL attempts: {data.get('sql_attempts', 1)}")

        if data.get("sql"):
            print(f"\n  SQL:\n  {data['sql']}")

        if data.get("stats"):
            print("\n  Statistics:")
            for col, stat in data["stats"].items():
                print(f"    {col}:")
                for k, v in stat.items():
                    print(f"      {k}: {v}")

        if data.get("chart") and data["chart"].get("spec", {}).get("required"):
            spec = data["chart"]["spec"]
            print(f"\n  Chart: {spec.get('chart_type')} — {spec.get('title')}")

        if data.get("data"):
            print(f"\n  Data (first 5 rows):")
            for row in data["data"][:5]:
                print(f"    {json.dumps(row, default=str)}")
            if len(data["data"]) > 5:
                print(f"    ... and {len(data['data']) - 5} more rows")

    elif data["type"] == "done":
        print("\n" + "─" * 60)
        print("  Pipeline complete.")
        print("─" * 60)


def run_question(question: str):
    """Run a single question through the pipeline."""
    print("\n" + "=" * 60)
    print(f"  Question: {question}")
    print("=" * 60 + "\n")

    for event_str in stream(question):
        if not event_str.startswith("data: "):
            continue
        try:
            data = json.loads(event_str[6:])
            print_step(data)
        except json.JSONDecodeError:
            continue


def interactive_mode():
    """Run in interactive loop — keep asking questions."""
    print("\n" + "=" * 60)
    print("  AI Data Analyst — Terminal Mode")
    print("  Type your question and press Enter.")
    print("  Type 'exit' or 'quit' to stop.")
    print("=" * 60)

    while True:
        try:
            print()
            question = input("  Question: ").strip()

            if not question:
                continue

            if question.lower() in ("exit", "quit", "q"):
                print("\n  Goodbye.\n")
                break

            run_question(question)

        except KeyboardInterrupt:
            print("\n\n  Interrupted. Goodbye.\n")
            break


if __name__ == "__main__":
    # If question passed as argument — run once
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        run_question(question)

    # Otherwise run in interactive mode
    else:
        interactive_mode()