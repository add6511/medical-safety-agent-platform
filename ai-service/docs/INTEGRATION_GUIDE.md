# Spring Boot 后端集成指南

> **安全声明**：本服务仅供教学演示，所有示例均为合成教学数据，不构成真实诊断或治疗建议。

---

## 1. 概述

本文档面向使用 Spring Boot 框架的后端开发人员，说明如何与基层医疗安全型预问诊AI服务进行集成。

### 1.1 架构说明

```
┌─────────────┐     HTTP/JSON     ┌─────────────┐
│   前端应用   │ ──────────────── │  Spring Boot │
└─────────────┘                   │    后端      │
                                  └──────┬──────┘
                                         │ HTTP/JSON
                                         ▼
                                  ┌─────────────┐
                                  │   AI 服务    │
                                  │  (FastAPI)   │
                                  └─────────────┘
```

**重要原则**：
- 后端服务通过 HTTP 调用 AI 服务
- 前端**不得**直接调用 AI 服务
- 所有请求必须经过后端服务转发和控制

### 1.2 集成范围

Spring Boot 后端需要集成以下 AI 服务功能：

1. **知识库管理** - 导入和管理教学文档
2. **知识检索** - 检索相关知识片段
3. **预问诊审核** - 执行安全审核流程

---

## 2. 服务地址与环境变量

### 2.1 AI 服务地址配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `AI_SERVICE_URL` | AI 服务基础地址 | `http://ai-service:8000` |
| `AI_SERVICE_TIMEOUT` | 请求超时时间（毫秒） | `30000` |
| `AI_SERVICE_API_KEY` | API 密钥（当前版本不需要） | 空 |

### 2.2 Spring Boot 配置示例

**application.yml**

```yaml
ai:
  service:
    url: ${AI_SERVICE_URL:http://localhost:8000}
    timeout: ${AI_SERVICE_TIMEOUT:30000}
    api-key: ${AI_SERVICE_API_KEY:}
```

**application.properties**

```properties
ai.service.url=${AI_SERVICE_URL:http://localhost:8000}
ai.service.timeout=${AI_SERVICE_TIMEOUT:30000}
ai.service.api-key=${AI_SERVICE_API_KEY:}
```

### 2.3 配置类示例

```java
@Configuration
@ConfigurationProperties(prefix = "ai.service")
public class AiServiceConfig {
    private String url = "http://localhost:8000";
    private int timeout = 30000;
    private String apiKey = "";

    // getters and setters
}
```

---

## 3. 请求规范

### 3.1 请求头要求

所有请求必须包含以下请求头：

| 请求头 | 值 | 是否必须 | 说明 |
|--------|-----|----------|------|
| Content-Type | `application/json; charset=utf-8` | 是 | 请求体格式 |
| Accept | `application/json` | 否 | 响应格式偏好 |
| X-Request-ID | UUID 字符串 | 否 | 请求追踪标识 |

### 3.2 超时配置

不同接口建议使用不同的超时时间：

| 接口 | 建议超时 | 说明 |
|------|----------|------|
| `POST /api/v1/preconsultation/review` | 30秒 | 审核流程涉及多Agent协作 |
| `POST /api/v1/knowledge/search` | 10秒 | 知识检索相对快速 |
| `POST /api/v1/knowledge/documents` | 15秒 | 文档导入涉及向量化处理 |
| `GET /api/v1/knowledge/documents` | 5秒 | 列表查询 |
| `DELETE /api/v1/knowledge/documents/{id}` | 5秒 | 删除操作 |
| `GET /health` | 3秒 | 健康检查 |

### 3.3 RestClient 配置示例

```java
@Configuration
public class RestClientConfig {

    @Bean
    public RestClient aiServiceRestClient(AiServiceConfig config) {
        return RestClient.builder()
                .baseUrl(config.getUrl())
                .defaultHeader("Content-Type", "application/json; charset=utf-8")
                .defaultHeader("Accept", "application/json")
                .requestFactory(requestFactory(config.getTimeout()))
                .build();
    }

    private ClientHttpRequestFactory requestFactory(int timeout) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofMillis(5000));
        factory.setReadTimeout(Duration.ofMillis(timeout));
        return factory;
    }
}
```

