import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from chinese_calendar import is_workday


FEISHU_WEBHOOK = (
    "https://open.feishu.cn/open-apis/bot/v2/hook/"
    "96ab3d4f-7ddd-4d43-8002-3ef94ca2659d"
)
TIANAPI_KEY = os.environ.get("TIANAPI_KEY")

FALLBACK_MESSAGES = [
    "今天辛苦了。工作是生活的一部分，但不是全部，今晚好好休息。",
    "今天的事先告一段落，明天的烦恼明天再说。先好好吃顿饭。",
    "数据、素材和账户都先放一放，今天的你已经很努力了。",
    "不管今天顺不顺，能坚持到下班就值得给自己一点掌声。",
    "工作可以明天继续，今晚的时间先留给自己。",
]

ENDINGS = [
    "🌙 今晚属于你自己",
    "🍜 好好吃顿饭",
    "🎵 来点音乐放松一下",
    "📵 可以暂时放下工作消息了",
    "🛋️ 找个舒服的姿势放松一下",
    "🌙 关掉屏幕，享受今晚",
    "🍵 泡杯茶，什么都不想",
    "🌙 今晚不谈工作",
    "🎮 玩一会儿，别卷了",
    "🌙 好好睡一觉",
]


def get_work_quote(fallback):
    if not TIANAPI_KEY:
        print("未配置 TIANAPI_KEY，使用备用文案")
        return fallback

    try:
        response = requests.get(
            "https://apis.tianapi.com/dgryl/index",
            params={"key": TIANAPI_KEY},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 200:
            print(f"语录接口返回错误：{data.get('code')} {data.get('msg')}")
            return fallback

        content = data.get("result", {}).get("content", "").strip()
        if not content or len(content) > 100:
            print("语录为空或过长，使用备用文案")
            return fallback

        return content

    except (requests.RequestException, ValueError, TypeError) as error:
        print(f"获取语录失败，使用备用文案：{error}")
        return fallback


def build_card():
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    today = now.date()

    if not is_workday(today):
        print("今日非工作日，跳过推送")
        return None

    day_index = now.timetuple().tm_yday
    fallback = FALLBACK_MESSAGES[day_index % len(FALLBACK_MESSAGES)]
    body = get_work_quote(fallback)
    ending = ENDINGS[day_index % len(ENDINGS)]

    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday_str = weekdays[now.weekday()]
    date_str = today.strftime("%Y年%m月%d日")

    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🌆 下班啦，今天辛苦了",
                },
                "template": "purple",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**{date_str}　{weekday_str}　19:00**\n\n"
                            f"{body}"
                        ),
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": ending,
                    },
                },
            ],
        },
    }


def send_to_feishu(card):
    try:
        response = requests.post(FEISHU_WEBHOOK, json=card, timeout=10)
        response.raise_for_status()

        result = response.json()
        if result.get("code", result.get("StatusCode", 0)) != 0:
            raise RuntimeError(f"飞书返回错误：{result}")

        print("飞书下班卡片推送成功")

    except (requests.RequestException, ValueError, RuntimeError) as error:
        print(f"飞书推送失败：{error}")
        sys.exit(1)


card = build_card()
if card is not None:
    send_to_feishu(card)
print("完成")
