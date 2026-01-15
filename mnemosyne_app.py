import argparse
from datetime import datetime
from typing import Dict, Any

from memory_pipeline import run_memory_pipeline
from memory_store import load_memories, append_memories
from mnemosyne_engine import answer_query
from thinking_sessions import run_thinking_session


def run_ingest(text: str, source: str, timestamp: str, store_path: str, profile: str = "default") -> Dict[str, Any]:
    if not timestamp:
        timestamp = datetime.utcnow().isoformat()
    existing = load_memories(store_path)
    result = run_memory_pipeline(text, timestamp, source, existing, profile=profile)
    combined = append_memories(store_path, result["new_memories"])
    summary = {
        "new_memories": result["new_memories"],
        "revisions": result["revisions"],
        "contradictions": result["contradictions"],
        "total_memories": len(combined),
    }
    return summary


def run_answer(question: str, store_path: str) -> Dict[str, Any]:
    memories = load_memories(store_path)
    if not memories:
        return {"has_memories": False, "answer": "No memories available in the store."}
    output = answer_query(memories, question)
    return {"has_memories": True, "answer": output}


def ingest_command(args: argparse.Namespace) -> None:
    summary = run_ingest(args.text, args.source, args.timestamp, args.store, profile=args.profile)
    print("New memories:")
    for m in summary["new_memories"]:
        print(m["memory_id"], m["created_at"], m["content"])
    if summary["revisions"]:
        print("Revisions:")
        for r in summary["revisions"]:
            print(r["memory_id"], "revises", r["revision_of"])
    if summary["contradictions"]:
        print("Contradictions:")
        for c in summary["contradictions"]:
            print("Topic:", c["topic"], "status:", c["status"])
    print("Total memories in store:", summary["total_memories"])


def answer_command(args: argparse.Namespace) -> None:
    result = run_answer(args.question, args.store)
    print(result["answer"])


def session_command(args: argparse.Namespace) -> None:
    result = run_thinking_session(args.topic, args.store, start_iso=args.start, end_iso=args.end)
    print(result["answer"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("--store", required=True)
    ingest.add_argument("--text", required=True)
    ingest.add_argument("--source", required=True, choices=["note", "pdf", "tweet", "chat", "voice"])
    ingest.add_argument("--timestamp")
    ingest.add_argument("--profile", default="default", choices=["default", "journal", "research"])
    ingest.set_defaults(func=ingest_command)

    answer = subparsers.add_parser("answer")
    answer.add_argument("--store", required=True)
    answer.add_argument("--question", required=True)
    answer.set_defaults(func=answer_command)

    session = subparsers.add_parser("session")
    session.add_argument("--store", required=True)
    session.add_argument("--topic", required=True)
    session.add_argument("--start")
    session.add_argument("--end")
    session.set_defaults(func=session_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return
    func(args)


if __name__ == "__main__":
    main()
