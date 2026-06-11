"""add_skill_manager

Revision ID: 7c3b2a1d9e4f
Revises: 0306640395d9
Create Date: 2026-06-11 00:00:00.000000

"""
from collections.abc import Sequence
from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c3b2a1d9e4f"
down_revision: str | None = "0306640395d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _now() -> datetime:
    return datetime.now()


def _has_table(conn, table_name: str) -> bool:
    return sa.inspect(conn).has_table(table_name)


def _insert_menu_if_missing(conn, values: dict) -> int:
    permission = values.get("permission")
    if permission:
        row = conn.execute(
            sa.text("SELECT id FROM sys_menu WHERE permission = :permission LIMIT 1"),
            {"permission": permission},
        ).fetchone()
    else:
        row = conn.execute(
            sa.text(
                "SELECT id FROM sys_menu WHERE name = :name AND type = :type "
                "AND ((parent_id IS NULL AND :parent_id IS NULL) OR parent_id = :parent_id) LIMIT 1"
            ),
            {
                "name": values["name"],
                "type": values["type"],
                "parent_id": values.get("parent_id"),
            },
        ).fetchone()
    if row:
        return int(row[0])

    now = _now()
    payload = {
        "uuid": str(uuid4()),
        "status": "0",
        "description": values.get("description"),
        "created_time": now,
        "updated_time": now,
        "is_deleted": 0,
        "tenant_id": 1,
        "params": None,
        "client": "pc",
        "hidden": 0,
        "keep_alive": 1,
        "always_show": 0,
        "affix": 0,
        **values,
    }
    conn.execute(
        sa.text(
            "INSERT INTO sys_menu (name, type, `order`, permission, icon, route_name, "
            "route_path, component_path, redirect, hidden, keep_alive, always_show, "
            "title, params, affix, parent_id, uuid, status, description, created_time, "
            "updated_time, is_deleted, deleted_time, tenant_id, client) "
            "VALUES (:name, :type, :order, :permission, :icon, :route_name, "
            ":route_path, :component_path, :redirect, :hidden, :keep_alive, :always_show, "
            ":title, :params, :affix, :parent_id, :uuid, :status, :description, :created_time, "
            ":updated_time, :is_deleted, NULL, :tenant_id, :client)"
        ),
        payload,
    )
    if permission:
        row = conn.execute(
            sa.text("SELECT id FROM sys_menu WHERE permission = :permission LIMIT 1"),
            {"permission": permission},
        ).fetchone()
    else:
        row = conn.execute(
            sa.text("SELECT id FROM sys_menu WHERE uuid = :uuid LIMIT 1"),
            {"uuid": payload["uuid"]},
        ).fetchone()
    return int(row[0])


def _grant_menu_to_roles(conn, menu_ids: list[int]) -> None:
    role_rows = conn.execute(
        sa.text("SELECT id FROM sys_role WHERE status = '0' AND is_deleted = 0")
    ).fetchall()
    for role_row in role_rows:
        role_id = int(role_row[0])
        for menu_id in menu_ids:
            exists = conn.execute(
                sa.text(
                    "SELECT 1 FROM sys_role_menus WHERE role_id = :role_id "
                    "AND menu_id = :menu_id LIMIT 1"
                ),
                {"role_id": role_id, "menu_id": menu_id},
            ).fetchone()
            if not exists:
                conn.execute(
                    sa.text(
                        "INSERT INTO sys_role_menus (role_id, menu_id) "
                        "VALUES (:role_id, :menu_id)"
                    ),
                    {"role_id": role_id, "menu_id": menu_id},
                )


