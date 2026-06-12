"""repair_skill_market_item_columns

Revision ID: a1b2c3d4e5f6
Revises: 9a8b7c6d5e4f
Create Date: 2026-06-12 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "9a8b7c6d5e4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(conn, table_name: str) -> bool:
    return sa.inspect(conn).has_table(table_name)


def _has_column(conn, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in sa.inspect(conn).get_columns(table_name))


def _add_column_if_missing(conn, table_name: str, column: sa.Column) -> None:
    if not _has_column(conn, table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    conn = op.get_bind()
    if not _has_table(conn, "skill_market_item"):
        return

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


def downgrade() -> None:
    conn = op.get_bind()
    if not _has_table(conn, "skill_market_item"):
        return

    for column_name in (
        "package_size",
        "file_count",
        "content_hash",
        "source_commit",
        "source_branch",
        "skill_paths",
        "plugin_description",
        "plugin_name",
        "market_kind",
    ):
        if _has_column(conn, "skill_market_item", column_name):
            op.drop_column("skill_market_item", column_name)
