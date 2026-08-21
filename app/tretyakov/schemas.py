from pydantic import BaseModel, Field


class TretyakovFilterAuthor(BaseModel):
    id: int
    code: str | None = None

    name: str

    property_im_value: str | None = Field(
        default=None,
        alias="propertyImValue",
    )

    property_im_value_id: str | None = Field(
        default=None,
        alias="propertyImValueId",
    )

    property_fam_value: str | None = Field(
        default=None,
        alias="propertyFamValue",
    )

    property_fam_value_id: str | None = Field(
        default=None,
        alias="propertyFamValueId",
    )

    property_name_value: str | None = Field(
        default=None,
        alias="propertyNameValue",
    )

    name_raw: str | None = Field(
        default=None,
        alias="nameRaw",
    )

    model_config = {
        "populate_by_name": True,
    }


class TretyakovFilterStyle(BaseModel):
    id: int
    code: str | None = None
    name: str

    property_name_en_value: str | None = Field(
        default=None,
        alias="propertyNameEnValue",
    )

    property_name_en_value_id: str | None = Field(
        default=None,
        alias="propertyNameEnValueId",
    )

    model_config = {
        "populate_by_name": True,
    }


class TretyakovGallerySearch(BaseModel):
    q: str | None = None


class TretyakovAuthor(BaseModel):
    id: int
    code: str | None = None
    name: str

    property_im_value: str | None = Field(
        default=None,
        alias="propertyImValue",
    )
    property_im_value_id: str | None = Field(
        default=None,
        alias="propertyImValueId",
    )
    property_fam_value: str | None = Field(
        default=None,
        alias="propertyFamValue",
    )
    property_fam_value_id: str | None = Field(
        default=None,
        alias="propertyFamValueId",
    )
    sort: str | None = None
    property_name_value: str | None = Field(
        default=None,
        alias="propertyNameValue",
    )
    name_raw: str | None = Field(
        default=None,
        alias="nameRaw",
    )

    model_config = {
        "populate_by_name": True,
    }


class TretyakovStyle(BaseModel):
    id: int
    code: str | None = None
    name: str

    property_name_en_value: str | None = Field(
        default=None,
        alias="propertyNameEnValue",
    )
    property_name_en_value_id: str | None = Field(
        default=None,
        alias="propertyNameEnValueId",
    )
    sort: str | None = None

    model_config = {
        "populate_by_name": True,
    }


class TretyakovSize(BaseModel):
    height: str | None = None
    width: str | None = None
    depth: str | None = None


class TretyakovGalleryItem(BaseModel):
    id: int
    code: str | None = None
    name: str

    author: list[TretyakovAuthor] = Field(
        default_factory=list,
    )

    unconfirmed_author_ids: list[int] | None = Field(
        default=None,
        alias="unconfirmedAuthorIds",
    )

    style: list[TretyakovStyle] = Field(
        default_factory=list,
    )

    picture: list[str] = Field(
        default_factory=list,
    )

    picture_big: list[str] = Field(
        default_factory=list,
        alias="pictureBig",
    )

    picture_thumb: list[str] = Field(
        default_factory=list,
        alias="pictureThumb",
    )

    picture_thumb2: list[str] = Field(
        default_factory=list,
        alias="pictureThumb2",
    )

    size: TretyakovSize | None = None

    is_pano360: bool = Field(
        default=False,
        alias="isPano360",
    )

    period: str | None = None

    in_loyalty_program: bool = Field(
        default=False,
        alias="inLoyaltyProgram",
    )

    is_open: bool = Field(
        default=False,
        alias="isOpen",
    )

    is_kit: bool = Field(
        default=False,
        alias="isKit",
    )

    positional: str | None = None

    under_patronage: bool = Field(
        default=False,
        alias="underPatronage",
    )

    in_current_user_mir_gallery: bool = Field(
        default=False,
        alias="inCurrentUserMirGallery",
    )

    model_config = {
        "populate_by_name": True,
    }


class TretyakovMaterial(BaseModel):
    id: int
    code: str | None = None
    name: str


class TretyakovTechnique(BaseModel):
    id: int
    code: str | None = None
    name: str


class TretyakovBuyTicketLink(BaseModel):
    button_text: str | None = Field(
        default=None,
        alias="buttonText",
    )

    model_config = {
        "populate_by_name": True,
    }


class TretyakovCompilation(BaseModel):
    is_set: bool | None = Field(
        default=None,
        alias="isSet",
    )

    button_text: str | None = Field(
        default=None,
        alias="buttonText",
    )

    comp_href: str | None = Field(
        default=None,
        alias="compHref",
    )

    model_config = {
        "populate_by_name": True,
    }


class TretyakovPano360(BaseModel):
    is_set: bool | None = Field(
        default=None,
        alias="isSet",
    )

    pano360: str | None = None

    model_config = {
        "populate_by_name": True,
    }


class TretyakovGalleryDetail(BaseModel):
    id: int
    name: str

    picture: list[str] = Field(
        default_factory=list,
    )

    picture_big: list[str] = Field(
        default_factory=list,
        alias="pictureBig",
    )

    picture_thumb: list[str] = Field(
        default_factory=list,
        alias="pictureThumb",
    )

    picture_thumb2: list[str] = Field(
        default_factory=list,
        alias="pictureThumb2",
    )

    size: TretyakovSize | None = None

    author: list[TretyakovAuthor] = Field(
        default_factory=list,
    )

    unconfirmed_author_ids: list[int] | None = Field(
        default=None,
        alias="unconfirmedAuthorIds",
    )

    material: list[TretyakovMaterial] = Field(
        default_factory=list,
    )

    technique: list[TretyakovTechnique] = Field(
        default_factory=list,
    )

    placement: str | None = None
    placement_schedule: str | None = Field(
        default=None,
        alias="placementSchedule",
    )

    invnum: str | None = None
    waydat: str | None = None
    creat: str | None = None
    creat_f: str | None = Field(
        default=None,
        alias="creatF",
    )

    buy_ticket_link: TretyakovBuyTicketLink | None = Field(
        default=None,
        alias="buyTicketLink",
    )

    compilation: TretyakovCompilation | None = None

    pano360: TretyakovPano360 | None = None

    facts: str | None = None
    description: str | None = None

    model_config = {
        "populate_by_name": True,
    }


class TretyakovGalleryResponse(BaseModel):
    count: int
    page_count: int = Field(alias="pageCount")

    filter: "TretyakovGalleryFilter"

    items: list[TretyakovGalleryItem]

    model_config = {
        "populate_by_name": True,
    }


class TretyakovFilterCategory(BaseModel):
    id: int
    code: str | None = None
    name: str
    sort: str | None = None


class TretyakovGalleryFilter(BaseModel):
    loyalty: bool
    loyalty_open: bool = Field(
        alias="loyaltyOpen",
    )

    author: list[TretyakovAuthor] = Field(
        default_factory=list,
    )

    categories: list[TretyakovFilterCategory] = Field(
        default_factory=list,
    )

    period: list[str] = Field(
        default_factory=list,
    )

    style: list[TretyakovStyle] = Field(
        default_factory=list,
    )

    model_config = {
        "populate_by_name": True,
    }
