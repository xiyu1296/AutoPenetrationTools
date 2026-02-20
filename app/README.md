# APP 应用程序文档
### AI喷的，大致看看了解下得了，不一定要完全一致的，出问题找cmr就行

## 项目架构说明

本项目采用 **FastAPI 分层架构** 设计，遵循清晰的职责分离原则：

```
app/
├── api/                 # API 接口层
│   └── v1/             # API 版本管理
│       └── module_system/  # 业务模块
│           ├── user/       # 用户模块
│           │   ├── controller.py  # 控制器层
│           │   ├── service.py     # 服务层
│           │   ├── crud.py        # 数据访问层
│           │   ├── model.py       # 数据模型
│           │   ├── schema.py      # 数据校验模式
│           │   └── param.py       # 参数校验
│           └── auth/       # 认证模块
├── common/              # 公共组件
│   ├── response.py     # 统一响应格式
│   ├── constant.py     # 常量定义
│   └── exception.py    # 自定义异常
├── config/             # 配置管理
│   └── setting.py      # 应用配置
├── core/               # 核心组件
│   ├── base_crud.py    # CRUD 基础类
│   ├── base_model.py   # 模型基类
│   └── base_schema.py  # Schema 基类
├── utils/              # 工具函数
│   └── hash_bcrpy_util.py  # 密码加密工具
└── main.py            # 应用入口
```

## 核心组件说明

### 1. 分层架构详解

#### Controller 层 (控制器层)
- **位置**: `api/v1/module_system/*/controller.py`
- **职责**: 处理 HTTP 请求，参数验证，调用 Service 层
- **示例**:
```python
@router.post("/register")
async def register(username: str, password: str, mobile: str):
    try:
        # 参数验证
        User(username=username, password=password, mobile=mobile)
        
        # 调用服务层
        await UserService.register(
            username=username,
            password=password,
            mobile=mobile,
            config=settings
        )
        
        return SuccessResponse(msg="注册成功")
    except Exception as e:
        return ErrorResponse(msg=str(e))
```

#### Service 层 (服务层)
- **位置**: `api/v1/module_system/*/service.py`
- **职责**: 业务逻辑处理，事务管理
- **特点**: 无状态，可复用的业务方法

#### CRUD 层 (数据访问层)
- **位置**: `api/v1/module_system/*/crud.py`
- **职责**: 数据库操作封装
- **继承**: `BaseCRUD` 提供基础数据库操作

#### Model 层 (数据模型层)
- **位置**: `api/v1/module_system/*/model.py`
- **职责**: 数据库表结构定义
- **继承**: `ModelMixin` 提供基础字段

### 2. 公共工具组件

#### 统一响应格式 (`common/response.py`)
提供标准化的 API 响应格式：

```python
# 成功响应
SuccessResponse(msg="操作成功", code=200)

# 错误响应  
ErrorResponse(msg="错误信息", code=500)
```

响应结构：
```json
{
    "msg": "响应消息",
    "code": 200,
    "success": true
}
```

#### 配置管理 (`config/setting.py`)
基于 Pydantic Settings 的配置管理：
- 环境变量自动加载
- 数据库连接配置
- 应用基础配置

#### 核心基类
- `BaseCRUD`: 数据库操作基类
- `MappedBase`: SQLAlchemy 模型基类
- `BaseSchema`: Pydantic Schema 基类

## 工具使用说明

### 1. 密码加密工具 (`utils/hash_bcrpy_util.py`)

```python
from app.utils.hash_bcrpy_util import PwdUtil

# 密码加密
hashed_password = PwdUtil.set_password_hash("your_password")

# 密码验证
is_valid = PwdUtil.verify_password("plain_password", hashed_password)
```

### 2. 数据库操作工具

```python
# CRUD 基础操作
class UserCRUD(BaseCRUD):
    async def create_user(self, user_data: dict):
        async with self.get_db() as db:
            new_user = User(**user_data)
            db.add(new_user)
            await db.commit()
            return new_user
```

### 3. 异常处理

```python
from app.common.exception import CustomException

# 抛出自定义异常
raise CustomException(msg="自定义错误信息")
```

