"""HTTP/SSE server primitives for SCMDB watcher."""

from __future__ import annotations

import json
import logging
import queue
import threading
import time

from flask import Flask, Response, request

SSE_HEARTBEAT_SEC = 15.0
SUBSCRIBER_QUEUE_MAXSIZE = 200


class EventBus:
    """Fan-out broadcaster for SSE subscribers."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subs: list[queue.Queue[str]] = []

    def subscribe(self) -> queue.Queue[str]:
        q: queue.Queue[str] = queue.Queue(maxsize=SUBSCRIBER_QUEUE_MAXSIZE)
        with self._lock:
            self._subs.append(q)
        return q

    def unsubscribe(self, q: queue.Queue[str]) -> None:
        with self._lock:
            try:
                self._subs.remove(q)
            except ValueError:
                pass

    def broadcast(self, event: dict) -> None:
        payload = json.dumps(event, separators=(",", ":"))
        with self._lock:
            subs = list(self._subs)
        for q in subs:
            try:
                q.put_nowait(payload)
            except queue.Full:
                logging.getLogger("scmdb-watcher").warning(
                    "Subscriber queue full, dropping event for one client"
                )


def build_app(state, bus: EventBus, allowed_origins: frozenset[str], version: str) -> Flask:
    app = Flask(__name__)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    @app.after_request
    def add_cors(response):  # type: ignore[no-untyped-def]
        origin = request.headers.get("Origin")
        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        return response

    @app.route("/ping")
    def ping():  # type: ignore[no-untyped-def]
        return {"status": "ok", "version": version}

    @app.route("/state")
    def get_state():  # type: ignore[no-untyped-def]
        return {"active": state.snapshot_active()}

    @app.route("/events")
    def events():  # type: ignore[no-untyped-def]
        q = bus.subscribe()
        snapshot = {"type": "state_snapshot", "active": state.snapshot_active()}

        def stream():
            try:
                yield f"data: {json.dumps(snapshot, separators=(',', ':'))}\n\n"
                last_heartbeat = time.time()
                while True:
                    timeout = max(0.0, SSE_HEARTBEAT_SEC - (time.time() - last_heartbeat))
                    try:
                        payload = q.get(timeout=timeout)
                        yield f"data: {payload}\n\n"
                    except queue.Empty:
                        yield ": heartbeat\n\n"
                        last_heartbeat = time.time()
            finally:
                bus.unsubscribe(q)

        return Response(
            stream(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    return app
