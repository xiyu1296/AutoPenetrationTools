import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class AfrogRunner(BaseRunner):
    """独立 afrog 模板扫描执行器"""

    def run_scan(self, target_url: str) -> List[Dict[str, Any]]:
        if not target_url:
            return []

        self.write_log("tool_afrog", f"启动 afrog 扫描，目标: {target_url}")

        binary_path = os.path.abspath(os.path.join(os.getcwd(), "afrog.exe"))
        binary = binary_path if os.path.exists(binary_path) else "afrog"

        tmp_output = self.base_dir / "afrog_raw.json"

        # afrog.exe -t <url> -j <output>
        cmd = [
            binary,
            "-t", target_url,
            "-j", str(tmp_output)
        ]

        self.run_tool(cmd, "tool_afrog")

        findings = []
        if tmp_output.exists():
            try:
                with open(tmp_output, "r", encoding="utf-8") as f:
                    # afrog 输出通常为 JSON 数组
                    data = json.load(f)
                    for item in data:
                        findings.append({
                            "poc_id": item.get("pocid"),
                            "severity": item.get("severity"),
                            "vuln_url": item.get("fulltarget"),
                            "request": item.get("request", "")
                        })
            except Exception as e:
                self.write_log("tool_afrog", f"解析输出失败: {e}")

        self.save_artifact("afrog_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings