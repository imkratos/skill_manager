# 后端代码模板（FastAPI 插件模块）

> 本文件供 `SKILL.md` 在 Step 3 执行后端文件写入前按需读取。涉及后端改动（操作类型 A、B）时读取。
> 模板取自真实模块 `backend/app/plugin/module_example/demo/`，生成前优先 Read 一个同类型真实模块对照。

## 文件清单（单资源标准结构）

```text
backend/app/plugin/module_<domain>/<resource>/
├── __init__.py        # 可为空，仅作包标识
├── model.py           # SQLAlchemy 2.0 ORM 模型
├── schema.py          # Create/Update/Out/QueryParam
├── crud.py            # 继承 CRUDBase
├── service.py         # 业务逻辑
└── controller.py      # APIRouter + 路由
```

> 插件顶级目录必须是 `module_*`，否则动态路由不扫描。每级 Python 目录需是合法标识符并含 `__init__.py`。

## Model

```python
from app.core.base_model import ModelMixin, TenantMixin, UserMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Text, JSON, DateTime, Date, Time

class XxxModel(ModelMixin, TenantMixin, UserMixin):
    """业务表说明"""
    __tablename__: str = "prefix_xxx"
    __table_args__: dict[str, str] = {"comment": "业务表说明"}
    __loader_options__: list[str] = ["created_by", "updated_by", "deleted_by"]

    # SQLAlchemy 2.0 写法
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="名称")
    status: Mapped[str] = mapped_column(String(2), default="0", nullable=False, comment="状态(0:启用 1:禁用)")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
```

规则：
- 业务表优先继承 `ModelMixin`；需要租户隔离加 `TenantMixin`；需要审计用户加 `UserMixin`。
- 表名使用业务前缀，如 `skill_definition`、`skill_version`。
- 字段用 SQLAlchemy 2.0 写法：`Mapped[T] = mapped_column(...)`。
- 多租户敏感表不绕过 `TenantMixin` 和权限过滤。

## Schema

```python
from dataclasses import dataclass
from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema, UserBySchema
from app.core.validator import DateStr, DateTimeStr, TimeStr

class XxxCreateSchema(BaseModel):
    """新增模型"""
    name: str = Field(..., description="名称")
    status: str = Field(default="0", description="状态(0:启用 1:禁用)")
    description: str | None = Field(default=None, description="描述")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("名称不能为空")
        return v

    @model_validator(mode="after")
    def _after_validation(self):
        """核心业务规则校验"""
        if self.status not in ["0", "1"]:
            raise ValueError("状态必须为0或1")
        return self

class XxxUpdateSchema(XxxCreateSchema):
    """更新模型"""

class XxxOutSchema(XxxCreateSchema, BaseSchema, UserBySchema):
    """响应模型"""
    model_config = ConfigDict(from_attributes=True)

@dataclass
class XxxQueryParam:
    """查询参数"""
    def __init__(
        self,
        name: str | None = Query(None, description="名称"),
        status: str | None = Query(None, description="状态"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围"),
    ) -> None:
        self.name = (QueueEnum.like.value, name)          # 模糊查询
        if status:
            self.status = (QueueEnum.eq.value, status)    # 精确查询
        if created_time and len(created_time) == 2:
            self.created_time = (QueueEnum.between.value, (created_time[0], created_time[1]))
```

规则：
- 创建、更新、输出、查询参数分开建模。
- 输出模型继承 `BaseSchema`；含审计用户时继承 `UserBySchema`。
- 查询参数用 dataclass + `fastapi.Query`，条件转换为 `QueueEnum.like/eq/between`。
- 字段级校验放 Pydantic validator；业务唯一性、关联存在性放 Service。
- 时间/日期字段用 `app.core.validator` 的 `DateStr/TimeStr/DateTimeStr`。

## CRUD

```python
from app.core.base_crud import CRUDBase
from app.api.v1.module_system.auth.schema import AuthSchema
from .model import XxxModel
from .schema import XxxCreateSchema, XxxUpdateSchema

class XxxCRUD(CRUDBase[XxxModel, XxxCreateSchema, XxxUpdateSchema]):
    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=XxxModel, auth=auth)

    async def get_by_id_crud(self, id: int) -> XxxModel | None:
        return await self.get(id=id)
```

