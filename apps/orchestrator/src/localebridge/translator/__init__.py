"""Translation providers."""

from ._base import Translator
from .fake import FakeTranslator

__all__ = ["Translator", "FakeTranslator"]
