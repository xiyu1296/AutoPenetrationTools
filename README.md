# 自动化渗透测试系统 API 文档

本文档面向前端与 Dify 平台，提供系统 API 的调用规范。

## 1. 全局说明

### 1.1 基础配置
* **认证方式**: 所有接口均依赖 HTTP Header 验证。需要在请求头中携带 `X-API-Key`。
* **默认密钥**: `test-key`（Dify 平台调用时需配置相同的 API Key）。
* **接口前缀**: 
  * 任务管理模块: `/task`
  * 渗透测试工作流模块: `/penetration`

### 1.2 通用错误响应
请求鉴权失败或参数错误时，系统抛出 401 或 422 等 HTTP 异常：
```json
{
  "detail": "Unauthorized: missing/invalid X-API-Key"
}

```

---

## 2. 任务管理模块 (Task Management)

### 2.1 创建任务

* **接口**: `POST /task/create`
* **说明**: 解析预算配置并初始化一个渗透测试任务物理目录。
* **Header**: `X-API-Key: string`
* **Body (JSON)**:
```json
{
  "target": "string",         // 扫描目标 (必填)
  "base_url": "string",       // 基础URL (可选)
  "budget": {                 // 预算配置 (支持对象/JSON字符串)
    "timeout_seconds": 900,
    "rate_limit_rps": 1.0
  }
}

```



### 2.2 运行任务

* **接口**: `POST /task/run`
* **说明**: 串行启动任务的执行流程（从侦察到交付）。
* **Header**: `X-API-Key: string`
* **Body (JSON)**:
```json
{
  "task_id": "string"         // 任务ID (必填)
}

```



### 2.3 获取任务状态

* **接口**: `GET /task/status`
* **说明**: 获取当前任务的执行状态及进度。
* **Header**: `X-API-Key: string`
* **Query 参数**:
* `task_id` (string): 任务ID (必填)



### 2.4 审批任务

* **接口**: `POST /task/approve`
* **说明**: 针对进入阻断状态的任务进行人工审批（通过或驳回）。
* **Header**: `X-API-Key: string`
* **Body (JSON)**:
```json
{
  "task_id": "string",        // 任务ID (必填)
  "action": "string",         // 审批动作: "approve" 或 "reject" (必填)
  "approver": "string",       // 审批人标识 (必填)
  "remark": "string"          // 审批备注 (可选)
}

```



### 2.5 列出制品 (Artifacts)

* **接口**: `GET /task/artifacts/list`
* **说明**: 获取任务执行过程中产生的所有制品文件列表。
* **Header**: `X-API-Key: string`
* **Query 参数**:
* `task_id` (string): 任务ID (必填)



### 2.6 下载制品

* **接口**: `GET /task/artifacts/download`
* **说明**: 将指定任务的产物以 ZIP 压缩包形式下载。
* **Header**: `X-API-Key: string`
* **Query 参数**:
* `task_id` (string): 任务ID (必填)
* `path` (string): 制品路径 (必填)


* **响应**: `application/zip` 文件流。

---

## 3. 渗透测试工作流模块 (Penetration Workflow)

本模块包含各阶段的独立触发端点。统一响应格式为：`{"ok": true, "data": {...}}`。

### 3.1 触发 Nmap 扫描 (Stage 1)

* **接口**: `POST /penetration/scan/nmap`
* **说明**: 手动触发 Nmap 扫描并生成资产证据。
* **Header**: `X-API-Key: string`
* **Query 参数**:
* `task_id` (string): 任务ID (必填)
* `target` (string): 扫描目标 (必填)



### 3.2 触发 HTTP 指纹识别 (Stage 2)

* **接口**: `POST /penetration/probe/httpx`
* **说明**: 调用 pd-httpx 执行 Web 指纹探测。
* **Header**: `X-API-Key: string`
* **Query 参数**:
* `task_id` (string): 任务ID (必填)



### 3.3 触发爬虫探测 (Stage 3)

* **接口**: `POST /penetration/crawl`
* **说明**: 调用 Katana 执行深度端点发现。
* **Header**: `X-API-Key: string`
* **Query 参数**:
* `task_id` (string): 任务ID (必填)



### 3.4 触发候选点筛选 (Stage 4)

* **接口**: `POST /penetration/candidate/rule`
* **说明**: 根据风险模式锁定高价值攻击路径。
* **Header**: `X-API-Key: string`
* **Query 参数**:
* `task_id` (string): 任务ID (必填)



### 3.5 触发受控验证 (Stage 5)

* **接口**: `POST /penetration/verify/controlled`
* **说明**: 调用 curl 等工具采集物理证据验证候选点真实性。
* **Header**: `X-API-Key: string`
* **Query 参数**:
* `task_id` (string): 任务ID (必填)



### 3.6 触发报告渲染 (Stage 6)

* **接口**: `POST /penetration/report/render`
* **说明**: 汇总所有阶段产物证据，生成 Markdown 报告并打包为归档文件。
* **Header**: `X-API-Key: string`
* **Query 参数**:
* `task_id` (string): 任务ID (必填)




