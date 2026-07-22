export interface CreateVisitRequest {
  chiefComplaint: string;
  caseTag: "synthetic";
  ageGroup: "child" | "youth" | "middle" | "senior";
  gender: "male" | "female" | "other";
  medicalHistorySummary?: string;
  symptoms: Array<{
    symptomName: string;
    bodyPart?: string;
    duration?: string;
    severity?: "mild" | "moderate" | "severe";
    originalText: string;
  }>;
}

export interface CreateVisitResponse {
  visitId: string;
  status: string;
  message: string;
}

export interface VisitListQuery {
  status?: string;
  riskLevel?: "high" | "medium" | "low";
  page?: number;
  pageSize?: number;
}

export interface VisitSummary {
  visitId: string;
  patientId: string;
  chiefComplaint: string;
  riskLevel: string;
  status: string;
  submitTime: string;
  reviewerId?: string;
}

export interface VisitListResponse {
  total: number;
  page: number;
  pageSize: number;
  items: VisitSummary[];
}

export interface SymptomDetail {
  symptomId: string;
  symptomName: string;
  bodyPart?: string;
  duration?: string;
  severity?: string;
  isRedFlag: boolean;
  originalText: string;
}

export interface VisitDetailResponse {
  visitId: string;
  patientId: string;
  status: string;
  chiefComplaint: string;
  riskLevel: string;
  submitTime: string;
  reviewTime?: string;
  reviewerId?: string;
  symptoms: SymptomDetail[];
  triageResult?: TriageResultDetail;
}

export interface TriageResultDetail {
  triageId: string;
  riskLevel: string;
  riskEvidence: Record<string, unknown>;
  ruleVersion: string;
  aiOutput: Record<string, unknown>;
  safetyCheckPassed: boolean;
  reviewStatus: string;
  reviewComment?: string;
}

export interface ResubmitVisitRequest {
  chiefComplaint: string;
  symptoms: Array<{
    symptomName: string;
    bodyPart?: string;
    duration?: string;
    severity?: "mild" | "moderate" | "severe";
    originalText: string;
  }>;
}