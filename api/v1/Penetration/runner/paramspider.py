import requests
from typing import List, Dict, Any
from .base import BaseRunner


class ParamSpiderRunner(BaseRunner):
    """独立 ParamSpider 执行器 (原生 Python 极速版，零第三方依赖)"""

    def run_scan(self, target_domain: str) -> List[Dict[str, Any]]:
        if not target_domain:
            return []

        self.write_log("tool_paramspider", f"启动 ParamSpider (Native版)，目标: {target_domain}")

        findings = set()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutoPenetrationTools/1.0"}

        # 1. 检索 Wayback Machine 历史快照
        wb_url = f"http://web.archive.org/cdx/search/cdx?url=*.{target_domain}/*&collapse=urlkey&output=text&fl=original"
        try:
            self.write_log("tool_paramspider", "正在请求 Wayback Machine API...")
            res = requests.get(wb_url, headers=headers, timeout=20)
            if res.status_code == 200:
                for line in res.text.splitlines():
                    # 只提取带有参数的 URL
                    if "?" in line and "=" in line:
                        findings.add(line.strip())
        except Exception as e:
            self.write_log("tool_paramspider", f"Wayback Machine 请求失败: {e}")

        # 2. 检索 AlienVault OTX 威胁情报库
        otx_url = f"https://otx.alienvault.com/api/v1/indicators/domain/{target_domain}/url_list?limit=500&page=1"
        try:
            self.write_log("tool_paramspider", "正在请求 AlienVault OTX API...")
            res = requests.get(otx_url, headers=headers, timeout=20)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("url_list", []):
                    url = item.get("url", "")
                    if "?" in url and "=" in url:
                        findings.add(url.strip())
        except Exception as e:
            self.write_log("tool_paramspider", f"AlienVault OTX 请求失败: {e}")

        # 格式化输出
        results = [{"url": url} for url in findings]
        self.save_artifact("paramspider_findings.json", {"task_id": self.task_id, "findings": results})

        self.write_log("tool_paramspider", f"提取完成，共捕获 {len(results)} 个带参 URL。")
        return results