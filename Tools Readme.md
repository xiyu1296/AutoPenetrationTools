模块一：信息收集与资产测绘 (Reconnaissance & OSINT)
侧重于“广撒网”，寻找目标的边缘资产和暴露面。

subfinder：快速被动子域名枚举（基于数百个 API 和源）。

amass：深度 DNS 侦察与外围资产测绘（适合需要彻底摸清网络拓扑的场景）。

dnsx：多用途 DNS 工具（用于验证 subfinder 找出的子域名是否存活）。

oneforall：专注于国内环境的子域名收集神器。

gau (GetAllUrls)：从 AlienVault、Wayback Machine 获取目标历史 URL。

theHarvester：收集目标公司的邮箱、员工姓名、子域和 IP（用于社会工程学或凭证撞库前置）。

gitrob / trufflehog：扫描目标 GitHub 仓库，寻找泄露的 API Key 和密码。

shodan-cli：通过 Shodan 搜索引擎直接获取目标 IP 的物联网暴露和历史开放端口。

模块二：端口服务与指纹识别 (Discovery & Fingerprinting)
用于精准识别目标主机的开放服务和 Web 技术栈。

nmap：(已集成) 经典的端口与服务版本探测。

masscan：极速异步端口扫描（适合扫描 /16 或 /8 的大网段 C 段）。

naabu：ProjectDiscovery 出品的快速端口扫描器（完美契合现有工作流）。

httpx：(已集成) Web 存活探测与基础技术栈指纹识别。

whatweb：下一代 Web 扫描器，专注于极度精细的 CMS 和框架指纹识别。

wafw00f：WAF（Web 应用防火墙）探测工具（在执行重型扫描前调用，避免被封 IP）。

模块三：爬虫与端点发现 (Crawling & Endpoint Extraction)
寻找 Web 应用内部的隐藏入口和参数。

katana：(已集成) 无头浏览器深度 Web 爬虫。

hakrawler：快速提取 Web 页面中的 JavaScript 文件和端点。

paramspider：专注于寻找带有参数的 URL（为 SQLMap 和 XSS 扫描准备弹药）。

arjun：隐藏 HTTP 参数爆破工具（发现 API 中未公开的 ?debug=1 等参数）。

kiterunner：针对 REST API 和 GraphQL 的路由爆破工具。

模块四：目录爆破与敏感信息泄露 (Content Discovery)
寻找未直接链接的隐藏资产。

ffuf：(已集成) 极速 Web 目录与虚拟主机（VHost）模糊测试。

dirsearch：经典的目录爆破工具，自带针对性极强的字典。

feroxbuster：基于 Rust 的递归目录发现工具（速度极快）。

gobuster：支持 DNS、VHost 和目录枚举的强力爆破工具。

模块五：综合漏洞扫描 (Comprehensive DAST)
广度漏洞探测阶段。

nuclei：(已集成) 基于模板的 CVE 和配置错误检测神器。

xray：国内最强的 Web 被动/主动扫描器（涵盖 XSS, SQLi, 逻辑漏洞）。

afrog：类似 Nuclei 的另一款优秀模板扫描器，国内漏洞 POC 覆盖率高。

nikto：老牌 Web 服务器扫描器（检查过时的 Apache/Nginx 配置、CGI 漏洞）。

模块六：专项深度利用 (Specialized Exploitation)
当发现特定疑似风险时，调用这些工具进行“外科手术式”打击。

sqlmap：(已集成) 自动化 SQL 注入与数据库接管。

dalfox：基于参数分析和智能 Payload 生成的 XSS 漏洞扫描利用工具。

xsstrike：最先进的 XSS 扫描器，自带 Payload 模糊测试和 WAF 绕过。

commix：自动化操作系统命令注入漏洞（OS Command Injection）利用工具。

ssrfmap：自动化 SSRF（服务器端请求伪造）漏洞挖掘与利用。

tplmap：SSTI（服务器端模板注入）漏洞利用工具。

crlfuzz：快速扫描 CRLF 注入漏洞。

lfisuite：LFI（本地文件包含）漏洞自动化挖掘与利用。

ysoserial：生成 Java 反序列化 Payload（可作为工具接口，供大模型生成攻击字符串）。

模块七：身份认证与暴力破解 (Authentication & Bruteforce)
非 Web 协议及登录框的攻击手段。

hydra：(已集成) 强大的在线网络登录破解工具。

medusa：Hydra 的极佳替代品，支持多线程并行网络爆破。

crackmapexec：Windows 活动目录（AD）和 SMB 协议渗透神器（用于内网横向）。

hashcat：世界上最快的密码恢复工具（若大模型获得了 MD5 密文，可调用它进行离线破解）。

jwt_tool：用于验证、伪造和破解 JWT（JSON Web Tokens）的工具。

模块八：云、容器与新型安全 (Cloud, API & AI Security)
针对现代化架构的渗透测试。

cloudfox：寻找 AWS/Azure/GCP 环境中的可利用攻击路径。

peirates：Kubernetes (K8s) 集群渗透与权限提升工具。

apifuzzer：读取 Swagger/OpenAPI 文档，对 API 接口进行深度 Fuzzing。

garak：LLM 漏洞扫描器（检测目标 AI 系统的 Prompt 注入、越狱等风险）。

模块九：无回显漏洞检测与辅助工具 (Out-of-Band & Utilities)
用于证明盲注漏洞（Blind SQLi, Blind RCE）。

interactsh-client：生成 OOB（带外）域名，检测无回显的漏洞（如 DNSLog 机制，渗透测试必备）。

searchsploit：Exploit-DB 的命令行搜索工具（大模型发现版本号后，调用它搜索现成 EXP）。

cyberchef：通过 API 封装的万能解码/编码器（Base64, Hex, AES 等），辅助大模型处理加密数据。

nxc (NetExec)：用于大规模网络协议枚举，CME 的现代替代分支。

msfconsole (RPC)：Metasploit 的远程过程调用接口，大模型可通过 API 直接下发指令打出复杂 EXP。