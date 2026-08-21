from app.tretyakov.schemas import TretyakovArtwork


class GalleryAPI:
    def __init__(self, client):
        self.client = client

    async def get(
        self,
        artwork_id: int,
    ) -> TretyakovArtwork | None:

        response = await self.client.request(
            "GET",
            "/gallery/getById/",
            params={
                "id": artwork_id,
                "lang": "ru",
            },
        )

        data = response.get("data")

        if not data:
            return None

        return TretyakovArtwork.model_validate(data)