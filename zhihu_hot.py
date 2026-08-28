import requests
import sys
from datetime import datetime
import xml.etree.ElementTree as ET

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/96ab3d4f-7ddd-4d43-8002-3ef94ca2659d"

SOURCES = [
      {
          "name": "BBC 中文",
          "url": "http://feeds.bbci.co.uk/zhongwen/simp/rss.xml",
          "count": 3,
          "icon": "🌐"
      },
      {
          "name": "路透社中文",
          "url": "https://feeds.reuters.com/reuters/CNTopNews",
          "count": 3,
          "icon": "📰"
      },
  ]

def fetch_rss(url, count):
      headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}
      try:
          res = requests.get(url, headers=headers, timeout=15)
          print(f"  状态码: {res.status_code}")
          if res.status_code != 200:
              return []
          root = ET.fromstring(res.content)
          channel = root.find("channel")
          if channel is None:
              return []
          items = channel.findall("item")
          result = []
          for item in items[:count]:
              title = item.findtext("title", "").strip()
              link = item.findtext("link", "").strip()
              if title and link:
                  result.append({"title": title, "url": link})
          return result
      except Exception as e:
          print(f"  请求失败: {e}")
          return []

def build_card(all_items):
      now = datetime.utcnow()
      beijing_hour = (now.hour + 8) % 24
      time_str = f"{beijing_hour:02d}:00"

      elements = []

      for source in all_items:
          if not source["items"]:
              continue

          content_lines = []
          for i, item in enumerate(source["items"], 1):
              content_lines.append(f"**{i}. [{item['title']}]({item['url']})**")

          elements.append({
              "tag": "div",
              "text": {
                  "tag": "lark_md",
                  "content": f"{source['icon']} **{source['name']}**\n" + "\n".join(content_lines)
              }
          })
          elements.append({"tag": "hr"})

      if not elements:
          return None
  
      card = {
          "msg_type": "interactive",
          "card": {
              "config": {"wide_screen_mode": True},
              "header": {
                  "title": {"tag": "plain_text", "content": f"🗞️  中文热点速览 · {time_str}"},
                  "template": "orange"
              },
              "elements": elements
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

all_items = []
for source in SOURCES:
      print(f"获取 {source['name']}...")
      items = fetch_rss(source["url"], source["count"])
      print(f"  获取到 {len(items)} 条")
      all_items.append({
          "name": source["name"],
          "icon": source["icon"],
          "items": items
      })
  
card = build_card(all_items)
if not card:
      print("所有源均获取失败")
      sys.exit(1)

send_to_feishu(card)
print("完成")
