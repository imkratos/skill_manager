from collections.abc import Sequence

from sqlalchemy import delete

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_crud import CRUDBase

from .model import SkillManagerFileModel, SkillManagerModel
from .schema import (
    SkillManagerCardOutSchema,
    SkillManagerCreateSchema,
    SkillManagerFileCreateSchema,
    SkillManagerFileUpdateSchema,
    SkillManagerUpdateSchema,
)


class SkillManagerCRUD(CRUDBase[SkillManagerModel, SkillManagerCreateSchema, SkillManagerUpdateSchema]):
    """Skill 管理数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=SkillManagerModel, auth=auth)

    async def get_by_id_crud(self, id: int, preload: list[str] | None = None) -> SkillManagerModel | None:
        return await self.get(id=id, preload=preload)

    async def list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict] | None = None,
        preload: list[str] | None = None,
    ) -> Sequence[SkillManagerModel]:
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def create_crud(self, data: dict) -> SkillManagerModel:
        return await self.create(data=data)

    async def update_crud(self, id: int, data: dict) -> SkillManagerModel:
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
            order_by=order_by or [{"updated_time": "desc"}],
            search=search or {},
            out_schema=SkillManagerCardOutSchema,
            preload=preload,
        )


class SkillManagerFileCRUD(
    CRUDBase[SkillManagerFileModel, SkillManagerFileCreateSchema, SkillManagerFileUpdateSchema]
):
    """Skill 引用文件数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=SkillManagerFileModel, auth=auth)

    async def list_by_skill_crud(self, skill_id: int) -> Sequence[SkillManagerFileModel]:
        return await self.list(search={"skill_id": skill_id}, order_by=[{"sort": "asc"}, {"id": "asc"}])

    async def create_crud(self, data: dict) -> SkillManagerFileModel:
        return await self.create(data=data)

    async def delete_by_skill_crud(self, skill_id: int) -> None:
        conditions = [SkillManagerFileModel.skill_id == skill_id]
        if self.auth.user and not self.auth.user.is_superuser:
            conditions.append(SkillManagerFileModel.tenant_id == self.auth.user.tenant_id)
        elif self.auth.tenant_id is not None:
            conditions.append(SkillManagerFileModel.tenant_id == self.auth.tenant_id)
        await self.auth.db.execute(delete(SkillManagerFileModel).where(*conditions))
        await self.auth.db.flush()

    async def delete_crud(self, ids: list[int]) -> None:
        return await self.delete(ids=ids)
