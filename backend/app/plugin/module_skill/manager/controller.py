import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.response import ResponseSchema, StreamResponse, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.logger import log
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response

from .schema import (
    SkillManagerCreateSchema,
    SkillManagerFileOutSchema,
    SkillManagerFileSaveSchema,
    SkillManagerOutSchema,
    SkillManagerQueryParam,
    SkillManagerUpdateSchema,
)
from .service import SkillManagerService

SkillManagerRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/manager",
    tags=["Skill 管理"],
)


@SkillManagerRouter.get(
    "/detail/{id}",
    summary="获取 Skill 详情",
    response_model=ResponseSchema[SkillManagerOutSchema],
)
async def get_skill_detail_controller(
    id: Annotated[int, Path(description="Skill ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:manager:detail"]))],
) -> JSONResponse:
    result = await SkillManagerService.detail_service(auth=auth, id=id)
    log.info(f"获取 Skill 详情成功: {id}")
    return SuccessResponse(data=result, msg="获取 Skill 详情成功")


@SkillManagerRouter.get(
    "/list",
    summary="查询 Skill 列表",
    response_model=ResponseSchema[list[SkillManagerOutSchema]],
)
async def get_skill_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[SkillManagerQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:manager:query"]))],
) -> JSONResponse:
    result = await SkillManagerService.page_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    log.info("查询 Skill 列表成功")
    return SuccessResponse(data=result, msg="查询 Skill 列表成功")


@SkillManagerRouter.post(
    "/create",
    summary="创建 Skill",
    response_model=ResponseSchema[SkillManagerOutSchema],
)
async def create_skill_controller(
    data: SkillManagerCreateSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:manager:create"]))],
) -> JSONResponse:
    result = await SkillManagerService.create_service(auth=auth, data=data)
    log.info(f"创建 Skill 成功: {result.get('name')}")
    return SuccessResponse(data=result, msg="创建 Skill 成功")


@SkillManagerRouter.put(
    "/update/{id}",
    summary="修改 Skill",
    response_model=ResponseSchema[SkillManagerOutSchema],
)
async def update_skill_controller(
    data: SkillManagerUpdateSchema,
    id: Annotated[int, Path(description="Skill ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:manager:update"]))],
) -> JSONResponse:
    result = await SkillManagerService.update_service(auth=auth, id=id, data=data)
    log.info(f"修改 Skill 成功: {result.get('name')}")
    return SuccessResponse(data=result, msg="修改 Skill 成功")


@SkillManagerRouter.delete(
    "/delete",
    summary="删除 Skill",
    response_model=ResponseSchema[None],
)
async def delete_skill_controller(
    ids: Annotated[list[int], Body(description="ID 列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:manager:delete"]))],
) -> JSONResponse:
    await SkillManagerService.delete_service(auth=auth, ids=ids)
    log.info(f"删除 Skill 成功: {ids}")
    return SuccessResponse(msg="删除 Skill 成功")


@SkillManagerRouter.get(
    "/{id}/files",
    summary="获取 Skill 引用文件",
    response_model=ResponseSchema[list[SkillManagerFileOutSchema]],
)
async def get_skill_files_controller(
    id: Annotated[int, Path(description="Skill ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:manager:detail"]))],
) -> JSONResponse:
    result = await SkillManagerService.file_list_service(auth=auth, skill_id=id)
    log.info(f"获取 Skill 引用文件成功: {id}")
    return SuccessResponse(data=result, msg="获取 Skill 引用文件成功")


@SkillManagerRouter.post(
    "/{id}/files/save",
    summary="保存 Skill 引用文件",
    response_model=ResponseSchema[list[SkillManagerFileOutSchema]],
)
async def save_skill_files_controller(
    id: Annotated[int, Path(description="Skill ID")],
    data: SkillManagerFileSaveSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:manager:update"]))],
) -> JSONResponse:
    result = await SkillManagerService.file_save_service(auth=auth, skill_id=id, data=data)
    log.info(f"保存 Skill 引用文件成功: {id}")
    return SuccessResponse(data=result, msg="保存 Skill 引用文件成功")


@SkillManagerRouter.get(
    "/{id}/download",
    summary="下载 Skill 标准目录包",
)
async def download_skill_controller(
    id: Annotated[int, Path(description="Skill ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:manager:download"]))],
) -> StreamingResponse:
    filename, content = await SkillManagerService.download_service(auth=auth, id=id)
    log.info(f"下载 Skill 标准目录包成功: {id}")
    return StreamResponse(
        data=bytes2file_response(content),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={urllib.parse.quote(filename)}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
