from textual.content import Span
from textual.fuzzy import FuzzySearch, Matcher
from textual.style import Style


def test_no_match():
    """Check non matching score of zero."""
    matcher = Matcher("x")
    assert matcher.match("foo") == 0


def test_match_single_group():
    """Check that single groups rang higher."""
    matcher = Matcher("abc")
    assert matcher.match("foo abc bar") > matcher.match("fooa barc")


def test_boosted_matches():
    """Check first word matchers rank higher."""
    matcher = Matcher("ss")

    # First word matchers should score higher
    assert matcher.match("Save Screenshot") > matcher.match("Show Keys abcde")


def test_highlight():
    matcher = Matcher("foo.bar")

    spans = matcher.highlight("foo/egg.bar").spans
    print(repr(spans))
    assert spans == [
        Span(0, 1, Style(reverse=True)),
        Span(1, 2, Style(reverse=True)),
        Span(2, 3, Style(reverse=True)),
        Span(7, 8, Style(reverse=True)),
        Span(8, 9, Style(reverse=True)),
        Span(9, 10, Style(reverse=True)),
        Span(10, 11, Style(reverse=True)),
    ]


def test_matcher_case_sensitive():
    matcher = Matcher("foo", case_sensitive=True)
    assert matcher.match("FOO") == 0.0
    assert matcher.match("foo") > 0.0


def test_fuzzy_search_cache_case_sensitive():
    search = FuzzySearch()
    score_insensitive, _ = search.match("foo", "FOO")
    assert score_insensitive > 0.0
    search.case_sensitive = True
    score_sensitive, _ = search.match("foo", "FOO")
    assert score_sensitive == 0.0

