# app/db/models/style.py

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.db.models.artwork import Artwork


class Style(Base):
    __tablename__ = "styles"

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str | None] = mapped_column(
        String(255),
    )

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    property_name_en_value: Mapped[str | None] = mapped_column(
        String(1000),
    )

    property_name_en_value_id: Mapped[str | None] = mapped_column(
        String(100),
    )

    artworks: Mapped[list["Artwork"]] = relationship(
        secondary="artwork_styles",
        back_populates="styles",
    )