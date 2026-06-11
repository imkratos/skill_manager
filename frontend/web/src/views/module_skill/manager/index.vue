<!-- Skill 管理：卡片列表 + 标准 Skill 目录文件维护 -->
<template>
  <div class="fa-full-height skill-manager-page">
    <FaSearchBarWithAudit
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="skillSearchItems"
      :is-expand="false"
      :show-expand="true"
      :show-reset="true"
      :show-search="true"
      :default-expanded="false"
      @search="handleSearch"
      @reset="onResetSearch"
    />

    <ElCard
      shadow="hover"
      class="fa-table-card skill-card-panel"
      :style="{ 'margin-top': showSearchBar ? '12px' : '0' }"
    >
      <div class="skill-toolbar">
        <div class="skill-toolbar__left">
          <ElButton
            v-if="hasAuth('module_skill:manager:create')"
            type="primary"
            icon="Plus"
            @click="openEditDialog('add')"
          >
            新增
          </ElButton>
          <ElButton :loading="loading" icon="Refresh" @click="fetchList">刷新</ElButton>
        </div>
        <div class="skill-toolbar__right">
          <ElSwitch
            v-model="showSearchBar"
            inline-prompt
            active-text="搜索"
            inactive-text="搜索"
          />
        </div>
      </div>

      <ElSkeleton v-if="loading" :rows="8" animated />
      <ElEmpty v-else-if="skillList.length === 0" description="暂无 Skill" />
      <div v-else class="skill-grid">
        <article v-for="item in skillList" :key="item.id" class="skill-card">
          <div class="skill-card__head">
            <div class="skill-card__title">
              <h3>{{ item.title || item.name }}</h3>
              <span>{{ item.name }}</span>
            </div>
            <ElTag :type="item.status === '0' ? 'success' : 'info'" size="small">
              {{ item.status === "0" ? "启用" : "停用" }}
            </ElTag>
          </div>
          <p class="skill-card__desc">{{ item.description || "—" }}</p>
          <div class="skill-card__meta">
            <span>v{{ item.version || "1.0.0" }}</span>
            <span>{{ item.category || "未分类" }}</span>
            <span>{{ item.updated_time || item.created_time || "—" }}</span>
          </div>
          <div v-if="item.tags?.length" class="skill-card__tags">
            <ElTag v-for="tag in item.tags" :key="tag" effect="plain" size="small">{{ tag }}</ElTag>
          </div>
          <div class="skill-card__actions">
            <ElButton
              v-if="hasAuth('module_skill:manager:detail')"
              text
              type="primary"
              icon="View"
              @click="openDetailDialog(item)"
            >
              详情
            </ElButton>
            <ElButton
              v-if="hasAuth('module_skill:manager:update')"
              text
              type="primary"
              icon="Edit"
              @click="openEditDialog('edit', item)"
            >
              编辑
            </ElButton>
            <ElButton
              v-if="hasAuth('module_skill:manager:download')"
              text
              type="primary"
              icon="Download"
              @click="downloadSkill(item)"
            >
              下载
            </ElButton>
            <ElButton
              v-if="hasAuth('module_skill:manager:delete')"
              text
              type="danger"
              icon="Delete"
              @click="deleteSkill(item)"
            >
              删除
            </ElButton>
          </div>
        </article>
      </div>

      <div class="skill-pagination">
        <ElPagination
          v-model:current-page="pagination.page_no"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[12, 24, 48, 96]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchList"
          @current-change="fetchList"
        />
      </div>
    </ElCard>

    <FaDialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="1040px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogFormMode"
      :confirm-loading="submitLoading"
      @cancel="closeDialog"
      @confirm="dialogMode === 'detail' ? closeDialog() : submitSkill()"
    >
      <ElTabs v-model="activeTab" class="skill-editor-tabs">
        <ElTabPane label="基础信息" name="base">
          <ElForm
            ref="formRef"
            :model="formData"
            :rules="rules"
            label-width="100px"
            class="skill-form"
            :disabled="dialogMode === 'detail'"
          >
            <ElRow :gutter="16">
              <ElCol :span="12">
                <ElFormItem label="Skill 标识" prop="name">
                  <ElInput v-model="formData.name" maxlength="100" placeholder="如 document-review" />
                </ElFormItem>
              </ElCol>
              <ElCol :span="12">
                <ElFormItem label="显示名称" prop="title">
                  <ElInput v-model="formData.title" maxlength="100" placeholder="请输入显示名称" />
                </ElFormItem>
              </ElCol>
              <ElCol :span="12">
                <ElFormItem label="分类">
                  <ElInput v-model="formData.category" maxlength="100" placeholder="请输入分类" />
                </ElFormItem>
              </ElCol>
              <ElCol :span="12">
                <ElFormItem label="版本号">
                  <ElInput v-model="formData.version" maxlength="50" placeholder="1.0.0" />
                </ElFormItem>
              </ElCol>
              <ElCol :span="12">
                <ElFormItem label="作者">
                  <ElInput v-model="formData.author" maxlength="100" placeholder="请输入作者" />
                </ElFormItem>
              </ElCol>
              <ElCol :span="12">
                <ElFormItem label="状态" prop="status">
                  <ElRadioGroup v-model="formData.status">
                    <ElRadioButton label="0">启用</ElRadioButton>
                    <ElRadioButton label="1">停用</ElRadioButton>
                  </ElRadioGroup>
                </ElFormItem>
              </ElCol>
              <ElCol :span="24">
                <ElFormItem label="标签">
                  <ElSelect
                    v-model="formData.tags"
                    multiple
                    filterable
                    allow-create
                    default-first-option
                    placeholder="输入后回车创建标签"
                    class="w-full"
                  />
                </ElFormItem>
              </ElCol>
              <ElCol :span="24">
                <ElFormItem label="简介" prop="description">
                  <ElInput
                    v-model="formData.description"
                    type="textarea"
                    :rows="4"
                    maxlength="500"
                    show-word-limit
                    placeholder="请输入 Skill 简介"
                  />
                </ElFormItem>
              </ElCol>
            </ElRow>
          </ElForm>
        </ElTabPane>

        <ElTabPane label="SKILL.md" name="skill">
          <ElInput
            v-model="formData.skill_md"
            type="textarea"
            :rows="18"
            :disabled="dialogMode === 'detail'"
            resize="none"
            class="skill-code-input"
          />
        </ElTabPane>

        <ElTabPane label="引用文件" name="files">
          <div class="file-toolbar" v-if="dialogMode !== 'detail'">
            <ElButton icon="FolderAdd" @click="addFileRow('directory')">新增目录</ElButton>
            <ElButton type="primary" icon="DocumentAdd" @click="addFileRow('file')">新增文件</ElButton>
          </div>
          <ElTable :data="formData.files" border height="360px" class="skill-file-table">
            <ElTableColumn label="类型" width="120">
              <template #default="{ row }">
                <ElSelect v-model="row.type" :disabled="dialogMode === 'detail'" @change="onFileTypeChange(row)">
                  <ElOption label="文件" value="file" />
                  <ElOption label="目录" value="directory" />
                </ElSelect>
              </template>
            </ElTableColumn>
            <ElTableColumn label="相对路径" min-width="220">
              <template #default="{ row }">
                <ElInput
                  v-model="row.path"
                  :disabled="dialogMode === 'detail'"
                  placeholder="references/api.md"
                />
              </template>
            </ElTableColumn>
            <ElTableColumn label="内容类型" width="140">
              <template #default="{ row }">
                <ElSelect v-model="row.content_type" :disabled="dialogMode === 'detail' || row.type === 'directory'">
                  <ElOption label="markdown" value="markdown" />
                  <ElOption label="python" value="python" />
                  <ElOption label="shell" value="shell" />
                  <ElOption label="json" value="json" />
                  <ElOption label="text" value="text" />
                  <ElOption label="binary" value="binary" />
                </ElSelect>
              </template>
            </ElTableColumn>
            <ElTableColumn label="说明" min-width="180">
              <template #default="{ row }">
                <ElInput v-model="row.description" :disabled="dialogMode === 'detail'" />
              </template>
            </ElTableColumn>
            <ElTableColumn label="排序" width="100">
              <template #default="{ row }">
                <ElInputNumber v-model="row.sort" :disabled="dialogMode === 'detail'" :min="0" controls-position="right" />
              </template>
            </ElTableColumn>
            <ElTableColumn label="操作" width="88" fixed="right" v-if="dialogMode !== 'detail'">
              <template #default="{ $index }">
                <ElButton text type="danger" icon="Delete" @click="removeFileRow($index)">删除</ElButton>
              </template>
            </ElTableColumn>
            <ElTableColumn type="expand">
              <template #default="{ row }">
                <ElInput
                  v-if="row.type === 'file'"
                  v-model="row.content"
                  type="textarea"
                  :rows="8"
                  :disabled="dialogMode === 'detail'"
                  resize="none"
                  placeholder="请输入文件内容"
                />
                <ElText v-else type="info">目录节点不保存正文内容。</ElText>
              </template>
            </ElTableColumn>
          </ElTable>
        </ElTabPane>

        <ElTabPane label="README.md" name="readme">
          <ElInput
            v-model="formData.readme"
            type="textarea"
            :rows="18"
            :disabled="dialogMode === 'detail'"
            resize="none"
            class="skill-code-input"
          />
        </ElTabPane>
      </ElTabs>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { useAuth } from "@/hooks/core/useAuth";
