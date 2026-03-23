ai4wechat — 让你的 AI 产品在微信里被使用

开源了一个工具叫 ai4wechat。

它做一件事：把你现有的 AI 服务接到微信里，让用户在微信对话中直接使用你的 AI。

你的 AI 已经有 HTTP 接口了？一条命令就能接到微信：

```
pip install ai4wechat
ai4wechat-serve --target-url http://你的服务地址/chat
```

扫码就完成了。用户在微信里发消息，你的 AI 回复。

👉 [在此插入截图：docs/demo-screenshot.png] 👈

你的服务不需要做任何修改。ai4wechat 在中间做桥接：

```
微信用户 → 发消息 → ai4wechat → 转发给你的服务
微信用户 ← 收回复 ← ai4wechat ← 你的服务返回
```

如果你的 AI 是 Python 写的，也可以直接嵌入：

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

功能：
- HTTP 桥接模式 + Python SDK 模式
- 大模型 Markdown 输出自动转成微信纯文本
- 超长消息自动分段带页码
- 服务器部署支持远程 Web 扫码
- 凭证持久化，重启不用重新扫

适用：ChatGPT 封装、Claude 应用、客服 AI、内部知识库、LangChain Agent、任何有 HTTP 接口的 AI 服务。

GitHub: github.com/yoligehude14753/ai4wechat

MIT 开源，欢迎 Star。
