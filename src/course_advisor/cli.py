"""Command-line interface for course-advisor."""
import argparse
import subprocess
import sys
from importlib.resources import files


def main():
    parser = argparse.ArgumentParser(prog="course-advisor",
                                     description="AI Course Advisor")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("test", help="Test Azure OpenAI connection")
    sub.add_parser("ingest", help="Ingest policy documents into ChromaDB")
    sub.add_parser("ui", help="Launch the Streamlit chat UI")

    args = parser.parse_args()

    if args.command == "test":
        from .test_connection import run_test
        run_test()
    elif args.command == "ingest":
        from .ingest import main as ingest_main
        ingest_main()
    elif args.command == "ui":
        app_path = files("course_advisor") / "app.py"
        subprocess.call([sys.executable, "-m", "streamlit", "run", str(app_path)])


if __name__ == "__main__":
    main()