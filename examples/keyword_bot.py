"""Keyword auto-reply bot — no AI, just pattern matching."""

from ai4wechat import Bot

bot = Bot()

REPLIES = {
    "hours": "We're open Mon-Fri, 9am-6pm.",
    "price": "See our pricing at example.com/pricing",
    "help": "Commands: hours, price, help",
}


@bot.on_message
async def handle(msg):
    text = msg.text.lower()
    for keyword, reply in REPLIES.items():
        if keyword in text:
            return reply
    return "Sorry, I didn't understand. Send 'help' for available commands."


bot.run()
