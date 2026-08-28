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

def get_ad_tip(yi, ji, lunar_day):
      yi_expand = any(k in yi for k in ["开市", "纳财", "交易", "立券", "开业"])
      yi_test   = any(k in yi for k in ["出行", "会友", "入学", "求职", "开光"])
      yi_clean  = any(k in yi for k in ["祭祀", "沐浴", "扫舍", "理发"])
      ji_expand = any(k in ji for k in ["开市", "纳财", "交易"])

      is_special = lunar_day in [1, 15, 30]

      if (yi_clean and not yi_expand) or (ji_expand and not yi_expand):
          if is_special:
              return f"📈 投放　**宜销户**　今为农历{LUNAR_DAY_NAMES[lunar_day-1]}，月节点流量结构易波动，黄历忌开市纳财。建议全面审查账户：暂停ACoS连续3日超目标150%的计划，下架曝光超5000零点击的关键词，SP自动投放仅保留紧密匹配，预算压缩至平日70%。适合操作的时辰：卯时（05:00-07:00）和酉时（17:00-19:00），避开午时流量高峰动刀"
          elif lunar_day in range(2, 8):
              return "📈 投放　**宜销户**　月初黄历偏清整，不宜开新。建议关停近7日ROAS低于1.5的广告组，归并同质化计划，删除重复竞价关键词。适合操作的时辰：辰时（07:00-09:00）完成清理，赶在巳时（09:00-11:00）流量起量前让账户结构干净利落"
          elif lunar_day in range(8, 15):
              return "📈 投放　**宜销户**　月中前夕黄历主收，不利扩张。识别本周跑量靠后20%的计划暂停，将节省预算集中补给核心SKU的SP精准计划。适合操作的时辰：寅时（03:00-05:00）系统流量低谷期操作不影响跑量；或选午时（11:00-13:00）复盘上午数据后再做减法"
          elif lunar_day in range(16, 23):
              return "📈 投放　**宜销户**　月中后黄历趋静，适合做账户体检。对比本周同期数据，找出CTR跌幅超20%的素材下架，清理预算消耗快但转化差的SD广告。适合操作的时辰：申时（15:00-17:00）下午流量开始分散，此时调整对当日数据影响最小"
          else:
              return "📈 投放　**宜销户**　月末黄历主收尾，适合彻底清整。复盘本月全量数据：标记需暂停的低效计划，整理否定关键词清单并批量更新，归档本月测试结论。适合操作的时辰：戌时（19:00-21:00）夜间流量收尾，此时操作不干扰次日早市开盘"

      elif yi_expand and not ji_expand:
          if lunar_day == 1:
              return "📈 投放　**宜扩量**　农历初一，月初流量蓄势，黄历宜开市纳财，扩量时机极佳。建议核心SP计划预算+30%，出价上调8-12%；新增1条SP自动投放探索长尾词，日预算100元；SD再营销受众新开1条定向近30天浏览未购买人群，预算50元。适合操作的时辰：卯时（05:00-07:00）挂单，巳时（09:00-11:00）流量起量时正好生效"
          elif lunar_day == 15:
              return "📈 投放　**宜扩量**　农历十五，月中流量峰值节点，黄历宜纳财，扩量胜率最高。将过去7日ROAS>3的计划预算提升25%，出价跟进5%；SP品牌词单独拎出做高出价保量；追加SD竞品定向1条，日预算80元。适合操作的时辰：辰时（07:00-09:00）完成调整，重点盯未时（13:00-15:00）至申时（15:00-17:00）的转化高峰"
          elif lunar_day in range(2, 8):
              return "📈 投放　**宜扩量**　月初黄历宜开市，流量处于爬坡阶段，适合稳步推进扩量。找出昨日转化率前30%的计划预算提升20%，出价上调10%；有新品跑满3天可从测试档（50元）升至正式档（150元+）。适合操作的时辰：辰时（07:00-09:00）早市调整生效最快，午时（11:00-13:00）补一次预算观察消耗节奏"
          elif lunar_day in range(16, 23):
              return "📈 投放　**宜扩量**　月中后黄历宜交易，消费者决策意愿强。对核心词SP出价上调5-8%，SP品牌词保持高出价托底；若今日整体消耗低于预期，补开1条SP自动投放，日预算80元跑晚间数据。适合操作的时辰：午时（11:00-13:00）流量旺盛时加价效果最直接，酉时（17:00-19:00）晚高峰前再做一次出价微调"
          else:
              return "📈 投放　**宜扩量**　今日黄历宜开市立券，财运亨通，是推进预算的好时机。重点补预算给消耗超60%的跑量计划，出价小幅上调5%趁热打铁；同步将SP自动投放中高点击词手动添加到精准计划。适合操作的时辰：巳时（09:00-11:00）与未时（13:00-15:00），流量稳定，调整后可快速看到反馈"

      elif yi_test and not ji_expand:
          if is_special:
              return f"📈 投放　**宜测新**　农历{LUNAR_DAY_NAMES[lunar_day-1]}，黄历宜开光探索，月节点流量结构变化是测试素材的好时机。启动素材AB测：同一计划下上传2支视频主图（功能演示 vs 场景痛点），各日预算80元，SP手动精准匹配选3-5个核心词，连跑3天对比CTR与转化率。适合操作的时辰：卯时（05:00-07:00）上线，让素材赶上巳时（09:00-11:00）第一波流量"
          elif lunar_day in range(2, 8):
              return "📈 投放　**宜测新**　月初黄历宜出行探索，适合测试新素材方向。建议聚焦'使用前后对比'或'用户证言'类主图，SP手动精准开1条，选竞争度中等关键词5个，日预算60-80元跑满一天再评。适合操作的时辰：辰时（07:00-09:00）上线，巳时到午时（09:00-13:00）是新素材获取第一批真实点击数据的黄金窗口"
          elif lunar_day in range(8, 15):
              return "📈 投放　**宜测新**　月中前夕黄历宜会友求新，午间流量多样，测新代表性强。在现有SP计划中新增广泛匹配关键词5-8个，独立设置日预算50元；同时测试1张新副图（强调场景或节日元素）与原主图对比点击率。适合操作的时辰：午时（11:00-13:00）上线，借助午间流量高峰快速积累展示量"
          elif lunar_day in range(16, 23):
              return "📈 投放　**宜测新**　月中后黄历宜开光，适合测试受众定向。新开1条SD展示广告定向'竞品ASIN相似受众'，主图用当前最高CTR素材，日预算50元；SP自动投放中开启'同类商品'匹配，预算30元独立跑。适合操作的时辰：申时（15:00-17:00）上线，测试酉时至亥时（17:00-23:00）晚间浏览型流量的点击成本"
          else:
              return "📈 投放　**宜测新**　月末黄历宜探索，为下月投放做好素材储备。上线以生活方式为主题的视频主图（15秒内，前3秒突出使用场景），SP手动精准选5个长尾词，日预算50元。适合操作的时辰：酉时（17:00-19:00）上线，测试夜间兴趣浏览型用户的反应，次日卯时看数据决定是否扩量"

      else:
          if is_special:
              return f"📈 投放　**观望为主**　农历{LUNAR_DAY_NAMES[lunar_day-1]}，黄历宜忌交织，月节点不宜大动。做一次全账户数据复盘：对比上月同期ROAS、ACoS、CTR三项指标，找出结构性问题，投放操作仅限±10%预算微调。适合操作的时辰：丑时（01:00-03:00）系统低谷期做数据导出与分析，不影响任何跑量计划"
          elif lunar_day in range(2, 8):
              return "📈 投放　**观望为主**　月初黄历平平，维持昨日预算和出价不变。重点观察：若有计划ACoS突然上涨超30%，可小幅降出价5%做保护。适合操作的时辰：午时（11:00-13:00）上午数据已足够判断当日走势，此时做出调整比早盘更有依据"
          elif lunar_day in range(8, 15):
              return "📈 投放　**观望为主**　月中前夕黄历中平，宜静观数据勿轻动。记录今日各计划消耗进度与近7日均值对比，若某计划消耗超预期但转化差，可临时暂停至次日重新评估。适合操作的时辰：未时（13:00-15:00）午后数据趋势已明朗，此时决策最为稳妥"
          else:
              return "📈 投放　**观望为主**　今日黄历平稳，宜守不宜攻。检查核心计划预算消耗进度，预防提前断投；SP精准计划若消耗偏慢可酌情上调出价3-5%补量，其余维持不动。适合操作的时辰：申时（15:00-17:00）下午流量尚在，小幅调整能在收盘前看到效果"

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
          ad_tip = get_ad_tip(yi, ji, lunar.day)

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
