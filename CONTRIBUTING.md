# Contributing to Titan Evolution OS

Thank you for helping make digital teamwork and agent evolution more accessible. This guide is bilingual (EN / 中文摘要).

---

## Ways to contribute

- **Issues**: bug reports, small feature ideas, documentation fixes — [open an issue](https://github.com/safevisa/Titan-Evolution-OS/issues).
- **Pull requests**: focused changes with a clear description; prefer small PRs over large rewrites unless discussed first.
- **Discussions** (if enabled): architecture questions and roadmap alignment.

---

## Development setup

1. Copy env: `cp .env.example .env` and set at least one LLM API key and `POSTGRES_PASSWORD`.
2. Start stack: `docker compose up -d` from repo root.
3. **Backend** (optional local without Docker): see `backend/requirements.txt`, use Python 3.12+, run migrations via `alembic upgrade head` when DB is available.
4. **Frontend**: see `frontend/package.json`; `npm install` and `npm run dev` for local UI against your API.

Run linters / tests if your change touches those areas (add or extend CI-friendly checks when you add them).

---

## Pull request checklist

- Describe **what** and **why** (user-visible behavior or data model impact).
- Avoid committing secrets (`.env`, keys, `token.pem`).
- Match existing code style and i18n patterns for UI copy where applicable.
- If you change the database schema, include an **Alembic migration** under `backend/alembic/versions/`.

---

## Code of conduct

We follow the [Contributor Covenant](CODE_OF_CONDUCT.md). Be respectful, assume good intent, and keep feedback constructive.

---

## 中文摘要

欢迎通过 **Issue** 反馈问题、通过 **Pull Request** 提交小步改进。请勿提交密钥与 `.env`；数据库变更请附带 **Alembic 迁移**。参与讨论时请遵守 [行为准则](CODE_OF_CONDUCT.md)。
