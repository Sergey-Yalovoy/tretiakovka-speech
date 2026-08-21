from pydantic import BaseModel


class AuthorResponse(BaseModel):
    id: int
    name: str
    years: str | None


class ArtworkResponse(BaseModel):
    id: int
    name: str

    authors: list[AuthorResponse]

    height: str | None
    width: str | None
    depth: str | None

    invnum: str | None
    waydat: str | None

    creat: str | None
    creat_f: str | None

    facts: str | None
    description: str | None

    picture: list[str]
    picture_big: list[str]
    picture_thumb: list[str]

    model_config = {
        "from_attributes": True,
    }


class ParseArtworkRequest(BaseModel):
    url: str
