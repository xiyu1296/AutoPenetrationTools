# api/v1/Penetration/runner/base.py
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class BaseRunner:
    def __init__(self, task_id: str):
        self.task_id = task_id
        # 严格遵守 Evidence Store 目录规范
        self.base_dir = Path(f"runs/{task_id}")
        self.log_dir = self.base_dir / "logs"
        self._initialize_environment()

    def _initialize_environment(self):
        """确保物理目录存在并初始化状态文件"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        # 修复回归问题：创建初始 status.json
        status_path = self.base_dir / "status.json"
        if not status_path.exists():
            self.update_status({
                "state": "init",
                "stage": "Stage0_Create",
                "percent": 0,
                "hint": "Task initialized",
                "blocked": {"is_blocked": False}
            })

    def update_status(self, status_update: Dict[str, Any]):
        """更新任务状态合同并落盘"""
        status_path = self.base_dir / "status.json"
        current_status = {}
        if status_path.exists():
            with open(status_path, "r", encoding="utf-8") as f:
                current_status = json.load(f)

        current_status.update(status_update)
        current_status["task_id"] = self.task_id
        current_status["updated_at"] = datetime.now().isoformat()

        with open(status_path, "w", encoding="utf-8") as f:
            json.dump(current_status, f, ensure_ascii=False, indent=2)

    def write_log(self, stage_name: str, message: str):
        """记录标准日志至 logs/stageX.log"""
        log_path = self.log_dir / f"{stage_name}.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    def save_artifact(self, filename: str, data: dict):
        """保存产物至 Evidence Store"""
        file_path = self.base_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # api/v1/Penetration/runner/base.py

        def run_tool(self, cmd: list, stage_name: str, timeout: int = 3600):
            self.write_log(stage_name, f"执行命令: {' '.join(cmd)}")
            try:
                # 核心修复：显式指定 encoding="utf-8"
                # 增加 errors="ignore" 以防止工具输出中包含乱码导致程序崩溃
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding="utf-8",
                    errors="ignore"
                )
                if result.stdout:
                    self.write_log(stage_name, f"STDOUT: {result.stdout}")
                if result.stderr:
                    self.write_log(stage_name, f"STDERR: {result.stderr}")
                return result.stdout
            except subprocess.TimeoutExpired:
                self.write_log(stage_name, "错误: 工具执行超时")
                return None