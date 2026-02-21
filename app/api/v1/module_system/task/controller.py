from fastapi import APIRouter
from .service import TaskService
from app.config.setting import settings

task_router = APIRouter(prefix="/task", tags=["主程序入口"])
# 这个是实例化的服务
taskservice = TaskService(settings)


@task_router.post("/run")
def run():
    """
        主程序入口
        包括读取目标参数
        并且运行主程序
    """
    pass
