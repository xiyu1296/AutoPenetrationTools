from typing import Dict, Any, Optional, List
from .model import TaskModel


class TaskCRUD:
    """任务数据操作"""

    def __init__(self):
        self._tasks: Dict[str, TaskModel] = {}

    def create(self, task_id: str, budget: Dict[str, Any]) -> TaskModel:
        """创建任务"""
        task = TaskModel(task_id, budget)
        self._tasks[task_id] = task
        return task

    def get(self, task_id: str) -> Optional[TaskModel]:
        """获取任务"""
        return self._tasks.get(task_id)

    def update(self, task_id: str, **kwargs) -> Optional[TaskModel]:
        """更新任务"""
        task = self.get(task_id)
        if task:
            task.update(**kwargs)
        return task

    def delete(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def list_all(self) -> List[TaskModel]:
        """列出所有任务"""
        return list(self._tasks.values())


# 全局CRUD实例
task_crud = TaskCRUD()