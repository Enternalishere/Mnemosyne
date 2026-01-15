from datetime import datetime
from typing import List, Dict, Any, Tuple


def build_belief_graph(memories: List[Dict[str, Any]], contradictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    topic_nodes = {}
    memory_nodes = {}
    for m in memories:
        memory_nodes[m["memory_id"]] = {
            "id": m["memory_id"],
            "type": "memory",
            "created_at": m.get("created_at"),
            "memory_type": m.get("memory_type"),
            "confidence": m.get("confidence"),
            "topic": m.get("topic", []),
        }
        for t in m.get("topic", []):
            if t not in topic_nodes:
                topic_nodes[t] = {
                    "id": f"topic:{t}",
                    "type": "topic",
                    "label": t,
                }
            edges.append(
                {
                    "source": m["memory_id"],
                    "target": f"topic:{t}",
                    "type": "about",
                }
            )
        if m.get("revision_of"):
            edges.append(
                {
                    "source": m["memory_id"],
                    "target": m["revision_of"],
                    "type": "revises",
                }
            )
    for c in contradictions:
        mem_ids = [x["memory_id"] for x in c.get("conflicting_memories", [])]
        for i in range(len(mem_ids)):
            for j in range(i + 1, len(mem_ids)):
                edges.append(
                    {
                        "source": mem_ids[i],
                        "target": mem_ids[j],
                        "type": "contradicts",
                    }
                )
    nodes.extend(topic_nodes.values())
    nodes.extend(memory_nodes.values())
    return {"nodes": nodes, "edges": edges}


def build_timeline(memories: List[Dict[str, Any]], topic: str = "") -> List[Dict[str, Any]]:
    filtered = []
    for m in memories:
        if topic:
            topics = [str(t).lower() for t in m.get("topic", [])]
            if topic.lower() not in topics:
                continue
        created_at = m.get("created_at")
        if created_at is None:
            continue
        filtered.append(m)
    filtered.sort(key=lambda x: x.get("created_at"))
    return filtered

