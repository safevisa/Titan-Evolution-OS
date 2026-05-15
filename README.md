# Titan Evolution OS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-safevisa%2FTitan--Evolution--OS-blue)](https://github.com/safevisa/Titan-Evolution-OS)

**Digital workforce + collaborative task pipelines** — Next.js, FastAPI, Celery, Postgres, Redis, Qdrant.  
**数字员工 + 协同任务流水线** — 面向真实工作场景的编排与执行骨架，持续开源演进。

---

## 愿景（为什么开源）

我们希望 **更多公司和个人** 能借助可组合的数字员工与流水线，**更高效地完成工作、创造更多价值**，并在数字世界里获得可复用的协作能力。

**长期方向**（与社区共建，非短期承诺）：

- 让 **每个人都能拥有自己的数字工作团队** —— 可配置角色、技能与记忆，围绕目标持续协作；
- 让 **个性与能力极强的超级 Agent** 能在 **可审计、可回滚** 的前提下，通过任务与反馈不断进化。

当前 **自动进化** 与 **行业可执行闭环** 仍处于 **早期 / 雏形** 阶段；我们坦诚写在 [愿景与路线图](docs/愿景与路线图.md)，并邀请你通过 Issue 与 PR 一起把它做成真正可靠的基础设施。

---

## 文档

| 文档 | 说明 |
|------|------|
| [愿景与路线图](docs/愿景与路线图.md) | 信念、长期目标、现阶段边界、共建路线图 |
| [项目自述与声明](docs/项目自述与声明.md) | 产品定位、免责声明、数据与安全原则 |
| [产品使用说明](docs/产品使用说明.md) | 安装、配置、主要功能与 FAQ |
| [贡献指南](CONTRIBUTING.md) | 如何参与开发与提交 PR |
| [行为准则](CODE_OF_CONDUCT.md) | 社区协作规范（Contributor Covenant 2.1） |
| [安全披露](SECURITY.md) | 漏洞报告方式 |

---

## 快速开始

```bash
git clone https://github.com/safevisa/Titan-Evolution-OS.git
cd Titan-Evolution-OS
cp .env.example .env
# 编辑 .env：至少填写 POSTGRES_PASSWORD、一种 LLM API Key、AUTH_SECRET 等
docker compose up -d
```

- 前端（默认映射）：`http://127.0.0.1:3001`  
- API：`http://127.0.0.1:8000`  
- 生产环境请配合 HTTPS 与反向代理（参见 `deploy/` 下示例配置）。

---

## 参与共建

1. **Star / Fork** 本仓库，便于他人发现你的分支实验。  
2. 阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，从 **文档、小修复、测试** 或 **行业插件示例** 开始 PR。  
3. 在 [Issues](https://github.com/safevisa/Titan-Evolution-OS/issues) 分享你的 **行业场景、失败案例、期望 API** —— 这会直接影响路线图优先级。

---

## 许可证

本项目以 [**MIT License**](LICENSE) 开源 —— 可自由使用、修改与再发布，**需保留版权声明**；软件按「现状」提供，无担保（详见许可证全文）。

---

**English one-liner:** *An open, evolvable OS-shaped stack for multi-agent work — early stage on auto-evolution and deep vertical playbooks; contributions welcome.*
