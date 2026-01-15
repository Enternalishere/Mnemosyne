from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import re


@dataclass
class Memory:
    memory_id: str
    content: str
    created_at: datetime
    memory_type: str
    confidence: float
    source: str
    topic: List[str]
    revision_of: Optional[str]


def parse_memory(raw: Dict[str, Any]) -> Memory:
    created_at = datetime.fromisoformat(raw["created_at"])
    topic = raw.get("topic")
    if topic is None:
        topic = []
    return Memory(
        memory_id=raw["memory_id"],
        content=raw["content"],
        created_at=created_at,
        memory_type=raw["memory_type"],
        confidence=float(raw["confidence"]),
        source=raw["source"],
        topic=list(topic),
        revision_of=raw.get("revision_of"),
    )


def parse_memories(raw_list: List[Dict[str, Any]]) -> List[Memory]:
    return [parse_memory(raw) for raw in raw_list]


def detect_time_mode(question: str) -> Tuple[str, Optional[Tuple[datetime, Optional[datetime]]]]:
    lower = question.lower()
    pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    dates = pattern.findall(question)
    parsed_dates: List[datetime] = []
    for d in dates:
        try:
            parsed_dates.append(datetime.fromisoformat(d))
        except ValueError:
            continue
    if "from" in lower and "to" in lower and len(parsed_dates) >= 2:
        start = parsed_dates[0]
        end = parsed_dates[1]
        return "range", (start, end)
    if any(phrase in lower for phrase in ["as of", "by ", "before "]):
        if parsed_dates:
            return "past", (parsed_dates[0], None)
        return "past_ambiguous", None
    return "present", None


def filter_by_time(memories: List[Memory], mode: str, payload: Optional[Tuple[datetime, Optional[datetime]]]) -> List[Memory]:
    if mode == "past" and payload is not None:
        cutoff = payload[0]
        return [m for m in memories if m.created_at <= cutoff]
    if mode == "range" and payload is not None:
        start, end = payload
        if end is None:
            return [m for m in memories if m.created_at >= start]
        return [m for m in memories if m.created_at >= start and m.created_at <= end]
    return list(memories)


def select_relevant_memories(memories: List[Memory], question: str) -> List[Memory]:
    lower = question.lower()
    selected: List[Memory] = []
    for m in memories:
        topics = [t.lower() for t in m.topic]
        if any(t in lower for t in topics):
            selected.append(m)
    if not selected:
        selected = list(memories)
    return selected


def build_revision_chains(memories: List[Memory]) -> Dict[str, List[Memory]]:
    by_id: Dict[str, Memory] = {m.memory_id: m for m in memories}
    chains: Dict[str, List[Memory]] = {}
    for m in memories:
        root = m.memory_id
        current = m.revision_of
        while current is not None and current in by_id:
            root = current
            current = by_id[current].revision_of
        if root not in chains:
            chains[root] = []
        chains[root].append(m)
    for root, chain in chains.items():
        chain.sort(key=lambda m: m.created_at)
    return chains


def format_answer_section(selected: List[Memory], mode: str, ambiguous_time: bool) -> str:
    if not selected:
        return "I don’t have enough memory to answer this confidently."
    lines: List[str] = []
    if mode == "past":
        lines.append("Answer is based on memories available up to the requested time.")
    elif mode == "range":
        lines.append("Answer is based on memories within the requested time range.")
    elif mode == "past_ambiguous":
        lines.append("Time reference in the question is ambiguous; using all available memories.")
        lines.append("Clarifying question: Which exact date or time boundary should be applied?")
    else:
        lines.append("Answer is based on the latest available relevant memories.")
    for m in selected:
        lines.append(f"- [{m.created_at.isoformat()}] {m.content}")
    return "\n".join(lines)


def format_belief_evolution_section(selected: List[Memory]) -> str:
    if not selected:
        return "No significant belief change detected."
    chains = build_revision_chains(selected)
    descriptive_lines: List[str] = []
    for root, chain in chains.items():
        if len(chain) < 2:
            continue
        first = chain[0]
        last = chain[-1]
        topics = ", ".join(last.topic) if last.topic else "unspecified topics"
        descriptive_lines.append(
            f"For {topics}, memory {first.memory_id} ({first.created_at.isoformat()}) "
            f"is revised by {last.memory_id} ({last.created_at.isoformat()})."
        )
    if not descriptive_lines:
        return "No significant belief change detected."
    return "\n".join(descriptive_lines)


def format_memories_used_section(selected: List[Memory], mode: str) -> str:
    if not selected:
        return "- None | N/A | N/A | No memory context was sufficient to answer."
    lines: List[str] = []
    time_reason = "Time-filtered relevant memory" if mode in ["past", "past_ambiguous", "range"] else "Relevant memory"
    for m in selected:
        reason = time_reason
        if m.topic:
            reason += f" for topics {', '.join(m.topic)}"
        lines.append(
            f"- {m.memory_id} | {m.created_at.isoformat()} | {m.confidence:.2f} | {reason}"
        )
    return "\n".join(lines)


def format_confidence_note(selected: List[Memory]) -> str:
    if not selected:
        return (
            "Confidence is low. No relevant memories were found for the question. "
            "Additional, more specific memories would be required."
        )
    avg_conf = sum(m.confidence for m in selected) / len(selected)
    if avg_conf >= 0.75:
        level = "high"
    elif avg_conf >= 0.4:
        level = "moderate"
    else:
        level = "low"
    return (
        f"Confidence is {level}. This reflects the average confidence value of the "
        f"selected memories ({avg_conf:.2f}) and their direct relevance to the question."
    )


def answer_query(raw_memories: List[Dict[str, Any]], question: str) -> str:
    memories = parse_memories(raw_memories)
    mode, payload = detect_time_mode(question)
    time_filtered = filter_by_time(memories, mode, payload)
    selected = select_relevant_memories(time_filtered, question)
    answer_section = format_answer_section(selected, mode, mode == "past_ambiguous")
    belief_evolution_section = format_belief_evolution_section(selected)
    memories_used_section = format_memories_used_section(selected, mode)
    confidence_note = format_confidence_note(selected)
    parts = [
        "---",
        "ANSWER:",
        answer_section,
        "",
        "BELIEF EVOLUTION:",
        belief_evolution_section,
        "",
        "MEMORIES USED:",
        memories_used_section,
        "",
        "CONFIDENCE NOTE:",
        confidence_note,
        "---",
    ]
    return "\n".join(parts)

