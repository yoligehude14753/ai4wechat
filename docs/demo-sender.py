#!/usr/bin/env python3
"""
Demo screenshot helper — send scripted responses from the WeChat bot.

Does NOT poll messages. Does NOT interfere with Yoli.
You manually trigger each response by pressing Enter.

Usage:
  python3 demo-sender.py

Flow:
  1. You send a message from your phone to the bot
  2. Yoli replies with its AI response (ignore it, or delete it from chat)
  3. You come back here, press Enter to send the next scripted reply
  4. The scripted reply appears in WeChat from the same bot account
  5. Screenshot — crop out Yoli's auto-reply if needed
"""

import asyncio
import os
import struct
import base64

import httpx

TOKEN = "64c8fd61ebba@im.bot:06000027d95de651fda0b8b76c30d9871f51bc"
BASE_URL = "https://ilinkai.weixin.qq.com"
CHANNEL_VERSION = "0.1.0"

# The user's WeChat ID — will be captured from first incoming message
USER_ID = None
CONTEXT_TOKEN = None

SCRIPT = [
    "收到 我来写",
    "初稿完成",
    "306页 150条逐项响应\n18处标了[待补充] 等你补材料",
    (
        "收到 8份 已分配：\n"
        "· 权限管理 → 1.2.3\n"
        "· 3D点云 → 2.1.1\n"
        "· 效率看板 → 2.2.8\n"
        "· OCC数据 → 2.1.3\n"
        "· ISO证书 → 1.2.2\n\n"
        "还差2张 20分钟出修订版"
    ),
    "312页 完成度94%",
    "提醒：4月15号截止 还有13天\n还差2张图 补了我30分钟出终稿",
    "314页 150条 全部完成 ✓",
]


def _random_uin():
    num = struct.unpack(">I", os.urandom(4))[0]
    return base64.b64encode(str(num).encode()).decode()


def _headers():
    return {
        "Content-Type": "application/json",
        "AuthorizationType": "ilink_bot_token",
        "X-WECHAT-UIN": _random_uin(),
        "Authorization": f"Bearer {TOKEN}",
    }


async def poll_once(client, sync_buf=""):
    """Single poll to capture user_id and context_token."""
    resp = await client.post(
        f"{BASE_URL}/ilink/bot/getupdates",
        json={"get_updates_buf": sync_buf, "base_info": {"channel_version": CHANNEL_VERSION}},
        headers=_headers(),
        timeout=40.0,
    )
    return resp.json()


async def send(client, to_user_id, text, context_token):
    body = {
        "msg": {
            "from_user_id": "",
            "to_user_id": to_user_id,
            "client_id": f"demo-{os.urandom(4).hex()}",
            "message_type": 2,
            "message_state": 2,
            "item_list": [{"type": 1, "text_item": {"text": text}}],
            "context_token": context_token,
        },
        "base_info": {"channel_version": CHANNEL_VERSION},
    }
    resp = await client.post(
        f"{BASE_URL}/ilink/bot/sendmessage",
        json=body,
        headers=_headers(),
        timeout=15.0,
    )
    data = resp.json()
    ret = data.get("ret", 0)
    if ret != 0:
        print(f"  ⚠ sendmessage ret={ret}")
    return data


async def main():
    global USER_ID, CONTEXT_TOKEN

    print("=" * 50)
    print("ai4wechat Demo — 截图发送工具")
    print("=" * 50)
    print()
    print("Yoli 不受影响，正常运行。")
    print("本工具只负责发送预设回复。")
    print()
    print(f"共 {len(SCRIPT)} 条预设回复：")
    for i, s in enumerate(SCRIPT):
        preview = s.replace('\n', ' ')[:50]
        print(f"  [{i+1}] {preview}...")
    print()

    async with httpx.AsyncClient() as client:

        # Step 1: Capture user_id and context_token
        print("-" * 50)
        print("第1步：从你的手机给 Bot 发任意一条消息")
        print("       （用来获取你的 user_id 和 context_token）")
        print()
        input("       发完消息后按回车...")
        print()
        print("正在获取...")

        sync_buf = ""
        found = False
        for attempt in range(5):
            data = await poll_once(client, sync_buf)
            if data.get("get_updates_buf"):
                sync_buf = data["get_updates_buf"]

            for msg in data.get("msgs", []):
                if msg.get("message_type") == 1:
                    USER_ID = msg.get("from_user_id", "")
                    CONTEXT_TOKEN = msg.get("context_token", "")
                    items = msg.get("item_list", [])
                    text = ""
                    for item in items:
                        if item.get("type") == 1 and item.get("text_item"):
                            text = item["text_item"].get("text", "")
                    print(f"  ✓ 收到消息: {text[:60]}")
                    print(f"  ✓ user_id: {USER_ID[:30]}...")
                    print(f"  ✓ context_token: {CONTEXT_TOKEN[:30]}...")
                    found = True
                    break
            if found:
                break
            print(f"  等待中... ({attempt+1}/5)")

        if not found:
            print("  ✗ 没有收到消息。确认你发了消息后重试。")
            return

        print()
        print("=" * 50)
        print("准备就绪！现在开始发送预设回复。")
        print()
        print("操作方式：")
        print("  1. 先在手机微信里发你的消息（按对话脚本）")
        print("  2. Yoli 会自动回复（忽略它，截图时裁掉或删掉）")
        print("  3. 回到这里按回车 → 发送预设回复")
        print("  4. 手机上截图")
        print()
        print("输入 's' 跳过当前条")
        print("输入 'c' 自定义发送内容")
        print("输入 'q' 退出")
        print("=" * 50)
        print()

        # Step 2: Send scripted replies one by one
        for i, reply_text in enumerate(SCRIPT):
            preview = reply_text.replace('\n', ' / ')[:60]
            print(f"[{i+1}/{len(SCRIPT)}] 下一条回复:")
            print(f"  \"{preview}\"")
            print()

            cmd = input("  按回车发送 (s=跳过, c=自定义, q=退出): ").strip().lower()

            if cmd == 'q':
                print("退出")
                break
            elif cmd == 's':
                print("  → 已跳过")
                print()
                continue
            elif cmd == 'c':
                custom = input("  输入自定义内容: ").strip()
                if custom:
                    await send(client, USER_ID, custom, CONTEXT_TOKEN)
                    print("  ✓ 自定义回复已发送")
                print()
                continue

            await send(client, USER_ID, reply_text, CONTEXT_TOKEN)
            print("  ✓ 已发送到微信")
            print()

        print()
        print("全部完成！去手机上截图吧。")
        print("Yoli 的自动回复如果在截图范围内，长按删除即可。")


if __name__ == "__main__":
    asyncio.run(main())
