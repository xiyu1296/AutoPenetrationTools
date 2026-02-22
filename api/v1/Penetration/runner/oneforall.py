import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class OneForAllRunner(BaseRunner):
    """独立 OneForAll 执行器"""

    def run_scan(self, target_domain: str) -> List[Dict[str, Any]]:
        if not target_domain:
            return []

        self.write_log("tool_oneforall", f"启动 OneForAll，目标: {target_domain}")

        script_path = os.path.abspath(os.path.join(os.getcwd(), "oneforall", "oneforall.py"))
        if not os.path.exists(script_path):
            self.write_log("tool_oneforall", f"未找到脚本: {script_path}")
            return []

        tmp_output = self.base_dir / "oneforall_raw.json"

        # 构造命令: python oneforall.py --target example.com --fmt json --path output.json run
        cmd = [
            "python", script_path,
            "--target", target_domain,
            "--fmt", "json",
            "--path", str(tmp_output),
            "run"
        ]

        self.run_tool(cmd, "tool_oneforall")

        findings = []
        if tmp_output.exists():
            try:
                with open(tmp_output, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        findings.append({
                            "subdomain": item.get("subdomain"),
                            "ip": item.get("ip"),
                            "source": item.get("source")
                        })
            except Exception as e:
                self.write_log("tool_oneforall", f"解析输出失败: {e}")

        self.save_artifact("oneforall_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings