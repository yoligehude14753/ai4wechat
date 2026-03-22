# ai4wechat Demo Recording Script

两套 demo 素材：一个短录屏（45 秒，用于 README 和社交媒体），一个场景截图组（用于配图）。

---

## 短录屏（45 秒）

展示 ai4wechat 的核心流程：安装 → 启动 → 扫码 → 微信里使用 AI。

### Scene 1 — Title (3s)

```
ai4wechat
Make your AI product usable inside WeChat
```

### Scene 2 — Install & Run (10s)

```bash
pip install ai4wechat
ai4wechat-serve --target-url http://localhost:8000/chat
```

QR code appears.

### Scene 3 — Scan (5s)

Split screen: terminal + phone scanning QR.

### Scene 4 — WeChat Conversation (22s)

Split screen: terminal logs (left) + WeChat (right).

展示 3-4 轮 AI 对话，使用真实场景（见下方场景截图）。

### Scene 5 — Closing (3s)

```
ai4wechat
pip install ai4wechat
github.com/ai4wechat/ai4wechat
```

---

## 场景截图组

使用 Yoli（AI 标书生成助手）作为 demo AI 服务，展示一个完整的专业工作流在微信里完成。

完整对话内容见 [demo-wechat-conversation.md](demo-wechat-conversation.md)。

### 截图 1 — 任务启动 + AI 结构化响应

用户在微信里发送标书需求 → Yoli 回复完整的章节框架、页数预估、所需材料清单。

用途：README 配图、小红书封面、X 推文配图。

### 截图 2 — 材料整合 + 智能修订

用户发送 8 份材料（证书、截图、案例、报价）→ Yoli 自动分类、发现缺失项、提出建议、交付修订版。

用途：知乎文章配图。

### 截图 3 — 主动跟进 + 时间管理

Yoli 在第三天主动提醒投标截止时间、列出待办和建议时间安排。

用途：展示 AI 不是一次性工具，而是持续的工作伙伴。

### 制作建议

- 使用真实微信聊天界面录制（手机投屏或模拟器）
- 对话内容从 demo-wechat-conversation.md 复制
- 所有公司名、人名、证书编号做脱敏处理
- 文件发送效果可以用微信发文件给自己来模拟
