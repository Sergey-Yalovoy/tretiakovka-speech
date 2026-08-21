import httpx

from app.tretyakov.schemas import (
    TretyakovGalleryDetail,
    TretyakovGalleryResponse,
)


class TretyakovClient:
    BASE_URL = "https://my.tretyakov.ru/api/v1"

    def __init__(
            self,
            client: httpx.AsyncClient,
    ):
        self.client = client

    async def gallery(
            self,
            *,
            page: int = 1,
            page_size: int = 18,
            authors: list[int] | None = None,
            styles: list[int] | None = None,
            categories: list[int] | None = None,
            periods: list[str] | None = None,
            sort: str = "",
            order: str = "",
            lang: str = "ru",
    ) -> TretyakovGalleryResponse:

        params: list[tuple[str, str]] = [
            ("pageNum", str(page)),
            ("pageSize", str(page_size)),
            ("sort", sort),
            ("order", order),
            ("lang", lang),
        ]

        for author_id in authors or []:
            params.append(
                ("filter[author][]", str(author_id))
            )

        for style_id in styles or []:
            params.append(
                ("filter[style][]", str(style_id))
            )

        for category_id in categories or []:
            params.append(
                ("filter[categories][]", str(category_id))
            )

        for period in periods or []:
            params.append(
                ("filter[period][]", period)
            )

        response = await self.client.get(
            "/gallery/get/",
            params=params,
        )

        response.raise_for_status()

        return TretyakovGalleryResponse.model_validate(
            response.json()["data"]
        )

    async def gallery_by_id(
            self,
            artwork_id: int,
            *,
            lang: str = "ru",
    ) -> TretyakovGalleryDetail:

        response = await self.client.get(
            "/gallery/getById/",
            params={
                "id": artwork_id,
                "lang": lang,
            },
        )

        response.raise_for_status()

        payload = response.json()

        if not payload.get("status"):
            raise LookupError(
                f"Artwork {artwork_id} not found"
            )

        return TretyakovGalleryDetail.model_validate(
            payload["data"]
        )
