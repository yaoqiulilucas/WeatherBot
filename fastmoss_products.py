import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


FASTMOSS_API_KEY = os.environ["FASTMOSS_API_KEY"]
FEISHU_WEBHOOK_URL = os.environ["FEISHU_WEBHOOK_URL"]

REGION = os.getenv("REGION") or "US"

category_value = os.getenv("CATEGORY_ID", "").strip()
CATEGORY_ID = int(category_value) if category_value else None

PAGE_SIZE = int(os.getenv("PAGE_SIZE") or "5")


def china_date(days_ago=0):
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    target = now - timedelta(days=days_ago)
    return target.strftime("%Y-%m-%d")


def fastmoss_request(api_path, request_body):
    url = f"https://openapi.fastmoss.com{api_path}"

    data = json.dumps(request_body).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {FASTMOSS_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        response_text = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"FastMoss HTTP {error.code}: {response_text}"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"无法连接 FastMoss：{error}") from error

    if result.get("code") != 0:
        raise RuntimeError(
            f"FastMoss 接口错误：{json.dumps(result, ensure_ascii=False)}"
        )

    return result.get("data", {}).get("list", [])


def create_filter(days_ago):
    filters = {
        "region": REGION,
        "is_cross_border": 1,
        "date_info": {
            "type": "day",
            "value": china_date(days_ago),
        },
    }

    if CATEGORY_ID is not None:
        filters["category_id"] = CATEGORY_ID

    return filters


def get_top_selling():
    return fastmoss_request(
        "/product/v1/rank/topSelling",
        {
            "filter": create_filter(1),
            "orderby": [
                {
                    "field": "gmv",
                    "order": "desc",
                }
            ],
            "page": 1,
            "pagesize": PAGE_SIZE,
        },
    )


def get_new_products():
    # FastMoss 新品榜要求查询三天前的日期
    return fastmoss_request(
        "/product/v1/rank/newListed",
        {
            "filter": create_filter(3),
            "orderby": [
                {
                    "field": "day3_units_sold",
                    "order": "desc",
                }
            ],
            "page": 1,
            "pagesize": PAGE_SIZE,
        },
    )


def get_most_promoted():
    return fastmoss_request(
        "/product/v1/rank/mostPromoted",
        {
            "filter": create_filter(1),
            "orderby": [
                {
                    "field": "affiliate_count",
                    "order": "desc",
                }
            ],
            "page": 1,
            "pagesize": PAGE_SIZE,
        },
    )


def number(value):
    if value is None:
        return "-"

    if isinstance(value, (int, float)):
        return f"{value:,.2f}".rstrip("0").rstrip(".")

    return str(value)


def product_title(item):
    title = item.get("title")

    if not title and isinstance(item.get("product"), dict):
        title = item["product"].get("title")

    return (title or "未命名商品").replace("\n", " ")[:70]


def product_id(item):
    value = item.get("product_id")

    if not value and isinstance(item.get("product"), dict):
        value = item["product"].get("product_id")

    return value or "-"

def product_link(item):
    # 如果接口直接返回 FastMoss 链接，优先使用
    direct_url = item.get("fastmoss_url")

    if not direct_url and isinstance(item.get("product"), dict):
        direct_url = item["product"].get("fastmoss_url")

    if direct_url:
        return direct_url

    # 排行榜接口通常只返回 product_id，因此自行生成 FastMoss 详情链接
    current_product_id = product_id(item)

    if current_product_id == "-":
        return ""

    return (
        "https://www.fastmoss.com/zh/e-commerce/detail/"
        f"{current_product_id}"
    )


