---
name: skill-manager
description: Use only when the user explicitly asks to use/call $skill-manager, skill-manager, or this project-specific SKILL, or explicitly requests Skill Manager project code generation/development guidance such as 本项目代码生成, 使用本项目SKILL, 调用skill-manager, 新增模块, 修改模块, 添加字段, 前后端联调, 插件开发, Skill IDE, Skill Runtime, Skill Registry, Skill Marketplace. Do not use merely because the current workspace is the Skill Manager repository.
---

# Skill Manager 项目开发技能

面向 `skill_manager` 仓库的全栈开发指南。目标是让 AI 在本项目中新增/修改功能时，优先沿用现有 FastAPIAdmin 二开结构、插件发现机制、Fa 前端组件体系和测试命令。

## 项目定位

- 产品方向：企业 AI Skill 工程平台，不是普通 Prompt 管理后台。
- 核心模块：Skill IDE、Skill Runtime、Skill Registry、Skill Marketplace。
- 当前基础：FastAPI 后端、Vue3 + TypeScript 前端、RBAC、多租户、工作流、AI 聊天、代码生成、监控。
- 开发原则：最小改动、先读现有模式、不要凭框架经验猜路径或接口。

---

## 参考文件读取规则（渐进式上下文）

> **不要在 Step 0-2 期间读取参考文件。** 只在 Step 3 执行写文件前，按操作类型按需 Read。
> 这样简单任务（加个字段）不会被无关模板淹没，复杂任务（新建模块）才加载全部参考。

| 操作类型 | Step 3 前必须 Read 的参考文件 |
|---------|--------------------------|
| **A（新增模块）** | `references/backend-templates.md` + `references/frontend-templates.md` + `references/migration-templates.md` |
| **B（修改已有模块）** | 仅读取本次涉及的参考（改后端 → backend；改前端 → frontend；涉及迁移 → migration） |
| **C（纯前端页面）** | `references/frontend-templates.md` + `references/migration-templates.md`（菜单迁移） |

**同时：** 无论哪种操作类型，Step 3 前都必须 Read **一个真实同类型模块**的对应文件，比对参考模板与实际代码的差异后再写新文件。

---

## ⛔ 写文件前强制自检清单（高频翻车点）

> **每次 Step 3（执行）之前，必须逐条 self-check，不能跳过。**

### 翻车点 1：路径必须与现有项目结构完全一致

- 后端插件目录必须是 `backend/app/plugin/module_<domain>/<resource>/`
- 控制器文件必须叫 `controller.py`，且顶层必须定义 `APIRouter` 实例
- 前端 API 文件路径：`frontend/web/src/api/module_<domain>/<resource>.ts`
- 前端页面路径：`frontend/web/src/views/module_<domain>/<resource>/index.vue`
- **禁止**凭 FastAPI/Vue 框架经验猜路径，必须先 `ls` 确认目录存在

### 翻车点 2：前后端字段必须完全一致

- 后端 Model 字段名 → Schema 字段名 → 前端 `Table`/`Form` interface 字段名，三者必须一一对应
- 新增字段后，必须同步：`model.py`、`schema.py`（Create/Update/Out/QueryParam）、前端 `*.ts` 的 `Table`/`Form` 类型、页面表格列、表单项
- **禁止**只改后端或只改前端

### 翻车点 3：API 路径必须来自 controller.py 实际定义

- `API_PATH` 值必须对应后端 `APIRouter.prefix` + 路由方法路径
- 路由容器前缀由目录推导：`module_example` → `/example`；控制器 `prefix="/demo"` → 完整路径 `/example/demo/...`
- **禁止**猜测 API 路径

### 翻车点 4：菜单迁移是强制项，不是可选项

- 每次新增可访问页面必须同时提供 Alembic 菜单迁移，不能只写前端页面或后端接口
- 迁移中插入前必须先查父菜单 ID 和角色 ID，不能写死

---

## ⛔ 错误降级模式清单（识别后立刻停止）

> 以下行为**全部视为违规**，即使表面"看起来合理"或"看起来能完成任务"：