## 新增模块指南

### 1. 创建模块目录结构

在 `app/api/v1/module_system/` 下创建新模块：

```
new_module/
├── __init__.py
├── controller.py
├── service.py
├── crud.py
├── model.py
├── schema.py
└── param.py
```

### 2. 编写 Model 层

```python
# model.py
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.base_model import ModelMixin

class NewModule(ModelMixin):
    __tablename__ = "new_module_table"
    __table_args__ = {"comment": "新模块表"}

    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="名称")
    description: Mapped[str] = mapped_column(String(255), nullable=True, comment="描述")
```

### 3. 编写 CRUD 层

```python
# crud.py
from app.core.base_crud import BaseCRUD
from app.config.setting import Settings

class NewModuleCRUD(BaseCRUD):
    def __init__(self, config: Settings):
        super().__init__(config)
    
    async def get_by_id(self, module_id: int):
        async with self.get_db() as db:
            return await db.get(NewModule, module_id)
```

### 4. 编写 Service 层

```python
# service.py
from app.config.setting import Settings

class NewModuleService:
    @classmethod
    async def create_module(cls, name: str, description: str, config: Settings):
        try:
            module_data = {
                "name": name,
                "description": description
            }
            
            crud = NewModuleCRUD(config)
            result = await crud.create_module(module_data)
            return result
            
        except Exception as e:
            raise CustomException(msg=f"创建模块失败: {str(e)}")
```

### 5. 编写 Controller 层

```python
# controller.py
from fastapi import APIRouter
from app.config.setting import settings
from app.common.response import SuccessResponse, ErrorResponse

router = APIRouter(prefix="/new-module", tags=["新模块"])

@router.post("/create")
async def create_module(name: str, description: str = None):
    try:
        result = await NewModuleService.create_module(
            name=name,
            description=description,
            config=settings
        )
        return SuccessResponse(msg="创建成功")
    except Exception as e:
        return ErrorResponse(msg=str(e))
```

### 6. 注册路由

在主应用中注册新模块路由：

```python
# main.py 或路由注册文件
from app.api.v1.module_system.new_module.controller import router as new_module_router

app.include_router(new_module_router, prefix="/api/v1")
```

### 7. 数据库迁移

如果涉及数据库表结构变更：

```bash
# 生成迁移文件
alembic revision --autogenerate -m "add new_module table"

# 执行迁移
alembic upgrade head
```

## 开发规范

### 1. 命名规范
- 类名: PascalCase (如 `UserService`)
- 函数名: snake_case (如 `create_user`)
- 常量: UPPER_SNAKE_CASE (如 `API_HOST`)

### 2. 异常处理
- 控制器层捕获所有异常并返回统一格式
- 服务层抛出具体业务异常
- 使用自定义异常类型

### 3. 日志记录
```python
import logging
logger = logging.getLogger(__name__)

logger.info("操作成功")
logger.error("操作失败", exc_info=True)
```

### 4. 文档注释
每个公共方法都需要添加 docstring：
```python
def create_user(self, user_data: dict) -> User:
    """
    创建新用户
    
    Args:
        user_data: 用户数据字典
        
    Returns:
        User: 创建的用户对象
        
    Raises:
        CustomException: 创建失败时抛出
    """
    pass
```

## 环境配置

### 开发环境
```bash
# 安装依赖
uv sync

# 启动开发服务器
python app.py
```

### 生产环境
```bash
# 使用 uvicorn 启动
uvicorn app.main:app --host 0.0.0.0 --port 8020 --workers 4
```

## API 文档

启动服务后访问：
- Swagger UI: `http://localhost:8020/docs`
- ReDoc: `http://localhost:8020/redoc`

## 常见问题

### 1. 数据库连接问题
检查 `config/.env` 文件中的数据库配置是否正确

### 2. 依赖包缺失
```bash
uv sync --frozen
```

### 3. 迁移文件冲突
```bash
# 查看迁移历史
alembic history

# 回滚到指定版本
alembic downgrade <revision_id>
```

---
**注意**: 本文档会随着项目发展持续更新，请关注最新版本。