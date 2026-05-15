# M04 — OpenHuman 侧车（GPL 并行线）

**前置**：M02 完成 `memory-push` 与 Qdrant ingest 管道  
**可与 M03 并行**  
**预估**：3–4 周（含合规审查）  

---

## 1. 模块边界

| 负责 | 不负责 |
|------|--------|
| Titan API：设备绑定、JWT、memory-push 接收 | 在 monorepo 编译 OpenHuman Rust |
| 部署文档与 compose 模板 | GPL 源码闭源分发 |
| 个人线产品配置说明 | 替代 OpenHuman 桌面安装包构建 |

---

## 2. 仓库策略

### 选项 A（推荐）

- GitHub **独立仓库** `titan-openhuman-sidecar`（fork `tinyhumansai/openhuman` 或 submodule）
- CI 构建镜像 `titan-openhuman-sidecar:latest`
- 主仓 `Titan Evolution OS` 仅含：
  - `deploy/docker-compose.sidecar.yml.example`
  - `docs/development/M04-OpenHuman-侧车.md`

### 选项 B

- 主仓 `titan-openhuman-sidecar/` 为 **git submodule**，`.gitmodules` 指向 fork

**禁止**：把 OpenHuman `src/` 复制进 `backend/app/`。

---

## 3. Titan API（B2B）

### 3.1 设备绑定

`POST /api/v1/integrations/sidecar/bind`

```json
{
  "tenant_id": "uuid",
  "device_id": "openhuman-uuid",
  "label": "MacBook Pro"
}
```

需用户 session + tenant admin。写入 `sidecar_device_bindings`。

返回 **侧车 JWT**（HS256，`titan_sidecar_jwt_secret`，claims: `tenant_id`, `device_id`, `exp` 90d）。

### 3.2 Memory Push

`POST /api/v1/integrations/sidecar/memory-push`

Header：`Authorization: Bearer <sidecar_jwt>`

```json
{
  "chunks": [
    {
      "external_id": "oh:doc:abc",
      "title": "Meeting notes",
      "compressed_body": "...",
      "occurred_at": "2026-05-15T10:00:00Z",
      "source": "openhuman"
    }
  ]
}
```

逻辑：

1. 校验 JWT `device_id` 已绑定
2. `Tenant.config.sidecar.allow_memory_push == true`
3. 转 `FetchedItem` → `context_sync.pipeline.ingest_items`（source=`openhuman`）
4. 返回 `{accepted: N, skipped: M}`

**不**存储 GPL 衍生代码；只存压缩文本。

### 3.3 列表与解绑

- `GET /tenants/{id}/sidecar/devices`
- `DELETE /tenants/{id}/sidecar/devices/{device_id}` → purge source=openhuman

---

## 4. 侧车配置（OpenHuman 侧文档）

侧车 `config.toml` 片段（由 OpenHuman 社区插件或 Titan 补丁提供，**在 GPL 仓库实现**）：

```toml
[titan_bridge]
enabled = true
api_base = "https://api.tokenply.world"
device_token = "<from bind>"
push_interval_sec = 3600
```

推送内容：Memory Tree 叶子节点摘要（已由 OpenHuman TokenJuice 压缩）。

---

## 5. 双轨产品关系

```
用户场景 A — 团队 SaaS：仅用 Titan 控制台 + Context Sync（无侧车）
用户场景 B — 个人助理：安装 OpenHuman 桌面 + 绑定租户 → memory-push
用户场景 C — 混合：团队 Agent 用 B2B sync；个人用侧车补充私有笔记
```

账号：NextAuth user 与 `sidecar_device_bindings.user_id` 可选关联。

---

## 6. 合规清单

- [ ] 法律/负责人确认：侧车镜像单独分发，含 GPL 源码 offer
- [ ] 主仓 LICENSE 不变；侧车仓库 LICENSE GPL-3.0
- [ ] Titan API 文档声明：push 内容为摘要，非 OpenHuman 二进制

---

## 7. 验收

- [ ] bind 拿到 JWT，push 10 chunks 可在 Qdrant 查到 `source=openhuman`
- [ ] 错误 JWT 401
- [ ] `allow_memory_push=false` 403
- [ ] backend 镜像构建无 OpenHuman 文件

---

## 8. 分 PR（仅 Titan 主仓）

| PR | 内容 |
|----|------|
| M04-a | bindings 表 API + JWT util |
| M04-b | memory-push → pipeline |
| M04-c | compose.example + 运维说明 |

侧车补丁在 **GPL 仓库** 独立 PR。
