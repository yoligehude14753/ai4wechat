# 让你的 AI 在微信里直接用

> 发布平台：小红书
> 封面：终端 ai4wechat-serve + 微信 AI 对话并排截图
> 图片数量：3 张

---

## 正文

做了个开源工具 ai4wechat。

解决的问题：你有一个 AI 服务在跑，怎么让用户在微信里直接用它，不用下 App 不用开网页。

用法很简单。你的 AI 服务有 HTTP 接口就行：

```
pip install ai4wechat
ai4wechat-serve --target-url http://你的AI服务/chat
```

扫码完成。微信里发消息，你的 AI 自动回复。

你的服务不用改。ai4wechat 在中间做桥接，把微信消息转成 JSON 发给你的服务，回复发回微信。

几个实用的点：
- 大模型输出的 Markdown 自动转成微信能正常显示的纯文本
- 超长回复自动分段带页码
- 处理消息时自动显示"对方正在输入中"
- 服务器部署用 --web 模式，浏览器扫码
- 支持文本、链接、emoji，图片和文件发送在路线图中

如果你的 AI 是 Python 写的，也可以直接嵌入不走 HTTP：

```python
from ai4wechat import Bot
from openai import OpenAI

bot = Bot()
ai = OpenAI()

@bot.on_message
async def handle(msg):
    r = ai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": msg.text}]
    )
    return r.choices[0].message.content

bot.run()
```

GitHub 搜 ai4wechat，MIT 开源。

---

#AI #微信 #开源 #大模型 #ChatGPT #开发者

---

## 配图说明

**图1（封面）：** 终端 ai4wechat-serve 运行 + 微信 AI 对话并排

**图2：** 微信里 3 轮 AI 对话，展示格式化后的干净排版（对比 raw Markdown）

**图3：** SDK 模式代码截图