import { confirmDelete } from "@/hooks/core/useConfirm";
import download from "@/utils/download";
import { cleanEmptyArrayParams } from "@/utils/query";
import type { AuditSearchFormParams } from "@/components/forms/fa-search-bar/auditSearchFormItems";
import SkillManagerAPI, {
  type SkillManagerFileForm,
  type SkillManagerDetail,
  type SkillManagerForm,
  type SkillManagerPageQuery,
  type SkillManagerTable,
} from "@/api/module_skill/manager";

defineOptions({
  name: "SkillManager",
  inheritAttrs: false,
});

type SkillSearchFormParams = {
  name?: string;
  title?: string;
  category?: string;
  status?: string;
} & AuditSearchFormParams;

const loading = ref(false);
const { hasAuth } = useAuth();
const submitLoading = ref(false);
const showSearchBar = ref(true);
const searchBarRef = ref<{ validate: () => Promise<boolean> } | null>(null);
const skillList = ref<SkillManagerTable[]>([]);
const activeTab = ref("base");
const dialogVisible = ref(false);
const dialogMode = ref<"add" | "edit" | "detail">("add");
const formRef = ref<FormInstance>();

const pagination = reactive({
  page_no: 1,
  page_size: 12,
  total: 0,
});

const searchForm = ref<SkillSearchFormParams>({
  name: undefined,
  title: undefined,
  category: undefined,
  status: undefined,
  created_id: undefined,
  updated_id: undefined,
  created_time: [],
  updated_time: [],
});

