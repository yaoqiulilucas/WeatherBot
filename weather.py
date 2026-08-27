  import requests
  import os
  import sys

  # 读取环境变量
  API_KEY = os.environ.get("QWEATHER_KEY")
  if not API_KEY:
      print("错误：未找到 QWEATHER_KEY")
      sys.exit(1)

  API_HOST = "pj6x8antvu.re.qweatherapi.com"
  FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/96ab3d4f-7ddd-4d43-8002-3ef94ca2659d"

  CITIES = [
      {"name": "上海", "id": "101020100"},
      {"name": "深圳", "id": "101280601"},
  ]

  def get_weather(city_name, location_id):
      url = f"https://{API_HOST}/v7/weather/now?location={location_id}&key={API_KEY}"
      try:
          res = requests.get(url, timeout=10)
          data = res.json()
          print(f"{city_name} API响应: {data}")
          if "now" not in data:
              print(f"{city_name} 错误：响应中没有 now 字段，code={data.get('code')}")
              return None
          return data["now"]
      except Exception as e:
          print(f"{city_name} 请求失败: {e}")
          return None

  def build_message():
      lines = ["🌈 每日天气播报\n"]
      for city in CITIES:
          w = get_weather(city["name"], city["id"])
          if w is None:
              lines.append(f"📍 {city['name']}：天气数据获取失败\n")
              continue
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
      return "\n".join(lines)
  
  def send_to_feishu(msg):
      try:
          res = requests.post(
              FEISHU_WEBHOOK,
              json={"msg_type": "text", "content": {"text": msg}},
              timeout=10
          )
          print(f"飞书响应: {res.status_code} {res.text}")
      except Exception as e:
          print(f"飞书推送失败: {e}")
          sys.exit(1)

  msg = build_message()
  print("=== 即将发送的消息 ===")
  print(msg)
  send_to_feishu(msg)
  print("完成")
