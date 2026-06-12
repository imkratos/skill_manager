<!-- 第三方 Skill 市场：市场源管理 + 市场 Skill 浏览安装 -->
<template>
  <div class="fa-full-height skill-market-page">
    <ElTabs v-model="activeTab" class="skill-market-tabs">
      <ElTabPane label="Skill 市场" name="items">
        <FaSearchBarWithAudit
          v-show="showItemSearchBar"
          ref="itemSearchBarRef"
          v-model="itemSearchForm"
          :items="itemSearchItems"
          :is-expand="false"
          :show-expand="true"
          :show-reset="true"
          :show-search="true"
          :default-expanded="false"
          @search="handleItemSearch"
          @reset="resetItemSearch"
        />

        <ElCard
          shadow="hover"
          class="fa-table-card market-card-panel"
          :style="{ 'margin-top': showItemSearchBar ? '12px' : '0' }"
        >
            <div class="market-toolbar">
              <div class="market-toolbar__left">
              <ElButton :loading="itemLoading" icon="Refresh" @click="() => fetchItems()">刷新缓存</ElButton>
              <ElButton
                v-if="hasAuth('module_skill:market:sync')"
                :loading="itemLoading"
                icon="Download"
                @click="fetchItems(true)"
              >
                刷新远端
              </ElButton>
            </div>
            <div class="market-toolbar__right">
              <ElSwitch v-model="showItemSearchBar" inline-prompt active-text="搜索" inactive-text="搜索" />
            </div>
          </div>

          <ElSkeleton v-if="itemLoading" :rows="8" animated />
          <ElEmpty v-else-if="itemList.length === 0" description="暂无市场 Skill">
            <ElButton type="primary" icon="Refresh" :loading="itemLoading" @click="() => fetchItems(true)">刷新市场</ElButton>
            <ElButton icon="Setting" @click="activeTab = 'sources'">查看市场源</ElButton>
          </ElEmpty>
          <div v-else class="market-grid">
            <article v-for="item in itemList" :key="item.id" class="market-card">
              <div class="market-card__head">
                <div class="market-card__title">
                  <h3>{{ item.title || item.name }}</h3>
                  <span>{{ item.name }}</span>
                </div>
                <ElTag :type="item.installed_skill_id ? 'success' : 'info'" size="small">
                  {{ item.installed_skill_id ? "已安装" : "未安装" }}
                </ElTag>
                <ElTag :type="item.market_kind === 'plugin' ? 'warning' : 'primary'" size="small">
                  {{ item.market_kind === "plugin" ? "插件包" : "Skill" }}
                </ElTag>
              </div>
              <p class="market-card__desc">{{ item.description || "暂无简介" }}</p>
              <div class="market-card__meta">
                <span>v{{ item.version || "1.0.0" }}</span>
                <span>{{ item.category || "未分类" }}</span>
                <span>{{ item.author || "未知作者" }}</span>
                <span v-if="item.file_count">{{ item.file_count }} 个文件</span>
              </div>
              <div v-if="item.tags?.length" class="market-card__tags">
                <ElTag v-for="tag in item.tags" :key="tag" effect="plain" size="small">{{ tag }}</ElTag>
              </div>
              <div class="market-card__actions">
                <ElButton
                  v-if="hasAuth('module_skill:market:detail')"
                  text
                  type="primary"
                  icon="View"
                  @click="openItemDetail(item)"
                >
                  详情
                </ElButton>
                <ElButton
                  v-if="hasAuth('module_skill:market:install')"
                  text
                  type="primary"
                  icon="Download"
                  :disabled="!!item.installed_skill_id"
                  :loading="installingId === item.id"
                  @click="installItem(item)"
                >
                  安装
                </ElButton>
              </div>
            </article>
          </div>

          <div class="market-pagination">
            <ElPagination
              v-model:current-page="itemPagination.page_no"
              v-model:page-size="itemPagination.page_size"
              :total="itemPagination.total"
              :page-sizes="[12, 24, 48, 96]"
              layout="total, sizes, prev, pager, next, jumper"
              background
              @size-change="() => fetchItems()"
              @current-change="() => fetchItems()"
            />
          </div>
        </ElCard>
      </ElTabPane>

      <ElTabPane label="市场源" name="sources">
        <FaSearchBarWithAudit
          v-show="showSourceSearchBar"
          ref="sourceSearchBarRef"
          v-model="sourceSearchForm"
          :items="sourceSearchItems"
          :is-expand="false"
          :show-expand="true"
          :show-reset="true"
          :show-search="true"
          :default-expanded="false"
          @search="handleSourceSearch"
          @reset="resetSourceSearch"
        />

        <ElCard
          shadow="hover"
          class="fa-table-card source-table-card"
          :style="{ 'margin-top': showSourceSearchBar ? '12px' : '0' }"
        >
          <FaTableHeader
            v-model:columns="sourceColumnChecks"
            v-model:showSearchBar="showSourceSearchBar"
            :loading="sourceLoading"
            @refresh="refreshSources"
          >
            <template #left>
              <ElButton
                v-if="hasAuth('module_skill:market:create')"
                type="primary"
                icon="Plus"
                @click="openSourceDialog('add')"
              >
                新增市场源
              </ElButton>
              <ElButton
                v-if="hasAuth('module_skill:market:delete')"
                type="danger"
                icon="Delete"
                :disabled="selectedSourceIds.length === 0"
                @click="deleteSelectedSources"
              >
                删除
              </ElButton>
            </template>
          </FaTableHeader>

          <FaTable
            ref="sourceTableRef"
            :loading="sourceLoading"
            :data="sourceData"
            :columns="sourceColumns"
            :pagination="sourcePagination"
            @selection-change="onSourceSelectionChange"
            @pagination:size-change="handleSourceSizeChange"
            @pagination:current-change="handleSourceCurrentChange"
          />
        </ElCard>
      </ElTabPane>
    </ElTabs>

    <FaDialog
      v-model="sourceDialogVisible.visible"
      :title="sourceDialogVisible.title"
      width="760px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="sourceDialogVisible.type"
      :confirm-loading="sourceSubmitLoading"
      @cancel="closeSourceDialog"
      @confirm="sourceDialogVisible.type === 'detail' ? closeSourceDialog() : submitSource()"
    >
      <ElForm
        ref="sourceFormRef"
        :model="sourceFormData"
        :rules="sourceRules"
        label-width="110px"
        :disabled="sourceDialogVisible.type === 'detail'"
      >
        <ElRow :gutter="16">
          <ElCol :span="12">
            <ElFormItem label="平台名称" prop="name">
              <ElInput v-model="sourceFormData.name" maxlength="100" placeholder="请输入平台名称" />
            </ElFormItem>
          </ElCol>
          <ElCol :span="12">
            <ElFormItem label="平台编码" prop="code">
              <ElInput v-model="sourceFormData.code" maxlength="100" placeholder="awesome-claude-skills" />
            </ElFormItem>
          </ElCol>
          <ElCol :span="12">
            <ElFormItem label="适配器" prop="adapter_type">
              <ElSelect v-model="sourceFormData.adapter_type" class="w-full">
                <ElOption label="GitHub 仓库" value="github_repo" />
              </ElSelect>
            </ElFormItem>
          </ElCol>
          <ElCol :span="12">
            <ElFormItem label="分支">
              <ElInput v-model="sourceFormData.branch" placeholder="main / master" />
            </ElFormItem>
          </ElCol>
          <ElCol :span="24">
            <ElFormItem label="市场地址" prop="base_url">
              <ElInput v-model="sourceFormData.base_url" placeholder="https://github.com/owner/repo" />
            </ElFormItem>
          </ElCol>
          <ElCol :span="24">
            <ElFormItem label="说明">
              <ElInput
                v-model="sourceFormData.description"
                type="textarea"
                :rows="3"
                maxlength="255"
                show-word-limit
              />
            </ElFormItem>
          </ElCol>
          <ElCol :span="12">
            <ElFormItem label="排序">
              <ElInputNumber v-model="sourceFormData.sort" :min="0" controls-position="right" />
            </ElFormItem>
          </ElCol>
          <ElCol :span="12">
            <ElFormItem label="状态" prop="status">
              <ElRadioGroup v-model="sourceFormData.status">
                <ElRadioButton label="0">启用</ElRadioButton>
                <ElRadioButton label="1">停用</ElRadioButton>
              </ElRadioGroup>
            </ElFormItem>
          </ElCol>
        </ElRow>
      </ElForm>
    </FaDialog>

    <FaDialog
      v-model="itemDetailVisible"
      title="市场 Skill 详情"
      width="860px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      form-mode="detail"
      @cancel="itemDetailVisible = false"
      @confirm="itemDetailVisible = false"
    >
      <FaDescriptions :column="3" :data="itemDetailData" :items="itemDetailItems" max-height="70vh">
        <template #tags="{ row }">
          <ElTag v-for="tag in row?.tags || []" :key="tag" class="mr-1" size="small">{{ tag }}</ElTag>
        </template>
      </FaDescriptions>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage, ElMessageBox, ElTag } from "element-plus";