def format_products(products, report_type):
    if not products:
        return "暂无符合条件的商品"

    lines = []

    for index, item in enumerate(products[:5], start=1):
        title = product_title(item)
        link = product_link(item)
        currency = item.get("currency", "")

        if report_type == "new":
            metrics = (
                f"销量 **{number(item.get('day3_units_sold'))}** · "
                f"GMV **{currency} "
                f"{number(item.get('day3_gmv'))}**"
            )

        elif report_type == "promoted":
            metrics = (
                f"销量 **{number(item.get('units_sold'))}** · "
                f"GMV **{currency} "
                f"{number(item.get('gmv'))}** · "
                f"达人 **{number(item.get('affiliate_count'))}**"
            )

        else:
            metrics = (
                f"销量 **{number(item.get('units_sold'))}** · "
                f"GMV **{currency} "
                f"{number(item.get('gmv'))}**"
            )

            if item.get("growth_rate") is not None:
                metrics += (
                    f" · 增长 **{item['growth_rate']}%**"
                )

        if link:
            link_text = f"[🔗 查看商品详情]({link})"
        else:
            link_text = "暂无商品链接"

        lines.append(
            f"**{index}. {title}**\n"
            f"{metrics}\n"
            f"{link_text}"
        )

    return "\n\n".join(lines)

def build_report_card(
    top_selling,
    new_products,
    most_promoted,
):
    category_text = (
        f"类目 {CATEGORY_ID}"
        if CATEGORY_ID is not None
        else "全部类目"
    )

    return {
        "config": {
            "wide_screen_mode": True,
            "enable_forward": True,
        },
        "header": {
            "template": "blue",
            "title": {
                "tag": "plain_text",
                "content": "📊 FastMoss 跨境产品趋势日报",
            },
            "subtitle": {
                "tag": "plain_text",
                "content": f"{REGION} 市场 · {category_text}",
            },
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"📅 **数据日期：** {china_date()}\n"
                        f"🌎 **目标市场：** {REGION}\n"
                        f"📦 **商品范围：** 跨境商品"
                    ),
                },
            },
            {
                "tag": "hr",
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        "🔥 **GMV 热销榜 TOP 5**\n\n"
                        + format_products(
                            top_selling,
                            "selling",
                        )
                    ),
                },
            },
            {
                "tag": "hr",
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        "🌱 **三日潜力新品 TOP 5**\n\n"
                        + format_products(
                            new_products,
                            "new",
                        )
                    ),
                },
            },
            {
                "tag": "hr",
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        "📣 **达人推广增长榜 TOP 5**\n\n"
                        + format_products(
                            most_promoted,
                            "promoted",
                        )
                    ),
                },
            },
            {
                "tag": "hr",
            },
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": (
                            "数据来源：FastMoss OpenAPI｜"
                            "榜单仅用于发现趋势，请结合利润、"
                            "物流和合规风险进行判断。"
                        ),
                    }
                ],
            },
        ],
    }


def send_to_feishu(card):
    payload = {
        "msg_type": "interactive",
        "card": card,
    }

    request = urllib.request.Request(
        FEISHU_WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        response_text = error.read().decode(
            "utf-8",
            errors="replace",
        )
        raise RuntimeError(
            f"飞书 HTTP {error.code}: {response_text}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"无法连接飞书：{error}"
        ) from error

    code = result.get(
        "code",
        result.get("StatusCode", 0),
    )

    if code != 0:
        raise RuntimeError(
            "飞书推送失败："
            + json.dumps(result, ensure_ascii=False)
        )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        response_text = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"飞书 HTTP {error.code}: {response_text}"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"无法连接飞书：{error}") from error

    code = result.get("code", result.get("StatusCode", 0))

    if code != 0:
        raise RuntimeError(
            f"飞书推送失败：{json.dumps(result, ensure_ascii=False)}"
        )


def main():
    print("正在获取 FastMoss 数据……")

    top_selling = get_top_selling()
    new_products = get_new_products()
    most_promoted = get_most_promoted()

    card = build_report_card(
        top_selling=top_selling,
        new_products=new_products,
        most_promoted=most_promoted,
    )

    send_to_feishu(card)

    print("FastMoss 飞书趋势卡片推送成功")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"运行失败：{error}")
        raise
