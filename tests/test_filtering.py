from xdigest.filtering import InterestProfile, score_post, select_interesting
from xdigest.models import Author, Post


def _post(text, likes=0, article=False, pid="1"):
    return Post(
        id=pid,
        author=Author(username="u", name="U"),
        text=text,
        created_at="2026-01-01T00:00:00Z",
        like_count=likes,
        is_article=article,
    )


def test_score_rewards_keyword_matches():
    profile = InterestProfile(keywords=["focus", "writing"])
    matched = score_post(_post("focus and writing matter"), profile)
    unmatched = score_post(_post("random unrelated content"), profile)
    assert matched.relevance == 2
    assert matched.score > unmatched.score


def test_word_boundary_matching():
    profile = InterestProfile(keywords=["ai"])
    # "brain" contains "ai" but should not match on a word boundary.
    assert score_post(_post("use your brain"), profile).relevance == 0
    assert score_post(_post("ai is useful"), profile).relevance == 1


def test_select_drops_irrelevant_when_interests_given():
    posts = [
        _post("focus is a strategy", likes=100, pid="1"),
        _post("cat pictures only", likes=5, pid="2"),
    ]
    profile = InterestProfile(keywords=["focus"])
    selected = select_interesting(posts, profile)
    assert [sp.post.id for sp in selected] == ["1"]


def test_articles_always_included():
    posts = [
        _post("unrelated long form", likes=1, article=True, pid="9"),
    ]
    profile = InterestProfile(keywords=["focus"], min_engagement=1000)
    selected = select_interesting(posts, profile)
    assert [sp.post.id for sp in selected] == ["9"]
