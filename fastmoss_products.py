import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# 请替换为重新生成的密钥和 Webhook，不要使用之前已暴露的旧值
FASTMOSS_API_KEY = "填写新的_FASTMOSS_API_KEY"
FEISHU_WEBHOOK_URL = "填写新的_飞书_WEBHOOK"

# 市场：美国 US、英国 GB、德国 DE、法国 FR、墨西哥 MX 等
REGION = "US"

# 留空代表全部类目；如果有 FastMoss 类目 ID，可填写数字
CATEGORY_ID = None

# 每个榜单展示数量
PAGE_SIZE = 10


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


def format_products(products, report_type):
    if not products:
        return "暂无数据"

    lines = []

    for index, item in enumerate(products, start=1):
        currency = item.get("currency", "")

        if report_type == "new":
            metrics = (
                f"3日销量：{number(item.get('day3_units_sold'))}｜"
                f"3日GMV：{currency} {number(item.get('day3_gmv'))}"
            )
        elif report_type == "promoted":
            metrics = (
                f"销量：{number(item.get('units_sold'))}｜"
                f"GMV：{currency} {number(item.get('gmv'))}｜"
                f"关联达人：{number(item.get('affiliate_count'))}"
            )
        else:
            metrics = (
                f"销量：{number(item.get('units_sold'))}｜"
                f"GMV：{currency} {number(item.get('gmv'))}"
            )

            if item.get("growth_rate") is not None:
                metrics += f"｜增长率：{item['growth_rate']}%"

        lines.append(
            f"{index}. {product_title(item)}\n"
            f"   {metrics}\n"
            f"   商品ID：{product_id(item)}"
        )

    return "\n".join(lines)


def send_to_feishu(message):
    payload = {
        "msg_type": "text",
        "content": {
            "text": message,
        },
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
    if "填写新的" in FASTMOSS_API_KEY:
        raise RuntimeError("请先填写新的 FastMoss API Key")

    if "填写新的" in FEISHU_WEBHOOK_URL:
        raise RuntimeError("请先填写新的飞书 Webhook")

    print("正在获取 FastMoss 数据……")

    top_selling = get_top_selling()
    new_products = get_new_products()
    most_promoted = get_most_promoted()

    report = "\n".join(
        [
            "📊 FastMoss 跨境产品趋势报告",
            f"日期：{china_date()}",
            f"市场：{REGION}",
            "",
            "🔥 GMV 热销商品榜",
            format_products(top_selling, "selling"),
            "",
            "🌱 三日潜力新品榜",
            format_products(new_products, "new"),
            "",
            "📣 达人推广商品榜",
            format_products(most_promoted, "promoted"),
            "",
            "提示：请结合采购成本、物流费用、利润和合规风险进行判断。",
            "数据来源：FastMoss OpenAPI",
        ]
    )

    # 防止消息过长
    send_to_feishu(report[:19000])
    print("飞书推送成功")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"运行失败：{error}")
        raise
