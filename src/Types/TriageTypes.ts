export interface ReviewTriageRequest {
  action: "confirm" | "return" | "flag";
  reviewComment?: string;
}

export interface ReviewTriageResponse {
  triageId: string;
  reviewStatus: "confirmed" | "returned" | "flagged";
  message: string;
}

export interface TriageListQuery {
  page?: number;
  pageSize?: number;
}