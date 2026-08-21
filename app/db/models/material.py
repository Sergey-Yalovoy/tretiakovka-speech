# app/db/models/material.py

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.db.models.artwork import Artwork


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str | None] = mapped_column(
        String(255),
    )

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    artworks: Mapped[list["Artwork"]] = relationship(
        secondary="artwork_materials",
        back_populates="materials",
    )