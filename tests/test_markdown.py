from xdigest.filtering import ScoredPost
from xdigest.markdown import post_to_markdown, write_digest
from xdigest.models import Author, Post


def _scored(pid="1", title=None):
    post = Post(
        id=pid,
        author=Author(username="alice", name="Alice"),
        text="Focus beats everything.",
        created_at="2026-01-01T00:00:00Z",
        url="https://x.com/alice/status/1",
        like_count=10,
        is_article=title is not None,
        title=title,
    )
    return ScoredPost(post=post, score=12.3, relevance=1, matched_keywords=["focus"])


def test_post_to_markdown_contains_key_fields():
    md = post_to_markdown(_scored())
    assert "Focus beats everything." in md
    assert "@alice" in md
    assert "Matched interests:** focus" in md


def test_write_digest_creates_files(tmp_path):
    summary = write_digest([_scored("1"), _scored("2", title="Deep work")], tmp_path)
    assert summary["count"] == 2
    assert summary["index"].exists()
    for path in summary["posts"]:
        assert path.exists()
    index_text = summary["index"].read_text()
    assert "Deep work" in index_text
    assert "posts/" in index_text
