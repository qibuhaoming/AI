import json
from pathlib import Path

import pytest

from xdigest.filtering import InterestProfile, score_post
from xdigest.sources.x_syndication import (
    SyndicationError,
    _syndication_token,
    extract_tweet_id,
    parse_syndication,
)

FIXTURE = Path(__file__).parent / "data" / "syndication_article.json"


def test_extract_tweet_id():
    url = "https://x.com/qihang_zeng6688/status/2082293843353821306"
    assert extract_tweet_id(url) == "2082293843353821306"
    assert extract_tweet_id("2082293843353821306") == "2082293843353821306"
    with pytest.raises(SyndicationError):
        extract_tweet_id("https://x.com/qihang_zeng6688")


def test_syndication_token_is_deterministic_string():
    token = _syndication_token("2082293843353821306")
    assert isinstance(token, str)
    assert token
    assert "." not in token


def test_parse_article_folds_title_into_text():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    post = parse_syndication(payload)
    assert post.author.username == "qihang_zeng6688"
    assert post.is_article is True
    assert post.title and "微信贴图号" in post.title
    # The article headline is folded into the searchable text.
    assert "微信贴图号" in post.text
    assert post.like_count == 690
    assert post.url.endswith("/status/2082293843353821306")


def test_keyword_matches_article_content():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    post = parse_syndication(payload)
    scored = score_post(post, InterestProfile(keywords=["微信贴图号"]))
    assert scored.relevance == 1
    assert "微信贴图号" in scored.matched_keywords
