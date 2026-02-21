### 环境配置
```bash
    # 安装uv
    pip install uv 
    
    # 配置环境
    uv sync
    
    # 添加新的包
    uv add <package>
```

### 运行方式

#### 本地运行
```bash
python app.py
```

#### Docker 部署（推荐）
```bash
# Linux/Mac
./deploy.sh

# Windows
deploy.bat

# 或手动部署
docker-compose build
docker-compose up -d
# 关闭服务
docker-compose down
```

##### 访问地址
- 应用主页：http://localhost:8020
- API 文档：http://localhost:8020/docs
- OpenAPI 规范：http://localhost:8020/openapi.json


### 项目架构说明

本项目采用双应用架构设计：

```
项目根目录/
├── api/              # Dify 工具 API 服务
│   └── v1/          # API 版本管理
│       ├── Penetration/     # 渗透测试工具模块
│       │   ├── controller.py   # 工具接口控制器
│       │   ├── crud.py        # 数据库操作
│       │   ├── model.py       # 数据模型
│       │   ├── schema.py      # 数据校验
│       │   └── service.py     # 业务逻辑
│       └── tasks/            # 任务管理模块
│
├── app/              # 主应用程序
│   ├── api/          # 主应用 API 接口
│   ├── common/       # 公共组件
│   ├── config/       # 配置管理
│   ├── core/         # 核心组件
│   ├── utils/        # 工具函数
│   └── main.py       # 主程序入口
│
├── data/             # 数据存储目录
├── config/           # 配置文件目录
├── Dockerfile        # Docker 构建文件
└── docker-compose.yaml  # Docker 编排配置
```

#### 架构分工

**1. API 服务层 (`api/`)**
- 专门为 Dify 平台提供工具接口
- 实现各种功能模块的 RESTful API
- 支持外部系统调用和集成
- 当前包含渗透测试、任务管理等模块

**2. 主应用层 (`app/`)**
- 最终的业务应用系统
- 整合 Dify 工作流和其他业务逻辑
- 提供完整的用户界面和业务功能
- 包含用户管理、权限控制、业务流程等

#### 模块扩展说明

在 `api/v1/` 下创建新模块时，遵循统一架构：

```
新模块名/
├── __init__.py      # 模块初始化
├── controller.py    # 路由接口定义
├── service.py       # 业务逻辑实现
├── crud.py          # 数据库操作封装
├── model.py         # 数据模型定义
└── schema.py        # 数据结构校验
```

### 部署架构

#### 开发环境
```bash
# 启动主应用
python app.py

# 启动 API 服务（如需要独立运行）
uvicorn api.main:app --host 0.0.0.0 --port 8010
```

#### 生产环境
使用 Docker Compose 一键部署：
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 集成说明

**与 Dify 平台集成：**
1. 将 `api/` 服务部署为独立的工具服务
2. 在 Dify 中导入 `http://api-service:8010/openapi.json`
3. 主应用 `app/` 通过调用 Dify 工作流完成复杂业务逻辑

### 注意事项
1. 导入 Dify 的 openapi.json 建议使用内部服务地址
2. 生产环境建议使用 HTTPS 和认证机制
3. 数据库存储路径需要持久化挂载
4. 日志文件建议统一收集和管理 


# API 接口文档

## 全局说明

* **认证方式**：所有接口均需在 HTTP Header 中提供 `X-API-Key` 进行鉴权。
* **认证失败**：缺失或无效的 API Key 将返回 `401 Unauthorized`。

---

## 模块一：任务管理 (Task Management)

**路由前缀**: `/task`

### 1. 创建任务

* **路径**: `/create`
* **方法**: `POST`
* **请求体**: `TaskCreateRequest` (包含 `target`, `base_url`, `budget`)
* **功能**: 解析预算配置，初始化并创建新的渗透测试任务。

### 2. 运行任务

* **路径**: `/run`
* **方法**: `POST`
* **请求体**: `TaskRunRequest` (包含 `task_id`)
* **功能**: 根据任务 ID 启动全自动化测试流程。

### 3. 获取任务状态

* **路径**: `/status`
* **方法**: `GET`
* **查询参数**:
* `task_id` (string)


* **功能**: 查询指定任务的当前执行状态。

### 4. 审批任务

* **路径**: `/approve`
* **方法**: `POST`
* **请求体**: `TaskApproveRequest` (包含 `task_id`, `action`, `approver`, `remark`)
* **功能**: 对处于挂起状态的任务执行人工审批（批准或拒绝）。

### 5. 列出制品

* **路径**: `/artifacts/list`
* **方法**: `GET`
* **查询参数**:
* `task_id` (string)


* **功能**: 获取指定任务生成的所有结果文件（制品）列表。

### 6. 下载制品

* **路径**: `/artifacts/download`
* **方法**: `GET`
* **查询参数**:
* `task_id` (string)
* `path` (string)


* **响应**: `application/zip`
* **功能**: 验证任务后，将指定路径的制品打包为 ZIP 格式供下载。

---

## 模块二：渗透测试工作流 (Penetration Workflow)

**路由前缀**: `/penetration`

### 阶段执行接口

*此类接口主要用于按步骤逐步执行流水线操作。*

| 路径 | 方法 | 查询参数 | 功能 |
| --- | --- | --- | --- |
| `/scan/nmap` | `POST` | `task_id`, `target` | 手动触发 Nmap 扫描并生成资产证据。 |
| `/probe/httpx` | `POST` | `task_id` | 执行 Httpx 指纹识别。 |
| `/crawl` | `POST` | `task_id` | 运行爬虫发现端点。 |
| `/candidate/rule` | `POST` | `task_id` | 执行规则筛选，生成漏洞候选点。 |
| `/verify/controlled` | `POST` | `task_id` | 执行受控物理验证。 |
| `/report/render` | `POST` | `task_id` | 渲染最终报告并打包制品。 |

### 独立工具调用接口 (Standalone Tools)

*此类接口接收标准 JSON 请求体，用于独立触发专项测试工具。*

#### 1. Nuclei 漏洞扫描

* **路径**: `/tool/nuclei`
* **方法**: `POST`
* **请求体**: `ToolNucleiRequest` (包含 `task_id`, `targets`, `templates`)
* **响应**: `ToolNucleiResponse`
* **功能**: 接收 URL 列表，调用 Nuclei 执行指定模板的漏洞扫描。

#### 2. SQLMap 注入探测

* **路径**: `/tool/sqlmap`
* **方法**: `POST`
* **请求体**: `ToolSqlmapRequest` (包含 `task_id`, `target_url`, `risk_level`)
* **响应**: `ToolSqlmapResponse` (包含 `SqlmapFinding`)
* **功能**: 接收带有参数的 URL，调用 SQLMap 验证 SQL 注入漏洞。

#### 3. FFUF 目录扫描

* **路径**: `/tool/dirscan`
* **方法**: `POST`
* **请求体**: `ToolDirScanRequest` (包含 `task_id`, `target_url`, `extensions`, `wordlist_type`)
* **响应**: `ToolDirScanResponse`
* **功能**: 集成 SecLists 字典，调用 FFUF 发现隐藏目录或备份文件。

#### 4. Hydra 弱口令爆破

* **路径**: `/tool/hydra`
* **方法**: `POST`
* **请求体**: `ToolHydraRequest` (包含 `task_id`, `target_ip`, `service`, `port`)
* **响应**: `ToolHydraResponse` (包含 `HydraFinding`)
* **功能**: 针对 SSH、FTP、MySQL、Redis 等协议进行密码暴力破解。