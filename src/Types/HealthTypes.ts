export interface HealthCheckResponse {
  status: "healthy" | "degraded" | "unhealthy";
  components: {
    database: "up" | "down";
    aiService: "up" | "down" | "unknown";
    guidelineService: "up" | "down" | "unknown";
  };
  timestamp: string;
}