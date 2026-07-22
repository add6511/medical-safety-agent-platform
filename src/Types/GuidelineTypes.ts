export interface GuidelineSearchQuery {
  keyword?: string;
  category?: string;
  page?: number;
  pageSize?: number;
}

export interface GuidelineSearchResponse {
  total: number;
  items: Array<{
    guidelineId: string;
    title: string;
    sourceOrg: string;
    publishDate: string;
    category: string;
    version: string;
  }>;
}

export interface CreateGuidelineRequest {
  title: string;
  sourceOrg: string;
  publishDate: string;
  category: string;
  content: string;
}

export interface UpdateGuidelineRequest {
  title?: string;
  sourceOrg?: string;
  publishDate?: string;
  category?: string;
  content?: string;
}