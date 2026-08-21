from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Artwork, Author, Material, Technique
from app.repositories.artwork import ArtworkRepository
from app.tretyakov.client import TretyakovClient


class ArtworkService:

    def __init__(
            self,
            repository: ArtworkRepository,
            tretyakov: TretyakovClient,
    ):
        self.repository = repository
        self.tretyakov = tretyakov

    async def get(
            self,
            session: AsyncSession,
            artwork_id: int,
    ) -> Artwork | None:

        return await self.repository.get(
            session,
            artwork_id,
        )

    async def get_or_fetch(
            self,
            session: AsyncSession,
            artwork_id: int,
    ) -> Artwork | None:

        artwork = await self.get(
            session,
            artwork_id,
        )

        if artwork is not None:
            return artwork

        remote = await self.tretyakov.gallery.get(
            artwork_id,
        )

        if remote is None:
            return None

        artwork = Artwork(
            id=remote.id,
            code=remote.code,
            name=remote.name,

            picture=remote.picture,
            picture_big=remote.picture_big,
            picture_thumb=remote.picture_thumb,
            picture_thumb2=remote.picture_thumb2,

            height=remote.size.height if remote.size else None,
            width=remote.size.width if remote.size else None,
            depth=remote.size.depth if remote.size else None,

            placement=remote.placement,
            placement_schedule=remote.placement_schedule,

            invnum=remote.invnum,
            waydat=remote.waydat,

            creat=remote.creat,
            creat_f=remote.creat_f,

            facts=remote.facts,
            description=remote.description,
        )

        for author in remote.author:
            artwork.authors.append(
                Author(
                    id=author.id,
                    code=author.code,
                    name=author.name,
                    years=author.years,
                )
            )

        for material in remote.material:
            artwork.materials.append(
                Material(
                    id=int(material.id),
                    code=material.code,
                    name=material.name,
                )
            )

        for technique in remote.technique:
            artwork.techniques.append(
                Technique(
                    id=int(technique.id),
                    code=technique.code,
                    name=technique.name,
                )
            )

        session.add(artwork)

        await session.commit()
        await session.refresh(artwork)

        return await self.repository.get(
            session,
            artwork_id,
        )
