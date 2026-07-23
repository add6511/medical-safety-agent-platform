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

1. 创建 MySQL 数据库：
   ```sql
   CREATE DATABASE medical_safety CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. 通过环境变量配置连接信息。Spring Boot 不会自动读取 `.env` 文件，需手动设置：

   **PowerShell (Windows)：**
   ```powershell
   $env:MYSQL_URL="jdbc:mysql://localhost:3306/medical_safety?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai&characterEncoding=UTF-8"
   $env:MYSQL_USERNAME="your_mysql_username"
   $env:MYSQL_PASSWORD="your_mysql_password"
   $env:JWT_SECRET="your_jwt_secret_at_least_32_bytes_long"
   mvn spring-boot:run
   ```

   **Bash (Linux/macOS)：**
   ```bash
   export MYSQL_URL="jdbc:mysql://localhost:3306/medical_safety?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai&characterEncoding=UTF-8"
   export MYSQL_USERNAME="your_mysql_username"
   export MYSQL_PASSWORD="your_mysql_password"
   export JWT_SECRET="your_jwt_secret_at_least_32_bytes_long"
   mvn spring-boot:run
   ```

   > **重要：** `JWT_SECRET` 必须至少 32 字节（256 位），否则应用启动时会报错。不得提交真实密钥。

## 启动

```bash
# 编译
mvn compile

# 生产模式运行（需先设置环境变量）
mvn spring-boot:run

# Demo 模式运行（自动创建合成演示账号）
mvn spring-boot:run -Dspring-boot.run.profiles=demo

# 或打包后运行
mvn package -DskipTests
java -jar target/platform-0.1.0-SNAPSHOT.jar
```

## Demo 演示账号

> **仅供教学演示，不得用于生产环境。** 所有账号均为合成数据，不包含真实个人信息。

使用 `demo` profile 启动时自动创建以下账号（密码均为 `demo123`）：

| 用户名 | 角色 | 说明 |
|--------|------|------|
| demo_patient | PATIENT | 合成患者A |
| demo_medical | MEDICAL_STAFF | 合成医生B |
| demo_followup | FOLLOWUP_STAFF | 合成随访员C |
| demo_admin | ADMIN | 合成管理员D |

默认生产环境不会创建任何演示账号。

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
