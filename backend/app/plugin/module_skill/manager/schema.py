import re
from dataclasses import dataclass

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema, UserBySchema
from app.core.validator import DateTimeStr

VALID_FILE_TYPES = {"file", "directory"}
VALID_CONTENT_TYPES = {"markdown", "python", "shell", "json", "text", "binary"}


def validate_relative_path(value: str) -> str:
    """校验 Skill 内部文件相对路径。"""
    path = value.strip().replace("\\", "/")
    if not path:
        raise ValueError("路径不能为空")
    if path.startswith("/") or path.startswith("./") or ".." in path.split("/"):
        raise ValueError("路径必须是安全的相对路径")
    if "//" in path:
        raise ValueError("路径不能包含连续斜杠")
    return path.rstrip("/")


class SkillManagerFileBaseSchema(BaseModel):
    """Skill 引用文件基础模型"""

    path: str = Field(..., description="相对路径")
    type: str = Field(default="file", description="类型(file/directory)")
    content: str | None = Field(default=None, description="文件内容")
    content_type: str = Field(default="markdown", description="内容类型")
    size: int = Field(default=0, ge=0, description="文件大小")
    sort: int = Field(default=0, description="排序")
    description: str | None = Field(default=None, description="说明")
    status: str = Field(default="0", description="状态(0:启用 1:禁用)")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        return validate_relative_path(v)

    @model_validator(mode="after")
    def validate_file(self):
        if self.type not in VALID_FILE_TYPES:
            raise ValueError("文件类型必须为 file 或 directory")
        if self.content_type not in VALID_CONTENT_TYPES:
            raise ValueError("内容类型不合法")
        if self.type == "directory":
            self.content = None
            self.size = 0
        elif self.content is not None:
            self.size = len(self.content.encode("utf-8"))
        return self


class SkillManagerFileCreateSchema(SkillManagerFileBaseSchema):
    """新增引用文件模型"""

    skill_id: int | None = Field(default=None, description="Skill ID")


class SkillManagerFileUpdateSchema(SkillManagerFileCreateSchema):
    """更新引用文件模型"""


class SkillManagerFileOutSchema(SkillManagerFileBaseSchema, BaseSchema, UserBySchema):
    """引用文件响应模型"""

    model_config = ConfigDict(from_attributes=True)

    skill_id: int = Field(..., description="Skill ID")


class SkillManagerCreateSchema(BaseModel):
    """新增 Skill 模型"""

    name: str = Field(..., description="Skill 唯一标识")
    title: str = Field(..., description="显示名称")
    description: str = Field(..., description="简介")
    category: str | None = Field(default=None, description="分类")
    tags: list[str] | None = Field(default=None, description="标签")
    version: str = Field(default="1.0.0", description="版本号")
    author: str | None = Field(default=None, description="作者")
    skill_md: str = Field(..., description="SKILL.md 内容")
    readme: str | None = Field(default=None, description="README.md 内容")
    sort: int = Field(default=0, description="排序")
    status: str = Field(default="0", description="状态(0:启用 1:停用)")
    files: list[SkillManagerFileCreateSchema] = Field(default_factory=list, description="引用文件")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        value = v.strip()
        if not re.fullmatch(r"[a-zA-Z0-9_-]{2,100}", value):
            raise ValueError("Skill 标识只能包含字母、数字、下划线和中划线，长度 2-100")
        return value

    @field_validator("title", "description", "skill_md")
    @classmethod
    def validate_required_text(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("必填文本不能为空")
        return value

    @model_validator(mode="after")
    def validate_skill(self):
        if self.status not in ["0", "1"]:
            raise ValueError("状态必须为0或1")
        if not self.skill_md.lstrip().startswith("---"):
            raise ValueError("SKILL.md 内容必须包含标准 YAML Frontmatter")
        return self


class SkillManagerUpdateSchema(SkillManagerCreateSchema):
    """更新 Skill 模型"""


class SkillManagerOutSchema(SkillManagerCreateSchema, BaseSchema, UserBySchema):
    """Skill 响应模型"""

    model_config = ConfigDict(from_attributes=True)

    files: list[SkillManagerFileOutSchema] = Field(default_factory=list, description="引用文件")


class SkillManagerCardOutSchema(BaseSchema, UserBySchema):
    """Skill 卡片列表响应模型"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Skill 唯一标识")
    title: str = Field(..., description="显示名称")
    description: str = Field(..., description="简介")
    category: str | None = Field(default=None, description="分类")
    tags: list[str] | None = Field(default=None, description="标签")
    version: str = Field(default="1.0.0", description="版本号")
    author: str | None = Field(default=None, description="作者")
    sort: int = Field(default=0, description="排序")
    status: str = Field(default="0", description="状态(0:启用 1:停用)")


class SkillManagerFileSaveSchema(BaseModel):
    """批量保存引用文件模型"""

    files: list[SkillManagerFileCreateSchema] = Field(default_factory=list, description="引用文件")


@dataclass
class SkillManagerQueryParam:
    """Skill 查询参数"""

    def __init__(
        self,
        name: str | None = Query(None, description="Skill 标识"),
        title: str | None = Query(None, description="显示名称"),
        category: str | None = Query(None, description="分类"),
        status: str | None = Query(None, description="状态"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围"),
        updated_time: list[DateTimeStr] | None = Query(None, description="更新时间范围"),
        created_id: int | None = Query(None, description="创建人"),
        updated_id: int | None = Query(None, description="更新人"),
    ) -> None:
        self.name = (QueueEnum.like.value, name)
        if title:
            self.title = (QueueEnum.like.value, title)
        if category:
            self.category = (QueueEnum.like.value, category)
        if status:
            self.status = (QueueEnum.eq.value, status)
        if created_time and len(created_time) == 2:
            self.created_time = (QueueEnum.between.value, (created_time[0], created_time[1]))
        if updated_time and len(updated_time) == 2:
            self.updated_time = (QueueEnum.between.value, (updated_time[0], updated_time[1]))
        if created_id:
            self.created_id = (QueueEnum.eq.value, created_id)
        if updated_id:
            self.updated_id = (QueueEnum.eq.value, updated_id)
