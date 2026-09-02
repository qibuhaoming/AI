"""Command-line interface for xdigest.

Examples
--------
Run entirely offline against the bundled sample timeline::

    python -m xdigest run --source fixture --out output \
        --interests focus,writing,productivity,learning

Run against your real X following timeline (requires X_BEARER_TOKEN)::

    python -m xdigest run --source x --out output --interests ai,startups
"""

from __future__ import annotations

import argparse
import sys

from xdigest.filtering import InterestProfile
from xdigest.pipeline import run_pipeline
from xdigest.sources.base import PostSource
from xdigest.sources.fixture import FixtureSource


def _build_source(name: str, fixture_path: str | None) -> PostSource:
    if name == "fixture":
        return FixtureSource(fixture_path)
    if name == "x":
        # Imported lazily so the fixture path never requires httpx/credentials.
        from xdigest.sources.x_api import XApiSource

        return XApiSource()
    raise ValueError(f"Unknown source: {name!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xdigest", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the digest pipeline")
    run.add_argument("--source", choices=["fixture", "x"], default="fixture")
    run.add_argument("--fixture-path", default=None, help="Path to a fixture JSON")
    run.add_argument("--out", default="output", help="Output directory")
    run.add_argument(
        "--interests",
        default="",
        help="Comma-separated interest keywords",
    )
    run.add_argument("--min-engagement", type=int, default=0)
    run.add_argument("--fetch-limit", type=int, default=100)
    run.add_argument("--select-limit", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "run":
        interests = [k.strip() for k in args.interests.split(",") if k.strip()]
        profile = InterestProfile(
            keywords=interests,
            min_engagement=args.min_engagement,
        )
        try:
            source = _build_source(args.source, args.fixture_path)
        except Exception as exc:  # noqa: BLE001 - surface a friendly message
            print(f"error: {exc}", file=sys.stderr)
            return 2

        result = run_pipeline(
            source,
            profile,
            args.out,
            fetch_limit=args.fetch_limit,
            select_limit=args.select_limit,
        )

        print(f"Fetched {result.fetched} posts from source '{args.source}'.")
        print(f"Selected {len(result.selected)} interesting posts.")
        print(f"Wrote index:       {result.index_path}")
        print(f"Wrote {len(result.post_paths)} post files under {args.out}/posts/")
        print(f"Wrote methodology: {result.methodology_path}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