import { useAuth } from "@/hooks/core/useAuth";
import { useCrudDialog } from "@/hooks/core/useCrudDialog";
import { useTable } from "@/hooks/core/useTable";
import { useTableSelection } from "@/hooks/core/useTableSelection";
import { renderTableOperationCell, type TableOperationAction } from "@/utils/table";
import { cleanEmptyArrayParams } from "@/utils/query";
import type { AuditSearchFormParams } from "@/components/forms/fa-search-bar/auditSearchFormItems";
import type { ColumnOption } from "@/types/component";
import SkillMarketAPI, {
  type SkillMarketItemPageQuery,
  type SkillMarketItemTable,
  type SkillMarketSourceForm,
  type SkillMarketSourcePageQuery,
  type SkillMarketSourceTable,
} from "@/api/module_skill/market";

defineOptions({
  name: "SkillMarket",
  inheritAttrs: false,
});

type SourceSearchFormParams = {
  name?: string;
  code?: string;
  adapter_type?: string;
  status?: string;
} & AuditSearchFormParams;

type ItemSearchFormParams = {
  source_id?: number;
  market_kind?: "skill" | "plugin";
  plugin_name?: string;
  name?: string;
  title?: string;
  category?: string;
  installed?: boolean;
} & AuditSearchFormParams;

