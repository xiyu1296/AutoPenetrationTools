import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class SubfinderRunner(BaseRunner):
    """独立 Subfinder 子域名枚举执行器"""

    def run_scan(self, target_domain: str) -> List[Dict[str, Any]]:
        if not target_domain:
            return []

        self.write_log("tool_subfinder", f"启动 Subfinder，目标: {target_domain}")

        binary_path = os.path.abspath(os.path.join(os.getcwd(), "subfinder.exe"))
        binary = binary_path if os.path.exists(binary_path) else "subfinder"

        tmp_output = self.base_dir / "subfinder_raw.jsonl"

        # -d: 目标域名, -silent: 静默模式, -j: JSONL输出, -o: 输出文件
        cmd = [binary, "-d", target_domain, "-silent", "-j", "-o", str(tmp_output)]

        self.run_tool(cmd, "tool_subfinder")

        findings = []
        if tmp_output.exists():
            with open(tmp_output, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        findings.append({
                            "host": data.get("host"),
                            "source": data.get("source")
                        })
                    except Exception:
                        continue

        self.save_artifact("subfinder_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings