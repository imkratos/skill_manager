import re
from dataclasses import dataclass
from datetime import datetime

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema, UserBySchema
from app.core.validator import DateTimeStr

SUPPORTED_ADAPTER_TYPES = {"github_repo"}


class SkillMarketSourceCreateSchema(BaseModel):
    """新增第三方市场源模型"""

    name: str = Field(..., description="平台名称")
    code: str = Field(..., description="平台编码")
    adapter_type: str = Field(default="github_repo", description="适配器类型")
    base_url: str = Field(..., description="市场地址")
    branch: str | None = Field(default=None, description="分支")
    config: dict | None = Field(default=None, description="适配器配置")
    sort: int = Field(default=0, description="排序")
    status: str = Field(default="0", description="状态(0:启用 1:停用)")
    description: str | None = Field(default=None, description="说明")

    @field_validator("name", "code", "base_url")
    @classmethod
    def validate_required_text(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("必填文本不能为空")
        return value

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        value = v.strip()
        if not re.fullmatch(r"[a-zA-Z0-9_-]{2,100}", value):
            raise ValueError("平台编码只能包含字母、数字、下划线和中划线，长度 2-100")
        return value

    @model_validator(mode="after")
    def validate_source(self):
        if self.adapter_type not in SUPPORTED_ADAPTER_TYPES:
            raise ValueError("暂不支持该适配器类型")
        if self.status not in ["0", "1"]:
            raise ValueError("状态必须为0或1")
        return self


class SkillMarketSourceUpdateSchema(SkillMarketSourceCreateSchema):
    """更新第三方市场源模型"""


class SkillMarketSourceOutSchema(SkillMarketSourceCreateSchema, BaseSchema, UserBySchema):
    """第三方市场源响应模型"""

    model_config = ConfigDict(from_attributes=True)

    last_sync_time: datetime | None = Field(default=None, description="最后同步时间")
    last_sync_status: str | None = Field(default=None, description="最后同步状态")
    last_sync_message: str | None = Field(default=None, description="最后同步消息")


class SkillMarketItemCreateSchema(BaseModel):
    """第三方市场 Skill 缓存模型"""

    source_id: int = Field(..., description="市场源ID")
    external_id: str = Field(..., description="外部唯一标识")
    name: str = Field(..., description="Skill 标识")
    title: str = Field(..., description="显示名称")
    description: str | None = Field(default=None, description="简介")
    category: str | None = Field(default=None, description="分类")
    tags: list[str] | None = Field(default=None, description="标签")
    version: str | None = Field(default=None, description="版本号")
    author: str | None = Field(default=None, description="作者")
    license: str | None = Field(default=None, description="许可证")
    homepage_url: str | None = Field(default=None, description="主页地址")
    repository_url: str | None = Field(default=None, description="仓库地址")
    skill_path: str = Field(..., description="Skill 目录路径")
    skill_md_url: str | None = Field(default=None, description="SKILL.md 地址")
    readme_url: str | None = Field(default=None, description="README 地址")
    raw_meta: dict | None = Field(default=None, description="原始元数据")
    market_kind: str = Field(default="skill", description="市场条目类型(skill/plugin)")
    plugin_name: str | None = Field(default=None, description="插件包名称")
    plugin_description: str | None = Field(default=None, description="插件包说明")
    skill_paths: list[str] | None = Field(default=None, description="插件包包含的 Skill 路径")
    source_branch: str | None = Field(default=None, description="来源分支")
    source_commit: str | None = Field(default=None, description="来源提交")
    content_hash: str | None = Field(default=None, description="内容哈希")
    file_count: int = Field(default=0, description="文件数量")
    package_size: int = Field(default=0, description="包大小")
    installed_skill_id: int | None = Field(default=None, description="已安装 Skill ID")
    last_sync_time: datetime | None = Field(default=None, description="最后同步时间")
    status: str = Field(default="0", description="状态(0:启用 1:停用)")


class SkillMarketItemUpdateSchema(SkillMarketItemCreateSchema):
    """更新第三方市场 Skill 缓存模型"""


class SkillMarketItemOutSchema(SkillMarketItemCreateSchema, BaseSchema, UserBySchema):
    """第三方市场 Skill 响应模型"""

    model_config = ConfigDict(from_attributes=True)


class SkillMarketSyncResultSchema(BaseModel):
    """市场同步结果"""

    source_id: int = Field(..., description="市场源ID")
    total: int = Field(..., description="同步条目总数")
    created: int = Field(..., description="新增数量")
    updated: int = Field(..., description="更新数量")


class SkillMarketRemoteInstallSchema(BaseModel):
    """远程市场 Skill 安装模型"""

    source_id: int = Field(..., description="市场源ID")
    external_id: str = Field(..., description="外部唯一标识")


@dataclass
class SkillMarketSourceQueryParam:
    """第三方市场源查询参数"""

    def __init__(
        self,
        name: str | None = Query(None, description="平台名称"),
        code: str | None = Query(None, description="平台编码"),
        adapter_type: str | None = Query(None, description="适配器类型"),
        status: str | None = Query(None, description="状态"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围"),
        updated_time: list[DateTimeStr] | None = Query(None, description="更新时间范围"),
    ) -> None:
        if name:
            self.name = (QueueEnum.like.value, name)
        if code:
            self.code = (QueueEnum.like.value, code)
        if adapter_type:
            self.adapter_type = (QueueEnum.eq.value, adapter_type)
        if status:
            self.status = (QueueEnum.eq.value, status)
        if created_time and len(created_time) == 2:
            self.created_time = (QueueEnum.between.value, (created_time[0], created_time[1]))
        if updated_time and len(updated_time) == 2:
            self.updated_time = (QueueEnum.between.value, (updated_time[0], updated_time[1]))


@dataclass
class SkillMarketItemQueryParam:
    """第三方市场 Skill 查询参数"""

    def __init__(
        self,
        source_id: int | None = Query(None, description="市场源ID"),
        market_kind: str | None = Query(None, description="市场条目类型"),
        plugin_name: str | None = Query(None, description="插件包名称"),
        name: str | None = Query(None, description="Skill 标识"),
        title: str | None = Query(None, description="显示名称"),
        category: str | None = Query(None, description="分类"),
        status: str | None = Query(None, description="状态"),
        installed: bool | None = Query(None, description="是否已安装"),
        refresh: bool = Query(False, description="是否刷新远端缓存"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围"),
        updated_time: list[DateTimeStr] | None = Query(None, description="更新时间范围"),
    ) -> None:
        self.refresh = refresh
        if source_id:
            self.source_id = (QueueEnum.eq.value, source_id)
        if market_kind:
            self.market_kind = (QueueEnum.eq.value, market_kind)
        if plugin_name:
            self.plugin_name = (QueueEnum.like.value, plugin_name)
        if name:
            self.name = (QueueEnum.like.value, name)
        if title:
            self.title = (QueueEnum.like.value, title)
        if category:
            self.category = (QueueEnum.like.value, category)
        if status:
            self.status = (QueueEnum.eq.value, status)
        if installed is True:
            self.installed_skill_id = (QueueEnum.not_none.value, None)
        elif installed is False:
            self.installed_skill_id = (QueueEnum.none.value, None)
        if created_time and len(created_time) == 2:
            self.created_time = (QueueEnum.between.value, (created_time[0], created_time[1]))
        if updated_time and len(updated_time) == 2:
            self.updated_time = (QueueEnum.between.value, (updated_time[0], updated_time[1]))