---

## 4. 端到端调用顺序

### 4.1 初始化阶段

**Step 1: 导入知识文档**

在应用启动时或首次部署时，导入教学知识文档到 AI 服务知识库。

```java
@Service
public class AiServiceClient {

    private final RestClient restClient;

    public DocumentImportResponse importDocument(DocumentImportRequest request) {
        return restClient.post()
                .uri("/api/v1/knowledge/documents")
                .body(request)
                .retrieve()
                .body(DocumentImportResponse.class);
    }
}
```

**请求示例**

```java
DocumentImportRequest request = new DocumentImportRequest();
request.setTitle("高血压基层诊疗指南（教学版）");
request.setPublisher("中华医学会（示例）");
request.setSourceUrl("https://example.org/guidelines/hypertension");
request.setDocumentVersion("2024教学版");
request.setContent("高血压定义为在未使用降压药物的情况下...");

DocumentImportResponse response = aiServiceClient.importDocument(request);
// response.getDocumentId() - 文档ID
// response.getChecksum() - 校验值
// response.getChunkCount() - 知识块数量
// response.isDuplicate() - 是否重复导入
```

### 4.2 查询阶段

**Step 2: 知识检索**

在需要检索相关知识时调用此接口。

```java
public SearchResponse searchKnowledge(String query, int topK) {
    SearchRequest request = new SearchRequest();
    request.setQuery(query);
    request.setTopK(topK);

    return restClient.post()
            .uri("/api/v1/knowledge/search")
            .body(request)
            .retrieve()
            .body(SearchResponse.class);
}
```

**使用场景**
- 用户查询相关医疗知识
- 辅助生成问诊问题
- 提供参考文献

### 4.3 审核阶段

**Step 3: 预问诊安全审核**

当患者提交问诊信息后，调用此接口进行安全审核。

```java
public PreconsultationResponse reviewPreconsultation(PreconsultationRequest request) {
    return restClient.post()
            .uri("/api/v1/preconsultation/review")
            .body(request)
            .retrieve()
            .body(PreconsultationResponse.class);
}
```

**请求示例**

```java
PreconsultationRequest request = new PreconsultationRequest();
request.setCaseId("synthetic-case-001");
request.setAge(45);

SymptomInput symptom = new SymptomInput();
symptom.setName("胸部不适");
symptom.setSeverity(7);
symptom.setDuration("30分钟");
request.setSymptoms(List.of(symptom));

request.setRedFlags(List.of("persistent_chest_discomfort"));
request.setFreeText("这是一个合成教学病例。");
request.setModelSuggestedRisk("LOW");

PreconsultationResponse response = aiServiceClient.reviewPreconsultation(request);
```

### 4.4 结果处理阶段

**Step 4: 检查 needs_human_review 并路由**

后端**必须**根据 `needs_human_review` 字段进行路由处理：

```java
@Service
public class PreconsultationService {

    private final AiServiceClient aiServiceClient;

    public PreconsultationResult processCase(PreconsultationRequest request) {
        // 调用 AI 服务进行审核
        PreconsultationResponse response = aiServiceClient.reviewPreconsultation(request);

        // 检查是否需要人工审核
        if (response.isNeedsHumanReview()) {
            // 路由到人工审核队列
            return routeToHumanReview(response);
        } else {
            // 低风险病例，可自动处理
            return processLowRiskCase(response);
        }
    }

    private PreconsultationResult routeToHumanReview(PreconsultationResponse response) {
        // 将病例添加到人工审核队列
        // 记录审核请求
        // 通知审核人员
        return PreconsultationResult.needsHumanReview(response);
    }

    private PreconsultationResult processLowRiskCase(PreconsultationResponse response) {
        // 处理低风险病例
        return PreconsultationResult.autoProcessed(response);
    }
}
```

