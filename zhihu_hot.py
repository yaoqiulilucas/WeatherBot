import requests
import sys
from datetime import datetime
import xml.etree.ElementTree as ET

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/96ab3d4f-7ddd-4d43-8002-3ef94ca2659d"

def get_zhihu_hot():
      url = "https://rsshub.app/zhihu/hotlist"
      headers = {"User-Agent": "Mozilla/5.0"}
      try:
          res = requests.get(url, headers=headers, timeout=15)
          print(f"状态码: {res.status_code}")
          root = ET.fromstring(res.text)
          channel = root.find("channel")
          items = channel.findall("item")
          result = []
          for item in items[:5]:
              title = item.findtext("title", "").strip()
              link = item.findtext("link", "").strip()
              result.append({"title": title, "url": link, "hot": ""})
          return result
      except Exception as e:
          print(f"知乎热榜请求失败: {e}")
          return None

def build_card(items):
      now = datetime.utcnow()
      beijing_hour = (now.hour + 8) % 24
      time_str = f"{beijing_hour:02d}:00"

      content_lines = []
      for i, item in enumerate(items, 1):
          content_lines.append(f"**{i}. [{item['title']}]({item['url']})**")

      card = {
          "msg_type": "interactive",
          "card": {
              "config": {"wide_screen_mode": True},
              "header": {
                  "title": {"tag": "plain_text", "content": f"🔥 知乎热榜 · {time_str}"},
                  "template": "red"
              },
              "elements": [
                  {
                      "tag": "div",
                      "text": {
                          "tag": "lark_md",
                          "content": "\n".join(content_lines)
                      }
                  },
                  {"tag": "hr"},
                  {
                      "tag": "div",
                      "text": {
                          "tag": "lark_md",
                          "content": "📡 数据来源：知乎热榜实时更新"
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

items = get_zhihu_hot()
if not items:
      print("获取知乎热榜失败")
      sys.exit(1)

card = build_card(items)
send_to_feishu(card)
print("完成")
  
