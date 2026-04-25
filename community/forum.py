"""JSON-backed storage for the Styio community forum."""

from __future__ import annotations

import copy
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .storage import RecordNotFoundError, ValidationError


Clock = Callable[[], str]
IdFactory = Callable[[], str]

ALLOWED_CATEGORIES = {
    "announcements",
    "syntax",
    "ide",
    "showcase",
    "help",
    "general",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def default_forum_path() -> Path:
    configured = os.environ.get("STYIO_COMMUNITY_FORUM_STORE")
    if configured:
        return Path(configured)
    return Path.cwd() / ".styio-community" / "forum.json"


class ForumStore:
    def __init__(
        self,
        path: str | os.PathLike[str] | None = None,
        *,
        clock: Clock = utc_now,
        id_factory: IdFactory | None = None,
    ) -> None:
        self.path = Path(path) if path is not None else default_forum_path()
        self._clock = clock
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))

    def list_posts(self) -> list[dict[str, Any]]:
        posts = self._read_posts()
        return [copy.deepcopy(post) for post in sorted(posts, key=_post_sort_key, reverse=True)]

    def get_post(self, post_id: str) -> dict[str, Any]:
        for post in self._read_posts():
            if post["id"] == post_id:
                return copy.deepcopy(post)
        raise RecordNotFoundError(f"post not found: {post_id}")

    def create_post(
        self,
        *,
        title: str,
        body: str,
        author: str,
        category: str = "general",
        tags: list[str] | tuple[str, ...] | None = None,
        pinned: bool = False,
    ) -> dict[str, Any]:
        title = _require_text(title, "title", max_length=120)
        body = _require_text(body, "body", max_length=4000)
        author = _require_text(author, "author", max_length=48)
        category = _normalize_category(category)
        tags = _normalize_tags(tags or [])

        posts = self._read_posts()
        now = self._clock()
        post = {
            "id": self._id_factory(),
            "title": title,
            "body": body,
            "author": author,
            "category": category,
            "tags": tags,
            "pinned": bool(pinned),
            "status": "open",
            "reactions": 0,
            "views": 1,
            "created_at": now,
            "updated_at": now,
            "comments": [],
        }
        posts.append(post)
        self._write_posts(posts)
        return copy.deepcopy(post)

    def add_comment(self, post_id: str, *, author: str, body: str) -> dict[str, Any]:
        author = _require_text(author, "author", max_length=48)
        body = _require_text(body, "body", max_length=2000)

        posts = self._read_posts()
        post = self._find_mutable(posts, post_id)
        now = self._clock()
        comment = {
            "id": self._id_factory(),
            "author": author,
            "body": body,
            "created_at": now,
        }
        post.setdefault("comments", []).append(comment)
        post["updated_at"] = now
        self._write_posts(posts)
        return copy.deepcopy(post)

    def react_to_post(self, post_id: str) -> dict[str, Any]:
        posts = self._read_posts()
        post = self._find_mutable(posts, post_id)
        post["reactions"] = int(post.get("reactions", 0)) + 1
        post["updated_at"] = self._clock()
        self._write_posts(posts)
        return copy.deepcopy(post)

    def seed_demo_posts(self) -> list[dict[str, Any]]:
        if self._read_posts():
            return self.list_posts()

        seed = [
            {
                "title": "返回管道语法的例子应该放在哪里？",
                "body": "我在整理 `@stdin := { <| [>_] }` 的示例，希望把最小示例、IDE 高亮截图和适配器注意事项放到同一条讨论里，方便后续决策记录引用。",
                "author": "Mika",
                "category": "syntax",
                "tags": ["return-pipe", "examples"],
                "pinned": True,
            },
            {
                "title": "Styio View 诊断面板需要哪些社区反馈？",
                "body": "目前缺少一组真实使用者的诊断用语反馈。请贴出你遇到的错误提示、期望解释和复现场景，我们会把高频问题收敛成上游适配请求。",
                "author": "Kai",
                "category": "ide",
                "tags": ["diagnostics", "styio-view"],
                "pinned": False,
            },
            {
                "title": "展示你的第一个 Styio 小工具",
                "body": "把你最近写的小工具、语法片段或插件草图发出来。帖子里最好包含目标、代码片段和你希望社区帮忙看的地方。",
                "author": "Luna",
                "category": "showcase",
                "tags": ["showcase", "plugin"],
                "pinned": False,
            },
        ]

        posts = [
            self.create_post(
                title=item["title"],
                body=item["body"],
                author=item["author"],
                category=item["category"],
                tags=item["tags"],
                pinned=bool(item["pinned"]),
            )
            for item in seed
        ]
        return posts

    def _find_mutable(self, posts: list[dict[str, Any]], post_id: str) -> dict[str, Any]:
        for post in posts:
            if post["id"] == post_id:
                return post
        raise RecordNotFoundError(f"post not found: {post_id}")

    def _read_posts(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        posts = payload.get("posts")
        if not isinstance(posts, list):
            raise ValidationError("forum storage file must contain a posts list")
        return posts

    def _write_posts(self, posts: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"posts": posts}
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            delete=False,
        ) as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            temp_name = handle.name
        os.replace(temp_name, self.path)


def _post_sort_key(post: Mapping[str, Any]) -> tuple[int, str]:
    return (1 if post.get("pinned") else 0, str(post.get("updated_at") or post.get("created_at") or ""))


def _require_text(value: Any, field_name: str, *, max_length: int) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValidationError(f"{field_name} must not be empty")
    if len(value) > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters")
    return value


def _normalize_category(value: Any) -> str:
    category = _require_text(value, "category", max_length=32).lower()
    if category not in ALLOWED_CATEGORIES:
        raise ValidationError(f"category must be one of: {', '.join(sorted(ALLOWED_CATEGORIES))}")
    return category


def _normalize_tags(values: list[str] | tuple[str, ...]) -> list[str]:
    normalized: list[str] = []
    for value in values[:5]:
        tag = _require_text(value, "tag", max_length=24).lower().replace(" ", "-")
        if tag not in normalized:
            normalized.append(tag)
    return normalized