---

## 5. 错误处理与安全策略

### 5.1 错误类型与处理策略

| 错误场景 | HTTP 状态码 | 处理策略 |
|----------|-------------|----------|
| AI 服务不可用 | 连接失败 | **必须进入人工审核** |
| 请求超时 | 超时异常 | **必须进入人工审核** |
| 服务未就绪 | 503 | 等待并重试（健康检查） |
| 参数校验失败 | 422 | 修正参数后重试 |
| 资源不存在 | 404 | 检查资源ID |

### 5.2 核心安全原则

**原则一：AI 服务不可用/超时时必须进入人工审核**

```java
@Service
public class SafePreconsultationService {

    private final AiServiceClient aiServiceClient;

    public PreconsultationResult safeReview(PreconsultationRequest request) {
        try {
            // 尝试调用 AI 服务
            PreconsultationResponse response = aiServiceClient.reviewPreconsultation(request);
            return PreconsultationResult.fromAiResponse(response);
        } catch (ResourceAccessException e) {
            // 连接失败或超时
            log.error("AI 服务不可用，进入人工审核: {}", e.getMessage());
            return PreconsultationResult.fallbackToHumanReview(request);
        } catch (HttpServerErrorException e) {
            // 服务端错误
            log.error("AI 服务返回错误: {}", e.getStatusCode());
            return PreconsultationResult.fallbackToHumanReview(request);
        }
    }
}
```

**原则二：AI 调用失败不得自动降低风险等级**

```java
// ❌ 错误做法：失败时自动设置为低风险
if (aiServiceFailed) {
    riskLevel = RiskLevel.LOW;  // 危险！
}

// ✅ 正确做法：失败时进入人工审核
if (aiServiceFailed) {
    return PreconsultationResult.needsHumanReview();
}
```

**原则三：人工审核是最高优先级**

无论 AI 服务返回什么结果，只要 `needs_human_review` 为 `true`，必须路由到人工审核。

### 5.3 重试策略

| 接口 | 是否可重试 | 重试策略 |
|------|------------|----------|
| `POST /api/v1/knowledge/documents` | ✅ 可重试 | 幂等操作，相同内容不会重复创建 |
| `POST /api/v1/knowledge/search` | ✅ 可重试 | 只读操作，可指数退避重试 |
| `POST /api/v1/preconsultation/review` | ⚠️ 谨慎重试 | 非幂等，需确认是否真的需要重试 |
| `GET /api/v1/knowledge/documents` | ✅ 可重试 | 只读操作 |
| `DELETE /api/v1/knowledge/documents/{id}` | ✅ 可重试 | 幂等操作 |

**知识检索重试示例（指数退避）**

```java
@Service
public class ResilientSearchService {

    private static final int MAX_RETRIES = 3;
    private static final long BASE_DELAY_MS = 1000;

    public SearchResponse searchWithRetry(String query, int topK) {
        int attempt = 0;
        while (attempt < MAX_RETRIES) {
            try {
                return aiServiceClient.searchKnowledge(query, topK);
            } catch (ResourceAccessException e) {
                attempt++;
                if (attempt >= MAX_RETRIES) {
                    throw e;
                }
                long delay = BASE_DELAY_MS * (long) Math.pow(2, attempt - 1);
                log.warn("知识检索失败，{}ms 后重试 (第{}次): {}", delay, attempt, e.getMessage());
                Thread.sleep(delay);
            }
        }
        throw new RuntimeException("重试次数已耗尽");
    }
}
```

**预问诊审核重试注意事项**

```java
// ⚠️ 预问诊审核不应盲目重试
// 原因：
// 1. 可能产生重复的审核记录
// 2. 患者可能收到多次通知
// 3. 审核结果可能不一致

// 建议做法：
// 1. 记录失败状态
// 2. 通知运维人员
// 3. 进入人工审核队列
```

### 5.4 健康检查与服务就绪

**定期健康检查**

