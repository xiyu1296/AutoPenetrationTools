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