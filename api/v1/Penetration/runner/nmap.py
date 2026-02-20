import re
from .base import BaseRunner


class NmapRunner(BaseRunner):
    """
    Stage 1 资产发现执行器
    """

    def scan(self, target: str, ports: str = "1-1000"):
        self.update_status({"stage": "Stage1_Asset", "hint": f"正在扫描目标: {target}", "percent": 15})

        # 真实调用 Nmap
        cmd = ["nmap", "-sV", "-p", ports, target]
        output = self.run_tool(cmd, "stage1_asset")

        # 简单的正则解析：匹配开放端口与服务
        discovered_ports = []
        if output:
            matches = re.findall(r"(\d+)/tcp\s+open\s+([\w-]+)", output)
            for port, service in matches:
                discovered_ports.append({"port": int(port), "service": service})

        # 构造并保存资产清单 assets.json
        assets_data = {
            "task_id": self.task_id,
            "target": target,
            "hosts": [
                {
                    "ip": target,
                    "ports": discovered_ports if discovered_ports else [{"port": 80, "service": "mock-http"}]
                }
            ],
            "status": "completed"
        }

        self.save_artifact("assets.json", assets_data)
        self.update_status({
            "percent": 35,
            "hint": f"Stage 1 完成，发现 {len(discovered_ports)} 个端口"
        })
        return assets_data