def upgrade() -> None:
    conn = op.get_bind()
    if not _has_table(conn, "skill_manager"):
        op.create_table(
            "skill_manager",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"),
            sa.Column("uuid", sa.String(length=64), nullable=False, comment="UUID全局唯一标识"),
            sa.Column("status", sa.String(length=10), nullable=False, comment="状态(0:正常 1:禁用)"),
            sa.Column("description", sa.Text(), nullable=True, comment="备注/描述"),
            sa.Column("created_time", sa.DateTime(), nullable=False, comment="创建时间"),
            sa.Column("updated_time", sa.DateTime(), nullable=False, comment="更新时间"),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, comment="是否已删除(0:未删除 1:已删除)"),
            sa.Column("deleted_time", sa.DateTime(), nullable=True, comment="删除时间"),
            sa.Column("tenant_id", sa.Integer(), nullable=False, comment="租户ID"),
            sa.Column("created_id", sa.Integer(), nullable=True, comment="创建人ID"),
            sa.Column("updated_id", sa.Integer(), nullable=True, comment="更新人ID"),
            sa.Column("deleted_id", sa.Integer(), nullable=True, comment="删除人ID"),
            sa.Column("name", sa.String(length=100), nullable=False, comment="Skill 唯一标识"),
            sa.Column("title", sa.String(length=100), nullable=False, comment="显示名称"),
            sa.Column("category", sa.String(length=100), nullable=True, comment="分类"),
            sa.Column("tags", sa.JSON(), nullable=True, comment="标签"),
            sa.Column("version", sa.String(length=50), nullable=False, comment="版本号"),
            sa.Column("author", sa.String(length=100), nullable=True, comment="作者"),
            sa.Column("skill_md", sa.Text(), nullable=False, comment="SKILL.md 内容"),
            sa.Column("readme", sa.Text(), nullable=True, comment="README.md 内容"),
            sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
            sa.ForeignKeyConstraint(["created_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["tenant_id"], ["sys_tenant.id"], onupdate="CASCADE", ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["updated_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tenant_id", "name", name="uq_skill_manager_tenant_name"),
            comment="Skill 主定义表",
        )
        op.create_index(op.f("ix_skill_manager_created_id"), "skill_manager", ["created_id"], unique=False)
        op.create_index(op.f("ix_skill_manager_created_time"), "skill_manager", ["created_time"], unique=False)
        op.create_index(op.f("ix_skill_manager_deleted_id"), "skill_manager", ["deleted_id"], unique=False)
        op.create_index(op.f("ix_skill_manager_deleted_time"), "skill_manager", ["deleted_time"], unique=False)
        op.create_index(op.f("ix_skill_manager_id"), "skill_manager", ["id"], unique=False)
        op.create_index(op.f("ix_skill_manager_is_deleted"), "skill_manager", ["is_deleted"], unique=False)
        op.create_index(op.f("ix_skill_manager_status"), "skill_manager", ["status"], unique=False)
        op.create_index(op.f("ix_skill_manager_tenant_id"), "skill_manager", ["tenant_id"], unique=False)
        op.create_index(op.f("ix_skill_manager_updated_id"), "skill_manager", ["updated_id"], unique=False)
        op.create_index(op.f("ix_skill_manager_updated_time"), "skill_manager", ["updated_time"], unique=False)
        op.create_index(op.f("ix_skill_manager_uuid"), "skill_manager", ["uuid"], unique=True)

    if not _has_table(conn, "skill_manager_file"):
        op.create_table(
            "skill_manager_file",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"),
            sa.Column("uuid", sa.String(length=64), nullable=False, comment="UUID全局唯一标识"),
            sa.Column("status", sa.String(length=10), nullable=False, comment="状态(0:正常 1:禁用)"),
            sa.Column("description", sa.Text(), nullable=True, comment="备注/描述"),
            sa.Column("created_time", sa.DateTime(), nullable=False, comment="创建时间"),
            sa.Column("updated_time", sa.DateTime(), nullable=False, comment="更新时间"),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, comment="是否已删除(0:未删除 1:已删除)"),
            sa.Column("deleted_time", sa.DateTime(), nullable=True, comment="删除时间"),
            sa.Column("tenant_id", sa.Integer(), nullable=False, comment="租户ID"),
            sa.Column("created_id", sa.Integer(), nullable=True, comment="创建人ID"),
            sa.Column("updated_id", sa.Integer(), nullable=True, comment="更新人ID"),
            sa.Column("deleted_id", sa.Integer(), nullable=True, comment="删除人ID"),
            sa.Column("skill_id", sa.Integer(), nullable=False, comment="Skill ID"),
            sa.Column("path", sa.String(length=500), nullable=False, comment="相对路径"),
            sa.Column("type", sa.String(length=20), nullable=False, comment="类型(file/directory)"),
            sa.Column("content", sa.Text(), nullable=True, comment="文件内容"),
            sa.Column("content_type", sa.String(length=50), nullable=False, comment="内容类型"),
            sa.Column("size", sa.Integer(), nullable=False, comment="文件大小"),
            sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
            sa.ForeignKeyConstraint(["created_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["skill_id"], ["skill_manager.id"], onupdate="CASCADE", ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tenant_id"], ["sys_tenant.id"], onupdate="CASCADE", ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["updated_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("skill_id", "path", name="uq_skill_manager_file_path"),
            comment="Skill 引用文件表",
        )
        op.create_index(op.f("ix_skill_manager_file_created_id"), "skill_manager_file", ["created_id"], unique=False)
        op.create_index(op.f("ix_skill_manager_file_created_time"), "skill_manager_file", ["created_time"], unique=False)
        op.create_index(op.f("ix_skill_manager_file_deleted_id"), "skill_manager_file", ["deleted_id"], unique=False)
        op.create_index(op.f("ix_skill_manager_file_deleted_time"), "skill_manager_file", ["deleted_time"], unique=False)
        op.create_index(op.f("ix_skill_manager_file_id"), "skill_manager_file", ["id"], unique=False)
        op.create_index(op.f("ix_skill_manager_file_is_deleted"), "skill_manager_file", ["is_deleted"], unique=False)
        op.create_index(op.f("ix_skill_manager_file_skill_id"), "skill_manager_file", ["skill_id"], unique=False)
        op.create_index(op.f("ix_skill_manager_file_status"), "skill_manager_file", ["status"], unique=False)
        op.create_index(op.f("ix_skill_manager_file_tenant_id"), "skill_manager_file", ["tenant_id"], unique=False)
        op.create_index(op.f("ix_skill_manager_file_updated_id"), "skill_manager_file", ["updated_id"], unique=False)
        op.create_index(op.f("ix_skill_manager_file_updated_time"), "skill_manager_file", ["updated_time"], unique=False)
        op.create_index(op.f("ix_skill_manager_file_uuid"), "skill_manager_file", ["uuid"], unique=True)

    root_id = _insert_menu_if_missing(
        conn,
        {
            "name": "Skill",
            "title": "Skill 管理",
            "type": 1,
            "order": 10,
            "permission": None,
            "icon": "el-icon-MagicStick",
            "route_name": "Skill",
            "route_path": "/skill",
            "component_path": None,
            "redirect": "/skill/manager",
            "parent_id": None,
            "description": "Skill 工程化管理",
        },
    )
    page_id = _insert_menu_if_missing(
        conn,
        {
            "name": "SkillManager",
            "title": "Skill 列表",
            "type": 2,
            "order": 1,
            "permission": "module_skill:manager:query",
            "icon": "el-icon-Collection",
            "route_name": "SkillManager",
            "route_path": "/skill/manager",
            "component_path": "module_skill/manager/index",
            "redirect": None,
            "parent_id": root_id,
            "description": "Skill 定义、引用文件与下载",
        },
    )
    button_defs = [
        ("SkillManagerCreate", "创建 Skill", "module_skill:manager:create", 1),
        ("SkillManagerUpdate", "修改 Skill", "module_skill:manager:update", 2),
        ("SkillManagerDelete", "删除 Skill", "module_skill:manager:delete", 3),
        ("SkillManagerDownload", "下载 Skill", "module_skill:manager:download", 4),
        ("SkillManagerDetail", "详情 Skill", "module_skill:manager:detail", 5),
    ]
    menu_ids = [root_id, page_id]
    for name, title, permission, order in button_defs:
        menu_ids.append(
            _insert_menu_if_missing(
                conn,
                {
                    "name": name,
                    "title": title,
                    "type": 3,
                    "order": order,
                    "permission": permission,
                    "icon": None,
                    "route_name": None,
                    "route_path": None,
                    "component_path": None,
                    "redirect": None,
                    "parent_id": page_id,
                    "description": title,
                },
            )
        )
    _grant_menu_to_roles(conn, menu_ids)


def downgrade() -> None:
    conn = op.get_bind()
    permissions = [
        "module_skill:manager:query",
        "module_skill:manager:create",
        "module_skill:manager:update",
        "module_skill:manager:delete",
        "module_skill:manager:download",
        "module_skill:manager:detail",
    ]
    menu_ids = []
    for permission in permissions:
        row = conn.execute(
            sa.text("SELECT id FROM sys_menu WHERE permission = :permission LIMIT 1"),
            {"permission": permission},
        ).fetchone()
        if row:
            menu_ids.append(int(row[0]))
    root_row = conn.execute(
        sa.text("SELECT id FROM sys_menu WHERE name = 'Skill' AND type = 1 LIMIT 1")
    ).fetchone()
    if root_row:
        menu_ids.append(int(root_row[0]))
    for menu_id in menu_ids:
        conn.execute(sa.text("DELETE FROM sys_role_menus WHERE menu_id = :menu_id"), {"menu_id": menu_id})
    for permission in permissions:
        conn.execute(sa.text("DELETE FROM sys_menu WHERE permission = :permission"), {"permission": permission})
    conn.execute(sa.text("DELETE FROM sys_menu WHERE name = 'Skill' AND type = 1"))

    op.drop_index(op.f("ix_skill_manager_file_uuid"), table_name="skill_manager_file")
    op.drop_index(op.f("ix_skill_manager_file_updated_time"), table_name="skill_manager_file")
    op.drop_index(op.f("ix_skill_manager_file_updated_id"), table_name="skill_manager_file")
    op.drop_index(op.f("ix_skill_manager_file_tenant_id"), table_name="skill_manager_file")
    op.drop_index(op.f("ix_skill_manager_file_status"), table_name="skill_manager_file")
    op.drop_index(op.f("ix_skill_manager_file_skill_id"), table_name="skill_manager_file")
    op.drop_index(op.f("ix_skill_manager_file_is_deleted"), table_name="skill_manager_file")
    op.drop_index(op.f("ix_skill_manager_file_id"), table_name="skill_manager_file")
    op.drop_index(op.f("ix_skill_manager_file_deleted_time"), table_name="skill_manager_file")
    op.drop_index(op.f("ix_skill_manager_file_deleted_id"), table_name="skill_manager_file")
    op.drop_index(op.f("ix_skill_manager_file_created_time"), table_name="skill_manager_file")
    op.drop_index(op.f("ix_skill_manager_file_created_id"), table_name="skill_manager_file")
    op.drop_table("skill_manager_file")

    op.drop_index(op.f("ix_skill_manager_uuid"), table_name="skill_manager")
    op.drop_index(op.f("ix_skill_manager_updated_time"), table_name="skill_manager")
    op.drop_index(op.f("ix_skill_manager_updated_id"), table_name="skill_manager")
    op.drop_index(op.f("ix_skill_manager_tenant_id"), table_name="skill_manager")
    op.drop_index(op.f("ix_skill_manager_status"), table_name="skill_manager")
    op.drop_index(op.f("ix_skill_manager_is_deleted"), table_name="skill_manager")
    op.drop_index(op.f("ix_skill_manager_id"), table_name="skill_manager")
    op.drop_index(op.f("ix_skill_manager_deleted_time"), table_name="skill_manager")
    op.drop_index(op.f("ix_skill_manager_deleted_id"), table_name="skill_manager")
    op.drop_index(op.f("ix_skill_manager_created_time"), table_name="skill_manager")
    op.drop_index(op.f("ix_skill_manager_created_id"), table_name="skill_manager")
    op.drop_table("skill_manager")
