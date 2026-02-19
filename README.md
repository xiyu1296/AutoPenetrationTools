### 环境配置
```bash
    # 安装uv
    pip install uv 
    
    # 配置环境
    uv sync
    
    # 添加新的包
    uv add <package>
```

### 运行
```bash
    python app.py
```
##### 调试页面：localhost:8010/docs
##### openai：localhost:8010/openapi.json


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