"""ICU MessageFormat structural validator.

We implement a small recursive-descent parser rather than pull in a binding to
ICU. The grammar we accept:

    message     = ( literal | placeholder )*
    placeholder = '{' ID ( ',' TYPE ( ',' STYLE )? )? '}'
    TYPE        = 'plural' | 'select' | 'selectordinal' | 'number' | 'date' | 'time'
    STYLE       = ( WORD '{' message '}' )+

This is enough to catch every malformed-brace case the validator must reject
and every plural/select shape the rest of the pipeline emits.
"""

from __future__ import annotations

from ..models import ValidationIssue

_VALID_TYPES = {"plural", "select", "selectordinal", "number", "date", "time"}


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.i = 0

    def parse(self) -> None:
        self._message(top=True)
        if self.i != len(self.text):
            raise _ParseError(f"unexpected character at {self.i}: {self.text[self.i]!r}")

    def _message(self, *, top: bool) -> None:
        while self.i < len(self.text):
            ch = self.text[self.i]
            if ch == "{":
                self._placeholder()
            elif ch == "}":
                if top:
                    raise _ParseError(f"unexpected '}}' at {self.i}")
                return
            else:
                self.i += 1

    def _placeholder(self) -> None:
        if self.text[self.i] != "{":
            raise _ParseError(f"expected '{{' at {self.i}")
        self.i += 1
        self._skip_ws()
        ident = self._ident()
        if not ident:
            raise _ParseError(f"empty placeholder id at {self.i}")
        self._skip_ws()
        if self.i < len(self.text) and self.text[self.i] == ",":
            self.i += 1
            self._skip_ws()
            ptype = self._ident()
            if ptype not in _VALID_TYPES:
                raise _ParseError(f"unknown placeholder type {ptype!r} at {self.i}")
            self._skip_ws()
            if self.i < len(self.text) and self.text[self.i] == ",":
                self.i += 1
                self._skip_ws()
                self._branches()
        self._skip_ws()
        if self.i >= len(self.text) or self.text[self.i] != "}":
            raise _ParseError(f"expected '}}' at {self.i}")
        self.i += 1

    def _branches(self) -> None:
        seen_any = False
        while self.i < len(self.text) and self.text[self.i] != "}":
            self._skip_ws()
            kw = self._branch_kw()
            if not kw:
                if seen_any:
                    return
                raise _ParseError(f"expected branch keyword at {self.i}")
            seen_any = True
            self._skip_ws()
            if self.i >= len(self.text) or self.text[self.i] != "{":
                raise _ParseError(f"expected '{{' after branch {kw!r} at {self.i}")
            self.i += 1
            self._message(top=False)
            if self.i >= len(self.text) or self.text[self.i] != "}":
                raise _ParseError(f"expected '}}' to close branch at {self.i}")
            self.i += 1
            self._skip_ws()

    def _branch_kw(self) -> str:
        start = self.i
        # `=N` exact-match branches are allowed in plural
        if self.i < len(self.text) and self.text[self.i] == "=":
            self.i += 1
            while self.i < len(self.text) and self.text[self.i].isdigit():
                self.i += 1
            return self.text[start:self.i]
        return self._ident()

    def _ident(self) -> str:
        start = self.i
        while self.i < len(self.text) and (
            self.text[self.i].isalnum() or self.text[self.i] in "_-"
        ):
            self.i += 1
        return self.text[start:self.i]

    def _skip_ws(self) -> None:
        while self.i < len(self.text) and self.text[self.i] in " \t\n\r":
            self.i += 1


class _ParseError(ValueError):
    pass


def validate_icu(key: str, locale: str, text: str) -> list[ValidationIssue]:
    """Return one error issue per ICU parse failure, empty list on success."""
    try:
        _Parser(text).parse()
    except _ParseError as exc:
        return [
            ValidationIssue(
                severity="error",
                code="ICU_PARSE",
                message=f"ICU MessageFormat parse failure: {exc}",
                key=key,
                locale=locale,
            )
        ]
    return []
