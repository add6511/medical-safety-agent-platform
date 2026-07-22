export interface CreateRuleRequest {
  ruleType: "red_flag" | "contraindication";
  name: string;
  condition: string;
  description: string;
}

export interface CreateRuleResponse {
  ruleId: string;
  version: string;
}

export interface UpdateModelConfigRequest {
  modelVersion: string;
  promptVersion: string;
  knowledgeBaseVersion: string;
}

export interface UpdateModelConfigResponse {
  modelVersion: string;
  promptVersion: string;
  knowledgeBaseVersion: string;
  updateTime: string;
}

export interface ChangeUserRoleRequest {
  newRole: "patient" | "doctor" | "follower" | "admin";
}

export interface UserListQuery {
  role?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}