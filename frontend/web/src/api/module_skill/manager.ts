import { request } from "@utils";

const API_PATH = "/skill/manager";

const SkillManagerAPI = {
  getSkillList(query: SkillManagerPageQuery) {
    return request<ApiResponse<PageResult<SkillManagerTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  getSkillDetail(id: number) {
    return request<ApiResponse<SkillManagerDetail>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  createSkill(body: SkillManagerForm) {
    return request<ApiResponse<SkillManagerDetail>>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateSkill(id: number, body: SkillManagerForm) {
    return request<ApiResponse<SkillManagerDetail>>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteSkill(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  getSkillFiles(id: number) {
    return request<ApiResponse<SkillManagerFile[]>>({
      url: `${API_PATH}/${id}/files`,
      method: "get",
    });
  },

  saveSkillFiles(id: number, body: { files: SkillManagerFileForm[] }) {
    return request<ApiResponse<SkillManagerFile[]>>({
      url: `${API_PATH}/${id}/files/save`,
      method: "post",
      data: body,
    });
  },

  getDownloadUrl(id: number) {
    return `${API_PATH}/${id}/download`;
  },
};

export default SkillManagerAPI;

export interface SkillManagerPageQuery extends PageQuery {
  name?: string;
  title?: string;
  category?: string;
  status?: string;
  created_time?: string[];
  updated_time?: string[];
  created_id?: number;
  updated_id?: number;
}

export interface SkillManagerTable extends BaseType {
  name?: string;
  title?: string;
  description?: string;
  category?: string;
  tags?: string[];
  version?: string;
  author?: string;
  sort?: number;
  status?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
}

export interface SkillManagerFile extends BaseType {
  skill_id?: number;
  path?: string;
  type?: "file" | "directory";
  content?: string;
  content_type?: "markdown" | "python" | "shell" | "json" | "text" | "binary";
  size?: number;
  sort?: number;
  description?: string;
  status?: string;
}

export interface SkillManagerFileForm {
  path: string;
  type: "file" | "directory";
  content?: string;
  content_type: "markdown" | "python" | "shell" | "json" | "text" | "binary";
  size?: number;
  sort?: number;
  description?: string;
  status?: string;
}

export interface SkillManagerDetail extends SkillManagerTable {
  skill_md?: string;
  readme?: string;
  files?: SkillManagerFile[];
}

export interface SkillManagerForm extends BaseFormType {
  name?: string;
  title?: string;
  description?: string;
  category?: string;
  tags?: string[];
  version?: string;
  author?: string;
  skill_md?: string;
  readme?: string;
  sort?: number;
  status?: string;
  files?: SkillManagerFileForm[];
}
