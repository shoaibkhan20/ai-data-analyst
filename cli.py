import sys
import os

# Must be BEFORE any app imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import argparse
from app.workflow.analyst_workflow import stream

def print_step(data: dict):
    """Print each step in a readable format."""
    if data["type"] == "step":
        status = data["status"].upper()
        name = data["name"]
        step = data["step"]

        colors = {
            "RUNNING": "\033[93m",
            "DONE": "\033[92m",
            "ERROR": "\033[91m",
            "BLOCKED": "\033[91m",
            "RETRYING": "\033[94m",
        }
        reset = "\033[0m"
        color = colors.get(status, "")

        print(f"  {color}[{status}]{reset} Step {step} — {name}")

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
    """Run in interactive loop."""
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


def main():
    parser = argparse.ArgumentParser(
        prog="data-analyst",
        description="AI Data Analyst — Ask business questions in plain English",
    )

    parser.add_argument(
        "question",
        nargs="?",
        help="Business question to ask (e.g. 'how many artists are in the database')",
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode — keep asking questions",
    )

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.question:
        run_question(args.question)
    else:
        # No arguments — default to interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()