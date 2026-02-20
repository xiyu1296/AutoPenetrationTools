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


### 文件架构

```commandline
│  app.py                           # 主程序
│  pyproject.toml
│  README.md
│  uv.lock
└─ api
    └─ v1
        │  __init__.py            # 模块路由挂载在此处，最后统一挂载到主路由
        │  
        └─Penetration             # 模块名（拓展只需创建相同架构的文件）
                controller.py     # 控制层：定义路由接口
                crud.py           # 数据层：进行数据库操作
                model.py          # 模型层：定义模型类
                schema.py         # 数据结构：数据校验
                service.py        # 业务层：具体业务逻辑
                __init__.py

```

### 注意事项
1. 导入 dify 的 openapi.json 最好只保留 Docker 内部访问的 url
2. 