import { request } from "@utils";

const API_PATH = "/skill/market";

const SkillMarketAPI = {
  getSourceList(query: SkillMarketSourcePageQuery) {
    return request<ApiResponse<PageResult<SkillMarketSourceTable>>>({
      url: `${API_PATH}/source/list`,
      method: "get",
      params: query,
    });
  },

  getSourceDetail(id: number) {
    return request<ApiResponse<SkillMarketSourceTable>>({
      url: `${API_PATH}/source/detail/${id}`,
      method: "get",
    });
  },

  createSource(body: SkillMarketSourceForm) {
    return request<ApiResponse<SkillMarketSourceTable>>({
      url: `${API_PATH}/source/create`,
      method: "post",
      data: body,
    });
  },

  updateSource(id: number, body: SkillMarketSourceForm) {
    return request<ApiResponse<SkillMarketSourceTable>>({
      url: `${API_PATH}/source/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteSource(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/source/delete`,
      method: "delete",
      data: body,
    });
  },

  syncSource(id: number) {
    return request<ApiResponse<SkillMarketSyncResult>>({
      url: `${API_PATH}/source/${id}/sync`,
      method: "post",
    });
  },

  getItemList(query: SkillMarketItemPageQuery) {
    return request<ApiResponse<PageResult<SkillMarketItemTable>>>({
      url: `${API_PATH}/item/list`,
      method: "get",
      params: query,
    });
  },

  getItemDetail(id: number) {
    return request<ApiResponse<SkillMarketItemTable>>({
      url: `${API_PATH}/item/detail/${id}`,
      method: "get",
    });
  },

  installItem(id: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/item/${id}/install`,
      method: "post",
    });
  },

  installRemoteItem(body: SkillMarketRemoteInstallForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/item/install-remote`,
      method: "post",
      data: body,
    });
  },
};

export default SkillMarketAPI;

export interface SkillMarketSourcePageQuery extends PageQuery {
  name?: string;
  code?: string;
  adapter_type?: string;
  status?: string;
  created_time?: string[];
  updated_time?: string[];
}

export interface SkillMarketSourceTable extends BaseType {
  name?: string;
  code?: string;
  adapter_type?: "github_repo";
  base_url?: string;
  branch?: string;
  config?: Record<string, unknown>;
  last_sync_time?: string;
  last_sync_status?: string;
  last_sync_message?: string;
  sort?: number;
  status?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
}

export interface SkillMarketSourceForm extends BaseFormType {
  name?: string;
  code?: string;
  adapter_type?: "github_repo";
  base_url?: string;
  branch?: string;
  config?: Record<string, unknown>;
  sort?: number;
  status?: string;
  description?: string;
}

export interface SkillMarketItemPageQuery extends PageQuery {
  source_id?: number;
  market_kind?: "skill" | "plugin";
  plugin_name?: string;
  name?: string;
  title?: string;
  category?: string;
  status?: string;
  installed?: boolean;
  refresh?: boolean;
  created_time?: string[];
  updated_time?: string[];
}

export interface SkillMarketItemTable extends BaseType {
  source_id?: number;
  external_id?: string;
  name?: string;
  title?: string;
  description?: string;
  category?: string;
  tags?: string[];
  version?: string;
  author?: string;
  license?: string;
  homepage_url?: string;
  repository_url?: string;
  skill_path?: string;
  skill_md_url?: string;
  readme_url?: string;
  raw_meta?: Record<string, unknown>;
  market_kind?: "skill" | "plugin";
  plugin_name?: string;
  plugin_description?: string;
  skill_paths?: string[];
  source_branch?: string;
  source_commit?: string;
  content_hash?: string;
  file_count?: number;
  package_size?: number;
  installed_skill_id?: number;
  last_sync_time?: string;
  status?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
}

export interface SkillMarketSyncResult {
  source_id: number;
  total: number;
  created: number;
  updated: number;
}

export interface SkillMarketRemoteInstallForm {
  source_id: number;
  external_id: string;
}
