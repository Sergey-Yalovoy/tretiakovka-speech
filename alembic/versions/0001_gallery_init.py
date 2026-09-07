"""gallery init

Revision ID: 0001_gallery_init
Revises:
Create Date: 2026-08-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_gallery_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "authors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=1000), nullable=False),
        sa.Column("years", sa.String(length=100), nullable=True),
        sa.Column("property_im_value", sa.String(length=1000), nullable=True),
        sa.Column("property_im_value_id", sa.String(length=100), nullable=True),
        sa.Column("property_fam_value", sa.String(length=1000), nullable=True),
        sa.Column("property_fam_value_id", sa.String(length=100), nullable=True),
        sa.Column("property_name_value", sa.String(length=1000), nullable=True),
        sa.Column("name_raw", sa.String(length=1000), nullable=True),
    )

    op.create_table(
        "styles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("property_name_en_value", sa.String(length=1000), nullable=True),
        sa.Column("property_name_en_value_id", sa.String(length=100), nullable=True),
    )

    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=500), nullable=False),
    )

    op.create_table(
        "techniques",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=500), nullable=False),
    )

    op.create_table(
        "artworks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=500), nullable=True),
        sa.Column("name", sa.String(length=1000), nullable=False),
        sa.Column("picture_big", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("picture_thumb", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("height", sa.String(length=100), nullable=True),
        sa.Column("width", sa.String(length=100), nullable=True),
        sa.Column("depth", sa.String(length=100), nullable=True),
        sa.Column("placement", sa.Text(), nullable=True),
        sa.Column("creat", sa.String(length=255), nullable=True),
        sa.Column("creat_f", sa.String(length=500), nullable=True),
        sa.Column("period", sa.String(length=500), nullable=True),
        sa.Column("facts", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("audio_key", sa.String(length=500), nullable=True),
        sa.Column("audio_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "artwork_authors",
        sa.Column("artwork_id", sa.Integer(), sa.ForeignKey("artworks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "artwork_styles",
        sa.Column("artwork_id", sa.Integer(), sa.ForeignKey("artworks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("style_id", sa.Integer(), sa.ForeignKey("styles.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "artwork_materials",
        sa.Column("artwork_id", sa.Integer(), sa.ForeignKey("artworks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "artwork_techniques",
        sa.Column("artwork_id", sa.Integer(), sa.ForeignKey("artworks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("technique_id", sa.Integer(), sa.ForeignKey("techniques.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_index("ix_artworks_period", "artworks", ["period"])
    op.create_index("ix_artworks_name", "artworks", ["name"])
    op.create_index("ix_artwork_authors_author_id", "artwork_authors", ["author_id"])
    op.create_index("ix_artwork_styles_style_id", "artwork_styles", ["style_id"])
    op.create_index("ix_artwork_materials_material_id", "artwork_materials", ["material_id"])
    op.create_index("ix_artwork_techniques_technique_id", "artwork_techniques", ["technique_id"])
    op.create_index(
        "ix_artworks_search_vector",
        "artworks",
        ["search_vector"],
        postgresql_using="gin",
    )

    op.execute("""
        CREATE OR REPLACE FUNCTION artworks_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('russian', coalesce(NEW.name, '')), 'A')
                || setweight(to_tsvector('russian', coalesce(NEW.creat, '')), 'B')
                || setweight(to_tsvector('russian', coalesce(NEW.placement, '')), 'B')
                || setweight(to_tsvector('russian', coalesce(NEW.description, '') || ' ' || coalesce(NEW.facts, '')), 'C');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_artworks_search_vector_update
        BEFORE INSERT OR UPDATE OF name, creat, placement, description, facts
        ON artworks
        FOR EACH ROW EXECUTE FUNCTION artworks_search_vector_update();
    """)


def downgrade() -> None:

    op.execute("DROP TRIGGER IF EXISTS trg_artworks_search_vector_update ON artworks;")
    op.execute("DROP FUNCTION IF EXISTS artworks_search_vector_update();")

    op.drop_index("ix_artworks_search_vector", table_name="artworks")
    op.drop_index("ix_artworks_name", table_name="artworks")
    op.drop_index("ix_artworks_period", table_name="artworks")
    op.drop_table("artwork_techniques")
    op.drop_table("artwork_materials")
    op.drop_table("artwork_styles")
    op.drop_table("artwork_authors")
    op.drop_table("artworks")
    op.drop_table("techniques")
    op.drop_table("materials")
    op.drop_table("styles")
    op.drop_table("authors")

