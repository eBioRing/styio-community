import tempfile
import unittest
from pathlib import Path

from community.forum import ForumStore
from community.storage import RecordNotFoundError, ValidationError


class ForumStoreTest(unittest.TestCase):
    def make_store(self, path: Path) -> ForumStore:
        times = iter(
            [
                "2026-04-24T00:00:00Z",
                "2026-04-24T00:01:00Z",
                "2026-04-24T00:02:00Z",
                "2026-04-24T00:03:00Z",
            ]
        )
        ids = iter(["post-1", "post-2", "comment-1", "reaction-1"])
        return ForumStore(path, clock=lambda: next(times), id_factory=lambda: next(ids))

    def test_create_post_persists_forum_thread(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "forum.json"
            post = self.make_store(path).create_post(
                title="Share your first Styio snippet",
                body="Post the example and the feedback you want.",
                author="Mika",
                category="showcase",
                tags=["snippet", "Feedback"],
            )

            self.assertEqual(post["id"], "post-1")
            self.assertEqual(post["category"], "showcase")
            self.assertEqual(post["tags"], ["snippet", "feedback"])
            self.assertEqual(post["reactions"], 0)
            self.assertEqual(post["comments"], [])

            reloaded = ForumStore(path).list_posts()
            self.assertEqual(len(reloaded), 1)
            self.assertEqual(reloaded[0]["title"], post["title"])

    def test_post_validation_rejects_empty_or_unknown_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self.make_store(Path(tmpdir) / "forum.json")

            with self.assertRaises(ValidationError):
                store.create_post(title=" ", body="Body", author="Mika")

            with self.assertRaises(ValidationError):
                store.create_post(title="Title", body="Body", author="Mika", category="unknown")

    def test_comments_and_reactions_update_post(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = self.make_store(Path(tmpdir) / "forum.json")
            store.create_post(title="Question", body="How should this work?", author="Kai")

            commented = store.add_comment("post-1", author="Luna", body="Here is a concrete example.")
            self.assertEqual(commented["comments"][0]["id"], "post-2")
            self.assertEqual(commented["comments"][0]["author"], "Luna")

            reacted = store.react_to_post("post-1")
            self.assertEqual(reacted["reactions"], 1)

            with self.assertRaises(RecordNotFoundError):
                store.add_comment("missing", author="Luna", body="No target.")

    def test_seed_demo_posts_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "forum.json"
            ids = iter(["post-1", "post-2", "post-3"])
            times = iter(
                [
                    "2026-04-24T00:00:00Z",
                    "2026-04-24T00:01:00Z",
                    "2026-04-24T00:02:00Z",
                ]
            )
            store = ForumStore(path, clock=lambda: next(times), id_factory=lambda: next(ids))

            posts = store.seed_demo_posts()
            again = store.seed_demo_posts()

            self.assertEqual(len(posts), 3)
            self.assertEqual(len(again), 3)
            self.assertTrue(any(post["pinned"] for post in again))


if __name__ == "__main__":
    unittest.main()
