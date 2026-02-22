import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class DnsxRunner(BaseRunner):
    """独立 Dnsx 多用途 DNS 工具执行器"""

    def run_scan(self, subdomains: List[str]) -> List[Dict[str, Any]]:
        if not subdomains:
            return []

        self.write_log("tool_dnsx", f"启动 Dnsx，目标数量: {len(subdomains)}")

        binary_path = os.path.abspath(os.path.join(os.getcwd(), "dnsx.exe"))
        binary = binary_path if os.path.exists(binary_path) else "dnsx"

        # 生成输入文件
        input_file = self.base_dir / "dnsx_input.txt"
        with open(input_file, "w", encoding="utf-8") as f:
            f.write("\n".join(subdomains))

        tmp_output = self.base_dir / "dnsx_raw.jsonl"

        # -l: 目标列表文件, -silent: 静默模式, -json: JSON输出, -a: 获取A记录
        cmd = [binary, "-l", str(input_file), "-silent", "-json", "-a", "-o", str(tmp_output)]

        self.run_tool(cmd, "tool_dnsx")

        findings = []
        if tmp_output.exists():
            with open(tmp_output, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        findings.append({
                            "host": data.get("host"),
                            "a_records": data.get("a", []),
                            "cname": data.get("cname", []),
                            "status_code": data.get("status_code", "")
                        })
                    except Exception:
                        continue

        self.save_artifact("dnsx_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings