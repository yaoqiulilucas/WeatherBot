import requests
import sys
from datetime import datetime

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/96ab3d4f-7ddd-4d43-8002-3ef94ca2659d"

def get_hn_hot():
      try:
          ids_res = requests.get(
              "https://hacker-news.firebaseio.com/v0/topstories.json",
              timeout=10
          )
          ids = ids_res.json()[:5]
          result = []
          for item_id in ids:
              item_res = requests.get(
                  f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
                  timeout=10
              )
              item = item_res.json()
              title = item.get("title", "")
              url = item.get("url", f"https://news.ycombinator.com/item?id={item_id}")
              score = item.get("score", 0)
              result.append({"title": title, "url": url, "score": score})
          return result
      except Exception as e:
          print(f"HackerNews 请求失败: {e}")
          return None

def build_card(items):
      now = datetime.utcnow()
      beijing_hour = (now.hour + 8) % 24
      time_str = f"{beijing_hour:02d}:00"

      content_lines = []
      for i, item in enumerate(items, 1):
          content_lines.append(f"**{i}. [{item['title']}]({item['url']})**")
          content_lines.append(f"⬆️  {item['score']} points")

      card = {
          "msg_type": "interactive",
          "card": {
              "config": {"wide_screen_mode": True},
              "header": {
                  "title": {"tag": "plain_text", "content": f"🔥 HackerNews 热榜 · {time_str}"},
                  "template": "red"
              },
              "elements": [
                  {
                      "tag": "div",
                      "text": {"tag": "lark_md", "content": "\n".join(content_lines)}
                  },
                  {"tag": "hr"},
                  {
                      "tag": "div",
                      "text": {"tag": "lark_md", "content": "📡 数据来源：Hacker News Top Stories"}
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

items = get_hn_hot()
if not items:
      sys.exit(1)

card = build_card(items)
send_to_feishu(card)
print("完成")

