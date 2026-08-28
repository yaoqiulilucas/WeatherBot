import requests
import os
import sys
from datetime import datetime
from lunardate import LunarDate

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

HEAVENLY_STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

LUNAR_MONTH_NAMES = ["正","二","三","四","五","六","七","八","九","十","冬","腊"]
LUNAR_DAY_NAMES = [
      "初一","初二","初三","初四","初五","初六","初七","初八","初九","初十",
      "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十",
      "廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十"
]

SOLAR_TERMS = {
      (1,6):"小寒",(1,20):"大寒",
      (2,4):"立春",(2,19):"雨水",
      (3,6):"惊蛰",(3,21):"春分",
      (4,5):"清明",(4,20):"谷雨",
      (5,6):"立夏",(5,21):"小满",
      (6,6):"芒种",(6,21):"夏至",
      (7,7):"小暑",(7,23):"大暑",
      (8,7):"立秋",(8,23):"处暑",
      (9,8):"白露",(9,23):"秋分",
      (10,8):"寒露",(10,23):"霜降",
      (11,7):"立冬",(11,22):"小雪",
      (12,7):"大雪",(12,22):"冬至",
}

YI_JI_TABLE = [
      ("祈福、出行、嫁娶", "动土、安葬"),
      ("入宅、开业、交易", "出行、探病"),
      ("开市、纳财、签约", "嫁娶、迁移"),
      ("祭祀、沐浴、扫舍", "开市、动土"),
      ("出行、会友、求职", "安床、安葬"),
      ("嫁娶、入宅、开光", "出行、伐木"),
      ("开市、立券、纳财", "祭祀、祈福"),
      ("动土、安床、装修", "开市、入宅"),
      ("出行、求医、理发", "嫁娶、开市"),
      ("祭祀、入学、求职", "动土、安葬"),
      ("嫁娶、开市、交易", "出行、探病"),
      ("纳财、开业、修缮", "嫁娶、祭祀"),
      ("出行、祭祀、开光", "动土、安床"),
      ("入宅、立券、栽种", "开市、出行"),
      ("开市、嫁娶、祭祀", "安葬、伐木"),
      ("出行、求财、会友", "入宅、动土"),
      ("动土、修缮、装修", "嫁娶、开市"),
      ("祭祀、沐浴、理发", "出行、安床"),
      ("入宅、开业、纳财", "动土、祭祀"),
      ("嫁娶、出行、开光", "开市、伐木"),
      ("开市、立券、交易", "嫁娶、安葬"),
      ("祭祀、入学、栽种", "出行、动土"),
      ("出行、会友、求职", "开市、入宅"),
      ("纳财、开业、嫁娶", "祭祀、安床"),
      ("动土、修缮、装修", "出行、开市"),
      ("祭祀、沐浴、开光", "嫁娶、伐木"),
      ("入宅、立券、纳财", "动土、祭祀"),
      ("嫁娶、出行、祭祀", "开市、安葬"),
      ("开市、交易、求财", "嫁娶、动土"),
      ("祭祀、入学、理发", "出行、安床"),
 ]

def get_ganzhi_year(year):
      stem = HEAVENLY_STEMS[(year - 4) % 10]
      branch = EARTHLY_BRANCHES[(year - 4) % 12]
      return f"{stem}{branch}"

def get_ad_tip(yi, ji):
      yi_expand = any(k in yi for k in ["开市", "纳财", "交易", "立券", "开业"])
      yi_test   = any(k in yi for k in ["出行", "会友", "入学", "求职", "开光"])
      yi_clean  = any(k in yi for k in ["祭祀", "沐浴", "扫舍", "理发"])
      ji_expand = any(k in ji for k in ["开市", "纳财", "交易"])
      ji_test   = any(k in ji for k in ["出行", "伐木"])

      if yi_expand and not ji_expand:
          return "📈 投放　**宜扩量**　将跑量计划预算提升20-30%，出价上调5-10%；重点扩高ROI计划，SP/SD各开1-2条，建议10:00前完成调整，观察至14:00数据"
      elif yi_clean or ji_expand:
          return "📈 投放　**宜销户**　关停近7日ACoS超阈值计划，下架零出单超14天的广告组；预算收紧至日常60%，仅保留核心词SP自动投放，避免新开计划"
      elif yi_test or ji_test:
          return "📈 投放　**宜测新**　测试1-2支新素材（建议方向：场景化使用/痛点切入），每条日预算50-100元，SP手动精准匹配开1条，9:00上线跑满一天再看数据"
      else:
          return "📈 投放　**宜测新**　稳预算维持现状，可小额测试1条新受众定向，日预算30-50元，不调整现有出价，16:00前观察CTR与加购率再决策"


