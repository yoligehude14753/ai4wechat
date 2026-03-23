现在已经可以把现有 AI 直接接进微信了。

而且重点不是只有 OpenClaw（龙虾）、Claude Code、Codex 这些热门产品能这样用。
你自己做的 AI 产品，也能接。

这件事真正值得说的，不是“又多了一个开发工具”，而是以前很多原来只能在网页、终端或者 API 里用的 AI，现在已经可以直接放进微信里。

用户不需要换入口。
你也不需要重新做一个新产品。

比如下面这个案例：

一个投研 AI 被接进微信之后，用户先问“上周 A 股资金往哪个方向集中”，它直接回板块扫描和资金分析；继续追问“算力这条线能不能做轮动策略”，它又继续给出策略回测、CSV 文件和后续操作建议。

👉 [在此插入截图：docs/demo-screenshot-1.png 和 docs/demo-screenshot-2.png] 👈

这个案例最重要的点，不是“投研 AI 很强”，而是：
这种本来已经跑起来的专业 AI 服务，现在已经可以在微信里直接被使用。

而且不只是少数热门工具：
- OpenClaw（龙虾）能接
- Claude Code 能接
- Codex 能接
- 你自己做的聊天助手、知识库问答、客服 AI、投研工具、工作流 Agent，也都能接

如果你的 AI 已经有 HTTP 接口，一条命令就能接到微信：

```bash
pip install ai4wechat
ai4wechat-serve --target-url http://你的服务地址/chat
```

如果你的 AI 是 Python 写的，也可以直接嵌进去：

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

它真正打开的是一类产品的新入口：
- 热门 AI 工具能接进微信
- 通用 AI 服务能接进微信
- 你自己做的 AI 产品，也能接进微信

GitHub: github.com/yoligehude14753/ai4wechat

MIT 开源。
