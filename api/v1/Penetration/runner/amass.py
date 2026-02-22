import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class AmassRunner(BaseRunner):
    """独立 Amass 资产测绘执行器 (被动模式)"""

    def run_scan(self, target_domain: str) -> List[Dict[str, Any]]:
        if not target_domain:
            return []

        self.write_log("tool_amass", f"启动 Amass 被动扫描，目标: {target_domain}")

        binary_path = os.path.abspath(os.path.join(os.getcwd(), "amass.exe"))
        binary = binary_path if os.path.exists(binary_path) else "amass"

        tmp_output = self.base_dir / "amass_raw.jsonl"

        # enum: 枚举模式, -passive: 被动收集(速度快/隐蔽), -d: 域名, -json: JSON输出
        cmd = [binary, "enum", "-passive", "-d", target_domain, "-json", str(tmp_output)]

        self.run_tool(cmd, "tool_amass")

        findings = []
        if tmp_output.exists():
            with open(tmp_output, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        findings.append({
                            "name": data.get("name"),
                            "domain": data.get("domain"),
                            "sources": data.get("sources", [])
                        })
                    except Exception:
                        continue

        self.save_artifact("amass_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings