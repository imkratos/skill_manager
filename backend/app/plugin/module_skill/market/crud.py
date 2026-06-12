from collections.abc import Sequence

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_crud import CRUDBase

from .model import SkillMarketItemModel, SkillMarketSourceModel
from .schema import (
    SkillMarketItemCreateSchema,
    SkillMarketItemOutSchema,
    SkillMarketItemUpdateSchema,
    SkillMarketSourceCreateSchema,
    SkillMarketSourceOutSchema,
    SkillMarketSourceUpdateSchema,
)


class SkillMarketSourceCRUD(
    CRUDBase[SkillMarketSourceModel, SkillMarketSourceCreateSchema, SkillMarketSourceUpdateSchema]
):
    """第三方市场源数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=SkillMarketSourceModel, auth=auth)

    async def get_by_id_crud(self, id: int, preload: list[str] | None = None) -> SkillMarketSourceModel | None:
        return await self.get(id=id, preload=preload)

    async def list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict] | None = None,
        preload: list[str] | None = None,
    ) -> Sequence[SkillMarketSourceModel]:
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def create_crud(self, data: dict) -> SkillMarketSourceModel:
        return await self.create(data=data)

    async def update_crud(self, id: int, data: dict) -> SkillMarketSourceModel:
        return await self.update(id=id, data=data)

    async def delete_crud(self, ids: list[int]) -> None:
        return await self.delete(ids=ids)

    async def page_crud(
        self,
        offset: int,
        limit: int,
        order_by: list[dict] | None = None,
        search: dict | None = None,
        preload: list | None = None,
    ) -> dict:
        return await self.page(
            offset=offset,
            limit=limit,
            order_by=order_by or [{"sort": "asc"}, {"updated_time": "desc"}],
            search=search or {},
            out_schema=SkillMarketSourceOutSchema,
            preload=preload,
        )


class SkillMarketItemCRUD(
    CRUDBase[SkillMarketItemModel, SkillMarketItemCreateSchema, SkillMarketItemUpdateSchema]
):
    """第三方市场 Skill 数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=SkillMarketItemModel, auth=auth)

    async def get_by_id_crud(self, id: int, preload: list[str] | None = None) -> SkillMarketItemModel | None:
        return await self.get(id=id, preload=preload)

    async def get_by_external_crud(self, source_id: int, external_id: str) -> SkillMarketItemModel | None:
        return await self.get(source_id=source_id, external_id=external_id, preload=[])

    async def list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict] | None = None,
        preload: list[str] | None = None,
    ) -> Sequence[SkillMarketItemModel]:
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def create_crud(self, data: dict) -> SkillMarketItemModel:
        return await self.create(data=data)

    async def update_crud(self, id: int, data: dict) -> SkillMarketItemModel:
        return await self.update(id=id, data=data)

    async def page_crud(
        self,
        offset: int,
        limit: int,
        order_by: list[dict] | None = None,
        search: dict | None = None,
        preload: list | None = None,
    ) -> dict:
        return await self.page(
            offset=offset,
            limit=limit,
            order_by=order_by or [{"updated_time": "desc"}],
            search=search or {},
            out_schema=SkillMarketItemOutSchema,
            preload=preload,
        )
