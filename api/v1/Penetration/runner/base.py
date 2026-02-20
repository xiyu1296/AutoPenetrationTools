import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class BaseRunner:
    """
    S3 Tool-Runner 基类：负责目录管理、日志追踪、状态同步及预算控制
    """

    def __init__(self, task_id: str):
        self.task_id = task_id
        # 严格遵守 Evidence Store 目录规范
        self.base_dir = Path(f"runs/{task_id}")
        self.log_dir = self.base_dir / "logs"
        self._initialize_environment()

    def _initialize_environment(self):
        """确保物理目录存在并初始化状态文件"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        status_path = self.base_dir / "status.json"
        if not status_path.exists():
            self.update_status({
                "state": "init",
                "stage": "Stage0_Create",
                "percent": 0,
                "hint": "任务初始化完成",
                "blocked": {"is_blocked": False}
            })

    def update_status(self, status_update: Dict[str, Any]):
        """更新物理 status.json 证据文件，确保状态合同一致"""
        status_path = self.base_dir / "status.json"
        current_status = {}
        if status_path.exists():
            try:
                with open(status_path, "r", encoding="utf-8") as f:
                    current_status = json.load(f)
            except Exception:
                current_status = {}

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

    def save_artifact(self, filename: str, data: Dict[str, Any]):
        """将生成的证据存入 Evidence Store"""
        file_path = self.base_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.write_log("system", f"产物已落盘: {filename}")

    def _get_budget_timeout(self) -> int:
        """从状态文件中读取预算的超时时间，默认 900 秒"""
        status_path = self.base_dir / "status.json"
        if status_path.exists():
            try:
                with open(status_path, "r", encoding="utf-8") as f:
                    return json.load(f).get("budget", {}).get("timeout_seconds", 900)
            except Exception:
                pass
        return 900

    def run_tool(self, cmd: list, stage_name: str, timeout: int = None) -> Optional[str]:
        if timeout is None:
            timeout = self._get_budget_timeout()

        self.write_log(stage_name, f"执行命令: {' '.join(cmd)}, 超时限制: {timeout}秒")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore",
                stdin=subprocess.DEVNULL
            )
            if result.stdout:
                self.write_log(stage_name, f"STDOUT 长度: {len(result.stdout)}")
            return result.stdout

        except subprocess.TimeoutExpired as e:
            self.write_log(stage_name, f"错误: 执行超时（> {timeout}秒），保留截断数据")
            self.update_status({"hint": f"警告: {stage_name} 触发超时限制，输出部分结果"})
            return e.stdout.decode(errors="ignore") if e.stdout else None
        except Exception as e:
            self.write_log(stage_name, f"异常: {str(e)}")
            return None