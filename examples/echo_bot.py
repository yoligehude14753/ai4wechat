"""Simplest possible bot — echoes everything back."""

from ai4wechat import Bot

bot = Bot()


@bot.on_message
async def handle(msg):
    return f"You said: {msg.text}"


@bot.on_login
def ready():
    print("Echo bot is online!")


bot.run()