const skillSearchItems = computed(() => [
  { label: "Skill 标识", key: "name", type: "input", placeholder: "请输入 Skill 标识", clearable: true, span: 6 },
  { label: "显示名称", key: "title", type: "input", placeholder: "请输入显示名称", clearable: true, span: 6 },
  { label: "分类", key: "category", type: "input", placeholder: "请输入分类", clearable: true, span: 6 },
  {
    label: "状态",
    key: "status",
    type: "select",
    props: {
      placeholder: "请选择状态",
      options: [
        { label: "启用", value: "0" },
        { label: "停用", value: "1" },
      ],
      clearable: true,
    },
    span: 6,
  },
]);

const defaultSkillMd = `---
name: my-skill
description: Describe when and how this skill should be used.
---

# My Skill

Write the skill instructions here.
`;

const initialFormData: SkillManagerForm = {
  id: undefined,
  name: "",
  title: "",
  description: "",
  category: undefined,
  tags: [],
  version: "1.0.0",
  author: undefined,
  skill_md: defaultSkillMd,
  readme: "",
  sort: 0,
  status: "0",
  files: [],
};

const formData = ref<SkillManagerForm>({ ...initialFormData, files: [] });

const rules = reactive<FormRules>({
  name: [{ required: true, message: "请输入 Skill 标识", trigger: "blur" }],
  title: [{ required: true, message: "请输入显示名称", trigger: "blur" }],
  description: [{ required: true, message: "请输入简介", trigger: "blur" }],
  skill_md: [{ required: true, message: "请输入 SKILL.md 内容", trigger: "blur" }],
  status: [{ required: true, message: "请选择状态", trigger: "change" }],
});

const dialogTitle = computed(() => {
  if (dialogMode.value === "detail") return "Skill 详情";
  if (dialogMode.value === "edit") return "编辑 Skill";
  return "新增 Skill";
});

const dialogFormMode = computed<"create" | "update" | "detail">(() => {
  if (dialogMode.value === "detail") return "detail";
  return dialogMode.value === "edit" ? "update" : "create";
});

function normalizeQuery(params: Record<string, unknown>): SkillManagerPageQuery {
  return cleanEmptyArrayParams({ ...params }, [
    "created_time",
    "updated_time",
  ]) as unknown as SkillManagerPageQuery;
}

async function fetchList() {
  loading.value = true;
  try {
    const query = normalizeQuery({
      ...searchForm.value,
      page_no: pagination.page_no,
      page_size: pagination.page_size,
    });
    const response = await SkillManagerAPI.getSkillList(query);
    const page = response.data.data;
    skillList.value = page?.items ?? [];
    pagination.total = page?.total ?? 0;
  } finally {
    loading.value = false;
  }
}

async function handleSearch(params: SkillSearchFormParams) {
  await searchBarRef.value?.validate();
  searchForm.value = { ...searchForm.value, ...params };
  pagination.page_no = 1;
  await fetchList();
}

async function onResetSearch() {
  searchForm.value = {
    name: undefined,
    title: undefined,
    category: undefined,
    status: undefined,
    created_id: undefined,
    updated_id: undefined,
    created_time: [],
    updated_time: [],
  };
  pagination.page_no = 1;
  await fetchList();
}

