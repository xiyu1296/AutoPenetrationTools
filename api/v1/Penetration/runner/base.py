import os
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

class BaseRunner:
    def __init__(self, task_id: str):
        self.task_id = task_id
        # 严格遵守 Evidence Store 目录规范
        self.base_dir = Path(f"runs/{task_id}")
        self.log_dir = self.base_dir / "logs"
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保产物和日志目录物理存在"""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def write_log(self, stage_name: str, message: str):
        """记录标准日志至 logs/stageX.log"""
        log_path = self.log_dir / f"{stage_name}.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    def save_artifact(self, filename: str, data: dict):
        """保存固定命名的 JSON 产物"""
        file_path = self.base_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def run_tool(self, cmd: list, stage_name: str, timeout: int = 3600):
        """
        封装工具执行逻辑，支持预算控制（超时）
        """
        self.write_log(stage_name, f"执行命令: {' '.join(cmd)}")
        try:
            # 这里的 timeout 直接对应 Stage0 定义的预算
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            if result.stdout:
                self.write_log(stage_name, f"STDOUT: {result.stdout}")
            if result.stderr:
                self.write_log(stage_name, f"STDERR: {result.stderr}")
            return result.stdout
        except subprocess.TimeoutExpired:
            self.write_log(stage_name, "错误: 工具执行超时（已触发预算控制）")
            return None
        except Exception as e:
            self.write_log(stage_name, f"异常: {str(e)}")
            return None