const { hasAuth } = useAuth();
const activeTab = ref("items");

const sourceOptions = ref<{ label: string; value: number }[]>([]);
const sourceSearchForm = ref<SourceSearchFormParams>({
  name: undefined,
  code: undefined,
  adapter_type: undefined,
  status: undefined,
  created_time: [],
  updated_time: [],
});
const itemSearchForm = ref<ItemSearchFormParams>({
  source_id: undefined,
  market_kind: undefined,
  plugin_name: undefined,
  name: undefined,
  title: undefined,
  category: undefined,
  installed: undefined,
  created_time: [],
  updated_time: [],
});
const showSourceSearchBar = ref(true);
const showItemSearchBar = ref(true);
const sourceSearchBarRef = ref<{ validate: () => Promise<boolean> } | null>(null);
const itemSearchBarRef = ref<{ validate: () => Promise<boolean> } | null>(null);

const statusOptions = [
  { label: "启用", value: "0" },
  { label: "停用", value: "1" },
];
const adapterOptions = [{ label: "GitHub 仓库", value: "github_repo" }];

const sourceSearchItems = computed(() => [
  { label: "平台名称", key: "name", type: "input", placeholder: "请输入平台名称", clearable: true, span: 6 },
  { label: "平台编码", key: "code", type: "input", placeholder: "请输入平台编码", clearable: true, span: 6 },
  { label: "适配器", key: "adapter_type", type: "select", props: { options: adapterOptions, clearable: true }, span: 6 },
  { label: "状态", key: "status", type: "select", props: { options: statusOptions, clearable: true }, span: 6 },
]);

const itemSearchItems = computed(() => [
  { label: "市场源", key: "source_id", type: "select", props: { options: sourceOptions.value, clearable: true }, span: 6 },
  {
    label: "条目类型",
    key: "market_kind",
    type: "select",
    props: {
      options: [
        { label: "Skill", value: "skill" },
        { label: "插件包", value: "plugin" },
      ],
      clearable: true,
    },
    span: 6,
  },
  { label: "Skill 标识", key: "name", type: "input", placeholder: "请输入 Skill 标识", clearable: true, span: 6 },
  { label: "显示名称", key: "title", type: "input", placeholder: "请输入显示名称", clearable: true, span: 6 },
  {
    label: "安装状态",
    key: "installed",
    type: "select",
    props: {
      options: [
        { label: "已安装", value: true },
        { label: "未安装", value: false },
      ],
      clearable: true,
    },
    span: 6,
  },
]);

