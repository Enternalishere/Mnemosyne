import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple


def split_sentences(text: str) -> List[str]:
    parts: List[str] = []
    buffer = []
    for ch in text:
        buffer.append(ch)
        if ch in ".!?":
            segment = "".join(buffer).strip()
            if segment:
                parts.append(segment)
            buffer = []
    if buffer:
        segment = "".join(buffer).strip()
        if segment:
            parts.append(segment)
    return parts


def classify_memory_type(sentence: str) -> str:
    lower = sentence.lower()
    if any(x in lower for x in ["i believe", "i think", "i feel", "i assume"]):
        return "belief"
    if any(x in lower for x in ["i decided", "i will", "i plan", "i intend"]):
        return "decision"
    if any(x in lower for x in ["i realized", "i noticed", "i reflected", "i am reflecting"]):
        return "reflection"
    return "fact"


def estimate_confidence(sentence: str) -> float:
    length = len(sentence)
    if length == 0:
        return 0.0
    if length < 40:
        return 0.7
    if length < 200:
        return 0.9
    return 0.6


def extract_topics(sentence: str) -> List[str]:
    tokens: List[str] = []
    current = []
    for ch in sentence:
        if ch.isalnum() or ch in ["_", "-"]:
            current.append(ch.lower())
        else:
            if current:
                tokens.append("".join(current))
                current = []
    if current:
        tokens.append("".join(current))
    stop = {
        "the",
        "and",
        "or",
        "but",
        "with",
        "for",
        "this",
        "that",
        "are",
        "is",
        "am",
        "i",
        "of",
        "in",
        "to",
        "a",
        "an",
    }
    filtered = [t for t in tokens if t not in stop and len(t) > 2]
    unique = []
    seen = set()
    for t in filtered:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def topics_overlap(t1: List[str], t2: List[str]) -> bool:
    return bool(set(t1) & set(t2))


def detect_revision(existing: Dict[str, Any], new: Dict[str, Any]) -> bool:
    old_text = existing["content"].lower()
    new_text = new["content"].lower()
    if "no longer" in new_text or "changed my mind" in new_text or "but now" in new_text:
        return True
    if "used to" in new_text and "now" in new_text:
        return True
    if "previously" in new_text and "now" in new_text:
        return True
    if "not" in new_text and "not" not in old_text:
        return True
    return False


def detect_contradiction_pair(m1: Dict[str, Any], m2: Dict[str, Any]) -> bool:
    t1 = m1["topic"]
    t2 = m2["topic"]
    if not topics_overlap(t1, t2):
        return False
    c1 = m1["content"].lower()
    c2 = m2["content"].lower()
    if c1 == c2:
        return False
    if " not " in c1 and " not " not in c2:
        return True
    if " not " in c2 and " not " not in c1:
        return True
    if "no longer" in c1 and "no longer" not in c2:
        return True
    if "no longer" in c2 and "no longer" not in c1:
        return True
    return False


def group_contradictions(memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    contradictions: List[Dict[str, Any]] = []
    n = len(memories)
    for i in range(n):
        for j in range(i + 1, n):
            m1 = memories[i]
            m2 = memories[j]
            if detect_contradiction_pair(m1, m2):
                topics = list(set(m1["topic"]) | set(m2["topic"]))
                topic = topics[0] if topics else "unspecified"
                contradictions.append(
                    {
                        "topic": topic,
                        "conflicting_memories": [
                            {
                                "memory_id": m1["memory_id"],
                                "created_at": m1["created_at"],
                                "content": m1["content"],
                            },
                            {
                                "memory_id": m2["memory_id"],
                                "created_at": m2["created_at"],
                                "content": m2["content"],
                            },
                        ],
                        "status": "unresolved",
                        "notes": "Memories differ on the same topic and include opposing phrasing.",
                    }
                )
    return contradictions


def extract_new_memories(raw_content: str, timestamp: str, source: str, profile: str = "default") -> List[Dict[str, Any]]:
    sentences = split_sentences(raw_content)
    created_at = datetime.fromisoformat(timestamp)
    new_memories: List[Dict[str, Any]] = []
    for sentence in sentences:
        memory_type = classify_memory_type(sentence)
        confidence = estimate_confidence(sentence)
        topics = extract_topics(sentence)
        if profile == "journal" and memory_type == "fact":
            continue
        memory = {
            "memory_id": str(uuid.uuid4()),
            "content": sentence,
            "created_at": created_at.isoformat(),
            "memory_type": memory_type,
            "confidence": confidence,
            "source": source,
            "topic": topics,
            "revision_of": None,
        }
        new_memories.append(memory)
    return new_memories


def link_revisions(
    existing_memories: List[Dict[str, Any]],
    new_memories: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    revisions: List[Dict[str, Any]] = []
    by_id = {m["memory_id"]: m for m in existing_memories}
    for new in new_memories:
        for old in existing_memories:
            if not topics_overlap(old.get("topic", []), new.get("topic", [])):
                continue
            if detect_revision(old, new):
                new["revision_of"] = old["memory_id"]
                revisions.append(
                    {
                        "memory_id": new["memory_id"],
                        "revision_of": old["memory_id"],
                    }
                )
                break
    return new_memories, revisions


def run_memory_pipeline(
    raw_content: str,
    timestamp: str,
    source: str,
    existing_memories: List[Dict[str, Any]],
    profile: str = "default",
) -> Dict[str, Any]:
    new_memories = extract_new_memories(raw_content, timestamp, source, profile=profile)
    new_memories, revisions = link_revisions(existing_memories, new_memories)
    combined = list(existing_memories) + list(new_memories)
    contradictions = group_contradictions(combined)
    result = {
        "new_memories": new_memories,
        "revisions": revisions,
        "contradictions": contradictions,
    }
    return result
