"""Mixins partagés par les modèles."""

from sqlalchemy import Column, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func


class TimestampMixin:
    """Ajoute created_at et updated_at automatiques."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SchoolScopedMixin:
    """Toutes les entités métier appartiennent à une école (multi-tenant)."""
    @classmethod
    def school_id_column(cls):
        return Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
