from pydantic import BaseModel


class AuthorResponse(BaseModel):
    id: int
    name: str
    years: str | None = None
    model_config = {"from_attributes": True}


class StyleResponse(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class MaterialResponse(BaseModel):
    id: int
    name: str


class TechniqueResponse(BaseModel):
    id: int
    name: str


class ArtworkListItemResponse(BaseModel):
    id: int
    name: str
    code: str | None = None

    authors: list[AuthorResponse]
    styles: list[StyleResponse]

    height: str | None
    width: str | None
    depth: str | None

    creat: str | None
    creat_f: str | None
    period: str | None

    picture_big: list[str]
    picture_thumb: list[str]

    has_audio: bool = False
    audio_url: str | None = None

    model_config = {"from_attributes": True}


class ArtworkDetailResponse(ArtworkListItemResponse):
    placement: str | None = None

    materials: list[MaterialResponse]
    techniques: list[TechniqueResponse]

    facts: str | None
    description: str | None


class ArtworkListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ArtworkListItemResponse]


class FindArtworkRequest(BaseModel):
    url: str


class FiltersResponse(BaseModel):
    authors: list[AuthorResponse]
    styles: list[StyleResponse]
    materials: list[MaterialResponse]
    techniques: list[TechniqueResponse]
    periods: list[str]
