import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class MasscanRunner(BaseRunner):
    """独立 Masscan 极速端口扫描执行器"""

    def run_scan(self, target_ip: str, ports: str = "1-65535", rate: int = 1000) -> List[Dict[str, Any]]:
        if not target_ip:
            return []

        self.write_log("tool_masscan", f"启动 Masscan，目标: {target_ip}, 端口: {ports}, 速率: {rate}")

        binary_path = os.path.abspath(os.path.join(os.getcwd(), "masscan.exe"))
        binary = binary_path if os.path.exists(binary_path) else "masscan"

        tmp_output = self.base_dir / "masscan_raw.json"

        # 构造命令: masscan <ip> -p <ports> --rate <rate> -oJ <output>
        cmd = [
            binary, target_ip,
            "-p", ports,
            "--rate", str(rate),
            "-oJ", str(tmp_output)
        ]

        self.run_tool(cmd, "tool_masscan")

        findings = []
        if tmp_output.exists():
            try:
                with open(tmp_output, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        ip = item.get("ip")
                        for port_info in item.get("ports", []):
                            findings.append({
                                "ip": ip,
                                "port": port_info.get("port"),
                                "protocol": port_info.get("proto"),
                                "status": port_info.get("status")
                            })
            except Exception as e:
                self.write_log("tool_masscan", f"解析输出失败: {e}")

        self.save_artifact("masscan_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings