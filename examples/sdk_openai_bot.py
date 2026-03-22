"""
SDK mode: embed ai4wechat directly in a Python AI app.

Use this approach when your AI logic is in Python and you want
to embed WeChat access directly in your codebase.
"""

from ai4wechat import Bot
from openai import OpenAI

bot = Bot()
ai = OpenAI()


@bot.on_message
async def handle(msg):
    response = ai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": msg.text}],
    )
    return response.choices[0].message.content


bot.run()
