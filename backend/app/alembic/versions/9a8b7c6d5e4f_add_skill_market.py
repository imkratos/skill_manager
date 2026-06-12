"""add_skill_market

Revision ID: 9a8b7c6d5e4f
Revises: 7c3b2a1d9e4f
Create Date: 2026-06-11 00:00:00.000000

"""
from collections.abc import Sequence
from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a8b7c6d5e4f"
down_revision: str | None = "7c3b2a1d9e4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _now() -> datetime:
    return datetime.now()


def _has_table(conn, table_name: str) -> bool:
    return sa.inspect(conn).has_table(table_name)


def _has_column(conn, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in sa.inspect(conn).get_columns(table_name))


def _add_column_if_missing(conn, table_name: str, column: sa.Column) -> None:
    if not _has_column(conn, table_name, column.name):
        op.add_column(table_name, column)


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


def _insert_default_source(conn) -> None:
    default_sources = [
        {
            "name": "Anthropic Agent Skills",
            "code": "anthropic-agent-skills",
            "description": "Anthropic 官方示例 Skills 与 Claude Code 插件市场源",
            "base_url": "https://github.com/anthropics/skills",
        },
        {
            "name": "Awesome Claude Skills",
            "code": "awesome-claude-skills",
            "description": "Composio 社区维护的 Claude Skills 市场源",
            "base_url": "https://github.com/ComposioHQ/awesome-claude-skills",
        },
    ]
    for source in default_sources:
        _insert_source_if_missing(conn, source)


def _insert_source_if_missing(conn, source: dict) -> None:
    exists = conn.execute(
        sa.text("SELECT id FROM skill_market_source WHERE code = :code LIMIT 1"),
        {"code": source["code"]},
    ).fetchone()
    if exists:
        return
    now = _now()
    conn.execute(
        sa.text(
            "INSERT INTO skill_market_source (uuid, status, description, created_time, updated_time, "
            "is_deleted, deleted_time, tenant_id, created_id, updated_id, deleted_id, name, code, "
            "adapter_type, base_url, branch, config, last_sync_time, last_sync_status, "
            "last_sync_message, sort) "
            "VALUES (:uuid, '0', :description, :created_time, :updated_time, 0, NULL, 1, NULL, "
            "NULL, NULL, :name, :code, :adapter_type, :base_url, :branch, NULL, NULL, NULL, NULL, 0)"
        ),
        {
            "uuid": str(uuid4()),
            "description": source["description"],
            "created_time": now,
            "updated_time": now,
            "name": source["name"],
            "code": source["code"],
            "adapter_type": "github_repo",
            "base_url": source["base_url"],
            "branch": "main",
        },
    )


