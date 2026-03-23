Tweet 1:

Open-sourced ai4wechat — make your existing AI service usable inside WeChat.

Your AI already has an HTTP endpoint. ai4wechat bridges it to WeChat. Users send messages in WeChat, your AI responds.

pip install ai4wechat
ai4wechat-serve --target-url http://your-service/chat

Scan QR. Done.

github.com/yoligehude14753/ai4wechat

👉 [发推时点附件上传：docs/demo-screenshot.png] 👈

---

Tweet 2:

What it does:

· Forwards WeChat messages to your service as JSON
· Sends your service's response back to WeChat
· Auto-converts LLM Markdown to WeChat-readable text
· Splits long messages with page numbers
· Shows typing indicator while AI processes
· Web login mode for remote servers

Your service needs zero changes.

---

Tweet 3:

Two integration modes:

HTTP bridge — for any AI with an HTTP endpoint
Python SDK — embed directly with @bot.on_message decorator

MIT license. pip install ai4wechat.

github.com/yoligehude14753/ai4wechat

---

Chinese reply (under tweet 1):

开源了 ai4wechat，让你现有的 AI 服务直接在微信里被使用。

你的服务有 HTTP 接口就行，不用改。安装，扫码，用户在微信里就能用你的 AI。

github.com/yoligehude14753/ai4wechat
