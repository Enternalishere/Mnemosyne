import json
import sys
from typing import Any, Dict, List

from mnemosyne_engine import answer_query


def load_input() -> Dict[str, Any]:
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    return data


def main() -> None:
    data = load_input()
    if "memories" not in data or "question" not in data:
        sys.stderr.write("Input must contain 'memories' and 'question' fields.\n")
        sys.exit(1)
    memories = data["memories"]
    question = data["question"]
    if not isinstance(memories, list):
        sys.stderr.write("'memories' must be a list of memory objects.\n")
        sys.exit(1)
    if not isinstance(question, str):
        sys.stderr.write("'question' must be a string.\n")
        sys.exit(1)
    output = answer_query(memories, question)
    sys.stdout.write(output + "\n")


if __name__ == "__main__":
    main()

