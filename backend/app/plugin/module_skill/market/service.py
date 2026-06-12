from datetime import datetime, timedelta

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.exceptions import CustomException
from app.plugin.module_skill.manager.crud import SkillManagerCRUD
from app.plugin.module_skill.manager.schema import (
    SkillManagerCreateSchema,
    SkillManagerFileCreateSchema,
)
from app.plugin.module_skill.manager.service import SkillManagerService

from .adapters import ADAPTERS, MarketAdapterItem
from .crud import SkillMarketItemCRUD, SkillMarketSourceCRUD
from .schema import (
    SkillMarketItemOutSchema,
    SkillMarketItemQueryParam,
    SkillMarketSourceCreateSchema,
    SkillMarketSourceOutSchema,
    SkillMarketSourceQueryParam,
    SkillMarketSourceUpdateSchema,
)


class SkillMarketService:
    """第三方 Skill 市场服务层"""

    @classmethod
    async def source_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        obj = await SkillMarketSourceCRUD(auth).get_by_id_crud(id=id, preload=[])
        if not obj:
            raise CustomException(msg="第三方市场源不存在")
        return SkillMarketSourceOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def source_page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: SkillMarketSourceQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        search_dict = search.__dict__ if search else {}
        offset = (page_no - 1) * page_size
        return await SkillMarketSourceCRUD(auth).page_crud(
            offset=offset,
            limit=page_size,
            order_by=order_by,
            search=search_dict,
            preload=[],
        )

    @classmethod
    async def source_create_service(cls, auth: AuthSchema, data: SkillMarketSourceCreateSchema) -> dict:
        exists = await SkillMarketSourceCRUD(auth).get(code=data.code, preload=[])
        if exists:
            raise CustomException(msg="创建失败，平台编码已存在")
        obj = await SkillMarketSourceCRUD(auth).create_crud(data=data.model_dump())
        return SkillMarketSourceOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def source_update_service(cls, auth: AuthSchema, id: int, data: SkillMarketSourceUpdateSchema) -> dict:
        obj = await SkillMarketSourceCRUD(auth).get_by_id_crud(id=id, preload=[])
        if not obj:
            raise CustomException(msg="更新失败，第三方市场源不存在")
        exists = await SkillMarketSourceCRUD(auth).get(code=data.code, preload=[])
        if exists and exists.id != id:
            raise CustomException(msg="更新失败，平台编码重复")
        updated = await SkillMarketSourceCRUD(auth).update_crud(id=id, data=data.model_dump())
        return SkillMarketSourceOutSchema.model_validate(updated).model_dump()

    @classmethod
    async def source_delete_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        for id in ids:
            obj = await SkillMarketSourceCRUD(auth).get_by_id_crud(id=id, preload=[])
            if not obj:
                raise CustomException(msg=f"删除失败，ID 为 {id} 的第三方市场源不存在")
        await SkillMarketSourceCRUD(auth).delete_crud(ids=ids)

    @classmethod
    async def item_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        obj = await SkillMarketItemCRUD(auth).get_by_id_crud(id=id, preload=[])
        if not obj:
            raise CustomException(msg="第三方 Skill 不存在")
        return SkillMarketItemOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def item_page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: SkillMarketItemQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        offset = (page_no - 1) * page_size
        if (
            getattr(search, "refresh", False)
            or await cls._cache_empty(auth=auth, search=search)
            or await cls._cache_stale(auth=auth, search=search)
        ):
            await cls._sync_matching_sources(auth=auth, search=search)

        search_dict = search.__dict__.copy() if search else {}
        search_dict.pop("refresh", None)
        return await SkillMarketItemCRUD(auth).page_crud(
            offset=offset,
            limit=page_size,
            order_by=order_by or [{"last_sync_time": "desc"}, {"updated_time": "desc"}],
            search=search_dict,
            preload=[],
        )

    @classmethod
    async def sync_source_service(cls, auth: AuthSchema, source_id: int) -> dict:
        source = await SkillMarketSourceCRUD(auth).get_by_id_crud(id=source_id, preload=[])
        if not source:
            raise CustomException(msg="同步失败，第三方市场源不存在")
        if source.status != "0":
            raise CustomException(msg="同步失败，第三方市场源已停用")

        adapter = cls._build_adapter(
            adapter_type=source.adapter_type,
            base_url=source.base_url,
            branch=source.branch,
            config=source.config,
        )
        now = datetime.now()
        created = 0
        updated = 0
        try:
            items = await adapter.list_items()
            active_external_ids = {item.external_id for item in items}
            for item in items:
                payload = cls._item_payload(source_id=source.id, item=item, sync_time=now)
                exists = await SkillMarketItemCRUD(auth).get_by_external_crud(
                    source_id=source.id,
                    external_id=item.external_id,
                )
                if exists:
                    await SkillMarketItemCRUD(auth).update_crud(id=exists.id, data=payload)
                    updated += 1
                else:
                    await SkillMarketItemCRUD(auth).create_crud(data=payload)
                    created += 1
            await cls._disable_missing_items(auth=auth, source_id=source.id, active_external_ids=active_external_ids)
            await SkillMarketSourceCRUD(auth).update_crud(
                id=source.id,
                data={
                    "last_sync_time": now,
                    "last_sync_status": "success",
                    "last_sync_message": f"同步成功：新增 {created} 个，更新 {updated} 个",
                },
            )
            return {"source_id": source.id, "total": len(items), "created": created, "updated": updated}
        except Exception as exc:
            await SkillMarketSourceCRUD(auth).update_crud(
                id=source.id,
                data={
                    "last_sync_time": now,
                    "last_sync_status": "failed",
                    "last_sync_message": str(exc),
                },
            )
            raise

    @classmethod
    async def install_item_service(cls, auth: AuthSchema, item_id: int) -> dict:
        item = await SkillMarketItemCRUD(auth).get_by_id_crud(id=item_id, preload=[])
        if not item:
            raise CustomException(msg="安装失败，第三方 Skill 不存在")
        source = await SkillMarketSourceCRUD(auth).get_by_id_crud(id=item.source_id, preload=[])
        if not source:
            raise CustomException(msg="安装失败，第三方市场源不存在")

        if item.market_kind == "skill":
            exists = await SkillManagerCRUD(auth).get(name=item.name, preload=[])
        else:
            exists = None
        if exists:
            await SkillMarketItemCRUD(auth).update_crud(id=item.id, data={"installed_skill_id": exists.id})
            return await SkillManagerService.detail_service(auth=auth, id=exists.id)

        adapter_item = MarketAdapterItem(
            external_id=item.external_id,
            name=item.name,
            title=item.title,
            description=item.description,
            category=item.category,
            tags=item.tags,
            version=item.version,
            author=item.author,
            license=item.license,
            homepage_url=item.homepage_url,
            repository_url=item.repository_url,
            skill_path=item.skill_path,
            skill_md_url=item.skill_md_url,
            readme_url=item.readme_url,
            market_kind=item.market_kind,
            plugin_name=item.plugin_name,
            plugin_description=item.plugin_description,
            skill_paths=item.skill_paths or [],
            source_branch=item.source_branch,
            source_commit=item.source_commit,
            content_hash=item.content_hash,
            file_count=item.file_count,
            package_size=item.package_size,
            raw_meta=item.raw_meta or {},
        )
        return await cls._install_adapter_item(
            auth=auth,
            source=source,
            item=adapter_item,
            cached_item_id=item.id,
        )

    @classmethod
    async def install_remote_item_service(cls, auth: AuthSchema, source_id: int, external_id: str) -> dict:
        source = await SkillMarketSourceCRUD(auth).get_by_id_crud(id=source_id, preload=[])
        if not source:
            raise CustomException(msg="安装失败，第三方市场源不存在")
        if source.status != "0":
            raise CustomException(msg="安装失败，第三方市场源已停用")
        adapter = cls._build_adapter(
            adapter_type=source.adapter_type,
            base_url=source.base_url,
            branch=source.branch,
            config=source.config,
        )
        for item in await adapter.list_items():
            if item.external_id == external_id:
                return await cls._install_adapter_item(auth=auth, source=source, item=item)
        raise CustomException(msg="安装失败，第三方 Skill 不存在")

    @classmethod
    async def _remote_items_service(
        cls,
        auth: AuthSchema,
        search: SkillMarketItemQueryParam | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        source_id = cls._query_value(search, "source_id")
        source_search = {"status": ("eq", "0")}
        if source_id:
            source_search["id"] = ("eq", source_id)
        sources = await SkillMarketSourceCRUD(auth).list_crud(search=source_search, preload=[])

        rows: list[dict] = []
        for source in sources:
            adapter = cls._build_adapter(
                adapter_type=source.adapter_type,
                base_url=source.base_url,
                branch=source.branch,
                config=source.config,
            )
            for index, item in enumerate(await adapter.list_items(limit=limit), start=1):
                exists = await SkillManagerCRUD(auth).get(name=item.name, preload=[])
                row = cls._remote_item_payload(
                    source_id=source.id,
                    item=item,
                    installed_skill_id=exists.id if exists else None,
                    index=index,
                )
                if cls._match_remote_item(row, search):
                    rows.append(row)
        return rows

    @classmethod
    async def _install_adapter_item(
        cls,
        auth: AuthSchema,
        source,
        item: MarketAdapterItem,
        cached_item_id: int | None = None,
        adapter=None,
    ) -> dict:
        if adapter is None:
            adapter = cls._build_adapter(
                adapter_type=source.adapter_type,
                base_url=source.base_url,
                branch=source.branch,
                config=source.config,
            )
        if item.market_kind == "plugin":
            return await cls._install_plugin_item(
                auth=auth,
                adapter=adapter,
                item=item,
                cached_item_id=cached_item_id,
            )

        exists = await SkillManagerCRUD(auth).get(name=item.name, preload=[])
        if exists:
            if cached_item_id:
                await SkillMarketItemCRUD(auth).update_crud(id=cached_item_id, data={"installed_skill_id": exists.id})
            return await SkillManagerService.detail_service(auth=auth, id=exists.id)

        package = await adapter.get_install_package(item)
        files = [
            SkillManagerFileCreateSchema(
                path=file_item["path"],
                type=file_item.get("type", "file"),
                content=file_item.get("content"),
                content_type=file_item.get("content_type", "text"),
                description=file_item.get("description"),
                status=file_item.get("status", "0"),
            )
            for file_item in package.files
        ]
        skill = await SkillManagerService.create_service(
            auth=auth,
            data=SkillManagerCreateSchema(
                name=item.name,
                title=item.title,
                description=item.description or item.title,
                category=item.category,
                tags=item.tags,
                version=item.version or "1.0.0",
                author=item.author,
                skill_md=package.skill_md,
                readme=package.readme,
                status="0",
                files=files,
            ),
        )
        if cached_item_id:
            await SkillMarketItemCRUD(auth).update_crud(id=cached_item_id, data={"installed_skill_id": skill["id"]})
        return skill

    @classmethod
    async def _install_plugin_item(
        cls,
        auth: AuthSchema,
        adapter,
        item: MarketAdapterItem,
        cached_item_id: int | None = None,
    ) -> dict:
        skill_items = await adapter.list_plugin_skill_items(item)
        installed: list[dict] = []
        for skill_item in skill_items:
            result = await cls._install_adapter_item(auth=auth, source=None, item=skill_item, adapter=adapter)
            installed.append(result)
        if cached_item_id and installed:
            await SkillMarketItemCRUD(auth).update_crud(
                id=cached_item_id,
                data={"installed_skill_id": installed[0].get("id")},
            )
        return {
            "market_kind": "plugin",
            "name": item.name,
            "title": item.title,
            "installed": installed,
        }

    @staticmethod
    def _remote_item_payload(
        source_id: int,
        item: MarketAdapterItem,
        installed_skill_id: int | None,
        index: int,
    ) -> dict:
        return {
            "id": source_id * 1_000_000 + index,
            "source_id": source_id,
            "external_id": item.external_id,
            "name": item.name,
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "tags": item.tags,
            "version": item.version,
            "author": item.author,
            "license": item.license,
            "homepage_url": item.homepage_url,
            "repository_url": item.repository_url,
            "skill_path": item.skill_path,
            "skill_md_url": item.skill_md_url,
            "readme_url": item.readme_url,
            "market_kind": item.market_kind,
            "plugin_name": item.plugin_name,
            "plugin_description": item.plugin_description,
            "skill_paths": item.skill_paths,
            "source_branch": item.source_branch,
            "source_commit": item.source_commit,
            "content_hash": item.content_hash,
            "file_count": item.file_count,
            "package_size": item.package_size,
            "raw_meta": item.raw_meta,
            "installed_skill_id": installed_skill_id,
            "last_sync_time": None,
            "status": "0",
        }

    @classmethod
    def _match_remote_item(cls, row: dict, search: SkillMarketItemQueryParam | None) -> bool:
        if not search:
            return True
        name = cls._query_value(search, "name")
        title = cls._query_value(search, "title")
        category = cls._query_value(search, "category")
        installed_filter = getattr(search, "installed_skill_id", None)
        if name and name.lower() not in str(row.get("name") or "").lower():
            return False
        if title and title.lower() not in str(row.get("title") or "").lower():
            return False
        if category and category.lower() not in str(row.get("category") or "").lower():
            return False
        if installed_filter:
            operator = installed_filter[0]
            if operator == "not None" and row.get("installed_skill_id") is None:
                return False
            if operator == "None" and row.get("installed_skill_id") is not None:
                return False
        return True

    @staticmethod
    def _query_value(search: object | None, key: str):
        if not search or not hasattr(search, key):
            return None
        value = getattr(search, key)
        if isinstance(value, tuple) and len(value) == 2:
            return value[1]
        return value

    @classmethod
    def _has_remote_filter(cls, search: SkillMarketItemQueryParam | None) -> bool:
        if not search:
            return False
        return any(hasattr(search, key) for key in ["source_id", "name", "title", "category", "installed_skill_id"])

    @staticmethod
    def _build_adapter(adapter_type: str, base_url: str, branch: str | None, config: dict | None):
        adapter_cls = ADAPTERS.get(adapter_type)
        if not adapter_cls:
            raise CustomException(msg="暂不支持该第三方市场适配器")
        return adapter_cls(base_url=base_url, branch=branch, config=config)

    @staticmethod
    def _item_payload(source_id: int, item: MarketAdapterItem, sync_time: datetime) -> dict:
        return {
            "source_id": source_id,
            "external_id": item.external_id,
            "name": item.name,
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "tags": item.tags,
            "version": item.version,
            "author": item.author,
            "license": item.license,
            "homepage_url": item.homepage_url,
            "repository_url": item.repository_url,
            "skill_path": item.skill_path,
            "skill_md_url": item.skill_md_url,
            "readme_url": item.readme_url,
            "market_kind": item.market_kind,
            "plugin_name": item.plugin_name,
            "plugin_description": item.plugin_description,
            "skill_paths": item.skill_paths,
            "source_branch": item.source_branch,
            "source_commit": item.source_commit,
            "content_hash": item.content_hash,
            "file_count": item.file_count,
            "package_size": item.package_size,
            "raw_meta": item.raw_meta,
            "last_sync_time": sync_time,
            "status": "0",
        }

    @classmethod
    async def _cache_empty(cls, auth: AuthSchema, search: SkillMarketItemQueryParam | None) -> bool:
        search_dict = {"status": ("eq", "0")}
        source_id = cls._query_value(search, "source_id")
        if source_id:
            search_dict["source_id"] = ("eq", source_id)
        rows = await SkillMarketItemCRUD(auth).list_crud(search=search_dict, preload=[])
        return len(rows) == 0

    @classmethod
    async def _sync_matching_sources(cls, auth: AuthSchema, search: SkillMarketItemQueryParam | None) -> None:
        source_id = cls._query_value(search, "source_id")
        source_search = {"status": ("eq", "0")}
        if source_id:
            source_search["id"] = ("eq", source_id)
        sources = await SkillMarketSourceCRUD(auth).list_crud(search=source_search, preload=[])
        for source in sources:
            await cls.sync_source_service(auth=auth, source_id=source.id)

    @classmethod
    async def _cache_stale(cls, auth: AuthSchema, search: SkillMarketItemQueryParam | None) -> bool:
        source_id = cls._query_value(search, "source_id")
        source_search = {"status": ("eq", "0")}
        if source_id:
            source_search["id"] = ("eq", source_id)
        sources = await SkillMarketSourceCRUD(auth).list_crud(search=source_search, preload=[])
        now = datetime.now()
        for source in sources:
            ttl_minutes = int((source.config or {}).get("cache_ttl_minutes") or 0)
            if ttl_minutes <= 0:
                continue
            if not source.last_sync_time or source.last_sync_time + timedelta(minutes=ttl_minutes) <= now:
                return True
        return False

    @staticmethod
    async def _disable_missing_items(auth: AuthSchema, source_id: int, active_external_ids: set[str]) -> None:
        rows = await SkillMarketItemCRUD(auth).list_crud(
            search={"source_id": ("eq", source_id)},
            preload=[],
        )
        for row in rows:
            if row.external_id not in active_external_ids and row.status == "0":
                await SkillMarketItemCRUD(auth).update_crud(id=row.id, data={"status": "1"})
