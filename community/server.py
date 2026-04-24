"""Stdlib HTTP server for Styio community forum and decision flows."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

try:
    from community.storage import (
        ConflictError,
        JsonRecordStore,
        RecordNotFoundError,
        StorageError,
        ValidationError,
        build_dispatch_payload,
    )
    from community.forum import ForumStore
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from community.storage import (
        ConflictError,
        JsonRecordStore,
        RecordNotFoundError,
        StorageError,
        ValidationError,
        build_dispatch_payload,
    )
    from community.forum import ForumStore


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"


def _optional_module(name: str) -> Any | None:
    try:
        return __import__(name, fromlist=["*"])
    except Exception:
        return None


STATE_MACHINE = _optional_module("community.state_machine")
ADAPTERS = _optional_module("community.adapters")


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _dispatch_to_adapter(payload: dict[str, Any]) -> dict[str, Any]:
    if ADAPTERS is not None:
        try:
            adapter_factory = getattr(ADAPTERS, "adapter_for_repository", None)
            if callable(adapter_factory):
                adapter = adapter_factory(str(payload.get("repository", "styio")))
                request = adapter.wrap_event(payload)
                to_mapping = getattr(request, "to_mapping", None)
                return {
                    "adapter": f"community.adapters.{adapter.__class__.__name__}",
                    "accepted": True,
                    "repository_request": _json_safe(to_mapping() if callable(to_mapping) else request),
                }

            for function_name in ("dispatch_decision", "dispatch", "send"):
                dispatcher = getattr(ADAPTERS, function_name, None)
                if callable(dispatcher):
                    return {
                        "adapter": f"community.adapters.{function_name}",
                        "accepted": True,
                        "response": _json_safe(dispatcher(payload)),
                    }
        except Exception as error:
            return {
                "adapter": "community.adapters",
                "accepted": False,
                "error": str(error),
            }

    return {
        "adapter": "fallback",
        "accepted": True,
        "message": "No community.adapters dispatcher was available; payload was recorded locally.",
    }


class CommunityRequestHandler(BaseHTTPRequestHandler):
    server_version = "StyioCommunity/0.2"

    @property
    def store(self) -> JsonRecordStore:
        return self.server.store  # type: ignore[attr-defined]

    @property
    def forum_store(self) -> ForumStore:
        return self.server.forum_store  # type: ignore[attr-defined]

    @property
    def web_root(self) -> Path:
        return self.server.web_root  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/records":
            self._send_json({"records": self.store.list_records()})
            return
        if path == "/api/forum/posts":
            self._send_json({"posts": self.forum_store.list_posts()})
            return
        forum_post_id = self._parse_forum_post_get(path)
        if forum_post_id is not None:
            try:
                self._send_json({"post": self.forum_store.get_post(forum_post_id)})
            except RecordNotFoundError as error:
                self._send_error(HTTPStatus.NOT_FOUND, str(error))
            return
        self._serve_static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/records":
                body = self._read_json_body()
                record = self.store.create_record(
                    kind=body.get("kind"),
                    title=body.get("title"),
                    summary=body.get("summary"),
                    proposal=body.get("proposal", {}),
                    source_repository=body.get("source_repository", "styio-community"),
                    target_repository=body.get("target_repository") or body.get("repository"),
                )
                self._send_json({"record": record}, HTTPStatus.CREATED)
                return

            if path == "/api/records/demo":
                self._send_json({"record": self.store.create_demo_syntax_change()}, HTTPStatus.CREATED)
                return

            if path == "/api/records/demo-ide-gap":
                self._send_json({"record": self.store.create_demo_ide_gap()}, HTTPStatus.CREATED)
                return

            if path == "/api/forum/posts":
                body = self._read_json_body()
                post = self.forum_store.create_post(
                    title=body.get("title"),
                    body=body.get("body"),
                    author=body.get("author", "Anonymous"),
                    category=body.get("category", "general"),
                    tags=body.get("tags", []),
                )
                self._send_json({"post": post}, HTTPStatus.CREATED)
                return

            if path == "/api/forum/posts/demo":
                self._send_json({"posts": self.forum_store.seed_demo_posts()}, HTTPStatus.CREATED)
                return

            forum_action = self._parse_forum_action(path)
            if forum_action is not None:
                post_id, action = forum_action
                body = self._read_json_body()
                if action == "comments":
                    post = self.forum_store.add_comment(
                        post_id,
                        author=body.get("author", "Anonymous"),
                        body=body.get("body"),
                    )
                    self._send_json({"post": post}, HTTPStatus.CREATED)
                    return
                if action == "react":
                    self._send_json({"post": self.forum_store.react_to_post(post_id)})
                    return
                self._send_error(HTTPStatus.NOT_FOUND, "unknown forum action")
                return

            record_id, action = self._parse_record_action(path)
            body = self._read_json_body()
            if action in {"approve", "reject"}:
                decision = "approved" if action == "approve" else "rejected"
                record = self.store.decide_record(record_id, decision, str(body.get("opinion", "")))
                self._send_json({"record": record})
                return

            if action == "dispatch":
                record = self.store.get_record(record_id)
                payload = build_dispatch_payload(record)
                adapter_result = _dispatch_to_adapter(payload)
                dispatched = self.store.dispatch_record(record_id, adapter_result=adapter_result)
                self._send_json({"record": dispatched, "dispatch": dispatched["dispatch"]})
                return

            self._send_error(HTTPStatus.NOT_FOUND, "unknown API action")
        except RecordNotFoundError as error:
            self._send_error(HTTPStatus.NOT_FOUND, str(error))
        except ValidationError as error:
            self._send_error(HTTPStatus.BAD_REQUEST, str(error))
        except ConflictError as error:
            self._send_error(HTTPStatus.CONFLICT, str(error))
        except StorageError as error:
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))
        except json.JSONDecodeError:
            self._send_error(HTTPStatus.BAD_REQUEST, "request body must be valid JSON")

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def _parse_record_action(self, path: str) -> tuple[str, str]:
        parts = [unquote(part) for part in path.split("/") if part]
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "records":
            return parts[2], parts[3]
        raise RecordNotFoundError("API route not found")

    def _parse_forum_action(self, path: str) -> tuple[str, str] | None:
        parts = [unquote(part) for part in path.split("/") if part]
        if len(parts) == 5 and parts[:3] == ["api", "forum", "posts"]:
            return parts[3], parts[4]
        return None

    def _parse_forum_post_get(self, path: str) -> str | None:
        parts = [unquote(part) for part in path.split("/") if part]
        if len(parts) == 4 and parts[:3] == ["api", "forum", "posts"]:
            return parts[3]
        return None

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValidationError("request body must be a JSON object")
        return parsed

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        self._send_json({"error": message, "status": status.value}, status)

    def _serve_static(self, path: str) -> None:
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        if path.startswith("/posts/"):
            relative = "post.html"
        web_root = self.web_root
        candidate = (web_root / relative).resolve()
        if candidate.is_dir():
            candidate = (candidate / "index.html").resolve()
        if web_root not in candidate.parents and candidate != web_root:
            self._send_error(HTTPStatus.FORBIDDEN, "forbidden")
            return
        if not candidate.is_file():
            self._send_error(HTTPStatus.NOT_FOUND, "not found")
            return

        content = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if candidate.suffix in {".html", ".css", ".js"}:
            content_type = f"{content_type}; charset=utf-8"

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def make_server(
    host: str,
    port: int,
    store: JsonRecordStore,
    web_root: str | Path = WEB_ROOT,
    forum_store: ForumStore | None = None,
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), CommunityRequestHandler)
    server.store = store  # type: ignore[attr-defined]
    server.forum_store = forum_store or ForumStore()  # type: ignore[attr-defined]
    server.web_root = Path(web_root).resolve()  # type: ignore[attr-defined]
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Styio community decision server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--data", default=None, help="Path to the JSON record store.")
    parser.add_argument("--data-dir", default=None, help="Directory that stores records.json.")
    parser.add_argument("--web-root", default=str(WEB_ROOT), help="Directory for static web files.")
    args = parser.parse_args(argv)

    if args.data and args.data_dir:
        parser.error("--data and --data-dir are mutually exclusive")

    data_path = Path(args.data_dir) / "records.json" if args.data_dir else args.data
    forum_path = Path(args.data_dir) / "forum.json" if args.data_dir else None
    store = JsonRecordStore(data_path)
    forum_store = ForumStore(forum_path)
    if STATE_MACHINE is None:
        print("community.state_machine not found; using storage-level state transitions.", file=sys.stderr)
    if ADAPTERS is None:
        print("community.adapters not found; dispatch will record a fallback adapter result.", file=sys.stderr)

    httpd = make_server(args.host, args.port, store, args.web_root, forum_store)
    print(
        f"Serving Styio community forum at http://{args.host}:{args.port}/",
        file=sys.stderr,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.", file=sys.stderr)
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
