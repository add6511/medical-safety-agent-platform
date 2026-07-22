export interface AuditLogQuery {
  operatorId?: string;
  action?: string;
  targetType?: string;
  startTime?: string;
  endTime?: string;
  page?: number;
  pageSize?: number;
}

export interface AuditLogListResponse {
  total: number;
  items: Array<{
    logId: string;
    operatorId: string;
    action: string;
    targetType: string;
    targetId: string;
    detail: Record<string, unknown>;
    createTime: string;
  }>;
}