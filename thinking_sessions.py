from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from memory_store import load_memories, append_memories, filter_by_topic, filter_by_time_range
from mnemosyne_engine import answer_query


def run_thinking_session(
    topic: str,
    store_path: str,
    start_iso: Optional[str] = None,
    end_iso: Optional[str] = None,
) -> Dict[str, Any]:
    memories = load_memories(store_path)
    topic_memories = filter_by_topic(memories, topic)
    if start_iso or end_iso:
        if start_iso is None:
            start_iso = "0001-01-01T00:00:00"
        if end_iso is None:
            end_iso = "9999-12-31T23:59:59"
        topic_memories = filter_by_time_range(topic_memories, start_iso, end_iso)
    answer = answer_query(topic_memories, f"How has my thinking about {topic} evolved?")
    now = datetime.utcnow().isoformat()
    summary_memory = {
        "memory_id": f"session-{now}",
        "content": f"Thinking session summary for topic '{topic}' at {now}.",
        "created_at": now,
        "memory_type": "reflection",
        "confidence": 0.8,
        "source": "session",
        "topic": [topic],
        "revision_of": None,
    }
    append_memories(store_path, [summary_memory])
    return {"answer": answer, "summary_memory": summary_memory}

