让你的 AI 在微信里直接用

做了个开源工具 ai4wechat。

解决的问题：你有一个 AI 服务在跑，怎么让用户在微信里直接用它，不用下 App 不用开网页。

用法很简单。你的 AI 服务有 HTTP 接口就行：

pip install ai4wechat
ai4wechat-serve --target-url http://你的AI服务/chat

扫码完成。微信里发消息，你的 AI 自动回复。

你的服务不用改。ai4wechat 在中间做桥接，把微信消息转成 JSON 发给你的服务，回复发回微信。

几个实用的点：
· 大模型输出的 Markdown 自动转成微信能正常显示的纯文本
· 超长回复自动分段带页码
· 处理消息时自动显示"对方正在输入中"
· 服务器部署用 --web 模式，浏览器扫码

如果你的 AI 是 Python 写的，也可以直接嵌入不走 HTTP。

GitHub 搜 ai4wechat，MIT 开源。

github.com/yoligehude14753/ai4wechat

#AI #微信 #开源 #大模型 #ChatGPT #开发者

配图：
图1（封面）：demo-screenshot.png
图2：README 截图
