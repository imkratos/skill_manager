<div align="center">
     <h1>Skill Manager</h1>
     <h3>AI Skill Engineering Platform</h3>
     <p>一个面向企业 AI 技能工程化的开发、调试、管理与发布平台。</p>
     <p>
          <b>FastAPI</b> + <b>Vue3</b> + <b>TypeScript</b> + <b>Workflow</b> + <b>Agent Runtime</b>
     </p>

简体中文 | [English](./README.en.md)

</div>

## 项目定位

Skill Manager 不是一个简单的 Prompt 管理后台，而是面向未来 Agent 应用落地的 **AI Skill 工程平台**。

在真实企业场景中，一个可复用、可治理、可交付的 Skill 不只是一段提示词，而是由 Prompt、Workflow、工具权限、模型配置、输入输出 Schema、测试集、版本、日志和发布信息共同组成的工程化单元。

本项目希望把这些能力统一管理起来，让团队可以像管理代码、API 和微服务一样管理 AI Skill。

## 为什么做这个项目

当前很多 AI Agent 项目还停留在“野生 Prompt”阶段：

| 现状 | 问题 |
| ---- | ---- |
| Prompt 到处复制 | 无法版本化、无法复用 |
| MCP / Tool 随意接入 | 权限边界不清晰 |
| Workflow 分散在不同项目 | 缺少统一编排和调试 |
| Agent 调试靠聊天记录 | 缺少 Trace、日志和评测 |
| 行业知识散落 | 难以沉淀成可交付能力 |

Skill Manager 关注的核心问题是：

> 如何管理 Skill 的完整生命周期，而不只是如何调用大模型。

## 目标形态

未来一个完整的 Skill 应该包含：

```text
Skill
├── Prompt
├── Workflow
├── Tool / MCP 权限
├── Memory
├── Model 配置
├── 输入输出 Schema
├── DSL
├── 测试集
├── 评测结果
├── 版本记录
├── Agent 策略
└── 发布信息
```

可以把 Skill 理解为 **AI 时代的微服务**：它需要被设计、调试、测试、发布、观测、复用和治理。

## 产品方向

Skill Manager 的长期目标由四部分组成：

| 模块 | 说明 | 状态 |
| ---- | ---- | ---- |
| Skill IDE | Prompt、Workflow、DSL、Schema 的编辑与调试入口 | 规划中 |
| Skill Runtime | 负责执行、沙箱、权限、Token、日志和监控 | 建设中 |
| Skill Registry | 类似 npm 的 Skill 上传、版本、标签、搜索和安装能力 | 规划中 |
| Skill Marketplace | 面向行业 Skill 的共享、分发和商业化 | 规划中 |

## 当前基础

项目当前基于 FastApiAdmin 进行二次建设，已经具备企业级后台系统的基础能力：

| 能力 | 说明 |
| ---- | ---- |
| 用户与权限 | 用户、角色、菜单、按钮权限等基础 RBAC 能力 |
| 多租户基础 | 租户管理、数据隔离和后台管理能力 |
| 工作流基础 | 流程定义、节点类型、发布与执行入口 |
| AI 助手基础 | 基于 Agent 框架的聊天入口和会话记忆 |
| 日志与监控 | 操作日志、在线用户、服务器和缓存监控 |
| 开发工具 | 代码生成、接口文档、文件管理等后台基础设施 |

这些能力是后续建设 Skill IDE、Skill Runtime、Skill Registry 和权限治理体系的基础。

## 适合的切入场景

本项目优先关注 **企业文档 Skill** 场景，而不是泛化的通用 Agent 平台。

典型方向包括：

- 公文、红头文件、审计报告、合同审核等文档 Skill
- 标书、PPT、Word 报告等生成类 Skill
- 林业、政务、审计等行业知识沉淀
- DSL 到 Word / PPT / 表格的结构化渲染流程
- 企业内部 Prompt、Workflow、Tool 权限的统一治理

## 路线图

第一阶段：Skill IDE

- Prompt 编辑与模板管理
- Workflow 可视化编排
- DSL 调试与渲染预览
- 输入输出 Schema 管理
- 本地调试体验，类似 Postman

第二阶段：Skill Runtime

- Skill 执行入口
- Tool / MCP 权限控制
- Token、日志、异常追踪
- Workflow Trace、Tool Trace、Memory Trace

第三阶段：Skill Registry

- Skill 上传、安装、版本管理
- 标签、分类、搜索
- 团队内共享和复用

第四阶段：Skill Marketplace

- 行业 Skill 发布
- 企业级 Skill 交付
- 权限、授权和商业化分发

> 说明：以上是产品建设方向，并不代表当前版本已经全部完成。当前仓库仍处于平台基础能力和 Skill 工程化能力逐步融合阶段。

## 本地启动

```bash
# 1. 配置环境
cp backend/env/.env.dev.example backend/env/.env.dev
cp frontend/web/.env.development.example frontend/web/.env.development

# 2. 启动后端
cd backend
uv sync
uv run main.py run --env=dev

# 3. 启动前端
cd ../frontend/web
pnpm install
pnpm run dev
```

浏览器打开：

```text
http://127.0.0.1:5173
```

默认账号请以初始化数据或本地环境配置为准。

## 环境要求

| 类型 | 要求 |
| ---- | ---- |
| Python | 3.10+，推荐 3.12 |
| Node.js | 20+ |
| 包管理 | uv、pnpm |
| 数据库 | MySQL 8.0+ 或 PostgreSQL 14+ |
| 缓存 | Redis 6.x / 7.x |

## 工程结构

```text
skill_manager/
├── backend/              # FastAPI 后端
├── frontend/
│   └── web/              # Vue3 + TypeScript 前端
├── docker/               # Docker 部署配置
├── scripts/              # 辅助脚本
├── README.md             # 中文说明
└── README.en.md          # 英文说明
```

## 技术栈

- 后端：FastAPI、Pydantic、SQLAlchemy、Alembic、Redis、APScheduler、Agno、Prefect
- 前端：Vue3、TypeScript、Vite、Element Plus、Pinia、Vue Flow、CodeMirror
- 工程化：uv、pnpm、Docker、Ruff、ESLint、Vitest

## 项目愿景

AI 应用的稳定交付不会只依赖一个 Agent，而会依赖一组可测试、可复用、可治理的 Skill。

Skill Manager 的目标是把企业中分散的 Prompt、Workflow、工具权限、行业规则和文档模板沉淀为可持续演进的 AI 能力资产，最终形成面向企业文档场景的 Skill Operating System。
