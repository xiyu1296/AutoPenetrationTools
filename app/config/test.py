# test_config.py
import sys

sys.path.append('.')
from app.config.setting import settings

print("✅ 配置加载成功！")
print("=" * 50)
print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
print(f"DEBUG: {settings.DEBUG}")

print(f"DATABASE_TYPE: {settings.DATABASE_TYPE}")
print(f"DATABASE_HOST: {settings.DATABASE_HOST}")
print(f"DATABASE_PORT: {settings.DATABASE_PORT}")
print(f"DATABASE_USER: {settings.DATABASE_USER}")
print(f"DATABASE_PASSWORD: {settings.DATABASE_PASSWORD}")
print(f"DATABASE_NAME: {settings.DATABASE_NAME}")

print("=" * 50)

# 验证配置来源
try:
    if hasattr(settings, '__pydantic_fields_set__'):
        print("从 .env.dev 文件加载的配置:")
        for field in settings.__pydantic_fields_set__:
            print(f"  ✓ {field}")
except:
    pass
