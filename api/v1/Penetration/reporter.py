import json
import shutil
from pathlib import Path
from datetime import datetime
from .runner.base import BaseRunner


class ReporterRunner(BaseRunner):
    """
    Stage 6: 报告生成与成果打包执行器
    """

    def generate_final_package(self):
        self.update_status({"stage": "Stage6_Report", "hint": "正在汇总证据并生成最终报告", "percent": 95})

        # 1. 汇总各阶段数据
        data = self._load_all_data()

        # 2. 渲染 Markdown 报告
        report_content = self._build_markdown(data)
        report_path = self.base_dir / "report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        # 3. 创建归档压缩包 (Artifacts)
        # 包含所有 JSON、日志和 Markdown 报告
        archive_name = f"artifacts_{self.task_id}"
        zip_path = shutil.make_archive(
            str(self.base_dir / archive_name),
            'zip',
            root_dir=str(self.base_dir)
        )

        self.write_log("stage6_report", f"报告已生成: report.md, 打包文件: {Path(zip_path).name}")
        self.update_status({"percent": 100, "hint": "任务圆满完成，交付物已就绪"})
        return {"report_path": str(report_path), "zip_path": zip_path}

    def _load_all_data(self):
        files = {
            "assets": "assets.json",
            "fingerprints": "http_fingerprints.json",
            "endpoints": "endpoints.json",
            "candidates": "candidates.json",
            "findings": "findings.json"
        }
        content = {}
        for key, name in files.items():
            path = self.base_dir / name
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    content[key] = json.load(f)
        return content

    def _build_markdown(self, data):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        findings = data.get("findings", {}).get("findings", [])

        # 报告模板
        md = f"""# 自动化渗透测试报告
## 1. 任务概览
- **任务 ID**: {self.task_id}
- **完成时间**: {now}
- **发现风险点**: {len(findings)}

## 2. 风险发现汇总
| 目标 URL | 漏洞类型 | 严重程度 | 物理证据 |
| :--- | :--- | :--- | :--- |
"""
        for f in findings:
            md += f"| {f['url']} | {f['vulnerability']} | {f['severity']} | `{f['evidence_data']}` |\n"

        md += f"\n## 3. 详细资产清单\n- **目标 IP**: {data.get('assets', {}).get('target', 'N/A')}\n"

        # 列出所有指纹信息
        md += "\n## 4. 指纹识别结果\n"
        for fp in data.get("fingerprints", {}).get("fingerprints", []):
            md += f"- **{fp.get('url')}**: {', '.join(fp.get('tech', []))} (Status: {fp.get('status_code')})\n"

        md += "\n---\n*报告由自动化渗透测试系统 S3 Runner 自动生成*"
        return md