| 错误行为 | 为什么是错的 | 正确做法 |
|---------|------------|---------|
| 凭框架经验猜 API 路径写前端 | 本项目路由通过插件发现自动挂载，路径不遵循通用约定 | Read controller.py 后再写 |
| 只改后端 Schema 不改前端 interface | 列表/表单出错，类型不匹配 | Model→Schema→前端 三处同步 |
| 新增页面不写菜单迁移 | 已有环境看不到菜单，JSON 初始化不会补 | 迁移文件幂等插入 |
| Alembic 迁移里写死父菜单 ID | 不同环境 ID 不同，迁移在测试/生产直接失败 | 先 SELECT 查 parent_id |
| 跳过 Step 1/2 直接写代码 | 字段/路径/权限码可能偏差，生成后全部返工 | 严格走流程等确认 |
| 数据库连不上就跳过迁移声称"已完成" | 迁移未执行=功能未部署 | 记录错误，标注"迁移未执行" |
| 不读真实同类模块直接按模板生成 | 模板是骨架，真实代码可能有项目特有的 import/命名差异 | 先 Read 同类模块再写 |

**任何时候若发现自己即将执行上述清单中的动作，必须立刻停下，回到 Step 1 或 Step 2 确认。**

---

## 交互流程（新增/修改功能）

> ### ⛔ 铁律：Step 1 + Step 2 是不可跳过的硬性停止门
>
> **必须严格按 Step 0 → Step 1 → Step 2（等用户确认）→ Step 3 → Step 4。**
> 在用户明确回复"确认"或等价表述之前，**绝对禁止**开始写任何文件。
>
> **以下念头出现时立刻停下，它们都是合理化跳过确认的借口：**
>
> | 借口 | 现实 |
> |------|------|
> | "需求描述足够清楚，可以直接推断" | 用户没有确认 ≠ 用户已认可。字段类型、路径都可能偏差。 |
> | "选项都是默认值，不需要问" | 默认值是否适用由用户决定，不由 AI 决定。 |
> | "先生成再改很方便" | 用户不得不事后检查所有文件，浪费双方时间。 |
> | "Skill 加载太慢，直接生成更高效" | 效率不是跳过确认的理由。 |

### Step 0：判断操作类型

- **新增插件模块** → 进入操作类型 A
- **修改已有模块**（加/改/删字段，调整逻辑）→ 进入操作类型 B
- **纯前端页面** → 进入操作类型 C

### Step 1：收集信息（必问）

**新增模块必问：**
1. 所属域（`module_<domain>`），如 `module_skill`、`module_task`
2. 资源名（`<resource>`），如 `definition`、`version`
3. 是否需要多租户隔离（加 `TenantMixin`）
4. 是否需要审计用户（加 `UserMixin`）
5. 字段列表（名称、类型、是否必填、说明）
6. 是否需要导入/导出功能
7. 菜单挂载位置（父菜单名称）

**修改模块必问：**
1. 目标模块路径（确认后端和前端文件位置）
2. 具体变更内容（加什么字段/改什么逻辑）
3. 是否需要数据库迁移

一次性展示上述问题，用户回复"确认"采用推断值，或只说需要改的项。

### Step 2：展示变更摘要（必须停止等待用户确认）

展示内容：
- 将要修改/新增的文件列表
- 每个文件的具体变更（新增哪些字段、哪些接口、哪些菜单）
- 数据库迁移内容摘要
- 权限码清单

> ✅ **只有用户明确确认后才能进入 Step 3。** 用户沉默、未回复、或继续追加需求，都不等于确认。

### Step 3：执行

> **执行前先按"参考文件读取规则"Read 对应参考文件，并 Read 一个真实同类型模块对照。**

按以下顺序并行发出文件写入调用（无依赖的文件在同一轮 response 中批量发出 Write，禁止逐文件串行等待）：

**新增模块（A）：**
- **第 1 轮前（强制）**：再次确认路径与现有目录结构一致（`ls` 确认 `module_<domain>` 是否已存在）
- **第 1 轮**（并行）：`model.py` + `schema.py` + `crud.py`
- **第 2 轮**（并行）：`service.py` + `controller.py` + `__init__.py`
- **第 3 轮前（强制）**：确认前端 `API_PATH` 来自刚写的 controller.py 路由，确认前后端字段一致
- **第 3 轮**（并行）：前端 API `*.ts` + 页面 `index.vue`
- **第 4 轮**：Alembic 迁移文件（含菜单/权限迁移）

