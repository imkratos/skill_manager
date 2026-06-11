# 数据库迁移与菜单权限模板（Alembic）

> 本文件供 `SKILL.md` 在 Step 3 写迁移文件前按需读取。涉及模型结构变更、新增可访问页面时读取。

## 生成迁移命令

新增/修改模型后，在 `backend` 下运行：

```bash
uv run python main.py revision --env=dev
uv run python main.py upgrade --env=dev
```

审查自动生成的迁移脚本，确认**没有误删系统表、误改无关字段**。自动迁移可能因 import 顺序漏识别新模型，必要时手动补全。

---

## ⛔ 菜单与按钮权限迁移（强制项）

> 新增后台可访问功能时，**必须**随代码提供菜单数据迁移，不能只创建前端页面或后端接口。

### 关键事实（务必理解，避免踩坑）

- `backend/app/scripts/data/sys_menu.json` **只在 `sys_menu` 表为空时初始化**。已有环境改 JSON 不会自动补菜单 —— 必须走迁移。
- 代码生成器中的 `MenuCRUD.create()` 只写当前数据库，**不能替代可随代码交付的迁移**。
- 迁移中插入前**必须先查父菜单 ID 和角色 ID，不能写死**（不同环境 ID 不同）。

### sys_menu 字段说明（取自真实 sys_menu.json）

- `type`：`1`=目录，`2`=页面菜单，`3`=按钮权限。
- 目录(type=1)：`permission=null`、`component_path=null`、有 `redirect`。
- 页面菜单(type=2)：需 `name`/`title`/`permission`/`route_name`/`route_path`/`component_path`/`icon`/`order`/`parent_id`。
- 按钮(type=3)：`permission` 必填，`route_*`/`component_path` 为 null，`parent_id` 指向所属页面菜单。
- 公共字段：`status="0"`、`client="pc"`、`tenant_id=1`、`keep_alive`、`hidden`、`always_show`、`affix`。
- 权限码必须与后端 `AuthPermission([...])` 和前端按钮权限**完全一致**。

### 幂等迁移模板

```python
# Alembic 迁移文件 upgrade() / downgrade()
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    conn = op.get_bind()

    # 1. 查询父菜单 ID（不能写死）
    parent = conn.execute(
        sa.text("SELECT id FROM sys_menu WHERE name = :name AND type = 1"),
        {"name": "父菜单名称"}
    ).fetchone()
    if not parent:
        raise Exception("父菜单不存在，请先创建父菜单")
    parent_id = parent[0]

    # 2. 幂等插入页面菜单（按 permission 去重），拿到自增 ID
    page_perm = "module_<domain>:<resource>:query"
    exists = conn.execute(
        sa.text("SELECT id FROM sys_menu WHERE permission = :perm"), {"perm": page_perm}
    ).fetchone()
    if exists:
        page_id = exists[0]
    else:
        conn.execute(sa.text(
            "INSERT INTO sys_menu (name, title, permission, route_name, route_path, "
            "component_path, icon, `order`, parent_id, type, status, client, tenant_id, "
            "keep_alive, hidden, always_show, affix) "
            "VALUES (:name, :title, :permission, :route_name, :route_path, "
            ":component_path, :icon, :order, :parent_id, 2, '0', 'pc', 1, "
            "1, 0, 0, 0)"
        ), {
            "name": "xxx_list", "title": "Xxx管理", "permission": page_perm,
            "route_name": "XxxList", "route_path": "/xxx",
            "component_path": "module_<domain>/<resource>/index",
            "icon": "ep:list", "order": 1, "parent_id": parent_id,
        })
        page_id = conn.execute(
            sa.text("SELECT id FROM sys_menu WHERE permission = :perm"), {"perm": page_perm}
        ).fetchone()[0]

    # 3. 幂等插入按钮权限（parent_id 指向页面菜单）
    buttons = [
        ("xxx_create", "新增", "module_<domain>:<resource>:create"),
        ("xxx_update", "修改", "module_<domain>:<resource>:update"),
        ("xxx_delete", "删除", "module_<domain>:<resource>:delete"),
        ("xxx_export", "导出", "module_<domain>:<resource>:export"),
        ("xxx_import", "导入", "module_<domain>:<resource>:import"),
        # 按实际接口增减：detail/patch/download 等
    ]
    for name, title, perm in buttons:
        b_exists = conn.execute(
            sa.text("SELECT id FROM sys_menu WHERE permission = :perm"), {"perm": perm}
        ).fetchone()
        if not b_exists:
            conn.execute(sa.text(
                "INSERT INTO sys_menu (name, title, permission, parent_id, type, status, "
                "client, tenant_id, keep_alive, hidden, always_show, affix, `order`) "
                "VALUES (:name, :title, :permission, :parent_id, 3, '0', 'pc', 1, 1, 0, 0, 0, 1)"
            ), {"name": name, "title": title, "permission": perm, "parent_id": page_id})


def downgrade() -> None:
    conn = op.get_bind()
    permissions = [
        "module_<domain>:<resource>:query",
        "module_<domain>:<resource>:create",
        "module_<domain>:<resource>:update",
        "module_<domain>:<resource>:delete",
        "module_<domain>:<resource>:export",
        "module_<domain>:<resource>:import",
    ]
    for perm in permissions:
        conn.execute(sa.text("DELETE FROM sys_menu WHERE permission = :perm"), {"perm": perm})
```

> **下列字段名以真实表为准**：写迁移前先 Read 一个已有的含 `sys_menu` INSERT 的迁移文件（如 `backend/app/alembic/versions/` 下含 `sys_menu` 的文件）核对列名与默认值，本模板仅为结构骨架。

---

## ⛔ 环境不可达降级规则

数据库连不上时（Alembic upgrade 失败、DB 服务未启动）：

1. 先检查 `.env` 或配置文件中的连接字符串是否正确。
2. 确认数据库服务是否运行：`pg_ctl status` / `docker ps | grep postgres` / `docker ps | grep mysql`。
3. 如果仍无法连接，**禁止**跳过迁移直接写代码并声称"已完成"。
4. 记录具体错误信息，在输出汇总中标注"迁移未执行，原因：{错误}"，等用户修复环境后重新执行。
