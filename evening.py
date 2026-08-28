import requests
import sys
from datetime import datetime, date
from chinese_calendar import is_workday

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/96ab3d4f-7ddd-4d43-8002-3ef94ca2659d"

MESSAGES = [
      ("今天辛苦了", "工作是生活的一部分，但不是全部。放下手头的事，好好休息。"),
      ("下班啦", "今天的事今天完成，明天的烦恼明天再说。先好好吃顿饭。"),
      ("收工了", "努力工作是为了更好地生活，别忘了今天也要善待自己。"),
      ("辛苦了，今天也很棒", "每一个认真工作的日子都算数。"),
      ("该休息了", "身体是革命的本钱，今晚好好充电。"),
      ("今天画上句号了", "不管今天顺不顺，能坚持到下班就是胜利。"),
      ("下班提醒", "工作告一段落，手机可以放一放，留点时间给自己和家人。"),
      ("今天也谢谢你了", "每一个平凡的工作日都是在积累，方向对了，慢慢也会到。"),
      ("打卡下班", "今天的数据、素材、账户都先放一放，明天继续。"),
      ("辛苦了", "投放的事交给系统跑，你先去休息。"),
]

ENDINGS = [
      "🌙 今晚属于你自己",
      "🍜 好好吃顿饭",
      "🎵 来点音乐放松一下",
      "📵 可以关掉工作群了",
      "🛋️  沙发、手机、随便",
      "🌙 关掉屏幕，享受今晚",
      "🍵 泡杯茶，什么都不想",
      "🌙 今晚不谈工作",
      "🎮 玩什么都行，别卷了",
      "🌙 好好睡一觉",
]

def build_card():
      now = datetime.utcnow()
      today = date(now.year, now.month, now.day)

      if not is_workday(today):
          print("今日非工作日，跳过推送")
          sys.exit(0)

      day_of_year = now.timetuple().tm_yday
      title, body = MESSAGES[day_of_year % len(MESSAGES)]
      ending = ENDINGS[day_of_year % len(ENDINGS)]

      weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
      weekday_str = weekdays[now.weekday()]
      date_str = today.strftime("%Y年%m月%d日")

      card = {
          "msg_type": "interactive",
          "card": {
              "config": {"wide_screen_mode": True},
              "header": {
                  "title": {"tag": "plain_text", "content": f"🌆 {title}"},
                  "template": "purple"
              },
              "elements": [
                  {
                      "tag": "div",
                      "text": {
                          "tag": "lark_md",
                          "content": (
                              f"**{date_str}　{weekday_str}　19:00**\n\n"
                              f"{body}"
                          )
                      }
                  },
                  {"tag": "hr"},
                  {
                      "tag": "div",
                      "text": {
                          "tag": "lark_md",
                          "content": ending
                      }
                  }
              ]
          }
      }
      return card

def send_to_feishu(card):
      try:
          res = requests.post(FEISHU_WEBHOOK, json=card, timeout=10)
          print(f"飞书响应: {res.status_code} {res.text}")
      except Exception as e:
          print(f"飞书推送失败: {e}")
          sys.exit(1)

card = build_card()
send_to_feishu(card)
print("完成")

