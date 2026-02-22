import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class GauRunner(BaseRunner):
    """独立 gau (GetAllUrls) 执行器"""

    def run_scan(self, target_domain: str) -> List[Dict[str, Any]]:
        if not target_domain:
            return []

        self.write_log("tool_gau", f"启动 gau，目标: {target_domain}")

        binary_path = os.path.abspath(os.path.join(os.getcwd(), "gau.exe"))
        binary = binary_path if os.path.exists(binary_path) else "gau"

        tmp_output = self.base_dir / "gau_raw.jsonl"

        # 构造命令: gau example.com --json -o output.jsonl
        cmd = [binary, target_domain, "--json", "-o", str(tmp_output)]

        self.run_tool(cmd, "tool_gau")

        findings = []
        if tmp_output.exists():
            with open(tmp_output, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        findings.append({
                            "url": data.get("url"),
                            "method": data.get("method", "GET"),
                            "status_code": data.get("status", "")
                        })
                    except Exception:
                        continue

        self.save_artifact("gau_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings