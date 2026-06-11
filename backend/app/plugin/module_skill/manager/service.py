import io
import zipfile
from pathlib import PurePosixPath

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.exceptions import CustomException

from .crud import SkillManagerCRUD, SkillManagerFileCRUD
from .schema import (
    SkillManagerCardOutSchema,
    SkillManagerCreateSchema,
    SkillManagerFileCreateSchema,
    SkillManagerFileOutSchema,
    SkillManagerFileSaveSchema,
    SkillManagerQueryParam,
    SkillManagerUpdateSchema,
)


class SkillManagerService:
    """Skill 管理服务层"""

    @classmethod
    async def detail_service(cls, auth: AuthSchema, id: int) -> dict:
        obj = await SkillManagerCRUD(auth).get_by_id_crud(id=id, preload=[])
        if not obj:
            raise CustomException(msg="Skill 不存在")
        result = SkillManagerCardOutSchema.model_validate(obj).model_dump()
        result["skill_md"] = obj.skill_md
        result["readme"] = obj.readme
        result["files"] = await cls.file_list_service(auth=auth, skill_id=id)
        return result

    @classmethod
    async def page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: SkillManagerQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict:
        search_dict = search.__dict__ if search else {}
        offset = (page_no - 1) * page_size
        return await SkillManagerCRUD(auth).page_crud(
            offset=offset,
            limit=page_size,
            order_by=order_by,
            search=search_dict,
            preload=[],
        )

    @classmethod
    async def create_service(cls, auth: AuthSchema, data: SkillManagerCreateSchema) -> dict:
        exists = await SkillManagerCRUD(auth).get(name=data.name)
        if exists:
            raise CustomException(msg="创建失败，Skill 标识已存在")

        payload = data.model_dump(exclude={"files"})
        obj = await SkillManagerCRUD(auth).create_crud(data=payload)
        await cls._replace_files(auth=auth, skill_id=obj.id, files=data.files)
        return await cls.detail_service(auth=auth, id=obj.id)

    @classmethod
    async def update_service(cls, auth: AuthSchema, id: int, data: SkillManagerUpdateSchema) -> dict:
        obj = await SkillManagerCRUD(auth).get_by_id_crud(id=id, preload=[])
        if not obj:
            raise CustomException(msg="更新失败，Skill 不存在")

        exists = await SkillManagerCRUD(auth).get(name=data.name, preload=[])
        if exists and exists.id != id:
            raise CustomException(msg="更新失败，Skill 标识重复")

        payload = data.model_dump(exclude={"files"})
        await SkillManagerCRUD(auth).update_crud(id=id, data=payload)
        await cls._replace_files(auth=auth, skill_id=id, files=data.files)
        return await cls.detail_service(auth=auth, id=id)

    @classmethod
    async def delete_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        if not ids:
            raise CustomException(msg="删除失败，删除对象不能为空")
        for id in ids:
            obj = await SkillManagerCRUD(auth).get_by_id_crud(id=id, preload=[])
            if not obj:
                raise CustomException(msg=f"删除失败，ID 为 {id} 的 Skill 不存在")
            await SkillManagerFileCRUD(auth).delete_by_skill_crud(skill_id=id)
        await SkillManagerCRUD(auth).delete_crud(ids=ids)

    @classmethod
    async def file_list_service(cls, auth: AuthSchema, skill_id: int) -> list[dict]:
        obj = await SkillManagerCRUD(auth).get_by_id_crud(id=skill_id, preload=[])
        if not obj:
            raise CustomException(msg="Skill 不存在")
        files = await SkillManagerFileCRUD(auth).list_by_skill_crud(skill_id=skill_id)
        return [SkillManagerFileOutSchema.model_validate(item).model_dump() for item in files]

    @classmethod
    async def file_save_service(
        cls,
        auth: AuthSchema,
        skill_id: int,
        data: SkillManagerFileSaveSchema,
    ) -> list[dict]:
        obj = await SkillManagerCRUD(auth).get_by_id_crud(id=skill_id, preload=[])
        if not obj:
            raise CustomException(msg="Skill 不存在")
        await cls._replace_files(auth=auth, skill_id=skill_id, files=data.files)
        return await cls.file_list_service(auth=auth, skill_id=skill_id)

    @classmethod
    async def download_service(cls, auth: AuthSchema, id: int) -> tuple[str, bytes]:
        obj = await SkillManagerCRUD(auth).get_by_id_crud(id=id, preload=[])
        if not obj:
            raise CustomException(msg="Skill 不存在")
        files = await SkillManagerFileCRUD(auth).list_by_skill_crud(skill_id=id)

        root_name = cls._safe_root_name(obj.name)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(f"{root_name}/SKILL.md", obj.skill_md)
            if obj.readme:
                zip_file.writestr(f"{root_name}/README.md", obj.readme)
            for item in sorted(files, key=lambda file: (file.sort, file.id)):
                if item.status != "0" or item.is_deleted:
                    continue
                path = PurePosixPath(item.path)
                zip_path = f"{root_name}/{path.as_posix()}"
                if item.type == "directory":
                    zip_file.writestr(f"{zip_path.rstrip('/')}/", "")
                else:
                    zip_file.writestr(zip_path, item.content or "")
        buffer.seek(0)
        return f"{root_name}.zip", buffer.getvalue()

    @classmethod
    async def _replace_files(
        cls,
        auth: AuthSchema,
        skill_id: int,
        files: list[SkillManagerFileCreateSchema],
    ) -> None:
        await SkillManagerFileCRUD(auth).delete_by_skill_crud(skill_id=skill_id)

        seen_paths: set[str] = set()
        for index, file_item in enumerate(files):
            payload = file_item.model_dump()
            payload["skill_id"] = skill_id
            payload["sort"] = payload.get("sort") or index
            path = payload["path"]
            if path in seen_paths:
                raise CustomException(msg=f"引用文件路径重复: {path}")
            seen_paths.add(path)
            await SkillManagerFileCRUD(auth).create_crud(data=payload)

    @staticmethod
    def _safe_root_name(name: str) -> str:
        safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in name.strip())
        return safe or "skill"
