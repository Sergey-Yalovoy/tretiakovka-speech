# app/db/models/artwork.py

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.db.models.author import Author
    from app.db.models.category import Category
    from app.db.models.style import Style
    from app.db.models.material import Material
    from app.db.models.technique import Technique


artwork_authors = Table(
    "artwork_authors",
    Base.metadata,

    Column(
        "artwork_id",
        ForeignKey(
            "artworks.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),

    Column(
        "author_id",
        ForeignKey(
            "authors.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


artwork_categories = Table(
    "artwork_categories",
    Base.metadata,

    Column(
        "artwork_id",
        ForeignKey(
            "artworks.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),

    Column(
        "category_id",
        ForeignKey(
            "categories.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


artwork_styles = Table(
    "artwork_styles",
    Base.metadata,

    Column(
        "artwork_id",
        ForeignKey(
            "artworks.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),

    Column(
        "style_id",
        ForeignKey(
            "styles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


artwork_materials = Table(
    "artwork_materials",
    Base.metadata,

    Column(
        "artwork_id",
        ForeignKey(
            "artworks.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),

    Column(
        "material_id",
        ForeignKey(
            "materials.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


artwork_techniques = Table(
    "artwork_techniques",
    Base.metadata,

    Column(
        "artwork_id",
        ForeignKey(
            "artworks.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),

    Column(
        "technique_id",
        ForeignKey(
            "techniques.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


class Artwork(Base):
    __tablename__ = "artworks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    code: Mapped[str | None] = mapped_column(
        String(500),
    )

    name: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    picture: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
    )

    picture_big: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
    )

    picture_thumb: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
    )

    picture_thumb2: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
    )

    height: Mapped[str | None] = mapped_column(
        String(100),
    )

    width: Mapped[str | None] = mapped_column(
        String(100),
    )

    depth: Mapped[str | None] = mapped_column(
        String(100),
    )

    placement: Mapped[str | None] = mapped_column(
        Text,
    )

    placement_schedule: Mapped[str | None] = mapped_column(
        Text,
    )

    invnum: Mapped[str | None] = mapped_column(
        String(255),
    )

    waydat: Mapped[str | None] = mapped_column(
        Text,
    )

    creat: Mapped[str | None] = mapped_column(
        String(255),
    )

    creat_f: Mapped[str | None] = mapped_column(
        String(500),
    )

    period: Mapped[str | None] = mapped_column(
        String(500),
    )

    facts: Mapped[str | None] = mapped_column(
        Text,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    authors: Mapped[list["Author"]] = relationship(
        secondary=artwork_authors,
        back_populates="artworks",
    )

    categories: Mapped[list["Category"]] = relationship(
        secondary=artwork_categories,
        back_populates="artworks",
    )

    styles: Mapped[list["Style"]] = relationship(
        secondary=artwork_styles,
        back_populates="artworks",
    )

    materials: Mapped[list["Material"]] = relationship(
        secondary=artwork_materials,
        back_populates="artworks",
    )

    techniques: Mapped[list["Technique"]] = relationship(
        secondary=artwork_techniques,
        back_populates="artworks",
    )