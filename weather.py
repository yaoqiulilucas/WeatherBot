  import requests
  import os
  import sys

  API_KEY = os.environ.get("QWEATHER_KEY")
  if not API_KEY:
      print("错误：未找到 QWEATHER_KEY 环境变量")
      sys.exit(1)

  API_HOST = "pj6x8antvu.re.qweatherapi.com"
  FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/96ab3d4f-7ddd-4d43-8002-3ef94ca2659d"

  CITIES = [
      {"name": "上海", "id": "101020100"},
      {"name": "深圳", "id": "101280601"},
  ]

  def get_weather(location_id):
      url = f"https://{API_HOST}/v7/weather/now?location={location_id}&key={API_KEY}"
      res = requests.get(url).json()
      print(f"API响应: {res}")
      return res["now"]

  lines = ["🌈 每日天气播报\n"]

  for city in CITIES:
      w = get_weather(city["id"])
      lines.append(
          f"━━━━━━━━━━━━━━━\n"
          f"📍 {city['name']}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"🌤 天气：{w['text']}\n"
          f"🌡 温度：{w['temp']}°C  体感：{w['feelsLike']}°C\n"
          f"💧 湿度：{w['humidity']}%  能见度：{w['vis']}km\n"
          f"💨 风向：{w['windDir']} {w['windScale']}级\n"
          f"🔵 气压：{w['pressure']}hPa\n"
      )

  msg = "\n".join(lines)
  requests.post(FEISHU_WEBHOOK, json={
      "msg_type": "text",
      "content": {"text": msg}
  })
  print("推送成功")


