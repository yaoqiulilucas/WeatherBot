import requests
import sys
from datetime import datetime

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/96ab3d4f-7ddd-4d43-8002-3ef94ca2659d"

WEATHER_CODES = {
      0: "晴空万里", 1: "基本晴朗", 2: "局部多云", 3: "阴天",
      45: "雾", 48: "冻雾",
      51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
      61: "小雨", 63: "中雨", 65: "大雨",
      71: "小雪", 73: "中雪", 75: "大雪", 77: "冰粒",
      80: "小阵雨", 81: "中阵雨", 82: "强阵雨",
      85: "小阵雪", 86: "大阵雪",
      95: "雷阵雨", 96: "雷阵雨伴小冰雹", 99: "雷阵雨伴大冰雹",
  }

def get_london_weather():
      url = (
          "https://api.open-meteo.com/v1/forecast"
          "?latitude=51.5074&longitude=-0.1278"
          "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
          "precipitation,weather_code,wind_speed_10m,wind_direction_10m,"
          "surface_pressure,visibility"
          "&timezone=Europe%2FLondon"
          "&wind_speed_unit=ms"
      )
      try:
          res = requests.get(url, timeout=10)
          data = res.json()
          print(f"伦敦天气响应: {data}")
          return data.get("current")
      except Exception as e:
          print(f"伦敦天气请求失败: {e}")
          return None

def get_wind_dir(degrees):
      dirs = ["北","东北","东","东南","南","西南","西","西北"]
      idx = round(degrees / 45) % 8
      return dirs[idx]

def get_life_tips(w):
      tips = []
      temp = w.get("temperature_2m", 15)
      feels = w.get("apparent_temperature", temp)
      humidity = w.get("relative_humidity_2m", 60)
      precip = w.get("precipitation", 0)
      code = w.get("weather_code", 0)

      rain_codes = [51,53,55,61,63,65,71,73,75,77,80,81,82,85,86,95,96,99]

      if feels >= 28:
          tips.append("👕 穿搭：短袖即可，伦敦难得的热天")
      elif feels >= 20:
          tips.append("👕 穿搭：轻薄长袖或薄外套")
      elif feels >= 12:
          tips.append("👕 穿搭：外套+毛衣，注意早晚温差")
      elif feels >= 5:
          tips.append("👕 穿搭：厚外套，围巾手套备上")
      else:
          tips.append("👕 穿搭：羽绒服全套，做好防寒")

      if precip > 0 or code in rain_codes:
          tips.append("☂️ 带伞：有降水，伦敦雨说来就来")
      elif humidity > 80:
          tips.append("☂️ 带伞：湿度偏高，备伞以防万一")
      else:
          tips.append("☂️ 带伞：暂时无雨，可不带")

      if code in [0, 1]:
          tips.append("🧴 防晒：难得出太阳，记得防晒")
      elif code in [2, 3]:
          tips.append("🧴 防晒：多云遮光，防晒可放宽")
      else:
          tips.append("🧴 防晒：阴雨天气，无需防晒")

      return "\n".join(tips)

def build_card(w):
      now_london = datetime.utcnow()
      today_str = now_london.strftime("%Y年%m月%d日")

      code = w.get("weather_code", 0)
      text = WEATHER_CODES.get(code, f"天气代码{code}")
      temp = w.get("temperature_2m", "--")
      feels = w.get("apparent_temperature", "--")
      humidity = w.get("relative_humidity_2m", "--")
      wind_speed = round(w.get("wind_speed_10m", 0) * 3.6, 1)
      wind_dir = get_wind_dir(w.get("wind_direction_10m", 0))
      pressure = round(w.get("surface_pressure", 0))
      vis = round(w.get("visibility", 0) / 1000, 1) if w.get("visibility") else "--"
      life_tips = get_life_tips(w)

      card = {
          "msg_type": "interactive",
          "card": {
              "config": {"wide_screen_mode": True},
              "header": {
                  "title": {"tag": "plain_text", "content": "🇬🇧 伦敦天气播报"},
                  "template": "green"
              },
              "elements": [
                  {
                      "tag": "div",
                      "text": {
                          "tag": "lark_md",
                          "content": (
                              f"**📅 {today_str} 北京时间15:00**\n"
                              f"**📍 伦敦 London**\n"
                              f"🌤 {text}　🌡 {temp}°C　体感 {feels}°C\n"
                              f"💧 湿度 {humidity}%　👁 能见度 {vis}km\n"
                              f"💨 {wind_dir}风 {wind_speed}km/h　🔵 气压 {pressure}hPa\n"
                              f"{life_tips}"
                          )
                      }
                  },
                  {"tag": "hr"}
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

w = get_london_weather()
if not w:
      print("获取伦敦天气失败")
      sys.exit(1)

card = build_card(w)
send_to_feishu(card)
print("完成")

