"""Property tests for the ICU MessageFormat validator (v1).

Strategy:
- Generate well-formed messages from a small ICU grammar -> validator MUST accept.
- Generate malformed strings (random brace mutations) -> validator MUST flag.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from localebridge.validators.icu import validate_icu

ident = st.from_regex(r"\A[A-Za-z_][A-Za-z0-9_]{0,7}\Z", fullmatch=True)
plain_text = st.text(
    alphabet=st.characters(blacklist_characters="{}", min_codepoint=32, max_codepoint=126),
    max_size=20,
)


@st.composite
def well_formed_icu(draw: st.DrawFn) -> str:
    leading = draw(plain_text)
    var = draw(ident)
    type_kw = draw(st.sampled_from(["plural", "select"]))
    if type_kw == "plural":
        branches = draw(st.lists(plural_branch(), min_size=1, max_size=4))
    else:
        branches = draw(st.lists(select_branch(), min_size=1, max_size=4))
    trailing = draw(plain_text)
    return f"{leading}{{{var}, {type_kw}, {' '.join(branches)}}}{trailing}"


@st.composite
def plural_branch(draw: st.DrawFn) -> str:
    kw = draw(st.sampled_from(["one", "few", "many", "other", "zero", "two"]))
    body = draw(plain_text)
    return f"{kw} {{{body}}}"


@st.composite
def select_branch(draw: st.DrawFn) -> str:
    kw = draw(ident)
    body = draw(plain_text)
    return f"{kw} {{{body}}}"


@given(well_formed_icu())
@settings(max_examples=300, deadline=None)
def test_well_formed_icu_always_passes(text: str) -> None:
    issues = validate_icu("k", "en", text)
    assert issues == [], f"unexpected ICU error for {text!r}: {issues}"


@given(st.text(min_size=1, max_size=80))
@settings(max_examples=500, deadline=None)
def test_arbitrary_text_does_not_crash(text: str) -> None:
    # Whatever the result, no exception should leak.
    validate_icu("k", "en", text)


_INVARIANTS = [
    "{",
    "}",
    "{x",
    "x}",
    "{x,",
    "{x, plural,",
    "{x, plural, one {",
    "{x, plural, one {a",
    "{x, plural, one {a}",
    "{x, plural, one {a} other y}",
    "{x, totallyfake, one {a} other {b}}",
]


def test_known_malformed_each_flagged() -> None:
    for text in _INVARIANTS:
        issues = validate_icu("k", "en", text)
        assert any(i.code == "ICU_PARSE" for i in issues), f"missed malformed {text!r}"
