import shodan
from typing import Dict, Any
from .base import BaseRunner


class ShodanRunner(BaseRunner):
    """独立 Shodan 执行器 (原生 Python API 版)"""

    def run_scan(self, target_ip: str) -> Dict[str, Any]:
        if not target_ip:
            return {}

        self.write_log("tool_shodan", f"启动 Shodan API 信息检索，目标 IP: {target_ip}")

        # TODO: 请在此处填入你真实的 Shodan API Key
        SHODAN_API_KEY = "penetration"

        finding = {}
        try:
            # 实例化 Shodan 客户端
            api = shodan.Shodan(SHODAN_API_KEY)

            # 直接调用底层 API 获取主机信息
            host_info = api.host(target_ip)

            finding = {
                "ip": host_info.get("ip_str"),
                "org": host_info.get("org", ""),
                "os": host_info.get("os", "Unknown"),
                "ports": host_info.get("ports", []),
                "hostnames": host_info.get("hostnames", []),
                "vulns": host_info.get("vulns", [])  # 提取历史 CVE 漏洞记录
            }

        except shodan.APIError as e:
            self.write_log("tool_shodan", f"Shodan API 返回错误 (请检查 Key 是否有效或是否超额): {e}")
        except Exception as e:
            self.write_log("tool_shodan", f"执行异常: {e}")

        # 证据物理落盘
        findings_list = [finding] if finding else []
        self.save_artifact("shodan_findings.json", {"task_id": self.task_id, "findings": findings_list})

        if finding:
            self.write_log("tool_shodan", f"检索完成，发现开放端口: {finding.get('ports', [])}")

        return finding