def get_almanac():
      today = datetime.now()
      try:
          lunar = LunarDate.fromSolarDate(today.year, today.month, today.day)
          gz_year = get_ganzhi_year(lunar.year)
          month_name = LUNAR_MONTH_NAMES[lunar.month - 1]
          day_name = LUNAR_DAY_NAMES[lunar.day - 1]
          lunar_str = f"{gz_year}年{month_name}月{day_name}"

          idx = (lunar.day - 1) % len(YI_JI_TABLE)
          yi, ji = YI_JI_TABLE[idx]
          ad_tip = get_ad_tip(yi, ji)

          solar_term = SOLAR_TERMS.get((today.month, today.day), "")

          return {
              "lunarStr": lunar_str,
              "yi": yi,
              "ji": ji,
              "adTip": ad_tip,
              "solarTerm": solar_term,
          }
      except Exception as e:
          print(f"农历计算失败: {e}")
          return None

def get_weather(city_name, location_id):
      url = f"https://{API_HOST}/v7/weather/now?location={location_id}&key={API_KEY}"
      try:
          res = requests.get(url, timeout=10)
          data = res.json()
          if "now" not in data:
              print(f"{city_name} 错误：code={data.get('code')}")
              return None
          return data["now"]
      except Exception as e:
          print(f"{city_name} 请求失败: {e}")
          return None

def get_life_tips(w):
      tips = []
      temp = int(w.get("temp", 20))
      feels = int(w.get("feelsLike", temp))
      text = w.get("text", "")
      humidity = int(w.get("humidity", 60))
      precip = float(w.get("precip", 0))
      scale = int(w.get("windScale", 0))

      if feels >= 35:
          tips.append("👕 穿搭：背心短裤，轻薄透气为主")
      elif feels >= 28:
          tips.append("👕 穿搭：短袖短裤，注意防晒")
      elif feels >= 20:
          tips.append("👕 穿搭：短袖或薄外套，早晚带一件")
      elif feels >= 12:
          tips.append("👕 穿搭：薄外套或毛衣，注意保暖")
      elif feels >= 5:
          tips.append("👕 穿搭：厚外套+毛衣，做好保暖")
      else:
          tips.append("👕 穿搭：羽绒服+厚围巾，注意防寒")

      if precip > 0 or any(k in text for k in ["雨","雷","雪","冻"]):
          tips.append("☂️ 带伞：今日有降水，务必携带雨具")
      elif humidity > 85:
          tips.append("☂️ 带伞：湿度较高，出门备伞以防阵雨")
      else:
          tips.append("☂️ 带伞：无需携带")

      if any(k in text for k in ["晴","少云"]):
          if temp >= 28:
              tips.append("🧴 防晒：紫外线强，涂防晒霜+戴遮阳帽")
          else:
              tips.append("🧴 防晒：阳光较足，建议涂防晒")
      elif any(k in text for k in ["多云","阴"]):
          tips.append("🧴 防晒：云层较厚，防晒可适当放宽")
      else:
          tips.append("🧴 防晒：无明显紫外线，无需特别防护")

      result = "\n".join(tips)
      if scale >= 6:
          result += f"\n🌬️  注意：{w.get('windDir')} {scale}级大风，户外注意安全"
      return result

def build_card(cities_data, almanac):
      today = datetime.now().strftime("%Y年%m月%d日")
      elements = []

      if almanac:
          solar_str = f"　🌿 {almanac['solarTerm']}" if almanac.get("solarTerm") else ""
          elements.append({
              "tag": "div",
              "text": {
                  "tag": "lark_md",
                  "content": (
                      f"**📅 {today}**　农历 {almanac['lunarStr']}{solar_str}\n"
                      f"✅ **宜**　{almanac['yi']}\n"
                      f"❌ **忌**　{almanac['ji']}\n"
                      f"{almanac['adTip']}"
                  )
              }
          })
          elements.append({"tag": "hr"})

      for city in cities_data:
          name = city["name"]
          w = city["weather"]
          if w is None:
              elements.append({
                  "tag": "div",
                  "text": {"tag": "lark_md", "content": f"**📍 {name}**\n数据获取失败"}
              })
          else:
              life_tips = get_life_tips(w)
              elements.append({
                  "tag": "div",
                  "text": {
                      "tag": "lark_md",
                      "content": (
                          f"**📍 {name}**\n"
                          f"🌤 {w['text']}　🌡 {w['temp']}°C　体感 {w['feelsLike']}°C\n"
                          f"💧 湿度 {w['humidity']}%　👁 能见度 {w['vis']}km\n"
                          f"💨 {w['windDir']} {w['windScale']}级　🔵 气压 {w['pressure']}hPa\n"
                          f"{life_tips}"
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
