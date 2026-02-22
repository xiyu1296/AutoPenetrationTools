import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class DirsearchRunner(BaseRunner):
    """独立 Dirsearch 目录爆破执行器"""

    def run_scan(self, target_url: str) -> List[Dict[str, Any]]:
        if not target_url:
            return []

        self.write_log("tool_dirsearch", f"启动 Dirsearch，目标: {target_url}")

        script_path = os.path.abspath(os.path.join(os.getcwd(), "dirsearch", "dirsearch.py"))
        if not os.path.exists(script_path):
            self.write_log("tool_dirsearch", f"未找到脚本: {script_path}")
            return []

        tmp_output = self.base_dir / "dirsearch_raw.json"

        # python dirsearch.py -u <url> --format=json -o <output>
        cmd = [
            "python", script_path,
            "-u", target_url,
            "--format=json",
            "-o", str(tmp_output)
        ]

        self.run_tool(cmd, "tool_dirsearch")

        findings = []
        if tmp_output.exists():
            try:
                with open(tmp_output, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Dirsearch JSON 结构：{"results": [{"url": "...", "status": 200, "content-length": 123}, ...]}
                    results = data.get("results", [])
                    for item in results:
                        findings.append({
                            "url": item.get("url"),
                            "status": item.get("status"),
                            "content_length": item.get("content-length"),
                            "redirect": item.get("redirect", "")
                        })
            except Exception as e:
                self.write_log("tool_dirsearch", f"解析输出失败: {e}")

        self.save_artifact("dirsearch_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings