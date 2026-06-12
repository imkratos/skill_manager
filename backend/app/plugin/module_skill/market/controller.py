from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.request import PageResultSchema
from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.logger import log
from app.core.router_class import OperationLogRoute

from .schema import (
    SkillMarketItemOutSchema,
    SkillMarketItemQueryParam,
    SkillMarketRemoteInstallSchema,
    SkillMarketSourceCreateSchema,
    SkillMarketSourceOutSchema,
    SkillMarketSourceQueryParam,
    SkillMarketSourceUpdateSchema,
    SkillMarketSyncResultSchema,
)
from .service import SkillMarketService

SkillMarketRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/market",
    tags=["Skill 第三方市场"],
)


@SkillMarketRouter.get(
    "/source/detail/{id}",
    summary="获取第三方市场源详情",
    response_model=ResponseSchema[SkillMarketSourceOutSchema],
)
async def get_market_source_detail_controller(
    id: Annotated[int, Path(description="市场源ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:market:detail"]))],
) -> JSONResponse:
    result = await SkillMarketService.source_detail_service(auth=auth, id=id)
    log.info(f"获取第三方市场源详情成功: {id}")
    return SuccessResponse(data=result, msg="获取第三方市场源详情成功")


@SkillMarketRouter.get(
    "/source/list",
    summary="查询第三方市场源列表",
    response_model=ResponseSchema[PageResultSchema],
)
async def get_market_source_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[SkillMarketSourceQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:market:query"]))],
) -> JSONResponse:
    result = await SkillMarketService.source_page_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    log.info("查询第三方市场源列表成功")
    return SuccessResponse(data=result, msg="查询第三方市场源列表成功")


@SkillMarketRouter.post(
    "/source/create",
    summary="创建第三方市场源",
    response_model=ResponseSchema[SkillMarketSourceOutSchema],
)
async def create_market_source_controller(
    data: SkillMarketSourceCreateSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:market:create"]))],
) -> JSONResponse:
    result = await SkillMarketService.source_create_service(auth=auth, data=data)
    log.info(f"创建第三方市场源成功: {result.get('code')}")
    return SuccessResponse(data=result, msg="创建第三方市场源成功")


@SkillMarketRouter.put(
    "/source/update/{id}",
    summary="修改第三方市场源",
    response_model=ResponseSchema[SkillMarketSourceOutSchema],
)
async def update_market_source_controller(
    data: SkillMarketSourceUpdateSchema,
    id: Annotated[int, Path(description="市场源ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:market:update"]))],
) -> JSONResponse:
    result = await SkillMarketService.source_update_service(auth=auth, id=id, data=data)
    log.info(f"修改第三方市场源成功: {result.get('code')}")
    return SuccessResponse(data=result, msg="修改第三方市场源成功")


@SkillMarketRouter.delete(
    "/source/delete",
    summary="删除第三方市场源",
    response_model=ResponseSchema[None],
)
async def delete_market_source_controller(
    ids: Annotated[list[int], Body(description="ID 列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:market:delete"]))],
) -> JSONResponse:
    await SkillMarketService.source_delete_service(auth=auth, ids=ids)
    log.info(f"删除第三方市场源成功: {ids}")
    return SuccessResponse(msg="删除第三方市场源成功")


@SkillMarketRouter.post(
    "/source/{id}/sync",
    summary="同步第三方市场源",
    response_model=ResponseSchema[SkillMarketSyncResultSchema],
)
async def sync_market_source_controller(
    id: Annotated[int, Path(description="市场源ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:market:sync"]))],
) -> JSONResponse:
    result = await SkillMarketService.sync_source_service(auth=auth, source_id=id)
    log.info(f"同步第三方市场源成功: {id}")
    return SuccessResponse(data=result, msg="同步第三方市场源成功")


@SkillMarketRouter.get(
    "/item/detail/{id}",
    summary="获取第三方 Skill 详情",
    response_model=ResponseSchema[SkillMarketItemOutSchema],
)
async def get_market_item_detail_controller(
    id: Annotated[int, Path(description="第三方 Skill ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:market:detail"]))],
) -> JSONResponse:
    result = await SkillMarketService.item_detail_service(auth=auth, id=id)
    log.info(f"获取第三方 Skill 详情成功: {id}")
    return SuccessResponse(data=result, msg="获取第三方 Skill 详情成功")


@SkillMarketRouter.get(
    "/item/list",
    summary="查询第三方 Skill 列表",
    response_model=ResponseSchema[PageResultSchema],
)
async def get_market_item_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[SkillMarketItemQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:market:query"]))],
) -> JSONResponse:
    result = await SkillMarketService.item_page_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by,
    )
    log.info("查询第三方 Skill 列表成功")
    return SuccessResponse(data=result, msg="查询第三方 Skill 列表成功")


@SkillMarketRouter.post(
    "/item/{id}/install",
    summary="安装第三方 Skill",
    response_model=ResponseSchema[dict],
)
async def install_market_item_controller(
    id: Annotated[int, Path(description="第三方 Skill ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:market:install"]))],
) -> JSONResponse:
    result = await SkillMarketService.install_item_service(auth=auth, item_id=id)
    log.info(f"安装第三方 Skill 成功: {id}")
    return SuccessResponse(data=result, msg="安装第三方 Skill 成功")


@SkillMarketRouter.post(
    "/item/install-remote",
    summary="安装远程第三方 Skill",
    response_model=ResponseSchema[dict],
)
async def install_remote_market_item_controller(
    data: SkillMarketRemoteInstallSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_skill:market:install"]))],
) -> JSONResponse:
    result = await SkillMarketService.install_remote_item_service(
        auth=auth,
        source_id=data.source_id,
        external_id=data.external_id,
    )
    log.info(f"安装远程第三方 Skill 成功: {data.source_id}/{data.external_id}")
    return SuccessResponse(data=result, msg="安装第三方 Skill 成功")