**修改模块（B）：**
1. 先定位后端模型、Schema、CRUD、Service、Controller 和前端 API/Page，并行 Read
2. 并行发出所有 Edit 调用（同一轮 response）
3. 从 ORM 模型与前端类型**同步字段**，不只改其中一端
4. 涉及数据库结构时新增 Alembic 迁移，**不直接改历史迁移**（除非用户明确要求整理未发布迁移）

### Step 4：验证与输出

运行验证命令，输出汇总（见"验证命令"与"输出要求"章节）。

---

## 操作类型详解

### A. 新增业务插件模块

适用：新增独立业务能力、Skill IDE 页面、Skill Runtime 能力、Registry/Marketplace 功能。
目录结构与硬性规则见 `references/backend-templates.md`、`references/frontend-templates.md`。

要点：
- 插件顶级目录必须是 `module_*`，否则动态路由不会扫描。
- 控制器文件必须叫 `controller.py`，顶层必须定义 `APIRouter` 实例。
- 路由前缀由目录推导：`module_skill` 自动挂到 `/skill`；控制器 `prefix="/definition"` 后完整路径是 `/skill/definition/...`。
- 权限码使用 `module_<domain>:<resource>:<action>`，通过 `AuthPermission([...])` 声明。

### B. 修改已有模块

适用：加字段、改字段、删字段、调整查询条件、修复业务逻辑。

流程：
1. 先定位后端模型、Schema、CRUD、Service、Controller 和前端 API/Page。
2. 从 ORM 模型与前端类型同步字段，不只改其中一端。
3. 涉及数据库结构时新增 Alembic 迁移，不直接改历史迁移。
4. 修改摘要要覆盖：数据库字段、Pydantic Schema、查询参数、API 类型、表格列、表单项、详情展示、导入导出映射。

### C. 前端页面开发

适用：新增列表页、表单弹窗、详情页、工作流画布、Skill 编辑器等。
组件复用清单见 `references/frontend-templates.md`。

硬性规则：
- API 路径必须来自后端 `APIRouter` 路径，禁止猜测。
- 列表响应默认按 `PageResult<T>` 处理；如果后端返回结构不同，必须显式写 adapter。
- 表单、表格、API 类型三者字段名必须一致。
- 页面风格跟随现有后台：紧凑、信息密度高、少装饰，避免营销式 hero 页面。

---

## 必须先读（执行任何代码修改前，按任务范围）

1. 总体说明：仓库根目录 `README.md`、`CLAUDE.md`。
2. 后端通用能力：`backend/app/core/base_model.py`、`backend/app/core/base_crud.py`、`backend/app/common/response.py`、`backend/app/core/dependencies.py`。
3. 插件路由发现：涉及插件模块时读 `backend/app/core/discover.py`。
4. 相近模块样例：优先读一个同类型模块的 `model.py`、`schema.py`、`crud.py`、`service.py`、`controller.py`（如 `backend/app/plugin/module_example/demo/`）。
5. 前端相近页面：优先读同目录或同业务风格的 `src/api/**.ts` 与 `src/views/**/index.vue`。

---

## 验证命令

根据改动范围选择最小但有效的验证：

```bash
# 后端
cd backend
uv run ruff check .
uv run pytest

# 前端
cd frontend/web
pnpm run type-check
pnpm run lint:eslint
pnpm run test
```

需要联调时启动：

```bash
cd backend
uv run python main.py run --env=dev

cd frontend/web
pnpm run dev
```

如果命令因本地数据库、Redis、依赖缺失失败，记录具体失败原因，不要把未验证说成已验证。

---

## 输出要求

完成后用中文汇总：

- 改了哪些文件和为什么改。
- 新增/修改的接口路径、权限码、菜单信息。
- 数据库迁移文件及是否已执行。
- 已运行的验证命令和结果。
- 未验证项与原因。
