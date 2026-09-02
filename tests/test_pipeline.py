from xdigest.filtering import InterestProfile
from xdigest.pipeline import run_pipeline
from xdigest.sources.fixture import FixtureSource


def test_end_to_end_with_fixture(tmp_path):
    source = FixtureSource()  # bundled sample_timeline.json
    profile = InterestProfile(
        keywords=["focus", "writing", "productivity", "learning", "leverage"],
        min_engagement=100,
    )
    result = run_pipeline(source, profile, tmp_path)

    assert result.fetched == 14
    assert len(result.selected) > 0
    # The low-engagement meme and off-topic ramen post should be filtered out.
    selected_ids = {sp.post.id for sp in result.selected}
    assert "1006" not in selected_ids  # meme
    assert "1009" not in selected_ids  # ramen

    assert result.index_path.exists()
    assert result.methodology_path.exists()
    assert len(result.post_paths) == len(result.selected)

    methodology = result.methodology_path.read_text()
    assert "# Methodology" in methodology


def test_end_to_end_with_chinese_interests(tmp_path):
    source = FixtureSource()
    profile = InterestProfile(
        keywords=["写作", "专注", "学习", "深度工作"],
        min_engagement=100,
    )
    result = run_pipeline(source, profile, tmp_path)

    selected_ids = {sp.post.id for sp in result.selected}
    # Chinese posts about writing/focus/learning should be selected.
    assert "1011" in selected_ids
    assert "1012" in selected_ids
    # The off-topic hot-pot post should be filtered out.
    assert "1014" not in selected_ids

    # Matched Chinese keywords should be recorded on at least one post.
    all_matched = {kw for sp in result.selected for kw in sp.matched_keywords}
    assert all_matched & {"写作", "专注", "学习", "深度工作"}