function normalizeSourceQuery(params: Record<string, unknown>): SkillMarketSourcePageQuery {
  return cleanEmptyArrayParams({ ...params }, ["created_time", "updated_time"]) as unknown as SkillMarketSourcePageQuery;
}

function normalizeItemQuery(params: Record<string, unknown>): SkillMarketItemPageQuery {
  return cleanEmptyArrayParams({ ...params }, ["created_time", "updated_time"]) as unknown as SkillMarketItemPageQuery;
}

const {
  columns: sourceColumns,
  columnChecks: sourceColumnChecks,
  data: sourceData,
  loading: sourceLoading,
  pagination: sourcePagination,
  getData: getSources,
  replaceSearchParams: replaceSourceSearchParams,
  resetSearchParams: resetSourceSearchParams,
  handleSizeChange: handleSourceSizeChange,
  handleCurrentChange: handleSourceCurrentChange,
  refreshData: refreshSources,
  refreshCreate: refreshSourceCreate,
  refreshUpdate: refreshSourceUpdate,
  refreshRemove: refreshSourceRemove,
} = useTable({
  core: {
    apiFn: SkillMarketAPI.getSourceList,
    apiParams: { page_no: 1, page_size: 10 },
    columnsFactory: (): ColumnOption<SkillMarketSourceTable>[] => [
      { type: "selection", width: 48, fixed: "left" },
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "name", label: "平台名称", minWidth: 150, showOverflowTooltip: true },
      { prop: "code", label: "平台编码", minWidth: 160, showOverflowTooltip: true },
      { prop: "adapter_type", label: "适配器", width: 120, formatter: () => "GitHub 仓库" },
      { prop: "base_url", label: "市场地址", minWidth: 260, showOverflowTooltip: true },
      {
        prop: "status",
        label: "状态",
        width: 88,
        formatter: (row: SkillMarketSourceTable) =>
          h(ElTag, { type: row.status === "0" ? "success" : "info" }, () => (row.status === "0" ? "启用" : "停用")),
      },
      {
        prop: "last_sync_status",
        label: "同步状态",
        width: 112,
        formatter: (row: SkillMarketSourceTable) => {
          if (!row.last_sync_status) return "未同步";
          return h(
            ElTag,
            { type: row.last_sync_status === "success" ? "success" : "danger" },
            () => (row.last_sync_status === "success" ? "成功" : "失败")
          );
        },
      },
      { prop: "last_sync_time", label: "最后同步", width: 168, showOverflowTooltip: true },
      {
        prop: "operation",
        label: "操作",
        width: 260,
        fixed: "right",
        align: "right",
        formatter: (row: SkillMarketSourceTable) => formatSourceOperationCell(row),
      },
    ],
  },
  hooks: {
    onSuccess: updateSourceOptions,
  },
});

const { selectedIds: selectedSourceIds, onTableSelectionChange: onSourceSelectionChange } =
  useTableSelection<SkillMarketSourceTable>();
const sourceTableRef = ref();

const itemList = ref<SkillMarketItemTable[]>([]);
const itemLoading = ref(false);
const itemPagination = reactive({ page_no: 1, page_size: 12, total: 0 });
const installingId = ref<number>();

async function fetchItems(refresh = false) {
  itemLoading.value = true;
  try {
    const query = normalizeItemQuery({
      ...itemSearchForm.value,
      page_no: itemPagination.page_no,
      page_size: itemPagination.page_size,
      refresh,
    });
    const res = await SkillMarketAPI.getItemList(query);
    const page = res.data.data;
    itemList.value = page?.items || [];
    itemPagination.total = page?.total || 0;
  } finally {
    itemLoading.value = false;
  }
}

async function handleItemSearch(params: ItemSearchFormParams) {
  await itemSearchBarRef.value?.validate();
  itemSearchForm.value = { ...params };
  itemPagination.page_no = 1;
  await fetchItems();
}

async function resetItemSearch() {
  itemSearchForm.value = {
    source_id: undefined,
    market_kind: undefined,
    plugin_name: undefined,
    name: undefined,
    title: undefined,
    category: undefined,
    installed: undefined,
    created_time: [],
    updated_time: [],
  };
  itemPagination.page_no = 1;
  await fetchItems();
}

