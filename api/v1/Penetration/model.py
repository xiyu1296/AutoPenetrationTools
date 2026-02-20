from typing import Dict, Any, Optional
from datetime import datetime, timezone


class TaskModel:
    """任务数据模型"""

    def __init__(self, task_id: str, budget: Dict[str, Any]):
        self.task_id = task_id
        self.state = "created"
        self.stage = "stage0_create"
        self.percent = 0
        self.hint = "Created"
        self.blocked = {"is_blocked": False}
        self.updated_at = self._now_iso()
        self.poll_count = 0
        self.budget = budget
        self.approved = None

    @staticmethod
    def _now_iso():
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "state": self.state,
            "stage": self.stage,
            "percent": self.percent,
            "hint": self.hint,
            "blocked": self.blocked,
            "updated_at": self.updated_at,
            "poll_count": self.poll_count,
            "budget": self.budget,
            "approved": self.approved,
        }

    def update(self, **kwargs):
        """更新模型属性"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = self._now_iso()