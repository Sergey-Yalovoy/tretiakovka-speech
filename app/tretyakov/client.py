import httpx

from app.config import get_settings
from app.tretyakov.schemas import (
    TretyakovGalleryDetail,
    TretyakovGalleryResponse,
)


class TretyakovClient:

    def __init__(
            self,
            base_url: str | None = None,
            timeout: float | None = None,
            client: httpx.AsyncClient | None = None,
    ):
        settings = get_settings()

        self._base_url = (
                base_url
                or settings.tretyakov_base_url
        ).rstrip("/")

        self._owns_client = client is None

        self.client = client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout or settings.http_timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "tretyakov-speech/1.0",
            },
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def __aenter__(self) -> "TretyakovClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def gallery(
            self,
            *,
            page: int = 1,
            page_size: int = 18,
            authors: list[int] | None = None,
            styles: list[int] | None = None,
            periods: list[str] | None = None,
            sort: str = "",
            order: str = "",
            lang: str | None = None,
    ) -> TretyakovGalleryResponse:

        params: list[tuple[str, str]] = [
            ("pageNum", str(page)),
            ("pageSize", str(page_size)),
            ("sort", sort),
            ("order", order),
            ("lang", lang or get_settings().tretyakov_lang),
        ]

        for author_id in authors or []:
            params.append(
                ("filter[author][]", str(author_id))
            )

        for style_id in styles or []:
            params.append(
                ("filter[style][]", str(style_id))
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
            lang: str | None = None,
    ) -> TretyakovGalleryDetail | None:

        response = await self.client.get(
            "/gallery/getById/",
            params={
                "id": artwork_id,
                "lang": lang or get_settings().tretyakov_lang,
            },
        )

        response.raise_for_status()

        payload = response.json()

        if not payload.get("status"):
            return None

        return TretyakovGalleryDetail.model_validate(
            payload["data"]
        )
