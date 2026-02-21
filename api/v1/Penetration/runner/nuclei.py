import json
import os
from typing import List
from .base import BaseRunner


class NucleiRunner(BaseRunner):
    """独立 Nuclei 漏洞扫描工具执行器"""

    def run_scan(self, targets: List[str], templates: List[str]) -> List[dict]:
        if not targets:
            return []

        self.write_log("tool_nuclei", f"接收到独立的 Nuclei 扫描请求，目标数: {len(targets)}")

        # 构造外部命令
        tmp_output = self.base_dir / "nuclei_raw.jsonl"
        binary = "./nuclei.exe" if os.path.exists("./nuclei.exe") else "nuclei"

        cmd = [binary, "-u", ",".join(targets), "-jsonl", "-silent", "-o", str(tmp_output)]
        for t in templates:
            cmd.extend(["-t", t])

        self.write_log("tool_nuclei", f"执行命令: {' '.join(cmd)}")
        self.run_tool(cmd, "tool_nuclei")

        # 解析输出并提取关键信息
        findings = []
        if tmp_output.exists():
            with open(tmp_output, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        findings.append({
                            "target": data.get("matched-at", data.get("host")),
                            "vulnerability": data.get("info", {}).get("name", "Unknown Vuln"),
                            "severity": data.get("info", {}).get("severity", "info").capitalize(),
                            "evidence": data.get("extracted-results", [data.get("matcher-name", "")])[0]
                        })
                    except:
                        continue

        # 依然进行证据留存，确保符合部署合规性
        self.save_artifact("nuclei_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings