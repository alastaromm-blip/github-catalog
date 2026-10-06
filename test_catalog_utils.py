"""RED: core pure functions for catalog sync (must fail until implemented)."""
from catalog_utils import parse_repo_url, dedupe_repos, is_fresh, hub_for_topics
from github_catalog_sync import parse_install, stars_human


def test_parse_repo_url():
    assert parse_repo_url("https://github.com/owner/repo/") == "owner/repo"


def test_dedupe_repos():
    repos = ["a/b", "A/B", "c/d"]
    assert dedupe_repos(repos) == ["a/b", "c/d"]


def test_is_fresh():
    assert is_fresh("2026-09-01T00:00:00Z", 180, "2026-10-04T00:00:00Z") is True
    assert is_fresh("2020-01-01T00:00:00Z", 180, "2026-10-04T00:00:00Z") is False


def test_hub_for_topics():
    assert hub_for_topics(["telegram-bot"]) == "bots"
    assert hub_for_topics(["ai-agent", "mcp"]) == "ai"
    assert hub_for_topics(["seo"]) == "seo"
    assert hub_for_topics(["unknown-xyz"]) == "other"


def test_parse_install_docker():
    assert parse_install("run it:\n```\ndocker compose up -d\n```", "o/r") == "docker compose up -d"


def test_parse_install_fallback():
    assert parse_install("", "o/r") == "git clone https://github.com/o/r.git"


def test_stars_human():
    assert stars_human(12400) == "⭐12,4 тыс."
    assert stars_human(850) == "⭐850"
