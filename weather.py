import requests

  API_KEY = "238af592792b4e25b12aab7e6ce5357b"
  API_HOST = "pj6x8antvu.re.qweatherapi.com"
  FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/96ab3d4f-7ddd-4d43-8002-3ef94ca2659d"

  CITIES = [
      {"name": "上海", "id": "101020100"},
      {"name": "深圳", "id": "101280601"},
  ]

  def get_weather(location_id):
      url = f"https://{API_HOST}/v7/weather/now?location={location_id}&key={API_KEY}"
      return requests.get(url).json()["now"]

  def get_indices(location_id):
      # 3=穿衣 5=紫外线 9=感冒 1=运动
      url = f"https://{API_HOST}/v7/indices/1d?location={location_id}&key={API_KEY}&type=1,3,5,9"
      data = requests.get(url).json()
      return {item["type"]: item for item in data.get("daily", [])}

  lines = ["🌈 每日天气播报\n"]

  for city in CITIES:
      w = get_weather(city["id"])
      idx = get_indices(city["id"])

      sport   = idx.get("1", {})
      cloth   = idx.get("3", {})
      uv      = idx.get("5", {})
      cold    = idx.get("9", {})

      lines.append(
          f"━━━━━━━━━━━━━━━\n"
          f"📍 {city['name']}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"🌤 天气：{w['text']}\n"
          f"🌡 温度：{w['temp']}°C  体感：{w['feelsLike']}°C\n"
          f"💧 湿度：{w['humidity']}%  能见度：{w['vis']}km\n"
          f"💨 风向：{w['windDir']} {w['windScale']}级  风速：{w['windSpeed']}km/h\n"
          f"🔵 气压：{w['pressure']}hPa  云量：{w['cloud']}%\n"
          f"\n"
          f"📋 生活建议\n"
          f"👕 穿衣：{cloth.get('category', 'N/A')} — {cloth.get('text', '')}\n"
          f"🕶 紫外线：{uv.get('category', 'N/A')} — {uv.get('text', '')}\n"
          f"🤧 感冒：{cold.get('category', 'N/A')} — {cold.get('text', '')}\n"
          f"🏃 运动：{sport.get('category', 'N/A')} — {sport.get('text', '')}\n"
      )

  msg = "\n".join(lines)
  requests.post(FEISHU_WEBHOOK, json={
      "msg_type": "text",
      "content": {"text": msg}
  })
  print("推送成功")

  ---
  .github/workflows/weather.yml（API Key 已写进代码，yml 不需要再配置 secret）：

  name: Daily Weather Push

  on:
    schedule:
      - cron: '30 23 * * *'  # 北京时间每天 8:00
    workflow_dispatch:

  jobs:
    push-weather:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - uses: actions/setup-python@v4
          with:
            python-version: '3.10'
        - run: pip install requests
        - run: python weather.py

