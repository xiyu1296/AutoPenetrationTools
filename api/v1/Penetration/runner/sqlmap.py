import os
import re
from typing import List, Dict, Any
from .base import BaseRunner


class SqlmapRunner(BaseRunner):
    """独立 SQLMap 注入探测工具执行器"""

    def run_injection_test(self, target_url: str, risk_level: int) -> Dict[str, Any]:
        if not target_url:
            return {"is_vulnerable": False, "databases": [], "evidence_log": "No URL provided."}

        self.write_log("tool_sqlmap", f"接收到 SQLMap 测试请求，目标: {target_url}")

        # 构造外部命令
        # --batch: 无交互执行
        # --dbs: 尝试枚举数据库
        # --level/--risk: 设置探测深度
        binary = "sqlmap"  # 假设 sqlmap 已配置在系统环境变量中
        cmd = [
            binary, "-u", target_url,
            "--batch", "--dbs",
            f"--level={min(risk_level, 5)}",
            f"--risk={min(risk_level, 3)}"
        ]

        self.write_log("tool_sqlmap", f"执行命令: {' '.join(cmd)}")
        output = self.run_tool(cmd, "tool_sqlmap")

        # 解析 SQLMap 的标准输出
        is_vulnerable = False
        databases = []
        evidence = "No injection points found."

        if output:
            # 检查是否存在注入点特征字符串
            if "sqlmap identified the following injection point(s)" in output or "is vulnerable" in output:
                is_vulnerable = True
                evidence = "Injection point successfully identified."

            # 提取获取到的数据库名称
            if "available databases" in output:
                # 寻找类似 [*] db_name 的输出行
                db_matches = re.findall(r'\[\*\]\s([a-zA-Z0-9_\-]+)', output)
                if db_matches:
                    databases = [db for db in db_matches if db not in ['starting', 'shutting', 'ending']]
                    evidence = f"Successfully extracted databases: {', '.join(databases)}"

        finding = {
            "url": target_url,
            "is_vulnerable": is_vulnerable,
            "databases": databases,
            "evidence_log": evidence
        }

        # 证据留存
        self.save_artifact("sqlmap_findings.json", {"task_id": self.task_id, "sqlmap_result": finding})
        return finding