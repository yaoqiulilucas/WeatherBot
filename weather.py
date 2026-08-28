import requests
import os
import sys
from datetime import date
from chinese_calendar import is_workday
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
              return f"**投放**　宜销户　今为农历{LUNAR_DAY_NAMES[lunar_day-1]}，月节点算法重新评估账户质量分，黄历忌开市。Meta建议关停近7日CPA超目标2倍的广告组，预算收缩至平日70%；Google暂停低QualityScore关键词，整理否定词库；TikTok下架完播率低于20%的视频素材。适合操作的时辰：卯时（05:00-07:00）平台流量低谷，操作不影响当日跑量；酉时（17:00-19:00）复查执行结果"
          elif lunar_day in range(2, 8):
              return "**投放**　宜销户　月初黄历偏清整，不宜开新计划。Meta关闭ROAS连续3日低于目标值的广告组，合并同质化受众；Google停投低转化率的展示广告，预算向搜索词组集中；TikTok清理CTR低于1%且跑量超3天的素材。适合操作的时辰：辰时（07:00-09:00）完成清理，赶在巳时（09:00-11:00）流量起量前让账户结构干净"
          elif lunar_day in range(8, 15):
              return "**投放**　宜销户　月中前夕黄历主收，账户做减法为主。Meta识别近期频次过高（>3）的广告组降预算或关停，避免受众疲劳；Google压缩宽泛匹配占比，提升精确匹配权重；TikTok下架播放超10万但加购率为零的内容。适合操作的时辰：寅时（03:00-05:00）低谷期批量操作效率最高，午时（11:00-13:00）复盘上午数据后收尾"
          elif lunar_day in range(16, 23):
              return "**投放**　宜销户　月中后黄历趋静，适合全面账户体检。Meta对比本周与上周同期CPM变化，下架创意疲劳素材；Google审查各广告组搜索词报告，补充否定词；TikTok检查各视频素材的3秒完播率与转化漏斗，去掉拖累整体质量分的内容。适合操作的时辰：申时（15:00-17:00）下午流量分散，操作对当日数据扰动最小"
          else:
              return "**投放**　宜销户　月末黄历主收尾，做好下月启动前的清仓。Meta归档本月测试结论，关停所有探索期计划，仅保留核心跑量组；Google导出本月搜索词报告，批量更新否定词库；TikTok整理素材表现数据，确认下月测新素材方向。适合操作的时辰：戌时（19:00-21:00）夜间收尾，次日卯时以干净账户迎接新月"

      elif yi_expand and not ji_expand:
          if lunar_day == 1:
              return "**投放**　宜扩量　农历初一，月初平台算法重新分配流量，黄历宜开市纳财，扩量时机极佳。Meta将跑量稳定的广告组预算提升30%，同步扩展Lookalike受众至3%-5%；Google对核心关键词出价上调10-15%，开启智能出价Target ROAS；TikTok把昨日完播率>40%的视频加投TopFeed，日预算+50%。适合操作的时辰：卯时（05:00-07:00）设置完毕，巳时（09:00-11:00）流量起量时正好生效"
          elif lunar_day == 15:
              return "**投放**　宜扩量　农历十五，月中流量峰值节点，黄历宜纳财，扩量胜率全月最高。Meta预算提升25%，追加再营销广告组定向近30天加购未付款人群；Google品牌词出价保量，同步开1条Performance Max测试全渠道覆盖；TikTok对近7日ROAS>2的计划全面提价，主推视频追加达人混剪版本测试。适合操作的时辰：辰时（07:00-09:00）完成调整，重点盯未时至申时（13:00-17:00）转化高峰数据"
          elif lunar_day in range(2, 8):
              return "**投放**　宜扩量　月初黄历宜开市，流量爬坡阶段，适合稳步扩量。Meta将过去7日CPA达标的广告组预算提升20%，受众扩展至Broad定向让算法探索；Google对高转化词组出价上调8-10%，新增1-2个相关搜索词组；TikTok把跑满3天数据的测试素材预算从¥100升至¥300+。适合操作的时辰：辰时（07:00-09:00）早盘调整效果最快，午时（11:00-13:00）补一次预算观察消耗节奏"
          elif lunar_day in range(16, 23):
              return "**投放**　宜扩量　月中后黄历宜交易，用户购买决策意愿强。Meta追加动态创意广告（DCA）测试多版本素材组合，预算集中在晚间时段投放；Google对购物广告出价策略切换为Target ROAS并上调目标值5%；TikTok新开1条Spark Ads推当前最高互动率的有机内容，预算¥200起跑。适合操作的时辰：午时（11:00-13:00）加价效果最直接，酉时（17:00-19:00）晚高峰前完成最后一次出价微调"
          else:
              return "**投放**　宜扩量　今日黄历宜开市立券，财气旺，是补量推进的好时机。Meta将消耗超日预算60%的广告组追加预算，出价小幅上浮5%趁热打铁；Google启动自动出价实验组对比当前出价策略；TikTok在现有跑量计划下复制一条新广告组，替换主图测试新视频封面。适合操作的时辰：巳时（09:00-11:00）与未时（13:00-15:00），流量稳定，调整后1-2小时可见反馈"

      elif yi_test and not ji_expand:
          if is_special:
              return f"**投放**　宜测新　农历{LUNAR_DAY_NAMES[lunar_day-1]}，黄历宜开光探索，月节点流量结构是测试的好时机。Meta新建1个广告组测试全新受众定向（兴趣词重新组合），搭配2支素材AB测，每组日预算¥150；Google开1条新广告系列测试新着陆页或新出价策略；TikTok同时上线功能演示与场景痛点两支视频，各日预算¥100跑满3天再比较完播与转化。适合操作的时辰：卯时（05:00-07:00）上线，赶上巳时（09:00-11:00）第一波流量"
          elif lunar_day in range(2, 8):
              return "**投放**　宜测新　月初黄历宜出行探索，适合测试新素材与新受众。Meta新建广告组测试'用户证言'或'使用前后对比'类视频素材，Advantage+受众开启让算法自动探索，日预算¥150；Google新增1组广泛匹配关键词探索长尾流量，预算独立设置；TikTok上线新素材选辰时（07:00-09:00），让早间流量为素材积累第一批真实数据"
          elif lunar_day in range(8, 15):
              return "**投放**　宜测新　月中前夕黄历宜会友求新，流量多样，测新结果代表性强。Meta在现有最优广告组下新增2支不同钩子（价格钩/痛点钩）的静态图测试，日预算各¥100；Google新增响应式搜索广告测试新标题组合；TikTok测试新封面图与新文案组合，不换视频内容只换外壳，日预算¥100独立观察CTR变化。适合操作的时辰：午时（11:00-13:00）上线，借午间流量高峰快速积累展示量"
          elif lunar_day in range(16, 23):
              return "**投放**　宜测新　月中后黄历宜开光，适合测试新受众与新渠道组合。Meta新开1个再营销广告组测试'浏览未购买7天内'人群，素材用高转化视频二剪版，日预算¥200；Google测试展示广告网络新受众定向（相似受众或自定义意向）；TikTok新开1条Spark Ads推近期评论最多的有机视频，测试真实内容的转化力。适合操作的时辰：申时（15:00-17:00）上线，观察酉时至亥时（17:00-23:00）晚间流量表现"
          else:
              return "**投放**　宜测新　月末黄历宜探索，为下月素材库做储备。Meta测试1支UGC风格短视频（15秒内，真实使用场景），新建广告组独立跑，日预算¥100；Google测试新着陆页版本，对比当前页面转化率；TikTok上线生活方式场景类视频，前3秒突出产品使用场景，日预算¥80，次日卯时看数据决定是否加量。适合操作的时辰：酉时（17:00-19:00）上线，测试夜间兴趣浏览用户的点击反应"
  
      else:
          if is_special:
              return f"**投放**　观望为主　农历{LUNAR_DAY_NAMES[lunar_day-1]}，黄历宜忌交织，月节点平台算法波动，不宜大动。Meta维持现有预算与出价，检查各广告组频次是否超过3，超则小幅降预算；Google不调出价，导出近7日搜索词报告备用；TikTok不新开计划，观察当日完播率与互动率走势。适合操作的时辰：丑时（01:00-03:00）系统低谷期拉取数据报告，不触碰任何投放设置"
          elif lunar_day in range(2, 8):
              return "**投放**　观望为主　月初黄历平平，维持昨日预算与出价不变。Meta重点观察新月首日CPM走势，若较昨日上涨超20%暂缓扩量；Google监控核心词质量分变化；TikTok查看昨日素材的2日留存数据，判断内容质量。适合操作的时辰：午时（11:00-13:00）上午数据足够判断当日走势，此时决策比早盘更有依据"
          elif lunar_day in range(8, 15):
              return "**投放**　观望为主　月中前夕黄历中平，宜静观数据勿轻动。Meta记录各广告组今日消耗进度与近7日均值对比，若某组消耗超预期但ROAS差，临时暂停至次日重新评估；Google不调出价，观察当日转化归因数据；TikTok查看各素材的7日累计数据曲线是否出现衰退拐点。适合操作的时辰：未时（13:00-15:00）午后数据趋势已明朗，决策最为稳妥"
          else:
              return "**投放**　观望为主　今日黄历平稳，宜守不宜攻。Meta检查预算消耗进度，预防核心广告组提前断投；Google若精准匹配词消耗偏慢可小幅上调出价3-5%补量；TikTok保持现有投放节奏，不新开计划，不换素材。适合操作的时辰：申时（15:00-17:00）下午流量尚在，小幅调整能在当日收盘前看到效果"

