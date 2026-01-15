import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

from mnemosyne_app import run_ingest, run_answer
from thinking_sessions import run_thinking_session
from memory_store import load_memories
from analytics import build_belief_graph, build_timeline


DEFAULT_STORE = "data/memories.json"


class MnemosyneHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length_header = self.headers.get("Content-Length")
        if length_header is None:
            self._send_json({"error": "Missing Content-Length header."}, status=400)
            return
        try:
            length = int(length_header)
        except ValueError:
            self._send_json({"error": "Invalid Content-Length header."}, status=400)
            return
        body_bytes = self.rfile.read(length)
        try:
            data = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON body."}, status=400)
            return

        if self.path == "/ingest":
            self._handle_ingest(data)
        elif self.path == "/answer":
            self._handle_answer(data)
        elif self.path == "/session":
            self._handle_session(data)
        elif self.path == "/graph":
            self._handle_graph(data)
        elif self.path == "/timeline":
            self._handle_timeline(data)
        else:
            self._send_json({"error": "Unknown endpoint."}, status=404)

    def _handle_ingest(self, data: Dict[str, Any]) -> None:
        text = data.get("text")
        source = data.get("source")
        timestamp = data.get("timestamp") or ""
        store_path = data.get("store") or DEFAULT_STORE
        profile = data.get("profile") or "default"
        if not text or not source:
            self._send_json({"error": "Fields 'text' and 'source' are required."}, status=400)
            return
        summary = run_ingest(text, source, timestamp, store_path, profile=profile)
        self._send_json(summary, status=200)

    def _handle_answer(self, data: Dict[str, Any]) -> None:
        question = data.get("question")
        store_path = data.get("store") or DEFAULT_STORE
        if not question:
            self._send_json({"error": "Field 'question' is required."}, status=400)
            return
        result = run_answer(question, store_path)
        self._send_json(result, status=200)

    def _handle_session(self, data: Dict[str, Any]) -> None:
        topic = data.get("topic")
        store_path = data.get("store") or DEFAULT_STORE
        start = data.get("start")
        end = data.get("end")
        if not topic:
            self._send_json({"error": "Field 'topic' is required."}, status=400)
            return
        result = run_thinking_session(topic, store_path, start_iso=start, end_iso=end)
        self._send_json(result, status=200)

    def _handle_graph(self, data: Dict[str, Any]) -> None:
        store_path = data.get("store") or DEFAULT_STORE
        memories = load_memories(store_path)
        contradictions = data.get("contradictions") or []
        graph = build_belief_graph(memories, contradictions)
        self._send_json(graph, status=200)

    def _handle_timeline(self, data: Dict[str, Any]) -> None:
        store_path = data.get("store") or DEFAULT_STORE
        topic = data.get("topic") or ""
        memories = load_memories(store_path)
        timeline = build_timeline(memories, topic=topic)
        self._send_json({"items": timeline}, status=200)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = HTTPServer((host, port), MnemosyneHandler)
    server.serve_forever()


if __name__ == "__main__":
    run_server()
