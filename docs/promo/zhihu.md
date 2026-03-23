开源 ai4wechat — 让你的 AI 产品在微信里被使用

做了一个开源项目，解决一个具体的问题：你有一个 AI 服务跑在服务器上，怎么让用户直接在微信里用它。

你的 AI 已经有 HTTP 接口了。ai4wechat 作为中间层，把微信消息转发给你的服务，把回复发回微信。你的服务不需要任何改动。

## 两种接入方式

**HTTP 桥接**：适合已有 HTTP 接口的 AI 服务

```
pip install ai4wechat
ai4wechat-serve --target-url http://localhost:8000/chat
```

扫码后，微信消息自动转发给你的服务，你的服务返回文本，用户在微信里收到回复。

**Python SDK**：适合 Python 原生项目

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

## 它做了什么

· 微信消息 → JSON 转发给你的服务 → 回复发回微信
· 大模型输出的 Markdown 自动转成微信能正常显示的纯文本
· 超长消息自动在段落边界分段，带页码
· 处理中自动显示"对方正在输入中"
· 服务器部署支持 Web 扫码登录
· 凭证保存，重启不用重新扫码

## 使用效果

👉 [在此插入截图：docs/demo-screenshot.png] 👈

## 如何使用

1. pip install ai4wechat
2. ai4wechat-serve --target-url http://你的服务地址/chat
3. 微信扫码
4. 用户在微信里发消息，你的 AI 回复

GitHub：github.com/yoligehude14753/ai4wechat

MIT 开源。
