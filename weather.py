import requests
import os
import sys
from datetime import datetime

API_KEY = os.environ.get("QWEATHER_KEY")
if not API_KEY:
      print("错误：未找到 QWEATHER_KEY")
      sys.exit(1)

API_HOST = "pj6x8antvu.re.qweatherapi.com"
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/96ab3d4f-7ddd-4d43-8002-3ef94ca2659d"
MXNZP_APP_ID = "mtppwrffovfiqxmk"
MXNZP_SECRET = "z2cq8svE1dGqHXexeEs7cR1iS7nzrBGK"

CITIES = [
      {"name": "上海", "id": "101020100"},
      {"name": "深圳", "id": "101280601"},
  ]

def get_weather(city_name, location_id):
      url = f"https://{API_HOST}/v7/weather/now?location={location_id}&key={API_KEY}"
      try:
          res = requests.get(url, timeout=10)
          data = res.json()
          print(f"{city_name} 天气响应: {data}")
          if "now" not in data:
              print(f"{city_name} 错误：code={data.get('code')}")
              return None
          return data["now"]
      except Exception as e:
          print(f"{city_name} 请求失败: {e}")
          return None

def get_almanac():
      today = datetime.now().strftime("%Y%m%d")
      url = f"https://www.mxnzp.com/api/lunar_calendar/single/{today}?app_id={MXNZP_APP_ID}&app_secret={MXNZP_SECRET}"
      try:
          res = requests.get(url, timeout=10)
          data = res.json()
          print(f"黄历响应: {data}")
          if data.get("code") != 1:
              print(f"黄历错误：{data.get('msg')}")
              return None
          return data.get("data")
      except Exception as e:
          print(f"黄历请求失败: {e}")
          return None

def build_card(cities_data, almanac):
      today = datetime.now().strftime("%Y年%m月%d日")
      elements = []

      # 黄历部分
      if almanac:
          lunar = f"{almanac.get('lunarYear', '')}年 {almanac.get('lunarMonth', '')}月{almanac.get('lunarDay', '')}"
          yi = almanac.get("yi", "暂无")
          ji = almanac.get("ji", "暂无")
          solar_term = almanac.get("solarTerms", "")
          solar_str = f"　🌿 节气：{solar_term}" if solar_term else ""

          elements.append({
              "tag": "div",
              "text": {
                  "tag": "lark_md",
                  "content": (
                      f"**📅 {today}**　{lunar}{solar_str}\n"
                      f"✅ **宜**　{yi}\n"
                      f"❌ **忌**　{ji}"
                  )
              }
          })
          elements.append({"tag": "hr"})

      # 天气部分
      for city in cities_data:
          name = city["name"]
          w = city["weather"]
          if w is None:
              elements.append({
                  "tag": "div",
                  "text": {"tag": "lark_md", "content": f"**📍 {name}**\n数据获取失败"}
              })
          else:
              elements.append({
                  "tag": "div",
                  "text": {
                      "tag": "lark_md",
                      "content": (
                          f"**📍 {name}**\n"
                          f"🌤 {w['text']}　🌡 {w['temp']}°C　体感 {w['feelsLike']}°C\n"
                          f"💧 湿度 {w['humidity']}%　👁 能见度 {w['vis']}km\n"
                          f"💨 {w['windDir']} {w['windScale']}级　🔵 气压 {w['pressure']}hPa"
                      )
                  }
              })
          elements.append({"tag": "hr"})

      card = {
          "msg_type": "interactive",
          "card": {
              "config": {"wide_screen_mode": True},
              "header": {
                  "title": {"tag": "plain_text", "content": "🌈 每日天气 & 黄历播报"},
                  "template": "blue"
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

cities_data = []
for city in CITIES:
      w = get_weather(city["name"], city["id"])
      cities_data.append({"name": city["name"], "weather": w})

almanac = get_almanac()
card = build_card(cities_data, almanac)
send_to_feishu(card)
print("完成")

