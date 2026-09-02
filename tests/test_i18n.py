"""Tests for Chinese (CJK) language support."""

from app.analyzer import analyze_text
from xdigest.filtering import InterestProfile, score_post
from xdigest.models import Author, Post
from xdigest.textutil import meaningful_tokens, tokenize, top_keywords


def test_tokenize_chinese():
    tokens = tokenize("我喜欢写作和学习")
    # jieba segments into multi-char words; stop words like 我/和/的 may appear.
    assert "喜欢" in tokens
    assert "写作" in tokens
    assert "学习" in tokens


def test_meaningful_tokens_drops_chinese_stopwords():
    tokens = meaningful_tokens("我们的目标是持续学习和写作")
    assert "学习" in tokens
    assert "写作" in tokens
    assert "我们" not in tokens  # stop word
    assert "的" not in tokens


def test_top_keywords_chinese():
    text = "学习 学习 写作 写作 写作 专注"
    kws = dict(top_keywords(text))
    assert kws["写作"] == 3
    assert kws["学习"] == 2


def test_chinese_keyword_matching():
    post = Post(
        id="1",
        author=Author(username="u"),
        text="坚持写作是最好的学习方法",
        created_at="2026-01-01T00:00:00Z",
        like_count=100,
    )
    scored = score_post(post, InterestProfile(keywords=["写作", "学习"]))
    assert scored.relevance == 2
    assert set(scored.matched_keywords) == {"写作", "学习"}


def test_chinese_sentiment_positive():
    result = analyze_text("这个产品非常优秀，我很喜欢，用起来很高效！")
    assert result.sentiment == "positive"
    assert result.sentiment_score > 0
    assert "产品" in result.keywords or "高效" in result.keywords


def test_chinese_sentiment_negative():
    result = analyze_text("这个体验太糟糕了，经常崩溃，让人失望。")
    assert result.sentiment == "negative"
    assert result.sentiment_score < 0


def _zh_scored(text, pid, likes=200):
    post = Post(
        id=pid,
        author=Author(username=f"u{pid}", name="作者"),
        text=text,
        created_at="2026-01-01T00:00:00Z",
        like_count=likes,
    )
    from xdigest.filtering import ScoredPost

    return ScoredPost(post=post, score=float(likes), relevance=1, matched_keywords=[])


def test_methodology_auto_detects_chinese():
    from xdigest.methodology import build_methodology

    posts = [
        _zh_scored("坚持写作和学习，写作让思考更清晰", "1"),
        _zh_scored("专注写作，每周学习复盘", "2"),
    ]
    md = build_methodology(posts, lang="auto")
    assert "关键主题" in md
    assert "行动计划" in md
    assert "亮点" in md


def test_methodology_force_english_on_chinese():
    from xdigest.methodology import build_methodology

    posts = [_zh_scored("写作与学习", "1"), _zh_scored("写作和专注", "2")]
    md = build_methodology(posts, lang="en")
    assert "Key themes" in md
    assert "Action plan" in md


def test_markdown_chinese_labels():
    from xdigest.markdown import post_to_markdown

    md = post_to_markdown(_zh_scored("坚持写作", "1"), lang="zh")
    assert "作者" in md
    assert "互动" in md


def test_detect_lang():
    from xdigest.textutil import detect_lang

    assert detect_lang("这是一段中文文本内容") == "zh"
    assert detect_lang("this is english text") == "en"