def get_sej_news():
      url = "https://www.searchenginejournal.com/feed/"
      headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}
      try:
          res = requests.get(url, headers=headers, timeout=15)
          import xml.etree.ElementTree as ET
          root = ET.fromstring(res.content)
          channel = root.find("channel")
          items = channel.findall("item")
          result = []
          for item in items[:3]:
              title = item.findtext("title", "").strip()
              link = item.findtext("link", "").strip()
              if title and link:
                  result.append({"title": title, "url": link})
          print(f"SEJ 获取到 {len(result)} 条")
          return result
      except Exception as e:
          print(f"SEJ 获取失败: {e}")
          return []

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


def build_card(cities_data, almanac, sej_news):
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
                      f"📈 {almanac['adTip']}"
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

      if sej_news:
          lines = ["📢 **Search Engine Journal 今日速览**"]
          for i, item in enumerate(sej_news, 1):
              lines.append(f"**{i}. [{item['title']}]({item['url']})**")
          elements.append({
              "tag": "div",
              "text": {"tag": "lark_md", "content": "\n".join(lines)}
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

if not is_workday(date.today()):
      print("今日非工作日，跳过推送")
      sys.exit(0)

cities_data = []
for city in CITIES:
      w = get_weather(city["name"], city["id"])
      cities_data.append({"name": city["name"], "weather": w})

almanac = get_almanac()
sej_news = get_sej_news()
card = build_card(cities_data, almanac, sej_news)
send_to_feishu(card)
print("完成")