async function handleSourceSearch(params: SourceSearchFormParams) {
  await sourceSearchBarRef.value?.validate();
  replaceSourceSearchParams(normalizeSourceQuery(params as Record<string, unknown>) as unknown as Record<string, unknown>);
  await getSources();
}

async function resetSourceSearch() {
  sourceSearchForm.value = {
    name: undefined,
    code: undefined,
    adapter_type: undefined,
    status: undefined,
    created_time: [],
    updated_time: [],
  };
  await resetSourceSearchParams();
}

function updateSourceOptions(rows: SkillMarketSourceTable[]) {
  sourceOptions.value = rows
    .filter((item) => item.id != null)
    .map((item) => ({ label: item.name || item.code || String(item.id), value: Number(item.id) }));
}

function buildSourceRowActions(row: SkillMarketSourceTable): TableOperationAction[] {
  const actions: TableOperationAction[] = [
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      icon: "ri:edit-line",
      perm: "module_skill:market:update",
      run: () => void openSourceDialog("edit", row),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-line",
      perm: "module_skill:market:delete",
      run: () => void deleteSource(row),
    },
  ];
  return actions.filter((action) => !action.perm || hasAuth(action.perm));
}

function formatSourceOperationCell(row: SkillMarketSourceTable) {
  return renderTableOperationCell(buildSourceRowActions(row), { maxInline: 3 });
}

const { dialogVisible: sourceDialogVisible } = useCrudDialog();
const sourceFormRef = ref<FormInstance>();
const sourceSubmitLoading = ref(false);
const sourceFormData = ref<SkillMarketSourceForm>({
  name: "",
  code: "",
  adapter_type: "github_repo",
  base_url: "",
  branch: "main",
  config: undefined,
  sort: 0,
  status: "0",
  description: undefined,
});
const sourceRules = reactive<FormRules>({
  name: [{ required: true, message: "请输入平台名称", trigger: "blur" }],
  code: [{ required: true, message: "请输入平台编码", trigger: "blur" }],
  adapter_type: [{ required: true, message: "请选择适配器", trigger: "change" }],
  base_url: [{ required: true, message: "请输入市场地址", trigger: "blur" }],
  status: [{ required: true, message: "请选择状态", trigger: "change" }],
});

const initialSourceForm: SkillMarketSourceForm = {
  name: "",
  code: "",
  adapter_type: "github_repo",
  base_url: "",
  branch: "main",
  config: undefined,
  sort: 0,
  status: "0",
  description: undefined,
};

function openSourceDialog(type: "add" | "edit" | "detail", row?: SkillMarketSourceTable) {
  sourceDialogVisible.visible = true;
  sourceDialogVisible.title = type === "add" ? "新增市场源" : type === "edit" ? "编辑市场源" : "市场源详情";
  sourceDialogVisible.type = type === "add" ? "create" : type === "edit" ? "update" : "detail";
  sourceFormData.value = type === "add" ? { ...initialSourceForm } : { ...initialSourceForm, ...row };
  nextTick(() => sourceFormRef.value?.clearValidate());
}

function closeSourceDialog() {
  sourceDialogVisible.visible = false;
}

async function submitSource() {
  await sourceFormRef.value?.validate();
  sourceSubmitLoading.value = true;
  try {
    if (sourceDialogVisible.type === "create") {
      await SkillMarketAPI.createSource(sourceFormData.value);
      ElMessage.success("创建市场源成功");
      await refreshSourceCreate();
    } else if (sourceFormData.value.id) {
      await SkillMarketAPI.updateSource(sourceFormData.value.id, sourceFormData.value);
      ElMessage.success("更新市场源成功");
      await refreshSourceUpdate();
    }
    closeSourceDialog();
  } finally {
    sourceSubmitLoading.value = false;
  }
}

async function deleteSource(row: SkillMarketSourceTable) {
  if (!row.id) return;
  await ElMessageBox.confirm(`确认删除市场源「${row.name || row.code}」？`, "删除确认", { type: "warning" });
  await SkillMarketAPI.deleteSource([row.id]);
  ElMessage.success("删除市场源成功");
  await refreshSourceRemove();
}

