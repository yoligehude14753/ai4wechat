怎么让现有的 AI 服务在微信里被使用

最近在做一个场景：AI 服务做好了，API 跑着，用户说能不能在微信里直接用。

这个需求很常见。你有一个 ChatGPT 封装、一个内部知识库问答、一个客服 AI，用户不想开浏览器或装 App，就想在微信对话里直接问。

问题是怎么接。

## 碰到的几个坑

**Markdown 格式问题**。大模型输出里全是 `##`、`**`、三个反引号。微信不渲染 Markdown，用户看到的是一堆原始符号。必须在发送前做一层转换。

**长消息截断**。微信单条消息上限约 4KB，大模型经常输出超过这个长度的内容。需要在段落边界做分段，不能从句子中间切开。

**不能主动推送**。用户必须先发一条消息，你才能回复。这是协议层面的限制，每条入站消息带一个 context_token，回复必须携带这个 token。

**会话会过期**。登录凭证有有效期，过期后需要重新扫码。

这些问题单独看都不大，但组合在一起挺烦的。

## 做了一个开源工具

做了 ai4wechat，专门解决这个问题。核心思路是做一个桥接层，你的 AI 服务不用改任何代码。

大多数 AI 服务已经有 HTTP 接口了。ai4wechat 作为中间层，把微信消息转发过去：

```
pip install ai4wechat
ai4wechat-serve --target-url http://localhost:8000/chat
```

扫码后的工作流程：

```
微信用户 → 发消息 → ai4wechat → POST JSON 到你的服务
微信用户 ← 收回复 ← ai4wechat ← 你的服务返回文本
```

你的服务收到的请求：

```json
{
  "conversation_id": "user_xxx",
  "text": "帮我总结一下这篇文章",
  "type": "text"
}
```

返回：

```json
{"text": "这篇文章主要讲了..."}
```

conversation_id 按用户稳定，你可以在服务端基于它做多轮对话。你的 AI 服务完全不知道用户是从微信来的还是从网页来的，它只看到一个标准的 HTTP 请求。

如果你的 AI 逻辑是 Python 写的，也可以直接嵌入：

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

实际使用效果：

[图片：demo-screenshot.png]

## 格式化怎么做的

ai4wechat 在发送前自动处理 Markdown：

- `## 标题` → 【标题】
- `**加粗**` → 加粗（去星号）
- 代码块用 ---- 分隔线包裹
- 表格转成键值列表
- 超长消息按段落分段，带页码

默认开启。如果你的服务已经输出纯文本了，用 --no-format 关掉。

## 部署

本地扫终端二维码。服务器上用 Web 登录：

```
ai4wechat-serve --target-url http://localhost:8000/chat --web --port 18891
```

浏览器打开服务器IP:18891 扫码。凭证保存后不用重复扫。

HTTP 超时默认 120 秒。推理慢的模型可以 --timeout 300 调大。

## 项目地址

GitHub: https://github.com/yoligehude14753/ai4wechat

```
pip install ai4wechat
```

MIT 协议。
