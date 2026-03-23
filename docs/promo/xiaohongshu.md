开源 ai4wechat

让现有 AI 服务在微信里直接被使用。

你的 AI 产品已经有 HTTP 接口了，用户在网页或 API 上用着没问题。ai4wechat 把它接到微信里，用户在微信对话里发消息就能直接用你的 AI。

不用改你的服务，不用做新 App，不用做新前端。

两种接入方式：
· HTTP 桥接 — 指向你现有服务的 URL，ai4wechat 负责收发微信消息
· Python SDK — 用装饰器直接嵌入你的 Python 项目

自动处理大模型输出的 Markdown 格式问题（标题、加粗、代码块、表格都会转成微信能正常显示的纯文本）。超长消息自动分段带页码。

如何使用？

1. pip install ai4wechat
2. ai4wechat-serve --target-url http://你的服务地址/chat
3. 微信扫码
4. 用户在微信里发消息，你的 AI 回复

👉 [在此插入截图：docs/demo-screenshot.png] 👈

GitHub: github.com/yoligehude14753/ai4wechat
MIT 开源

#AI #微信 #开源 #大模型 #开发者工具
