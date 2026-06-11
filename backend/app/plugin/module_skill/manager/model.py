from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import ModelMixin, TenantMixin, UserMixin


class SkillManagerModel(ModelMixin, TenantMixin, UserMixin):
    """Skill 主定义表"""

    __tablename__: str = "skill_manager"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_skill_manager_tenant_name"),
        {"comment": "Skill 主定义表"},
    )
    __loader_options__: list[str] = ["created_by", "updated_by", "deleted_by", "files"]

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Skill 唯一标识")
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="显示名称")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="分类")
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, comment="标签")
    version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False, comment="版本号")
    author: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="作者")
    skill_md: Mapped[str] = mapped_column(Text, nullable=False, comment="SKILL.md 内容")
    readme: Mapped[str | None] = mapped_column(Text, nullable=True, comment="README.md 内容")
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")

    files: Mapped[list["SkillManagerFileModel"]] = relationship(
        back_populates="skill",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SkillManagerFileModel.sort",
    )


class SkillManagerFileModel(ModelMixin, TenantMixin, UserMixin):
    """Skill 引用文件表"""

    __tablename__: str = "skill_manager_file"
    __table_args__ = (
        UniqueConstraint("skill_id", "path", name="uq_skill_manager_file_path"),
        {"comment": "Skill 引用文件表"},
    )
    __loader_options__: list[str] = ["created_by", "updated_by", "deleted_by"]

    skill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("skill_manager.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="Skill ID",
    )
    path: Mapped[str] = mapped_column(String(500), nullable=False, comment="相对路径")
    type: Mapped[str] = mapped_column(String(20), default="file", nullable=False, comment="类型(file/directory)")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文件内容")
    content_type: Mapped[str] = mapped_column(String(50), default="markdown", nullable=False, comment="内容类型")
    size: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="文件大小")
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")

    skill: Mapped["SkillManagerModel"] = relationship(back_populates="files")
