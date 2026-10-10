import requests
import os
import sys
import xml.etree.ElementTree as ET
import cnlunar

from datetime import datetime
from zoneinfo import ZoneInfo
from chinese_calendar import is_workday
from email.utils import parsedate_to_datetime
from urllib.parse import quote

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


def get_ad_news():
    """获取北京时间当天的投放运营资讯，最多返回 3 条。"""
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()

    sources = (
        "site:cifnews.com OR site:ebrun.com OR "
        "site:amz123.com OR site:yfchuhai.com"
    )
    markets = (
        "美国 OR 美区 OR 韩国 OR 英国 OR 欧洲 OR 欧盟 "
        "OR Germany OR UK OR US"
    )
    topics = [
        "TikTok OR TikTok Shop",
        "Google Ads OR 谷歌广告",
        "Meta OR Facebook Ads OR Instagram Ads",
    ]

    articles = []
    seen_titles = set()

    for topic in topics:
        query = (
            f"({topic}) "
            f"(广告 OR 投放 OR 运营 OR 店铺 OR GMV Max OR AI Max) "
            f"({markets}) "
            f"({sources}) when:1d"
        )
        url = (
            "https://news.google.com/rss/search"
            f"?q={quote(query)}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        )

        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            response.raise_for_status()
            root = ET.fromstring(response.content)

            for item in root.findall("./channel/item"):
                raw_title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                published = (item.findtext("pubDate") or "").strip()

                if not raw_title or not link or not published:
                    continue

                try:
                    published_at = parsedate_to_datetime(
                        published
                    ).astimezone(ZoneInfo("Asia/Shanghai"))
                except (TypeError, ValueError):
                    continue

                # 只展示北京时间今天发布的文章
                if published_at.date() != today:
                    continue

                source = (item.findtext("source") or "").strip()
                title = raw_title

                # Google News 标题常在末尾附加“ - 媒体名”
                if source and title.endswith(f" - {source}"):
                    title = title[: -(len(source) + 3)].strip()

                key = title.casefold()
                if key in seen_titles:
                    continue

                seen_titles.add(key)
                articles.append({
                    "title": title,
                    "url": link,
                    "source": source or "行业媒体",
                    "published_at": published_at,
                })

        except Exception as error:
            print(f"投放运营资讯获取失败：{error}")
            continue

    # 按发布时间选最新三条；不是阅读量/热度排行榜
    articles.sort(
        key=lambda article: article["published_at"],
        reverse=True,
    )
    return articles[:3]


def get_almanac():
    today = datetime.now(ZoneInfo("Asia/Shanghai"))

    try:
        # cnlunar 内部使用不带时区的 datetime；
        # 先取北京时间日期，再构造当天日期。
        lunar = cnlunar.Lunar(
            datetime(today.year, today.month, today.day)
        )

        month = lunar.lunarMonthCn.rstrip("大小")
        lunar_str = (
            f"{lunar.lunarYear}年（{lunar.year8Char}年）"
            f"{month}{lunar.lunarDayCn}"
        )

        solar_term = (
            lunar.todaySolarTerms
            if lunar.todaySolarTerms != "无"
            else ""
        )

        return {
            "lunarStr": lunar_str,
            "yi": "、".join(lunar.goodThing),
            "ji": "、".join(lunar.badThing),
            "solarTerm": solar_term,
        }

    except Exception as error:
        print(f"黄历计算失败：{error}")
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


def short_outfit(w):
    feels = int(w.get("feelsLike", w.get("temp", 20)))

    if feels >= 35:
        return "背心短裤"
    if feels >= 28:
        return "短袖短裤"
    if feels >= 20:
        return "短袖/薄外套"
    if feels >= 12:
        return "薄外套/毛衣"
    if feels >= 5:
        return "厚外套/毛衣"
    return "羽绒服/围巾"


def short_umbrella(w):
    text = str(w.get("text", ""))

    if float(w.get("precip", 0)) > 0 or any(
        word in text for word in ("雨", "雷", "雪", "冻")
    ):
        return "带伞"

    if int(w.get("humidity", 60)) > 85:
        return "备伞"

    return "无需带伞"


def short_sunscreen(w):
    text = str(w.get("text", ""))
    temp = int(w.get("temp", 20))

    if any(word in text for word in ("晴", "少云")):
        return "加强防晒" if temp >= 28 else "注意防晒"

    if any(word in text for word in ("多云", "阴")):
        return "适当防晒"

    return "按需防晒"


def weather_column(city):
    name = city["name"]
    w = city["weather"]

    if w is None:
        rows = [
            f"**📍 {name}**",
            "🌤 天气暂缺",
            "🌡 体感 —",
            "💧湿度— · 👁能见度—",
            "💨风力— · 🔵气压—",
            "👕 穿搭待确认",
            "☂️天气待确认 · 🧴按需防晒",
        ]
    else:
        weather = str(w.get("text", "未知"))[:4]
        wind = str(w.get("windDir", "未知"))[:3]

        rows = [
            f"**📍 {name}**",
            f"🌤 {weather} · {w.get('temp', '—')}°C",
            f"🌡 体感 {w.get('feelsLike', '—')}°C",
            f"💧{w.get('humidity', '—')}% · 👁{w.get('vis', '—')}km",
            f"💨{wind}{w.get('windScale', '—')}级 · 🔵{w.get('pressure', '—')}hPa",
            f"👕 {short_outfit(w)}",
            f"☂️{short_umbrella(w)} · 🧴{short_sunscreen(w)}",
        ]

    return {
        "tag": "column",
        "width": "weighted",
        "weight": 1,
        "vertical_align": "top",
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "\n".join(rows),
                },
            }
        ],
    }


def build_card(cities_data, almanac, ad_news):
    today = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y年%m月%d日")
    elements = []

    if almanac:
        solar_str = (
            f"　🌿 {almanac['solarTerm']}"
            if almanac.get("solarTerm")
            else ""
        )

        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"**📅 {today}**　农历 {almanac['lunarStr']}{solar_str}\n"
                    f"✅ **宜**　{almanac['yi']}\n"
                    f"❌ **忌**　{almanac['ji']}"
                ),
            },
        })
        elements.append({"tag": "hr"})

    elements.append({
        "tag": "column_set",
        "flex_mode": "none",
        "columns": [
            weather_column(city)
            for city in cities_data
        ],
    })

    if ad_news:
        elements.append({"tag": "hr"})
        lines = ["📡 **投放运营雷达**"]

        for index, article in enumerate(ad_news, 1):
            time_text = article["published_at"].strftime("%H:%M")
            lines.append(
                f"{index}. [{article['title']}]({article['url']})\n"
                f"{article['source']} · 今日 {time_text}"
            )

        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "\n\n".join(lines),
            },
        })

    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🌈 每日天气 & 黄历播报",
                },
                "template": "blue",
            },
            "elements": elements,
        },
    }

def send_to_feishu(card):
    try:
        res = requests.post(FEISHU_WEBHOOK, json=card, timeout=10)
        print(f"飞书响应: {res.status_code} {res.text}")
    except Exception as e:
        print(f"飞书推送失败: {e}")
        sys.exit(1)


today_cn = datetime.now(ZoneInfo("Asia/Shanghai")).date()
if not is_workday(today_cn):
    print("今日非工作日，跳过推送")
    sys.exit(0)

cities_data = []
for city in CITIES:
    w = get_weather(city["name"], city["id"])
    cities_data.append({
        "name": city["name"],
        "weather": w,
    })

almanac = get_almanac()
ad_news = get_ad_news()
card = build_card(cities_data, almanac, ad_news)
send_to_feishu(card)
print("完成")
