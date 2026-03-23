现在已经可以把现有 AI 直接接进微信了

如果你最近在看 OpenClaw（龙虾）、Claude Code、Codex 这类产品，应该已经发现一个很现实的问题：

这些 AI 工具本身越来越强，但真正给人用的时候，入口还是不够顺。

网页能用。
终端能用。
API 能用。

但很多用户最终还是会问一句：

**能不能直接在微信里用？**

这次想说的，就是这件事现在已经可以这样做了：

**把现有 AI 服务直接接进微信。**

不是再做一个聊天产品。
不是再做一个 App。
而是把你已经跑着的 AI，直接放到微信这个入口里去用。

而且关键点不只是热门产品能接。

OpenClaw（龙虾）能接。
Claude Code 能接。
Codex 能接。

更重要的是：
**你自己做的 AI 产品，也能接。**

这件事为什么重要？

因为很多时候，真正卡住产品使用的，不是模型能力，而是入口。

用户不想再打开一个网页。
不想再装一个 App。
也不想记一个新的域名。

他们更愿意直接在微信里发一句话，然后拿到结果。

比如下面这个场景：

一个投研 AI 被接进微信之后，用户在对话里直接问上周 A 股资金往哪个方向集中，AI 不只是回一段话，而是直接给出结构化分析、策略回测结果，甚至把 CSV 文件一起发回来。

👉 [在此插入截图：docs/demo-screenshot.png] 👈

这件事背后的接法也很直接。

如果你的 AI 已经有 HTTP 接口，一条命令就能接到微信：

```bash
pip install ai4wechat
ai4wechat-serve --target-url http://你的服务地址/chat
```

扫码之后，链路就是：

```text
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

它真正有价值的地方，不是“支持某个产品”，而是把一类产品的使用方式打开了：

- 热门 AI 工具能接
- 通用 AI 服务能接
- 你自己做的 AI 产品也能接

功能上，它把最麻烦的几件事一起处理了：

- 微信消息和现有服务之间的桥接
- 大模型 Markdown 输出自动转成微信可读格式
- 超长消息自动分段
- 服务器上远程扫码登录
- 凭证保存，重启不用重新扫

GitHub: github.com/yoligehude14753/ai4wechat

MIT 开源。
