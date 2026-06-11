# 前端代码模板（Vue3 + TypeScript）

> 本文件供 `SKILL.md` 在 Step 3 执行前端文件写入前按需读取。涉及前端改动（操作类型 A、B、C）时读取。
> 模板取自真实模块的已有页面和 API 文件，生成前优先 Read 一个同类型真实页面对照。

## 文件清单

```text
frontend/web/src/api/module_<domain>/<resource>.ts       # API + 类型定义
frontend/web/src/views/module_<domain>/<resource>/index.vue  # 主页面
```

---

## API 文件

```typescript
// frontend/web/src/api/module_<domain>/<resource>.ts
import { request } from "@utils";

const API_PATH = "/<domain>/<resource>";  // 对应后端 module_<domain> 推导前缀 + controller prefix

const XxxAPI = {
  getXxxList(query: XxxPageQuery) {
    return request<ApiResponse<PageResult<XxxTable>>>({ url: `${API_PATH}/list`, method: "get", params: query });
  },
  getXxxDetail(id: number) {
    return request<ApiResponse<XxxTable>>({ url: `${API_PATH}/detail/${id}`, method: "get" });
  },
  createXxx(body: XxxForm) {
    return request<ApiResponse>({ url: `${API_PATH}/create`, method: "post", data: body });
  },
  updateXxx(id: number, body: XxxForm) {
    return request<ApiResponse>({ url: `${API_PATH}/update/${id}`, method: "put", data: body });
  },
  deleteXxx(body: number[]) {
    return request<ApiResponse>({ url: `${API_PATH}/delete`, method: "delete", data: body });
  },
  batchXxx(body: BatchType) {
    return request<ApiResponse>({ url: `${API_PATH}/available/setting`, method: "patch", data: body });
  },
  exportXxx(body: XxxPageQuery) {
    return request<Blob>({ url: `${API_PATH}/export`, method: "post", data: body, responseType: "blob" });
  },
  importXxx(body: FormData) {
    return request<ApiResponse>({ url: `${API_PATH}/import`, method: "post", data: body, headers: { "Content-Type": "multipart/form-data" } });
  },
};

export default XxxAPI;

// ==== 类型定义 ====

export interface XxxPageQuery extends PageQuery {
  name?: string;
  status?: string;
  created_time?: string[];
}

export interface XxxTable extends BaseType {
  name?: string;
  status?: string;
  description?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
}

export interface XxxForm extends BaseFormType {
  name?: string;
  status?: string;
  description?: string;
}
```

规则：
- `API_PATH` **必须**对应后端 `APIRouter.prefix` + 路由容器前缀，**禁止猜测**。
- 先 Read 后端 `controller.py` 确认路由路径后再填 `API_PATH`。
- 导出默认 API 对象 + `PageQuery`/`Table`/`Form` 类型。
- 创建/更新/删除/批量状态/导入/导出方法命名与现有模块保持一致。

---

## 页面骨架

```vue
<!-- frontend/web/src/views/module_<domain>/<resource>/index.vue -->
<template>
  <div class="fa-full-height">
    <FaSearchBarWithAudit
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="xxxSearchItems"
      :is-expand="false"
      @search="handleSearch"
      @reset="onResetSearch"
    />

    <ElCard shadow="hover" class="fa-table-card" :style="{ 'margin-top': showSearchBar ? '12px' : '0' }">
      <FaTableHeader v-model:columns="columnChecks" v-model:showSearchBar="showSearchBar" :loading="loading" @refresh="refreshData">
        <template #left>
          <FaTableHeaderLeft
            :remove-ids="selectedIds"
            :perm-create="['module_<domain>:<resource>:create']"
            :perm-delete="['module_<domain>:<resource>:delete']"
            :perm-export="['module_<domain>:<resource>:export']"
            :perm-import="['module_<domain>:<resource>:import']"
            :perm-patch="['module_<domain>:<resource>:patch']"
            :delete-loading="batchDeleting"
            @add="openEditDialog('add')"
            @delete="handleBatchDelete"
            @export="openExport"
            @import="openImport"
            @more="runBatchStatus"
          />
        </template>
      </FaTableHeader>

      <FaTable
        ref="faTableRef"
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        @selection-change="onTableSelectionChange"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </ElCard>

    <FaDialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      width="860px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @confirm="dialogVisible.type === 'detail' ? handleCloseDialog() : handleSubmit()"
    >
      <!-- 表单内容：FaForm 或直接 ElForm -->
    </FaDialog>

    <!-- 导出/导入弹窗 -->
    <FaExportDialog
      v-model="exportDialogVisible"
      :api="XxxAPI.exportXxx"
      :search="searchForm"
      filename="xxx.xlsx"
    />
    <FaImportDialog
      v-model="importDialogVisible"
      :api="XxxAPI.importXxx"
      @success="refreshData"
    />
  </div>
</template>
```

