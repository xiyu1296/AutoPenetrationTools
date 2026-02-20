import json
import os
from urllib.parse import urljoin
from .base import BaseRunner


class CrawlerRunner(BaseRunner):
    """Stage 3: 强化爬虫执行器"""

    def run_crawl(self):
        self.update_status({"stage": "Stage3_Surface", "hint": "执行深度端点发现", "percent": 65})

        fp_path = self.base_dir / "http_fingerprints.json"
        if not fp_path.exists(): return {"endpoints": []}

        with open(fp_path, "r", encoding="utf-8") as f:
            fps = json.load(f).get("fingerprints", [])

        urls = [fp.get("url") for fp in fps if fp.get("url")]
        if not urls: return self._save_empty()

        # 执行外部工具
        binary = "./katana.exe" if os.path.exists("./katana.exe") else "katana"
        cmd = [binary, "-u", ",".join(urls), "-d", "3", "-fl", "-jc", "-jsonl", "-silent"]
        output = self.run_tool(cmd, "stage3_crawler")

        endpoints = []
        if output:
            for line in output.strip().split('\n'):
                try:
                    endpoints.append(json.loads(line))
                except:
                    continue

        # 核心修复：注入指纹中的重定向目标作为端点
        if not endpoints:
            self.write_log("stage3_crawler", "爬虫未发现路径，正在从指纹库提取重定向目标")
            for fp in fps:
                # 添加基础 URL
                endpoints.append({"request": {"url": fp.get("url"), "method": "GET"}})
                # 显式提取并合并 Location
                if fp.get("location"):
                    redirect_url = urljoin(fp.get("url"), fp.get("location"))
                    endpoints.append({"request": {"url": redirect_url, "method": "GET"}})

        result = {"task_id": self.task_id, "endpoints": endpoints}
        self.save_artifact("endpoints.json", result)
        self.update_status({"percent": 75, "hint": f"发现 {len(endpoints)} 个端点"})
        return result

    def _save_empty(self):
        self.save_artifact("endpoints.json", {"task_id": self.task_id, "endpoints": []})
        return {"endpoints": []}