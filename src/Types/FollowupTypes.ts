export interface CreateFollowupPlanRequest {
  patientId: string;
  visitId: string;
  frequency: "weekly" | "biweekly" | "monthly" | "quarterly";
  startDate: string;
  endDate: string;
}

export interface CreateFollowupPlanResponse {
  planId: string;
  tasks: Array<{
    taskId: string;
    plannedDate: string;
    status: string;
  }>;
}

export interface TerminatePlanRequest {
  terminateReason: string;
}

export interface TerminatePlanResponse {
  planId: string;
  status: "terminated";
  cancelledTaskCount: number;
}

export interface CompleteTaskRequest {
  resultNote: string;
}

export interface CompleteTaskResponse {
  taskId: string;
  status: "completed";
  completionDate: string;
}

export interface FollowupPlanListQuery {
  status?: string;
  page?: number;
  pageSize?: number;
}