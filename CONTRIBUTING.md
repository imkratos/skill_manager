# 参与贡献

感谢你参与 Skill Manager。这个项目面向企业 AI Skill 的开发、调试、管理、运行和分发，贡献时请优先围绕“让 Skill 成为安全、可测试、可复用、可治理的工程化能力单元”这个方向推进。

## 开始之前

1. 先阅读 [README.md](./README.md)，理解项目定位、路线图和当前基础能力。
2. 较大的功能改动请先通过 Issue 或设计说明讨论清楚边界，避免实现方向偏离 Skill IDE、Skill Runtime、Skill Registry、Skill Marketplace 的主线。
3. 修改代码前先看相关模块的 README 和现有实现，尽量沿用当前分层、命名和工程约定。
4. 不要提交本地环境文件、密钥、数据库账号、Token、日志或构建产物。

## 项目结构

```text
skill_manager/
├── backend/              # FastAPI 后端
├── frontend/
│   └── web/              # Vue3 + TypeScript 前端
├── docker/               # Docker 部署配置
├── scripts/              # 辅助脚本
├── skills/               # Skill 相关资源与项目内 Skill
├── README.md             # 中文项目说明
└── README.en.md          # 英文项目说明
```

## 环境要求

| 类型 | 要求 |
| ---- | ---- |
| Python | 3.10+，推荐 3.12 |
| Node.js | 20.19+ |
| 包管理 | uv、pnpm 9.x |
| 数据库 | MySQL 8.0+ 或 PostgreSQL 14+ |
| 缓存 | Redis 6.x / 7.x |

## 本地开发

首次启动前复制环境配置：

```bash
cp backend/env/.env.dev.example backend/env/.env.dev
cp frontend/web/.env.development.example frontend/web/.env.development
```

启动后端：

```bash
cd backend
uv sync
uv run main.py run --env=dev
```

启动前端：

```bash
cd frontend/web
pnpm install
pnpm run dev
```

默认访问地址：

```text
http://127.0.0.1:5173
```

后端接口文档通常在：

```text
http://127.0.0.1:8001/docs
```

实际端口以 `backend/env/.env.dev` 和 `frontend/web/.env.development` 为准。

## 后端贡献规范

后端位于 `backend/`，核心技术栈是 FastAPI、Pydantic、SQLAlchemy、Alembic、Redis、APScheduler、Agno 和 Prefect。

业务模块优先沿用现有分层：

```text
module_*/
├── controller.py    # HTTP 请求处理
├── service.py       # 业务逻辑
├── crud.py          # 数据库访问
├── model.py         # ORM 模型
├── schema.py        # Pydantic 模型
└── param.py         # 查询或请求参数
```

常用检查命令：

```bash
cd backend
uv run ruff check .
uv run pytest
```

修改 ORM、SQL、初始化数据或权限菜单时，需要特别注意迁移纪律：

1. 已应用过的迁移不要直接改历史文件，应新增向前迁移。
2. 面向已有数据库的字段、索引、菜单和权限数据要尽量做到幂等。
3. 新增非空字段必须考虑默认值或回填路径。
4. 提交前至少验证一次对应查询或接口路径；如果无法验证，请在 PR 中说明原因。

生成和应用迁移：

```bash
cd backend
uv run main.py revision --env=dev
uv run main.py upgrade --env=dev
```

## 前端贡献规范

前端位于 `frontend/web/`，核心技术栈是 Vue 3、TypeScript、Vite、Element Plus、Pinia、Vue Router、Tailwind CSS、SCSS、Vue Flow 和 CodeMirror。

常用命令：

```bash
cd frontend/web
pnpm run type-check
pnpm run lint
pnpm run test
pnpm run build
```

开发约定：

1. 页面放在 `src/views/`，接口封装放在 `src/api/`，通用逻辑优先放在 `src/hooks/` 或 `src/utils/`。
2. 新增业务页时，视图、路由、菜单、权限和 i18n 文案要保持一致。
3. 只有 `VITE_` 前缀的环境变量会进入前端代码；修改 `.env` 后需要重启 `pnpm run dev`。
4. 不要手动修改自动生成的类型文件，尤其是 `src/types/import/` 下的内容。

## Skill 功能贡献建议

Skill Manager 的核心不是单个 Prompt，而是 Prompt、Workflow、工具权限、模型配置、输入输出 Schema、测试集、版本、日志和发布信息组成的工程化单元。

新增或修改 Skill 相关能力时，请优先回答以下问题：

1. 这个能力属于 Skill IDE、Skill Runtime、Skill Registry 还是 Skill Marketplace？
2. 是否影响租户隔离、工具权限、模型权限、执行沙箱或审计日志？
3. 是否能被测试集、Trace、日志或评测结果复盘？
4. 是否需要版本记录、发布状态或回滚依据？
5. 前后端接口、数据模型和权限菜单是否同步更新？

## 提交信息

推荐使用约定式提交：

```text
feat(skill): 新增 Skill 调试入口
fix(runtime): 修复工具调用权限校验
docs: 更新本地启动说明
refactor(registry): 调整市场源适配器结构
test: 增加 Skill 市场服务测试
```

前端可使用项目内 Commitizen：

```bash
cd frontend/web
pnpm run commit
```

## Pull Request 流程

1. 从最新主干创建功能分支，例如 `feature/skill-debugger`、`fix/runtime-permission`。
2. 保持变更聚焦，一个 PR 解决一个明确问题。
3. 补充必要测试或手工验证说明。
4. 提交前按影响范围运行检查：
   - 后端：`cd backend && uv run ruff check . && uv run pytest`
   - 前端：`cd frontend/web && pnpm run type-check && pnpm run lint && pnpm run test`
   - 构建：涉及前端构建或部署时运行 `cd frontend/web && pnpm run build`
5. PR 描述中说明变更内容、验证结果、数据库迁移影响和已知风险。

## 文档贡献

文档请优先使用中文，表达要具体、可执行。涉及命令时注明执行目录；涉及配置时注明文件路径；涉及接口或数据结构时说明字段含义和兼容性影响。

## 许可证

提交贡献即表示你同意将代码和文档以项目的 [MIT 协议](./LICENSE) 开源。
