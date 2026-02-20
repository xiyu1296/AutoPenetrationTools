# api/v1/Penetration/runner/nmap.py
from .base import BaseRunner
import re


class NmapRunner(BaseRunner):
    def scan(self, target: str, ports: str = "80,443,8080"):
        """
        执行端口扫描并解析结果存入 assets.json
        """
        self.update_status({"stage": "Stage1_Asset", "hint": f"正在扫描目标: {target}"})

        # 实际调用工具
        # 注意：演示环境下如果未安装 nmap，这里会捕获异常并记录日志
        cmd = ["nmap", "-sV", "-p", ports, target]
        output = self.run_tool(cmd, "stage1_asset")

        # 简单的正则解析逻辑（实际开发建议使用 python-nmap 库）
        discovered_ports = []
        if output:
            # 匹配 80/tcp open  http 之类的行
            matches = re.findall(r"(\d+)/tcp\s+open\s+([\w-]+)", output)
            for port, service in matches:
                discovered_ports.append({"port": int(port), "service": service})

        # 构造标准产物数据
        assets_data = {
            "task_id": self.task_id,
            "target": target,
            "hosts": [
                {
                    "ip": target,
                    "ports": discovered_ports if discovered_ports else [{"port": 80, "service": "unknown"}]
                }
            ],
            "scan_time": self.log_dir.parent.name  # 简单的占位符
        }

        # 落盘至 Evidence Store
        self.save_artifact("assets.json", assets_data)

        self.update_status({
            "percent": 30,
            "hint": f"Stage 1 完成，发现 {len(discovered_ports)} 个开放端口"
        })

        return assets_data