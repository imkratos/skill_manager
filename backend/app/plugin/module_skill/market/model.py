from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, TenantMixin, UserMixin


class SkillMarketSourceModel(ModelMixin, TenantMixin, UserMixin):
    """第三方 Skill 市场源"""

    __tablename__: str = "skill_market_source"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_skill_market_source_tenant_code"),
        {"comment": "第三方 Skill 市场源"},
    )
    __loader_options__: list[str] = ["created_by", "updated_by", "deleted_by"]

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="平台名称")
    code: Mapped[str] = mapped_column(String(100), nullable=False, comment="平台编码")
    adapter_type: Mapped[str] = mapped_column(String(50), default="github_repo", nullable=False, comment="适配器类型")
    base_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="市场地址")
    branch: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="分支")
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="适配器配置")
    last_sync_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最后同步时间")
    last_sync_status: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="最后同步状态")
    last_sync_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="最后同步消息")
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")


class SkillMarketItemModel(ModelMixin, TenantMixin, UserMixin):
    """第三方市场 Skill 条目"""

    __tablename__: str = "skill_market_item"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_skill_market_item_source_external"),
        {"comment": "第三方市场 Skill 条目"},
    )
    __loader_options__: list[str] = ["created_by", "updated_by", "deleted_by"]

    source_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("skill_market_source.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="市场源ID",
    )
    external_id: Mapped[str] = mapped_column(String(500), nullable=False, comment="外部唯一标识")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Skill 标识")
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="显示名称")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="分类")
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, comment="标签")
    version: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="版本号")
    author: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="作者")
    license: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="许可证")
    homepage_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="主页地址")
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="仓库地址")
    skill_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="Skill 目录路径")
    skill_md_url: Mapped[str | None] = mapped_column(String(800), nullable=True, comment="SKILL.md 地址")
    readme_url: Mapped[str | None] = mapped_column(String(800), nullable=True, comment="README 地址")
    raw_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="原始元数据")
    market_kind: Mapped[str] = mapped_column(String(20), default="skill", nullable=False, comment="市场条目类型(skill/plugin)")
    plugin_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="插件包名称")
    plugin_description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="插件包说明")
    skill_paths: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, comment="插件包包含的 Skill 路径")
    source_branch: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="来源分支")
    source_commit: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="来源提交")
    content_hash: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="内容哈希")
    file_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="文件数量")
    package_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="包大小")
    installed_skill_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("skill_manager.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
        comment="已安装 Skill ID",
    )
    last_sync_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最后同步时间")
