# app/db/models/__init__.py

from app.db.models.artwork import (
    Artwork,
    artwork_authors,
    artwork_categories,
    artwork_materials,
    artwork_styles,
    artwork_techniques,
)
from app.db.models.author import Author
from app.db.models.category import Category
from app.db.models.material import Material
from app.db.models.style import Style
from app.db.models.technique import Technique


__all__ = [
    "Artwork",
    "Author",
    "Category",
    "Material",
    "Style",
    "Technique",
    "artwork_authors",
    "artwork_categories",
    "artwork_materials",
    "artwork_styles",
    "artwork_techniques",
]