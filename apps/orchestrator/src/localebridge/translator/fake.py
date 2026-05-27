"""Deterministic scripted translator for tests and CI.

The FakeTranslator is the cornerstone of hermetic CI: it never reaches the
network, always produces the same output for the same input, and exposes a
small per-locale prefix/suffix scheme that's good enough to exercise every
validator.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..validators.plural import CLDR_PLURAL_CATEGORIES, source_has_plural

_LOCALE_TRANSFORMS: dict[str, tuple[str, str]] = {
    "es": ("es:", ""),
    "fr": ("fr:", ""),
    "de": ("de:", ""),
    "ja": ("", ""),
    "ar": ("", ""),
    "zh-CN": ("", ""),
    "hi": ("", ""),
    "ru": ("", ""),
}

# Token-level translations used for the example app keys so the e2e output
# looks plausible. Anything not in this map falls back to prefix/suffix wrap.
_TOKEN_TABLE: dict[str, dict[str, str]] = {
    "Home": {
        "es": "Inicio", "fr": "Accueil", "de": "Startseite",
        "ja": "ホーム", "ar": "الرئيسية", "zh-CN": "首页", "hi": "मुख्य पृष्ठ",
    },
    "Settings": {
        "es": "Ajustes", "fr": "Paramètres", "de": "Einstellungen",
        "ja": "設定", "ar": "الإعدادات", "zh-CN": "设置", "hi": "सेटिंग्स",
    },
    "Sign in": {
        "es": "Iniciar sesión", "fr": "Se connecter", "de": "Anmelden",
        "ja": "サインイン", "ar": "تسجيل الدخول", "zh-CN": "登录", "hi": "साइन इन करें",
    },
    "Sign out": {
        "es": "Cerrar sesión", "fr": "Se déconnecter", "de": "Abmelden",
        "ja": "サインアウト", "ar": "تسجيل الخروج", "zh-CN": "退出", "hi": "साइन आउट",
    },
}


@dataclass
class FakeTranslator:
    """Deterministic translator. Reproduces output for any input."""

    _human_overrides: dict[tuple[str, str], str] = field(default_factory=dict)

    def set_human_edit(self, key: str, locale: str, text: str) -> None:
        """Pin a human-edited translation; bypasses scripted output."""
        self._human_overrides[(key, locale)] = text

    def translate(
        self, key: str, source_text: str, target_locale: str, *, note: str | None = None
    ) -> str:
        override = self._human_overrides.get((key, target_locale))
        if override is not None:
            return override
        if target_locale == "en":
            return source_text
        # ICU MessageFormat passthrough: re-translate textual segments and
        # expand plural categories to match the target locale's CLDR rules.
        if source_has_plural(source_text):
            return _translate_plural(source_text, target_locale)
        if _looks_like_icu(source_text):
            return _translate_icu(source_text, target_locale)
        if source_text in _TOKEN_TABLE and target_locale in _TOKEN_TABLE[source_text]:
            return _TOKEN_TABLE[source_text][target_locale]
        prefix, suffix = _LOCALE_TRANSFORMS.get(target_locale, (f"{target_locale}:", ""))
        return f"{prefix}{source_text}{suffix}".strip()


_ICU_KEYWORDS = {"plural", "select", "selectordinal", "one", "two", "few", "many", "other",
                 "zero", "male", "female"}
_PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}")


def _looks_like_icu(text: str) -> bool:
    return any(f", {kw}" in text or f"{{{kw}" in text or text.startswith("{") for kw in _ICU_KEYWORDS)


def _translate_icu(text: str, target_locale: str) -> str:
    """Translate the prose between ICU control structures.

    The strategy: keep every `{...}` and every ICU keyword untouched, prepend
    the locale prefix to the first textual chunk inside each branch.
    """
    prefix, _ = _LOCALE_TRANSFORMS.get(target_locale, (f"{target_locale}:", ""))
    # naive: replace runs of letters/spaces outside braces with `<prefix><text>`
    out: list[str] = []
    i = 0
    depth = 0
    buf: list[str] = []
    while i < len(text):
        ch = text[i]
        if ch == "{":
            if buf:
                out.append(_wrap_text(buf, prefix))
                buf = []
            depth += 1
            out.append(ch)
        elif ch == "}":
            depth -= 1
            out.append(ch)
        elif depth == 0:
            buf.append(ch)
        else:
            out.append(ch)
        i += 1
    if buf:
        out.append(_wrap_text(buf, prefix))
    return "".join(out)


def _wrap_text(buf: list[str], prefix: str) -> str:
    text = "".join(buf)
    if not text.strip():
        return text
    return f"{prefix}{text}"


_PLURAL_RE = re.compile(
    r"\{(?P<var>[A-Za-z_][\w-]*)\s*,\s*plural\s*,\s*(?P<branches>.*)\}",
    re.DOTALL,
)


def _translate_plural(source: str, target_locale: str) -> str:
    """Expand the source plural block into all CLDR-required categories for
    `target_locale`, deriving each branch text from the source's `other` branch
    (or its `one` branch if no `other` is present).
    """
    m = _PLURAL_RE.search(source)
    if m is None:
        return source
    var = m.group("var")
    branches = _parse_branches(m.group("branches"))
    template = branches.get("other") or branches.get("one") or next(iter(branches.values()), "")
    required = CLDR_PLURAL_CATEGORIES.get(target_locale, frozenset({"other"}))
    prefix, _ = _LOCALE_TRANSFORMS.get(target_locale, (f"{target_locale}:", ""))
    out_branches: list[str] = []
    for cat in sorted(required, key=_category_sort_key):
        body = branches.get(cat, template)
        out_branches.append(f"{cat} {{{prefix}{body}}}")
    return f"{{{var}, plural, {' '.join(out_branches)}}}"


_CATEGORY_ORDER = {"zero": 0, "one": 1, "two": 2, "few": 3, "many": 4, "other": 5}


def _category_sort_key(c: str) -> tuple[int, str]:
    return (_CATEGORY_ORDER.get(c, 99), c)


def _parse_branches(s: str) -> dict[str, str]:
    """Read `cat {body} cat {body}` into a {cat: body} dict, allowing the body
    to contain nested braces."""
    out: dict[str, str] = {}
    i = 0
    while i < len(s):
        while i < len(s) and s[i].isspace():
            i += 1
        start = i
        while i < len(s) and (s[i].isalnum() or s[i] in "_-="):
            i += 1
        cat = s[start:i]
        while i < len(s) and s[i].isspace():
            i += 1
        if i >= len(s) or s[i] != "{":
            break
        i += 1
        depth = 1
        body_start = i
        while i < len(s) and depth > 0:
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = s[body_start:i]
        if i < len(s):
            i += 1  # consume closing }
        if cat:
            out[cat] = body
    return out
