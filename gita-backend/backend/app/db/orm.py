"""SQLAlchemy ORM models (SQLite)."""

from __future__ import annotations

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class VerseRow(Base):
    """
    Canonical verse row in SQLite.
    Tag columns store JSON arrays as TEXT (practical for SQLite without extra tables).
    """

    __tablename__ = "verses"
    __table_args__ = (UniqueConstraint("chapter", "verse", name="uq_verses_chapter_verse"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter: Mapped[int] = mapped_column(Integer, nullable=False)
    verse: Mapped[int] = mapped_column(Integer, nullable=False)
    citation_key: Mapped[str] = mapped_column(String(32), nullable=False)
    sanskrit: Mapped[str | None] = mapped_column(Text, nullable=True)
    transliteration: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation: Mapped[str] = mapped_column(Text, nullable=False)
    theme_tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    situation_tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    use_with_care_tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    translation_source: Mapped[str | None] = mapped_column(Text, nullable=True)