async function deleteSelectedSources() {
  if (selectedSourceIds.value.length === 0) return;
  await ElMessageBox.confirm(`确认删除选中的 ${selectedSourceIds.value.length} 个市场源？`, "删除确认", { type: "warning" });
  await SkillMarketAPI.deleteSource(selectedSourceIds.value);
  ElMessage.success("批量删除市场源成功");
  sourceTableRef.value?.elTableRef?.clearSelection?.();
  await refreshSourceRemove();
}

const itemDetailVisible = ref(false);
const itemDetailData = ref<SkillMarketItemTable>({});
const itemDetailItems: import("@/components/others/fa-descriptions/index.vue").DescriptionsItem[] = [
  { label: "Skill 标识", prop: "name" },
  { label: "显示名称", prop: "title" },
  { label: "分类", prop: "category" },
  { label: "版本", prop: "version" },
  { label: "作者", prop: "author" },
  { label: "许可证", prop: "license" },
  { label: "目录路径", prop: "skill_path" },
  { label: "条目类型", prop: "market_kind" },
  { label: "插件包", prop: "plugin_name" },
  { label: "来源提交", prop: "source_commit" },
  { label: "文件数量", prop: "file_count" },
  { label: "仓库地址", prop: "repository_url" },
  { label: "已安装ID", prop: "installed_skill_id" },
  { label: "标签", prop: "tags", slot: "tags" },
  { label: "简介", prop: "description", span: 3 },
];

async function openItemDetail(row: SkillMarketItemTable) {
  if (row.source_id && row.external_id) {
    itemDetailData.value = row;
  } else if (row.id) {
    const res = await SkillMarketAPI.getItemDetail(row.id);
    itemDetailData.value = res.data.data || row;
  }
  itemDetailVisible.value = true;
}

async function installItem(row: SkillMarketItemTable) {
  if (!row.id && (!row.source_id || !row.external_id)) return;
  const installText =
    row.market_kind === "plugin"
      ? `确认安装插件包「${row.title || row.name}」包含的 ${row.skill_paths?.length || 0} 个 Skill？`
      : `确认安装「${row.title || row.name}」到本地 Skill 列表？`;
  await ElMessageBox.confirm(installText, "安装确认", { type: "info" });
  installingId.value = row.id;
  try {
    if (row.source_id && row.external_id) {
      await SkillMarketAPI.installRemoteItem({ source_id: row.source_id, external_id: row.external_id });
    } else if (row.id) {
      await SkillMarketAPI.installItem(row.id);
    }
    ElMessage.success("安装成功");
    await fetchItems();
  } finally {
    installingId.value = undefined;
  }
}

onMounted(async () => {
  await getSources();
  await fetchItems();
});
</script>

<style scoped lang="scss">
.skill-market-page {
  .skill-market-tabs {
    height: 100%;
  }

  :deep(.el-tabs__content) {
    height: calc(100% - 54px);
    overflow: hidden;
  }

  :deep(.el-tab-pane) {
    display: flex;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    flex-direction: column;
  }
}

.market-card-panel {
  display: flex;
  min-height: 0;
  flex: 1;
  overflow: hidden;

  :deep(.el-card__body) {
    display: flex;
    width: 100%;
    min-height: 0;
    flex: 1;
    flex-direction: column;
    overflow: hidden;
  }
}

.source-table-card {
  min-height: calc(100% - 72px);

  :deep(.el-card__body) {
    overflow: hidden;
  }

  :deep(.fa-table) {
    min-width: 0;
  }
}

.market-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.market-grid {
  display: grid;
  min-height: 0;
  padding-right: 4px;
  overflow: auto;
  flex: 1;
  align-content: start;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}

.market-card {
  display: flex;
  min-height: 210px;
  padding: 14px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
  flex-direction: column;
}

.market-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.market-card__title {
  min-width: 0;

  h3 {
    margin: 0;
    overflow: hidden;
    font-size: 16px;
    font-weight: 600;
    line-height: 22px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  span {
    display: block;
    margin-top: 2px;
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }
}

.market-card__desc {
  display: -webkit-box;
  min-height: 44px;
  margin: 12px 0;
  overflow: hidden;
  color: var(--el-text-color-regular);
  line-height: 22px;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.market-card__meta,
.market-card__tags,
.market-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.market-card__meta {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.market-card__tags {
  margin-top: 12px;
}

.market-card__actions {
  margin-top: auto;
  justify-content: flex-end;
}

.market-pagination {
  display: flex;
  flex-shrink: 0;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
