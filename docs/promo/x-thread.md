Tweet 1:

I open-sourced ai4wechat — a bridge that makes existing AI services usable inside WeChat.

If your AI has an HTTP endpoint:

pip install ai4wechat
ai4wechat-serve --target-url http://your-service/chat

Scan QR code. Your AI now works inside WeChat conversations.

github.com/yoligehude14753/ai4wechat

[attach demo-screenshot.png]

---

Tweet 2:

How it works:

User sends message in WeChat → ai4wechat forwards as JSON to your service → your service responds → reply appears in WeChat.

Your service sees: {"text": "user message", "conversation_id": "..."}
Returns: {"text": "response"}

No changes to your existing service.

---

Tweet 3:

Things I had to solve:

- LLM Markdown doesn't render in WeChat → auto-convert headings, bold, code blocks, tables to plain text
- WeChat message limit ~4KB → auto-split at paragraph boundaries with page numbers
- Session expiry → auto-detect + prompt re-scan
- Typing indicator while AI processes

---

Tweet 4:

Also works as embedded Python SDK:

from ai4wechat import Bot

bot = Bot()

@bot.on_message
async def handle(msg):
    return call_your_ai(msg.text)

bot.run()

MIT license. pip install ai4wechat.

github.com/yoligehude14753/ai4wechat

---

Chinese reply (under tweet 1):

做了个开源工具 ai4wechat，让你现有的 AI 服务可以直接在微信里被使用。

一条命令 + 扫码，你的服务不用改。大模型输出的 Markdown 自动转成微信能读的格式。

GitHub 搜 ai4wechat。
