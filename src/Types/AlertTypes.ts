export interface SafetyAlertQuery {
  alertType?: "unauthorized_diagnosis" | "prompt_attack" | "privacy_leak";
  severity?: "critical" | "warning" | "info";
  isResolved?: boolean;
  page?: number;
  pageSize?: number;
}

export interface SafetyAlertListResponse {
  total: number;
  items: Array<{
    alertId: string;
    alertType: string;
    severity: string;
    sourceType: string;
    sourceId: string;
    detail: Record<string, unknown>;
    createTime: string;
    isResolved: boolean;
  }>;
}