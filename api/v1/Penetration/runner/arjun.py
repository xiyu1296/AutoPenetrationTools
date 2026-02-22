import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class ArjunRunner(BaseRunner):
    """独立 Arjun 隐藏参数爆破执行器"""

    def run_scan(self, target_url: str) -> List[Dict[str, Any]]:
        if not target_url:
            return []

        self.write_log("tool_arjun", f"启动 Arjun，目标: {target_url}")

        tmp_output = self.base_dir / "arjun_raw.json"

        # arjun -u <url> -oJ <output>
        cmd = ["arjun", "-u", target_url, "-oJ", str(tmp_output)]

        self.run_tool(cmd, "tool_arjun")

        findings = []
        if tmp_output.exists():
            try:
                with open(tmp_output, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Arjun 输出格式通常为 {"url": ["param1", "param2"]}
                    for url, params in data.items():
                        findings.append({
                            "url": url,
                            "parameters": params
                        })
            except Exception as e:
                self.write_log("tool_arjun", f"解析输出失败: {e}")

        self.save_artifact("arjun_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings