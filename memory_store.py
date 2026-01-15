import json
import os
from typing import List, Dict, Any


def load_memories(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    if not isinstance(data, list):
        return []
    return data


def save_memories(path: str, memories: List[Dict[str, Any]]) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)


def snapshot_memories(path: str, snapshot_dir: str) -> None:
    memories = load_memories(path)
    if not memories:
        return
    if not os.path.exists(snapshot_dir):
        os.makedirs(snapshot_dir, exist_ok=True)
    base = os.path.basename(path) or "memories.json"
    snapshot_name = base.replace(".json", "")
    from datetime import datetime

    ts = datetime.utcnow().isoformat().replace(":", "").replace("-", "")
    snapshot_path = os.path.join(snapshot_dir, f"{snapshot_name}_{ts}.json")
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)


def append_memories(path: str, new_memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    existing = load_memories(path)
    combined = existing + list(new_memories)
    save_memories(path, combined)
    return combined


def filter_by_topic(memories: List[Dict[str, Any]], topic: str) -> List[Dict[str, Any]]:
    lower = topic.lower()
    result: List[Dict[str, Any]] = []
    for m in memories:
        topics = [str(t).lower() for t in m.get("topic", [])]
        if any(lower == t or lower in t for t in topics):
            result.append(m)
    return result


def filter_by_time_range(
    memories: List[Dict[str, Any]],
    start_iso: str,
    end_iso: str,
) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for m in memories:
        created_at = m.get("created_at")
        if created_at is None:
            continue
        if created_at >= start_iso and created_at <= end_iso:
            result.append(m)
    return result
