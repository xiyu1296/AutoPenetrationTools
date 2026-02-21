import os
import re
from typing import List, Dict, Any
from .base import BaseRunner


class HydraRunner(BaseRunner):
    """独立 Hydra 弱口令爆破执行器 (可移植绿色版)"""

    def run_bruteforce(self, target_ip: str, service: str, port: int) -> Dict[str, Any]:
        if not target_ip or not service:
            return {"is_cracked": False, "findings": []}

        self.write_log("tool_hydra", f"接收到弱口令爆破请求，目标: {target_ip}:{port} ({service})")

        # 1. 动态定位可移植目录中的工具与字典
        # os.getcwd() 指向项目根目录 AutoPenetrationTools
        hydra_dir = os.path.abspath(os.path.join(os.getcwd(), "hydra"))
        binary = os.path.join(hydra_dir, "hydra.exe")

        user_dict = os.path.abspath(os.path.join(os.getcwd(), "users.txt"))
        pass_dict = os.path.abspath(os.path.join(os.getcwd(), "pass.txt"))

        # 健壮性检查
        if not os.path.exists(binary):
            error_msg = f"未找到 Hydra 主程序: {binary}。请确认已将 hydra 文件夹放入项目根目录。"
            self.write_log("tool_hydra", error_msg)
            return {"is_cracked": False, "findings": []}

        if not os.path.exists(user_dict) or not os.path.exists(pass_dict):
            self.write_log("tool_hydra", "字典文件缺失，请确保项目根目录存在 users.txt 和 pass.txt")
            return {"is_cracked": False, "findings": []}

        # 2. 构造命令
        # -L: 用户名字典
        # -P: 密码字典
        # -s: 指定端口
        # -f: 爆破成功一个就停止 (极大节约时间)
        # -t: 线程数 (Windows 下建议不要太高，4-8 即可)
        cmd = [
            binary,
            "-L", user_dict,
            "-P", pass_dict,
            "-s", str(port),
            "-f", "-t", "4",
            target_ip,
            service
        ]

        self.write_log("tool_hydra", f"执行命令: {' '.join(cmd)}")

        # 3. 核心执行逻辑
        # 注意：subprocess 运行时，它会自动在 binary 所在的 hydra/ 目录里找到那些 .dll
        output = self.run_tool(cmd, "tool_hydra")

        # 4. 解析结果 (提取爆破成功的凭证)
        findings = []
        is_cracked = False

        if output:
            # 兼容 Hydra 成功时的经典输出格式
            success_pattern = re.compile(r'host:\s*([^\s]+)\s+login:\s*([^\s]+)\s+password:\s*([^\s]+)', re.IGNORECASE)
            matches = success_pattern.findall(output)

            for match in matches:
                is_cracked = True
                findings.append({
                    "service": service,
                    "ip": match[0],
                    "port": port,
                    "username": match[1],
                    "password": match[2]
                })

        # 5. 证据物理落盘
        result = {"task_id": self.task_id, "is_cracked": is_cracked, "findings": findings}
        self.save_artifact(f"hydra_{service}_{port}_findings.json", result)

        if is_cracked:
            self.write_log("tool_hydra", f"爆破成功！发现 {len(findings)} 组有效凭证。")
        else:
            self.write_log("tool_hydra", "爆破完成，未发现弱口令。")

        return result