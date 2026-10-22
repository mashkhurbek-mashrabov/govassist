"""Tests for the RFC 9309 robots.txt matcher (wildcards, longest match, groups)."""

import pytest

from apps.collector.robots import RobotsRules

UA = "GovAssist-research/1.0 (+https://example.org)"
# Shaped like goldenpages.uz's robots.txt (NAMUNA host).
WILDCARDS = """
User-agent: *
Disallow: *&region=*
Disallow: *.html
Disallow: */search/*
Disallow: */maps/*
Disallow: *?Print
Allow: *.css

User-agent: Yandex
Disallow: /
"""


@pytest.mark.parametrize(
    ("url", "allowed"),
    [
        ("https://namuna.uz/uz/rubrics/?Id=106916", True),
        ("https://namuna.uz/uz/rubrics/?Id=1153&Page=2", True),
        ("https://namuna.uz/uz/company/?Id=85503", True),
        ("https://namuna.uz/uz/company/85503.html", False),
        ("https://namuna.uz/uz/search/?q=pasport", False),
        ("https://namuna.uz/uz/rubrics/?Id=1&region=5", False),
        ("https://namuna.uz/uz/maps/12/", False),
        ("https://namuna.uz/uz/company/?Id=1?Print", False),
        ("https://namuna.uz/static/site.css", True),
    ],
)
def test_wildcard_rules_are_matched(url: str, allowed: bool) -> None:
    """``*`` matches any run of characters (the stdlib parser treats it literally)."""
    assert RobotsRules(WILDCARDS, UA).allowed(url) is allowed


def test_longest_match_wins_and_allow_wins_ties() -> None:
    """A longer Allow overrides a shorter Disallow; equal lengths favour Allow."""
    rules = RobotsRules(
        "User-agent: *\nDisallow: /uz/\nAllow: /uz/company/\nDisallow: /x\nAllow: /x\n", UA
    )
    assert not rules.allowed("https://namuna.uz/uz/rubrics/")
    assert rules.allowed("https://namuna.uz/uz/company/?Id=1")
    assert rules.allowed("https://namuna.uz/x")


def test_dollar_anchors_the_end() -> None:
    """``$`` matches only at the end of the path."""
    rules = RobotsRules("User-agent: *\nDisallow: /*.pdf$\n", UA)
    assert not rules.allowed("https://namuna.uz/a/b.pdf")
    assert rules.allowed("https://namuna.uz/a/b.pdf?download=1")


def test_our_group_replaces_the_star_group() -> None:
    """A group naming our product token is used instead of ``*``; comments are ignored."""
    text = (
        "User-agent: *\nDisallow: /\n\n"
        "# NAMUNA\nUser-agent: GovAssist-research\nUser-agent: other\nDisallow: /private  # x\n"
    )
    rules = RobotsRules(text, UA)
    assert rules.allowed("https://namuna.uz/public")
    assert not rules.allowed("https://namuna.uz/private/1")


def test_empty_disallow_and_no_rules_allow_everything() -> None:
    """An empty Disallow and an empty file both allow crawling."""
    assert RobotsRules("User-agent: *\nDisallow:\n", UA).allowed("https://namuna.uz/a")
    assert RobotsRules("", UA).allowed("https://namuna.uz/a")
