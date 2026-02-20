# AutoAttack Tools Backend

这是一个基于 FastAPI 构建的自动化渗透测试工具后端服务。该项目提供了一套 RESTful API，用于管理渗透测试任务的生命周期，包括任务创建、执行、状态查询、人工审批以及报告/制品下载。

目前项目处于演示/开发阶段，核心业务逻辑（如扫描、验证）主要通过 Mock（模拟）方式实现。

## 项目结构

```text
Tools/
├── app.py                      # 程序入口，启动 FastAPI 服务
├── api/
│   └── v1/
│       ├── __init__.py         # v1 路由聚合
│       └── Penetration/        # 渗透测试核心模块
│           ├── controller.py   # API 控制器 (路由定义)
│           ├── service.py      # 业务逻辑层 (任务状态流转、Mock逻辑)
│           ├── crud.py         # 数据访问层 (内存存储)
│           ├── model.py        # 数据模型 (TaskModel)
│           └── schema.py       # Pydantic 数据校验模型 (Request/Response)
├── pyproject.toml              # 项目配置文件
└── README.md                   # 项目说明文档
```

## 快速开始

### 1. 环境准备

确保已安装 Python 3.8+。

### 2. 安装依赖

项目使用 `fastapi`, `uvicorn` 等库。

```bash
pip install fastapi uvicorn
# 如果有其他依赖请一并安装
```

### 3. 启动服务

在项目根目录下运行：

```bash
python app.py
```

服务默认运行在 `http://0.0.0.0:8020`。

## 核心功能与执行流程

该系统模拟了一个需要"人工介入"的自动化渗透测试流程。

### 1. 任务生命周期

1.  **创建任务 (Create)**: 用户提交目标 (Target) 和预算 (Budget)，系统生成唯一的 `task_id`。
2.  **运行任务 (Run)**: 用户触发任务执行，任务状态变为 `running`。
3.  **状态轮询 (Poll)**: 客户端定期查询任务状态。
    *   系统会模拟扫描进度。
    *   当进度达到一定阶段时，系统会自动进入 **阻塞状态 (Blocked)**，提示需要人工审批 (`human_gate`)。
4.  **人工审批 (Approve)**: 管理员调用审批接口，选择 `approve` (通过) 或 `reject` (拒绝)。
    *   **Approve**: 任务继续执行后续阶段 (如验证)，最终完成。
    *   **Reject**: 任务直接结束，仅生成报告。
5.  **结果获取 (Artifacts)**: 任务结束后，用户可以查看和下载生成的制品 (如报告、日志)。

### 2. API 接口说明

所有接口位于 `/v1/penetration` 下。
**注意**: 大部分接口需要 Header `X-API-Key: test-key` 进行鉴权。

| 方法 | 路径 | 描述 | 关键参数 |
| :--- | :--- | :--- | :--- |
| POST | `/task/create` | 创建新任务 | `target`, `budget` |
| POST | `/task/run` | 开始执行任务 | `task_id` |
| GET | `/task/status` | 查询任务状态 | `task_id` |
| POST | `/task/approve` | 审批任务 | `task_id`, `action` (approve/reject) |
| GET | `/artifacts/list` | 获取制品列表 | `task_id` |
| GET | `/artifacts/download` | 下载制品文件 | `task_id`, `path` |

### 3. 示例调用流程

#### 1. 创建任务
```http
POST /v1/penetration/task/create
X-API-Key: test-key
Content-Type: application/json

{
  "target": "example.com",
  "budget": {
    "timeout_seconds": 3600,
    "rate_limit_rps": 5
  }
}
```
*响应*: 获得 `task_id` (例如 `t_abcd1234`)

#### 2. 运行任务
```http
POST /v1/penetration/task/run
X-API-Key: test-key
Content-Type: application/json

{
  "task_id": "t_abcd1234"
}
```

#### 3. 查询状态 (直到被阻塞)
```http
GET /v1/penetration/task/status?task_id=t_abcd1234
X-API-Key: test-key
```
*响应示例*:
```json
{
  "state": "blocked",
  "blocked": {
    "is_blocked": true,
    "reason": "Needs approval to proceed"
  }
}
```

#### 4. 审批通过
```http
POST /v1/penetration/task/approve
X-API-Key: test-key
Content-Type: application/json

{
  "task_id": "t_abcd1234",
  "action": "approve",
  "approver": "admin"
}
```

#### 5. 下载报告
```http
GET /v1/penetration/artifacts/download?task_id=t_abcd1234&path=runs/t_abcd1234/download.zip
X-API-Key: test-key
```

## 开发说明

*   **数据存储**: 目前使用内存字典存储 (`crud.py`)，重启服务后数据会丢失。
*   **Mock 逻辑**: `service.py` 中的 `get_status` 方法包含模拟进度的逻辑，`download` 接口返回的是动态生成的 ZIP 文件。
