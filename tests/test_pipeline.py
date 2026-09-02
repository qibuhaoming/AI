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

    assert result.fetched == 10
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