## Service

```python
from app.core.exceptions import CustomException
from app.core.logger import log
from .crud import XxxCRUD
from .schema import XxxCreateSchema, XxxOutSchema, XxxQueryParam, XxxUpdateSchema

class XxxService:
    @classmethod
    async def detail_service(cls, auth, id: int) -> dict:
        obj = await XxxCRUD(auth).get_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg="该数据不存在")
        return XxxOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def page_service(cls, auth, page_no: int, page_size: int, search=None, order_by=None) -> dict:
        search_dict = search.__dict__ if search else {}
        order_by_list = order_by or [{"id": "asc"}]
        offset = (page_no - 1) * page_size
        return await XxxCRUD(auth).page_crud(offset=offset, limit=page_size, order_by=order_by_list, search=search_dict)

    @classmethod
    async def create_service(cls, auth, data: XxxCreateSchema) -> dict:
        obj = await XxxCRUD(auth).get(name=data.name)
        if obj:
            raise CustomException(msg="创建失败，名称已存在")
        obj = await XxxCRUD(auth).create_crud(data=data)
        return XxxOutSchema.model_validate(obj).model_dump()
```

规则：
- Service 负责业务规则、重复校验、存在性校验、导入导出转换。
- 返回错误使用 `CustomException`，不要直接返回不一致的 dict。
- 日志使用 `app.core.logger.log`，中文消息要能定位业务动作。

## Controller

```python
from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, Body
from fastapi.responses import JSONResponse, StreamingResponse
from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.base_schema import BatchSetAvailable
from app.core.dependencies import AuthPermission
from app.core.router_class import OperationLogRoute
from .schema import XxxCreateSchema, XxxOutSchema, XxxQueryParam, XxxUpdateSchema
from .service import XxxService

XxxRouter = APIRouter(route_class=OperationLogRoute, prefix="/xxx", tags=["Xxx模块"])

@XxxRouter.get("/detail/{id}", summary="详情", response_model=ResponseSchema[XxxOutSchema])
async def get_detail(
    id: Annotated[int, Path(description="ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_<domain>:xxx:detail"]))],
) -> JSONResponse:
    data = await XxxService.detail_service(auth=auth, id=id)
    return SuccessResponse(data)

@XxxRouter.get("/list", summary="分页列表", response_model=ResponseSchema[list[XxxOutSchema]])
async def get_list(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[XxxQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_<domain>:xxx:query"]))],
) -> JSONResponse:
    data = await XxxService.page_service(auth=auth, page_no=page.page_no, page_size=page.page_size, search=search, order_by=page.order_by)
    return SuccessResponse(data)

@XxxRouter.post("/create", summary="创建", response_model=ResponseSchema)
async def create(
    body: Annotated[XxxCreateSchema, Body()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_<domain>:xxx:create"]))],
) -> JSONResponse:
    await XxxService.create_service(auth=auth, data=body)
    return SuccessResponse()
```

规则：
- Controller 只做 HTTP 入参、权限依赖、调用 Service、返回 `SuccessResponse`。
- `prefix` 由控制器自身定义；完整路径 = 目录推导前缀 + 控制器 prefix，如 `module_skill` + `prefix="/definition"` → `/skill/definition/...`。
- 权限码格式：`module_<domain>:<resource>:<action>`（query/detail/create/update/delete/patch/import/export/download）。
- 标准 CRUD 端点：`/detail/{id}`、`/list`、`/create`、`/update/{id}`、`/delete`、`/available/setting`(patch)、`/export`、`/import`、`/download/template`。按实际需要裁剪，但权限码必须与菜单迁移、前端按钮三处一致。

## plugin.toml（可选，建议创建）

每个插件顶级目录（`module_<domain>/`）可放 `plugin.toml`，供文档/运维/门户展示。**不用于运行时 pip 安装依赖。**

```toml
# backend/app/plugin/module_<domain>/plugin.toml
name = "<domain>"
title = "<中文插件名>"
version = "1.0.0"
description = "<功能简述>"
optional = true
tags = ["<tag1>", "<tag2>"]
```