---

## 核心 Fa 组件复用清单

| 组件 | 功能 | 何时使用 |
|------|------|---------|
| `FaTable` | 列表表格 + 分页 + 列选择 | 所有列表页 |
| `FaTableHeader` | 表头按钮栏（刷新 + 列选择 + 展开搜索） | 搭配 FaTable |
| `FaTableHeaderLeft` | 左侧操作按钮（新增/删除/导入/导出/批量） | 搭配 FaTableHeader |
| `FaSearchBarWithAudit` | 搜索栏 + 审计字段（created_time/updated_time/created_by/updated_by） | 有搜索条件的列表 |
| `FaForm` | 表单组件（支持动态项） | 弹窗/页面表单 |
| `FaDialog` | 弹窗容器（add/edit/detail 三态） | CRUD 弹窗 |
| `FaExportDialog` | 导出弹窗 | 有导出功能时 |
| `FaImportDialog` | 导入弹窗 | 有导入功能时 |
| `useTable` | 表格数据 hook（分页/排序/刷新） | 所有列表页 |
| `useCrudDialog` | CRUD 弹窗状态管理 hook | 所有 CRUD 页 |
| `useTableSelection` | 表格多选 hook（selectedIds） | 有批量操作时 |
| `useAuth().hasAuth` | 权限判断 | 按钮显隐 |
| `auditSearchFormItems` | 审计搜索项（标准化） | FaSearchBarWithAudit |

---

## 字段类型对照表（后端 → 前端）

| Python 类型 | 前端类型 | 表格列/表单项建议 |
|------------|---------|-----------------|
| `str` (status 0/1) | `string` | 状态标签 + 下拉选 |
| `str` (name/title) | `string` | ElInput |
| `str \| None` (text/desc) | `string?` | ElInput type="textarea" |
| `int` | `number` | ElInputNumber |
| `float` | `number` | ElInputNumber :precision="2" |
| `bool` | `boolean` | ElSwitch |
| `DateStr` | `string` | ElDatePicker type="date" |
| `TimeStr` | `string` | ElTimePicker |
| `DateTimeStr` | `string` | ElDatePicker type="datetime" |
| `dict / JSON` | `Record<string,any>?` | CodeMirror / JSON 编辑器 |

---

## ⛔ 前端常见错误清单（补强护栏）

| 错误行为 | 后果 | 正确做法 |
|---------|------|---------|
| API_PATH 凭猜测写（如 `/api/v1/skill/...`） | 404，接口不通 | Read controller.py 确认路由后再写 |
| Table 类型字段多于/少于后端 Schema | 列不显示 / 报类型错误 | 以 `XxxOutSchema` 为准 |
| 权限码与后端 `AuthPermission` 不一致 | 按钮不显示或无权限 | 三处(controller/migration/front)统一管理 |
| 直接用 ElTable 不用 FaTable | 缺少分页/列选择/统一样式 | 列表页统一用 FaTable |
| 自行实现搜索栏而不用 FaSearchBarWithAudit | 缺少审计字段标准搜索、风格不统一 | 复用 Fa 搜索栏 |
| 响应按 `response.data` 直接取 | 实际结构可能是 `response.data.data` | 看 `request` 封装的 transform 逻辑 |
