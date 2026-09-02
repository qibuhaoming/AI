import pytest

from app.analyzer import analyze_text


def test_positive_sentiment():
    result = analyze_text("I love this, it is great and amazing!")
    assert result.sentiment == "positive"
    assert result.sentiment_score > 0


def test_negative_sentiment():
    result = analyze_text("This is terrible and awful, I hate it.")
    assert result.sentiment == "negative"
    assert result.sentiment_score < 0


def test_neutral_sentiment():
    result = analyze_text("The box is on the table.")
    assert result.sentiment == "neutral"
    assert result.sentiment_score == 0


def test_counts_and_keywords():
    result = analyze_text("Cats chase cats. Dogs chase cats too!")
    assert result.word_count == 7
    assert result.sentence_count == 2
    assert "cats" in result.keywords


def test_reading_time_is_non_negative():
    result = analyze_text("word " * 200)
    assert result.reading_time_seconds == 60


def test_empty_text_raises():
    with pytest.raises(ValueError):
        analyze_text("   ")
