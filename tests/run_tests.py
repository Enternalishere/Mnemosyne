import os
import sys
from datetime import datetime, timedelta

root_dir = os.path.dirname(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from mnemosyne_engine import answer_query
from memory_pipeline import run_memory_pipeline
from memory_store import save_memories, load_memories, snapshot_memories
from mnemosyne_app import run_ingest, run_answer
from thinking_sessions import run_thinking_session
from analytics import build_belief_graph, build_timeline


def build_memory(
    memory_id: str,
    content: str,
    created_at: datetime,
    memory_type: str = "belief",
    confidence: float = 0.8,
    source: str = "note",
    topic=None,
    revision_of=None,
):
    if topic is None:
        topic = []
    return {
        "memory_id": memory_id,
        "content": content,
        "created_at": created_at.isoformat(),
        "memory_type": memory_type,
        "confidence": confidence,
        "source": source,
        "topic": topic,
        "revision_of": revision_of,
    }


def test_simple_present_answer():
    now = datetime.now()
    memories = [
        build_memory("m1", "You believed X about topic alpha.", now, topic=["alpha"])
    ]
    question = "What do I currently believe about alpha?"
    output = answer_query(memories, question)
    assert "You believed X about topic alpha." in output
    assert "No significant belief change detected." in output


def test_past_filtering():
    now = datetime.now()
    past = now - timedelta(days=10)
    memories = [
        build_memory("m1", "Earlier belief about beta.", past, topic=["beta"]),
        build_memory("m2", "Newer belief about beta.", now, topic=["beta"]),
    ]
    cutoff_date = (now - timedelta(days=5)).date().isoformat()
    question = f"What did I believe about beta as of {cutoff_date}?"
    output = answer_query(memories, question)
    assert "Earlier belief about beta." in output
    assert "Newer belief about beta." not in output


def test_revision_chain_detection():
    now = datetime.now()
    earlier = now - timedelta(days=3)
    memories = [
        build_memory("m1", "Initial view on gamma.", earlier, topic=["gamma"]),
        build_memory("m2", "Updated view on gamma.", now, topic=["gamma"], revision_of="m1"),
    ]
    question = "How has my thinking on gamma evolved?"
    output = answer_query(memories, question)
    assert "Initial view on gamma." in output
    assert "Updated view on gamma." in output
    assert "is revised by" in output


def test_no_relevant_memories():
    now = datetime.now()
    memories = [
        build_memory("m1", "Belief about delta.", now, topic=["delta"])
    ]
    question = "What do I think about epsilon?"
    output = answer_query(memories, question)
    assert "Belief about delta." in output


def test_empty_memories():
    question = "Any belief?"
    output = answer_query([], question)
    assert "I don’t have enough memory to answer this confidently." in output


def test_memory_pipeline_extraction():
    now = datetime.now().isoformat()
    raw = "I believe RAG is the future of personal AI. I decided to invest more time into it."
    result = run_memory_pipeline(raw, now, "note", [])
    new_memories = result["new_memories"]
    assert len(new_memories) == 2
    types = {m["memory_type"] for m in new_memories}
    assert "belief" in types
    assert "decision" in types


def test_memory_pipeline_revision_and_contradiction():
    ts1 = datetime.now().isoformat()
    ts2 = datetime.now().isoformat()
    existing = [
        {
            "memory_id": "m1",
            "content": "I believe RAG is the future of personal AI.",
            "created_at": ts1,
            "memory_type": "belief",
            "confidence": 0.9,
            "source": "note",
            "topic": ["rag", "ai"],
            "revision_of": None,
        }
    ]
    raw = "I no longer believe RAG is the complete future of personal AI."
    result = run_memory_pipeline(raw, ts2, "note", existing)
    new_memories = result["new_memories"]
    assert len(new_memories) == 1
    revision_links = result["revisions"]
    assert len(revision_links) == 1
    assert revision_links[0]["revision_of"] == "m1"
    contradictions = result["contradictions"]
    assert len(contradictions) >= 1


def test_memory_store_roundtrip(tmp_path=None):
    if tmp_path is None:
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, "temp_store.json")
    else:
        path = os.path.join(tmp_path, "store.json")
    now = datetime.now()
    memories = [
        build_memory("m1", "Belief about storage.", now, topic=["storage"]),
        build_memory("m2", "Another belief.", now, topic=["other"]),
    ]
    save_memories(path, memories)
    loaded = load_memories(path)
    assert len(loaded) == 2
    assert loaded[0]["content"] == "Belief about storage."


def test_snapshot_memories(tmp_path=None):
    if tmp_path is None:
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, "temp_store_snapshot.json")
        snapshot_dir = os.path.join(base_dir, "snapshots")
    else:
        path = os.path.join(tmp_path, "store_snapshot.json")
        snapshot_dir = os.path.join(tmp_path, "snapshots")
    now = datetime.now()
    memories = [
        build_memory("m1", "Belief for snapshot.", now, topic=["snap"]),
    ]
    save_memories(path, memories)
    snapshot_memories(path, snapshot_dir)
    files = os.listdir(snapshot_dir)
    assert files


def test_thinking_session(tmp_path=None):
    if tmp_path is None:
        base_dir = os.path.dirname(__file__)
        store_path = os.path.join(base_dir, "temp_session_store.json")
    else:
        store_path = os.path.join(tmp_path, "session_store.json")
    ts1 = datetime.now().isoformat()
    run_ingest("I believe RAG is the future of personal AI.", "note", ts1, store_path)
    session_result = run_thinking_session("rag", store_path)
    assert "Thinking session summary for topic" in session_result["summary_memory"]["content"]


def test_analytics_graph_and_timeline(tmp_path=None):
    now = datetime.now()
    memories = [
        build_memory("m1", "Belief about rag.", now, topic=["rag"]),
        build_memory("m2", "Updated belief about rag.", now, topic=["rag"], revision_of="m1"),
    ]
    contradictions = [
        {
            "topic": "rag",
            "conflicting_memories": [
                {"memory_id": "m1", "created_at": now.isoformat(), "content": "Belief about rag."},
                {"memory_id": "m2", "created_at": now.isoformat(), "content": "Updated belief about rag."},
            ],
            "status": "unresolved",
            "notes": "test",
        }
    ]
    graph = build_belief_graph(memories, contradictions)
    assert graph["nodes"]
    assert graph["edges"]
    timeline = build_timeline(memories, topic="rag")
    assert len(timeline) == 2


def test_app_ingest_and_answer(tmp_path=None):
    if tmp_path is None:
        base_dir = os.path.dirname(__file__)
        store_path = os.path.join(base_dir, "temp_app_store.json")
    else:
        store_path = os.path.join(tmp_path, "app_store.json")
    ts1 = datetime.now().isoformat()
    ingest_summary = run_ingest(
        "I believe RAG is the future of personal AI.",
        "note",
        ts1,
        store_path,
    )
    assert ingest_summary["total_memories"] >= 1
    answer_result = run_answer(
        "What do I currently believe about RAG?",
        store_path,
    )
    assert answer_result["has_memories"] is True
    assert "RAG" in answer_result["answer"]


def run_all():
    test_simple_present_answer()
    test_past_filtering()
    test_revision_chain_detection()
    test_no_relevant_memories()
    test_empty_memories()
    test_memory_pipeline_extraction()
    test_memory_pipeline_revision_and_contradiction()
    test_memory_store_roundtrip()
    test_app_ingest_and_answer()
    test_snapshot_memories()
    test_thinking_session()
    test_analytics_graph_and_timeline()
    print("All tests passed.")


if __name__ == "__main__":
    run_all()