```java
@Component
public class AiServiceHealthIndicator implements HealthIndicator {

    private final RestClient restClient;

    @Override
    public Health health() {
        try {
            HealthResponse response = restClient.get()
                    .uri("/health")
                    .retrieve()
                    .body(HealthResponse.class);

            if ("ok".equals(response.getStatus())) {
                return Health.up()
                        .withDetail("service", response.getService())
                        .withDetail("version", response.getVersion())
                        .withDetail("environment", response.getEnvironment())
                        .build();
            }
            return Health.down().withDetail("status", response.getStatus()).build();
        } catch (Exception e) {
            return Health.down(e).build();
        }
    }
}
```

**503 处理**

```java
// 当收到 503 响应时，表示 AI 服务未就绪
// 可能原因：
// 1. 服务正在启动
// 2. 知识库服务初始化失败
// 3. 依赖服务不可用

// 处理策略：
// 1. 等待服务就绪（通过健康检查确认）
// 2. 临时使用降级策略（进入人工审核）
// 3. 记录错误日志
```

---

## 6. Docker Compose 对接示例

### 6.1 AI 服务配置片段

以下为 AI 服务的 Docker Compose 配置片段，可集成到项目的 `docker-compose.yml` 中：

```yaml
services:
  ai-service:
    image: medical-safety-ai:0.1.0
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - VECTOR_STORE_MODE=memory
      - EMBEDDING_MODE=mock
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
```

### 6.2 Spring Boot 后端配置片段

```yaml
services:
  backend:
    image: medical-safety-backend:latest
    ports:
      - "8080:8080"
    environment:
      - AI_SERVICE_URL=http://ai-service:8000
      - AI_SERVICE_TIMEOUT=30000
      - SPRING_PROFILES_ACTIVE=production
    depends_on:
      ai-service:
        condition: service_healthy
    restart: unless-stopped
```

### 6.3 完整网络配置

```yaml
services:
  ai-service:
    image: medical-safety-ai:0.1.0
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - VECTOR_STORE_MODE=memory
      - EMBEDDING_MODE=mock
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - medical-safety-network

  backend:
    image: medical-safety-backend:latest
    ports:
      - "8080:8080"
    environment:
      - AI_SERVICE_URL=http://ai-service:8000
      - AI_SERVICE_TIMEOUT=30000
    depends_on:
      ai-service:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - medical-safety-network

networks:
  medical-safety-network:
    driver: bridge
```

---

## 7. 安全声明

### 7.1 服务用途

本服务及本文档中的所有示例：
- 仅供教学演示使用
- 所有数据均为合成生成
- 不构成真实医疗诊断
- 不替代医生专业判断

### 7.2 集成责任

集成开发人员应确保：
- 前端不得直接调用 AI 服务
- AI 服务不可用时必须进入人工审核
- 不得自动降低风险等级
- 正确处理 `needs_human_review` 字段

### 7.3 数据安全

- 不得在 AI 服务中存储真实患者数据
- 所有测试数据必须为合成数据
- 遵守相关数据保护法规

---

## 附录

### A. 常见问题

**Q: AI 服务启动失败怎么办？**
A: 检查日志输出，确认知识库服务是否初始化成功。如果初始化失败，服务仍会启动，但知识库相关接口将返回 503。

**Q: 文档导入重复会怎样？**
A: 相同内容的文档重复导入是幂等的，不会创建重复数据，`duplicate` 字段会返回 `true`。

**Q: 如何判断是否需要人工审核？**
A: 检查响应中的 `needs_human_review` 字段，如果为 `true`，必须路由到人工审核队列。

**Q: 请求超时应该设置多少？**
A: 建议预问诊审核接口设置 30 秒，知识检索接口设置 10 秒。

### B. 相关文档

- [API 接口契约](./API_CONTRACT.md) - 详细的接口定义和字段说明

---

*文档版本：v1.0.0*  
*最后更新：2024-01-20*  
*安全声明：本服务仅供教学演示，不构成真实医疗诊断或治疗建议。*