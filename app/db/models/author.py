# app/db/models/author.py

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.db.models.artwork import Artwork


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str | None] = mapped_column(String(255))

    name: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    years: Mapped[str | None] = mapped_column(
        String(100),
    )

    property_im_value: Mapped[str | None] = mapped_column(
        String(1000),
    )

    property_im_value_id: Mapped[str | None] = mapped_column(
        String(100),
    )

    property_fam_value: Mapped[str | None] = mapped_column(
        String(1000),
    )

    property_fam_value_id: Mapped[str | None] = mapped_column(
        String(100),
    )

    property_name_value: Mapped[str | None] = mapped_column(
        String(1000),
    )

    name_raw: Mapped[str | None] = mapped_column(
        String(1000),
    )

    artworks: Mapped[list["Artwork"]] = relationship(
        secondary="artwork_authors",
        back_populates="authors",
    )