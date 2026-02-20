from .base import BaseRunner


class NmapRunner(BaseRunner):
    def scan(self, target: str, ports: str = "1-1000"):
        # 模拟执行 Nmap（演示环境下可使用 Mock 数据或真实调用）
        # 产物必须命名为 assets.json
        cmd = ["nmap", "-sV", "-p", ports, target]

        # 1. 执行工具并记录日志
        output = self.run_tool(cmd, "stage1_asset")

        # 2. 结构化解析（此处简略展示逻辑）
        assets_data = {
            "task_id": self.task_id,
            "target": target,
            "hosts": [
                {"ip": target, "ports": [{"port": 80, "service": "http"}]}
            ]
        }

        # 3. 落盘
        self.save_artifact("assets.json", assets_data)
        return assets_data