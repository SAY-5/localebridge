"""SQLAlchemy persistence layer for translations.

The default pipeline uses `InMemoryTM` from `tm.py`. This module documents the
production shape and gives the API server something to swap in later.
"""

from __future__ import annotations

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TranslationRow(Base):
    __tablename__ = "translations"

    key = Column(String(256), primary_key=True)
    locale = Column(String(16), primary_key=True)
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="pending_review")
    edit_reason = Column(Text, nullable=True)
    reject_reason = Column(Text, nullable=True)