function resetForm() {
  formData.value = {
    ...initialFormData,
    tags: [],
    files: [],
  };
  activeTab.value = "base";
  formRef.value?.clearValidate();
}

async function openDetailDialog(row: SkillManagerTable) {
  if (!row.id) return;
  const response = await SkillManagerAPI.getSkillDetail(row.id);
  formData.value = toSkillForm(response.data.data ?? {});
  dialogMode.value = "detail";
  activeTab.value = "base";
  dialogVisible.value = true;
}

async function openEditDialog(type: "add" | "edit", row?: SkillManagerTable) {
  resetForm();
  dialogMode.value = type;
  if (type === "edit" && row?.id) {
    const response = await SkillManagerAPI.getSkillDetail(row.id);
    formData.value = toSkillForm(response.data.data ?? {});
  }
  dialogVisible.value = true;
}

function closeDialog() {
  dialogVisible.value = false;
  resetForm();
}

function toSkillForm(data: Partial<SkillManagerDetail>): SkillManagerForm {
  return {
    ...initialFormData,
    ...data,
    tags: Array.isArray(data.tags) ? data.tags : [],
    files: Array.isArray(data.files) ? data.files.map(normalizeFileForm) : [],
  };
}

function normalizeFileForm(file: Partial<SkillManagerFileForm>): SkillManagerFileForm {
  return {
    path: file.path || "",
    type: file.type || "file",
    content: file.type === "directory" ? undefined : file.content || "",
    content_type: file.content_type || "markdown",
    size: file.size || 0,
    sort: file.sort || 0,
    description: file.description,
    status: file.status || "0",
  };
}

function addFileRow(type: "file" | "directory") {
  formData.value.files = formData.value.files || [];
  formData.value.files.push({
    path: type === "directory" ? "references" : "references/example.md",
    type,
    content: type === "directory" ? undefined : "",
    content_type: type === "directory" ? "text" : "markdown",
    sort: formData.value.files.length,
    status: "0",
  });
}

function removeFileRow(index: number) {
  formData.value.files?.splice(index, 1);
}

function onFileTypeChange(row: SkillManagerFileForm) {
  if (row.type === "directory") {
    row.content = undefined;
    row.content_type = "text";
  }
}

async function submitSkill() {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    activeTab.value = "base";
    return;
  }
  submitLoading.value = true;
  try {
    const payload = {
      ...formData.value,
      files: (formData.value.files || []).map((item, index) => ({
        ...item,
        sort: item.sort ?? index,
      })),
    };
    if (formData.value.id) {
      await SkillManagerAPI.updateSkill(formData.value.id, payload);
      ElMessage.success("修改成功");
    } else {
      await SkillManagerAPI.createSkill(payload);
      ElMessage.success("创建成功");
    }
    closeDialog();
    await fetchList();
  } finally {
    submitLoading.value = false;
  }
}

async function deleteSkill(row: SkillManagerTable) {
  if (!row.id) return;
  try {
    await confirmDelete(`确定删除「${row.title || row.name}」吗？此操作不可恢复！`);
    await SkillManagerAPI.deleteSkill([row.id]);
    ElMessage.success("删除成功");
    await fetchList();
  } catch {
    // 用户取消
  }
}

function downloadSkill(row: SkillManagerTable) {
  if (!row.id) return;
  download.zip(SkillManagerAPI.getDownloadUrl(row.id), `${row.name || "skill"}.zip`);
}

onMounted(() => {
  fetchList();
});
</script>

<style scoped>
.skill-manager-page {
  min-width: 0;
}

.skill-card-panel {
  min-height: calc(100vh - 180px);
}

.skill-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.skill-toolbar__left,
.skill-toolbar__right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.skill-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.skill-card {
  display: flex;
  min-height: 218px;
  flex-direction: column;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 14px;
  background: var(--el-bg-color);
}

.skill-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.skill-card__title {
  min-width: 0;
}

.skill-card__title h3 {
  margin: 0;
  overflow: hidden;
  color: var(--el-text-color-primary);
  font-size: 16px;
  font-weight: 600;
  line-height: 22px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skill-card__title span,
.skill-card__meta {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.skill-card__desc {
  display: -webkit-box;
  min-height: 44px;
  margin: 12px 0;
  overflow: hidden;
  color: var(--el-text-color-regular);
  font-size: 13px;
  line-height: 22px;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.skill-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}

.skill-card__tags {
  display: flex;
  min-height: 24px;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.skill-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: flex-end;
  margin-top: auto;
}

.skill-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.skill-editor-tabs {
  min-height: 520px;
}

.skill-form {
  padding-top: 8px;
}

.skill-code-input :deep(textarea) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  line-height: 1.55;
}

.file-toolbar {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 10px;
}

.skill-file-table :deep(.el-input-number) {
  width: 100%;
}
</style>
