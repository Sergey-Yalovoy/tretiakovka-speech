from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.deps import get_runtime
from app.repositories.artwork import DictionaryRepository
from app.schemas.artwork import (
    AuthorResponse,
    FiltersResponse,
    MaterialResponse,
    StyleResponse,
    TechniqueResponse,
)

router = APIRouter(
    prefix="/api/v1/filters",
    tags=["filters"],
)


@router.get(
    "",
    response_model=FiltersResponse,
    summary="Справочники для фильтров каталога",
)
async def get_filters(
        session: Annotated[AsyncSession, Depends(get_session)],
):
    repository = DictionaryRepository()

    authors = await repository.authors(session)
    styles = await repository.styles(session)
    materials = await repository.materials(session)
    techniques = await repository.techniques(session)
    periods = await repository.periods(session)

    return FiltersResponse(
        authors=[
            AuthorResponse(id=a.id, name=a.name, years=a.years)
            for a in authors
        ],
        styles=[
            StyleResponse(id=s.id, name=s.name)
            for s in styles
        ],
        materials=[
            MaterialResponse(id=m.id, name=m.name)
            for m in materials
        ],
        techniques=[
            TechniqueResponse(id=t.id, name=t.name)
            for t in techniques
        ],
        periods=periods,
    )