def upgrade() -> None:
    conn = op.get_bind()
    if not _has_table(conn, "skill_market_source"):
        op.create_table(
            "skill_market_source",
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
            sa.Column("name", sa.String(length=100), nullable=False, comment="平台名称"),
            sa.Column("code", sa.String(length=100), nullable=False, comment="平台编码"),
            sa.Column("adapter_type", sa.String(length=50), nullable=False, comment="适配器类型"),
            sa.Column("base_url", sa.String(length=500), nullable=False, comment="市场地址"),
            sa.Column("branch", sa.String(length=100), nullable=True, comment="分支"),
            sa.Column("config", sa.JSON(), nullable=True, comment="适配器配置"),
            sa.Column("last_sync_time", sa.DateTime(), nullable=True, comment="最后同步时间"),
            sa.Column("last_sync_status", sa.String(length=20), nullable=True, comment="最后同步状态"),
            sa.Column("last_sync_message", sa.Text(), nullable=True, comment="最后同步消息"),
            sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
            sa.ForeignKeyConstraint(["created_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["tenant_id"], ["sys_tenant.id"], onupdate="CASCADE", ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["updated_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tenant_id", "code", name="uq_skill_market_source_tenant_code"),
            comment="第三方 Skill 市场源",
        )
        op.create_index(op.f("ix_skill_market_source_created_id"), "skill_market_source", ["created_id"], unique=False)
        op.create_index(op.f("ix_skill_market_source_created_time"), "skill_market_source", ["created_time"], unique=False)
        op.create_index(op.f("ix_skill_market_source_deleted_id"), "skill_market_source", ["deleted_id"], unique=False)
        op.create_index(op.f("ix_skill_market_source_deleted_time"), "skill_market_source", ["deleted_time"], unique=False)
        op.create_index(op.f("ix_skill_market_source_id"), "skill_market_source", ["id"], unique=False)
        op.create_index(op.f("ix_skill_market_source_is_deleted"), "skill_market_source", ["is_deleted"], unique=False)
        op.create_index(op.f("ix_skill_market_source_status"), "skill_market_source", ["status"], unique=False)
        op.create_index(op.f("ix_skill_market_source_tenant_id"), "skill_market_source", ["tenant_id"], unique=False)
        op.create_index(op.f("ix_skill_market_source_updated_id"), "skill_market_source", ["updated_id"], unique=False)
        op.create_index(op.f("ix_skill_market_source_updated_time"), "skill_market_source", ["updated_time"], unique=False)
        op.create_index(op.f("ix_skill_market_source_uuid"), "skill_market_source", ["uuid"], unique=True)

    if not _has_table(conn, "skill_market_item"):
        op.create_table(
            "skill_market_item",
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
            sa.Column("source_id", sa.Integer(), nullable=False, comment="市场源ID"),
            sa.Column("external_id", sa.String(length=500), nullable=False, comment="外部唯一标识"),
            sa.Column("name", sa.String(length=100), nullable=False, comment="Skill 标识"),
            sa.Column("title", sa.String(length=200), nullable=False, comment="显示名称"),
            sa.Column("category", sa.String(length=100), nullable=True, comment="分类"),
            sa.Column("tags", sa.JSON(), nullable=True, comment="标签"),
            sa.Column("version", sa.String(length=50), nullable=True, comment="版本号"),
            sa.Column("author", sa.String(length=100), nullable=True, comment="作者"),
            sa.Column("license", sa.String(length=100), nullable=True, comment="许可证"),
            sa.Column("homepage_url", sa.String(length=500), nullable=True, comment="主页地址"),
            sa.Column("repository_url", sa.String(length=500), nullable=True, comment="仓库地址"),
            sa.Column("skill_path", sa.String(length=500), nullable=False, comment="Skill 目录路径"),
            sa.Column("skill_md_url", sa.String(length=800), nullable=True, comment="SKILL.md 地址"),
            sa.Column("readme_url", sa.String(length=800), nullable=True, comment="README 地址"),
            sa.Column("raw_meta", sa.JSON(), nullable=True, comment="原始元数据"),
            sa.Column("market_kind", sa.String(length=20), nullable=False, server_default="skill", comment="市场条目类型(skill/plugin)"),
            sa.Column("plugin_name", sa.String(length=100), nullable=True, comment="插件包名称"),
            sa.Column("plugin_description", sa.Text(), nullable=True, comment="插件包说明"),
            sa.Column("skill_paths", sa.JSON(), nullable=True, comment="插件包包含的 Skill 路径"),
            sa.Column("source_branch", sa.String(length=100), nullable=True, comment="来源分支"),
            sa.Column("source_commit", sa.String(length=100), nullable=True, comment="来源提交"),
            sa.Column("content_hash", sa.String(length=100), nullable=True, comment="内容哈希"),
            sa.Column("file_count", sa.Integer(), nullable=False, server_default="0", comment="文件数量"),
            sa.Column("package_size", sa.Integer(), nullable=False, server_default="0", comment="包大小"),
            sa.Column("installed_skill_id", sa.Integer(), nullable=True, comment="已安装 Skill ID"),
            sa.Column("last_sync_time", sa.DateTime(), nullable=True, comment="最后同步时间"),
            sa.ForeignKeyConstraint(["created_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["deleted_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["installed_skill_id"], ["skill_manager.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["source_id"], ["skill_market_source.id"], onupdate="CASCADE", ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tenant_id"], ["sys_tenant.id"], onupdate="CASCADE", ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["updated_id"], ["sys_user.id"], onupdate="CASCADE", ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("source_id", "external_id", name="uq_skill_market_item_source_external"),
            comment="第三方市场 Skill 条目",
        )
        op.create_index(op.f("ix_skill_market_item_created_id"), "skill_market_item", ["created_id"], unique=False)
        op.create_index(op.f("ix_skill_market_item_created_time"), "skill_market_item", ["created_time"], unique=False)
        op.create_index(op.f("ix_skill_market_item_deleted_id"), "skill_market_item", ["deleted_id"], unique=False)
        op.create_index(op.f("ix_skill_market_item_deleted_time"), "skill_market_item", ["deleted_time"], unique=False)
        op.create_index(op.f("ix_skill_market_item_id"), "skill_market_item", ["id"], unique=False)
        op.create_index(op.f("ix_skill_market_item_installed_skill_id"), "skill_market_item", ["installed_skill_id"], unique=False)
        op.create_index(op.f("ix_skill_market_item_is_deleted"), "skill_market_item", ["is_deleted"], unique=False)
        op.create_index(op.f("ix_skill_market_item_source_id"), "skill_market_item", ["source_id"], unique=False)
        op.create_index(op.f("ix_skill_market_item_status"), "skill_market_item", ["status"], unique=False)
        op.create_index(op.f("ix_skill_market_item_tenant_id"), "skill_market_item", ["tenant_id"], unique=False)
        op.create_index(op.f("ix_skill_market_item_updated_id"), "skill_market_item", ["updated_id"], unique=False)
        op.create_index(op.f("ix_skill_market_item_updated_time"), "skill_market_item", ["updated_time"], unique=False)
        op.create_index(op.f("ix_skill_market_item_uuid"), "skill_market_item", ["uuid"], unique=True)
    else:
        _add_column_if_missing(
            conn,
            "skill_market_item",
            sa.Column("market_kind", sa.String(length=20), nullable=False, server_default="skill", comment="市场条目类型(skill/plugin)"),
        )
        _add_column_if_missing(conn, "skill_market_item", sa.Column("plugin_name", sa.String(length=100), nullable=True, comment="插件包名称"))
        _add_column_if_missing(conn, "skill_market_item", sa.Column("plugin_description", sa.Text(), nullable=True, comment="插件包说明"))
        _add_column_if_missing(conn, "skill_market_item", sa.Column("skill_paths", sa.JSON(), nullable=True, comment="插件包包含的 Skill 路径"))
        _add_column_if_missing(conn, "skill_market_item", sa.Column("source_branch", sa.String(length=100), nullable=True, comment="来源分支"))
        _add_column_if_missing(conn, "skill_market_item", sa.Column("source_commit", sa.String(length=100), nullable=True, comment="来源提交"))
        _add_column_if_missing(conn, "skill_market_item", sa.Column("content_hash", sa.String(length=100), nullable=True, comment="内容哈希"))
        _add_column_if_missing(
            conn,
            "skill_market_item",
            sa.Column("file_count", sa.Integer(), nullable=False, server_default="0", comment="文件数量"),
        )
        _add_column_if_missing(
            conn,
            "skill_market_item",
            sa.Column("package_size", sa.Integer(), nullable=False, server_default="0", comment="包大小"),
        )

    _insert_default_source(conn)

    root_row = conn.execute(
        sa.text("SELECT id FROM sys_menu WHERE name = 'Skill' AND type = 1 LIMIT 1")
    ).fetchone()
    if not root_row:
        raise RuntimeError("Skill 父菜单不存在，请先执行 Skill 管理模块迁移")
    root_id = int(root_row[0])
    page_id = _insert_menu_if_missing(
        conn,
        {
            "name": "SkillMarket",
            "title": "第三方市场",
            "type": 2,
            "order": 2,
            "permission": "module_skill:market:query",
            "icon": "el-icon-Shop",
            "route_name": "SkillMarket",
            "route_path": "/skill/market",
            "component_path": "module_skill/market/index",
            "redirect": None,
            "parent_id": root_id,
            "description": "第三方 Skill 平台源、同步与安装",
        },
    )
    button_defs = [
        ("SkillMarketDetail", "市场详情", "module_skill:market:detail", 1),
        ("SkillMarketCreate", "新增市场源", "module_skill:market:create", 2),
        ("SkillMarketUpdate", "修改市场源", "module_skill:market:update", 3),
        ("SkillMarketDelete", "删除市场源", "module_skill:market:delete", 4),
        ("SkillMarketSync", "同步市场源", "module_skill:market:sync", 5),
        ("SkillMarketInstall", "安装 Skill", "module_skill:market:install", 6),
    ]
    menu_ids = [page_id]
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
        "module_skill:market:query",
        "module_skill:market:detail",
        "module_skill:market:create",
        "module_skill:market:update",
        "module_skill:market:delete",
        "module_skill:market:sync",
        "module_skill:market:install",
    ]
    menu_ids = []
    for permission in permissions:
        row = conn.execute(
            sa.text("SELECT id FROM sys_menu WHERE permission = :permission LIMIT 1"),
            {"permission": permission},
        ).fetchone()
        if row:
            menu_ids.append(int(row[0]))
    for menu_id in menu_ids:
        conn.execute(sa.text("DELETE FROM sys_role_menus WHERE menu_id = :menu_id"), {"menu_id": menu_id})
    for permission in permissions:
        conn.execute(sa.text("DELETE FROM sys_menu WHERE permission = :permission"), {"permission": permission})

    if _has_table(conn, "skill_market_item"):
        op.drop_index(op.f("ix_skill_market_item_uuid"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_updated_time"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_updated_id"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_tenant_id"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_status"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_source_id"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_is_deleted"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_installed_skill_id"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_id"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_deleted_time"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_deleted_id"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_created_time"), table_name="skill_market_item")
        op.drop_index(op.f("ix_skill_market_item_created_id"), table_name="skill_market_item")
        op.drop_table("skill_market_item")

    if _has_table(conn, "skill_market_source"):
        op.drop_index(op.f("ix_skill_market_source_uuid"), table_name="skill_market_source")
        op.drop_index(op.f("ix_skill_market_source_updated_time"), table_name="skill_market_source")
        op.drop_index(op.f("ix_skill_market_source_updated_id"), table_name="skill_market_source")
        op.drop_index(op.f("ix_skill_market_source_tenant_id"), table_name="skill_market_source")
        op.drop_index(op.f("ix_skill_market_source_status"), table_name="skill_market_source")
        op.drop_index(op.f("ix_skill_market_source_is_deleted"), table_name="skill_market_source")
        op.drop_index(op.f("ix_skill_market_source_id"), table_name="skill_market_source")
        op.drop_index(op.f("ix_skill_market_source_deleted_time"), table_name="skill_market_source")
        op.drop_index(op.f("ix_skill_market_source_deleted_id"), table_name="skill_market_source")
        op.drop_index(op.f("ix_skill_market_source_created_time"), table_name="skill_market_source")
        op.drop_index(op.f("ix_skill_market_source_created_id"), table_name="skill_market_source")
        op.drop_table("skill_market_source")
