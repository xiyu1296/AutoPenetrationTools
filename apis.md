第一篇：RESTful API 核心集成指南（针对前端与通用开发）
后端基于 FastAPI 构建，采用标准的 REST 风格和 Pydantic 数据验证。
1. 基础连接与安全认证
服务地址: http://localhost:8020/v1。
认证 Header: 必须携带 X-API-Key，默认值为 test-key。
数据模型: 所有复杂对象均遵循 schema.py 中的定义。
2. 接口详解
任务初始化 (/penetration/task/create):
参数逻辑: 接收 target（目标 IP/域名）和 budget（预算配置）。
Budget 对象: 包含 timeout_seconds（默认 900s）和 rate_limit_rps（默认 1.0），用于控制扫描强度。
业务流程: 前端应首先调用此接口获取 task_id，这是后续所有操作的唯一凭证。
全流程启动 (/penetration/task/run):
执行机制: 传入 task_id 后，后端将按顺序触发 Nmap -> Httpx -> Crawler -> Candidate -> Validator -> Reporter。
异步建议: 由于渗透扫描耗时较长，此接口会立即返回启动成功，前端需通过轮询状态接口获取进度。
状态监控与进度条 (/penetration/task/status):
关键字段: 返回的 progress 包含 percent（百分比）和 hint（步骤描述），stage 指明当前运行的阶段。
阻塞处理: 检查 blocked.is_blocked 字段。如果为 true，说明任务正在等待人工审批（如 /task/approve）。
证据链管理 (/artifacts/list & /artifacts/download):
制品发现: 返回 ArtifactInfo 列表，包含文件名、MIME 类型和字节大小。
下载逻辑: 前端通过 path 参数请求具体文件，后端返回一个包含原始证据及 scope.json 的 ZIP 压缩包。







第二篇：Dify 深度集成指南（AI 增强与工作流）
Dify 的集成分为“作为外部工具”和“作为智能决策大脑”两个维度。
1. 维度一：将后端封装为 Dify 自定义工具 (Custom Tool)
使 Dify 能够像调用搜索插件一样调用您的渗透测试能力。
配置步骤:
在 Dify 侧边栏进入“工具” -> “创建自定义工具”。
鉴权配置: 选择 API Key 类型，Header 填入 X-API-Key，Value 填入 test-key。
OpenAPI Schema: 将 app.py 自动生成的 /docs 下的 JSON 定义填入。
接口映射重点:
task/create: 给 Dify 的 Prompt 描述为：“用于开启一个新的安全审计任务，输入参数为目标域名”。
task/status: 描述为：“用于轮询任务进度，直到 percent 达到 100 且 findings 有数据”。
artifacts/list: 描述为：“任务完成后，用于获取报告文件列表”。
2. 维度二：利用 Dify 替代 Stage 4 智能决策 (LLM Logic)
当前的 candidate.py 依赖正则匹配（如 admin, login）。您可以用 Dify 工作流替换这部分逻辑，实现 AI 级别的攻击面分析。
集成架构:
数据外传: 在 CandidateRunner 中，读取 endpoints.json 的全量路径数据。
调用 Dify API: 将端点列表作为 inputs 发送到 Dify 的工作流应用。
Prompt 设计: “作为渗透测试专家，分析以下路径列表中哪些最具有被 SQL 注入或敏感泄露的风险，请以 JSON 格式返回候选点及推荐理由”。
结果反馈: 接收 Dify 返回的 JSON，将其写入 candidates.json 供后续 ValidatorRunner 执行物理验证。
3. 维度三：Dify 自动化报告解析
利用 Dify 读取任务产生的 report.md 和 findings.json。
接口对接:
Dify 调取 artifacts/download 获取数据包。
AI 总结: Dify 读取 findings.json 中的 evidence_data（如 HTTP/1.1 200 OK）。
交互输出: 用户在 Dify 对话框询问“这次扫描发现了什么？”，AI 根据 findings.json 解释：“发现一个活跃的登录页面 login.php，已确认为 200 OK，建议进行暴力破解防护检查”。



