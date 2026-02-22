import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class NaabuRunner(BaseRunner):
    """独立 Naabu 端口扫描执行器"""

    def run_scan(self, target: str) -> List[Dict[str, Any]]:
        if not target:
            return []

        self.write_log("tool_naabu", f"启动 Naabu，目标: {target}")

        binary_path = os.path.abspath(os.path.join(os.getcwd(), "naabu.exe"))
        binary = binary_path if os.path.exists(binary_path) else "naabu"

        tmp_output = self.base_dir / "naabu_raw.jsonl"

        # 构造命令: naabu -host <target> -json -o output.jsonl
        cmd = [
            binary,
            "-host", target,
            "-json",
            "-o", str(tmp_output)
        ]

        self.run_tool(cmd, "tool_naabu")

        findings = []
        if tmp_output.exists():
            with open(tmp_output, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        findings.append({
                            "host": data.get("host"),
                            "ip": data.get("ip"),
                            "port": data.get("port"),
                            "protocol": data.get("protocol", "tcp")
                        })
                    except Exception:
                        continue

        self.save_artifact("naabu_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings