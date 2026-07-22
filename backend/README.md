# 基层医疗安全型预问诊与随访平台 - 后端服务

## 技术栈

- Java 21
- Spring Boot 3.3.x
- Spring Security + JWT
- Spring Data JPA
- MySQL + Flyway
- springdoc OpenAPI

## 环境要求

- JDK 21+
- Maven 3.9+
- MySQL 8.0+

## 安装与配置

1. 复制环境变量文件并填写实际值：
   ```bash
   cp .env.example .env
   ```

2. 创建 MySQL 数据库：
   ```sql
   CREATE DATABASE medical_safety CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. 设置环境变量（或直接修改 `.env` 文件）：
   - `MYSQL_URL` - 数据库连接地址
   - `MYSQL_USERNAME` - 数据库用户名
   - `MYSQL_PASSWORD` - 数据库密码
   - `JWT_SECRET` - JWT 签名密钥（至少 256 位）

## 启动

```bash
# 编译
mvn compile

# 运行
mvn spring-boot:run

# 或打包后运行
mvn package -DskipTests
java -jar target/platform-0.1.0-SNAPSHOT.jar
```

## 测试

```bash
mvn test
```

测试使用 H2 内存数据库，不依赖外部 MySQL。

## API 文档

启动后访问：
- Swagger UI: http://localhost:8080/swagger-ui.html
- OpenAPI JSON: http://localhost:8080/api-docs

## 健康检查

```
GET /actuator/health
```

## 项目说明

本项目为教学演示用途，仅使用合成病例数据，不保存真实患者信息，不提供真实诊断和治疗方案。