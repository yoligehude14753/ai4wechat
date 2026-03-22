# ai4wechat

让你的 AI 产品在微信中被使用。

ai4wechat 架在你的 AI 服务和微信之间。用户在微信对话里发消息，你的 AI 回复 — 不需要做新 App，不需要新前端。两种接入方式：指向现有 HTTP 接口，或嵌入 Python 代码。

[English](README.md) · [![PyPI](https://img.shields.io/pypi/v/ai4wechat.svg)](https://pypi.org/project/ai4wechat/) · [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 快速开始

### 接入现有 AI 服务（HTTP 桥接）

```bash
pip install ai4wechat
ai4wechat-serve --target-url http://localhost:8000/chat
```

微信扫码。消息会转发给你的服务，回复自动发回微信。

### 嵌入 Python 应用

```bash
pip install ai4wechat
```

```python
from ai4wechat import Bot
from openai import OpenAI

bot = Bot()
ai = OpenAI()

@bot.on_message
async def handle(msg):
    r = ai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": msg.text}],
    )
    return r.choices[0].message.content

bot.run()
```

## HTTP 桥接工作原理

```mermaid
sequenceDiagram
    participant Service as 你的 AI 服务
    participant Bridge as ai4wechat
    participant User as 微信用户

    User->>Bridge: 在微信里发消息
    Bridge->>Service: POST {"text": "...", "conversation_id": "..."}
    Service-->>Bridge: {"text": "AI 回复"}
    Bridge->>Bridge: Markdown 格式化
    Bridge->>User: 在微信里回复
```

你的服务收到的 JSON：

```json
{
  "message_id": "123456",
  "conversation_id": "user_abc",
  "user_id": "user_abc",
  "text": "今天天气怎么样？",
  "type": "text",
  "timestamp": "2026-03-23T10:00:00+00:00",
  "session_id": "sess_xyz"
}
```

你的服务返回：

```json
{
  "text": "上海今天 22°C，晴天。"
}
```

`conversation_id` 按用户稳定，可用于维护对话历史。响应字段接受 `text`、`reply` 或 `message`。

## 它帮你处理什么

**Markdown 转微信格式** — 大模型输出 Markdown，微信显示为原始符号。ai4wechat 自动把标题转成【Title】、去掉加粗斜体标记、代码块用 ---- 分隔、表格转成列表。默认开启。

**长消息分段** — 超过微信 ~4KB 限制的消息在段落边界分段，带页码 (1/3)、(2/3) 等。

**输入状态** — AI 处理消息时自动显示"对方正在输入中"。

**会话管理** — 扫码凭证保存到 `~/.ai4wechat/`，重启复用。会话过期自动检测并提示重新扫码。

**断线重连** — 网络中断自动指数退避重试。

## 支持的消息类型

| 类型 | 接收 | 发送 | 状态 |
|---|---|---|---|
| 文本 | 支持 | 支持 | 稳定 |
| 图片 | 支持（元数据） | 规划中 | CDN 上传协议已验证 |
| 文件 | 支持（元数据） | 规划中 | CDN 上传协议已验证 |
| 语音 | 支持（元数据） | 规划中 | — |
| 视频 | 支持（元数据） | 规划中 | — |
| URL / 链接 | — | 支持（文本内） | 微信自动识别 |
| Emoji | — | 支持（文本内） | 完全支持 |

文本消息已可用于生产。图片和文件发送的 CDN 上传协议已验证，在路线图中。

## 已知限制

- **用户必须先发消息** — 不能主动给没发过消息的用户推送（微信需要来自首条入站消息的 `context_token`）
- **会话会过期** — 需要定期重新扫码（自动检测，会记录日志）
- **目前仅文本** — 媒体发送协议已验证但 SDK 尚未实现
- **仅一对一** — 暂不支持群聊

## 远程服务器部署

在无法扫终端二维码的服务器上：

```bash
ai4wechat-serve --target-url http://localhost:8000/chat --web --port 18891
```

浏览器打开 `http://服务器IP:18891` 扫码。凭证持久化到会话过期。

## 命令行参考

```bash
ai4wechat-serve --target-url <url>                     # 启动桥接
ai4wechat-serve --target-url <url> --web --port 18891  # 桥接 + Web 登录
ai4wechat-serve --target-url <url> --timeout 180       # 慢模型超时
ai4wechat-serve --target-url <url> --no-format         # 跳过 Markdown 转换
ai4wechat-login                                         # 仅登录
ai4wechat-login --web --port 18891                      # Web 登录
```

## Python API

```python
from ai4wechat import Bot, serve, format_for_wechat, truncate_for_wechat

# HTTP 桥接
serve("http://localhost:8000/chat", timeout=120, web_login=False)

# SDK 模式
bot = Bot(token_dir="~/.ai4wechat", auto_format=True)

@bot.on_message
async def handle(msg):
    return "reply"        # 返回字符串回复，None 跳过

@bot.on_login
def ready():
    print("已连接")

bot.run()

# 单独使用格式化
clean = format_for_wechat(markdown_text)
chunks = truncate_for_wechat(long_text, max_bytes=3900)
```

### Message 对象

```python
msg.id         # str
msg.text       # str
msg.sender     # str — 用户 ID，同 conversation_id
msg.type       # MessageType — text / image / voice / file / video
msg.timestamp  # datetime
msg.session_id # str
msg.raw        # dict
```

## 安装

```bash
pip install ai4wechat                  # 核心
pip install 'ai4wechat[qrcode]'        # + 终端二维码显示
pip install 'ai4wechat[web]'           # + Web 登录模式
pip install 'ai4wechat[all]'           # 全部
```

Python 3.10+。

## 贡献

欢迎 Issue 和 Pull Request。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 致谢

协议研究和核心 SDK 模式来自 [@epiral](https://github.com/epiral) 的 [weixin-bot](https://github.com/epiral/weixin-bot)。

## 协议

[MIT](LICENSE)
