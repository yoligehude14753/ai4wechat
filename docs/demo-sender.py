#!/usr/bin/env python3
"""
截图工具 — 用微信 Bot 账号发送预设回复。
不停 Yoli，不影响其他服务。
Yoli 会自动回复一条（微信里长按删掉），然后你按回车发预设内容。
"""

import asyncio
import os
import struct
import base64

import httpx

TOKEN = "64c8fd61ebba@im.bot:06000027d95de651fda0b8b76c30d9871f51bc"
BASE_URL = "https://ilinkai.weixin.qq.com"
CHANNEL_VERSION = "0.1.0"

USER_ID = None
CONTEXT_TOKEN = None

SCRIPT = [
    # 第1条：用户问资金方向后的回复
    (
        "扫了一遍行业和概念板块，本周资金最集中的方向是算力基础设施。\n\n"
        "三条线同时放量：\n\n"
        "· 算电协同 — 协鑫能科5天3板、累计涨50%，华电能源4连板涨33%。"
        "驱动是"算电协同"首次写入今年政府工作报告，叠加协鑫能科旗下蚂蚁鑫能虚拟电厂落地、可调负荷690MW\n"
        "· 算力租赁 — 拓维信息2连板，润泽科技绑定字节跳动、智算上架率超90%。"
        "板块逻辑是GPU租赁价格企稳+头部厂商业绩预告大幅超预期（润泽科技净利预增179%-196%，拓维信息预增149%-174%）\n"
        "· 智算中心 — 优刻得3月20日公告定增募资15亿建乌兰察布智算中心，"
        "云赛智联签约上海市智能算力资源统筹调度平台\n\n"
        "另外两个有异动的：\n"
        "· 机器人 — 宇树科技3月20日科创板IPO获受理，募资42亿，2025年营收17亿同比增335%、"
        "扣非净利6亿增674%。板块联动但分化，注意区分整机和零部件\n"
        "· 化工 — 金牛化工近20日涨115%、近10日6个涨停板，甲醇涨价驱动。"
        "但公司自己都发了风险提示，PE 199倍，前三季度净利还同比降了7.5%"
    ),

    # 第2条：用户问轮动策略后的回复
    (
        "用算力产业链相关ETF做板块轮动。\n\n"
        "策略设计：\n"
        "· 标的池：算力设备/电力/通信/计算机/人工智能5只行业ETF\n"
        "· 轮动信号：20日调整动量（区间收益率÷区间波动率），周频调仓\n"
        "· 持仓：选动量排名前2的ETF等权持有，跌出前3换仓\n"
        "· 风控：单标的回撤超20%触发止损\n\n"
        "回测区间：2025-03-24 至 2026-03-21\n\n"
        "结果：\n"
        "· 年化收益：34.6%（同期沪深300 +4.2%）\n"
        "· 最大回撤：-27.8%（2025年8月市场系统性调整）\n"
        "· 年化波动率：29.1%\n"
        "· 夏普比率：1.10（按无风险利率2.5%计）\n"
        "· Calmar比率：1.24\n"
        "· 月均换手：1.8次\n\n"
        "超额主要来自两段：2025Q4算力硬件周期启动，以及2026Q1算电协同政策催化。"
        "8月那波回撤比较深，主要是跟着大盘调整，9月底恢复。\n\n"
        "脚本已封装，可以每天盘前自动跑一次，把当日操作建议推到这里。要部署吗？"
    ),

    # 第3条：用户说"部署"后的回复
    "好了，每个交易日早上8:30自动执行，结果直接推到这个对话。",
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
    if data.get("ret", 0) != 0:
        print(f"  ⚠ ret={data.get('ret')}")
    return data


async def main():
    global USER_ID, CONTEXT_TOKEN

    print()
    print("=" * 50)
    print("  ai4wechat 截图工具")
    print("=" * 50)
    print()
    print(f"  共 {len(SCRIPT)} 条预设回复")
    print()
    print("  操作流程：")
    print("  1. 你在手机微信里发消息")
    print("  2. Yoli 会自动回复（长按删掉）")
    print("  3. 回到这里按回车 → 发送预设回复")
    print("  4. 手机截图")
    print()
    print("-" * 50)

    async with httpx.AsyncClient() as client:

        # 获取 user_id
        print()
        print("  先给 Bot 发一条任意消息（比如"你好"）")
        input("  发完后按回车...")
        print("  获取中...")

        sync_buf = ""
        found = False
        for _ in range(5):
            data = await poll_once(client, sync_buf)
            if data.get("get_updates_buf"):
                sync_buf = data["get_updates_buf"]
            for msg in data.get("msgs", []):
                if msg.get("message_type") == 1:
                    USER_ID = msg.get("from_user_id", "")
                    CONTEXT_TOKEN = msg.get("context_token", "")
                    found = True
                    break
            if found:
                break

        if not found:
            print("  ✗ 没收到消息，重试")
            return

        print(f"  ✓ 已获取")
        print()
        print("=" * 50)
        print("  开始截图流程")
        print("=" * 50)
        print()

        # 逐条发送
        steps = [
            "手机发：帮我看下本周A股资金在往哪个方向集中\n  → Yoli 回复后长按删掉，然后回来按回车",
            "手机发：算力这条线能做个轮动策略吗 回测看看\n  → Yoli 回复后长按删掉，然后回来按回车",
            "手机发：部署\n  → Yoli 回复后长按删掉，然后回来按回车",
        ]

        for i, (step, reply_text) in enumerate(zip(steps, SCRIPT)):
            print(f"  [{i+1}/{len(SCRIPT)}]")
            print(f"  {step}")
            print()

            cmd = input("  按回车发送预设回复 (q=退出): ").strip().lower()
            if cmd == 'q':
                break

            await send(client, USER_ID, reply_text, CONTEXT_TOKEN)
            print("  ✓ 已发送")
            print()

        print()
        print("  全部完成！去手机截图。")
        print("  Yoli 的自动回复如果还在，长按删掉。")


if __name__ == "__main__":
    asyncio.run(main())
