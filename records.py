import csv
from datetime import datetime
from pathlib import Path

ORDERS_FILE = Path(__file__).parent / "data" / "orders.csv"

HEADER = ["注文ID", "日時", "品名", "単価", "数量", "小計", "注文合計"]


def save_order(order, path=ORDERS_FILE):
    """注文を明細1行ずつ CSV に追記し、注文IDを返す。"""
    now = datetime.now()
    order_id = now.strftime("%Y%m%d-%H%M%S")
    ordered_at = now.strftime("%Y-%m-%d %H:%M:%S")
    total = order.total()

    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    # utf-8-sig: Excel で開いても文字化けしないよう BOM を付ける
    with path.open("a", newline="", encoding="utf-8-sig" if is_new else "utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(HEADER)
        for line in order.lines:
            writer.writerow([
                order_id,
                ordered_at,
                line["name"],
                line["price"],
                line["quantity"],
                line["price"] * line["quantity"],
                total,
            ])
    return order_id


def load_orders(path=ORDERS_FILE):
    """記録された注文を読み込み、注文ごとにまとめて古い順に返す。

    戻り値: [{"id", "ordered_at", "lines": [{"name", "price", "quantity"}], "total"}]
    """
    if not path.exists():
        return []
    orders = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                line = {
                    "name": row["品名"],
                    "price": int(row["単価"]),
                    "quantity": int(row["数量"]),
                }
            except (KeyError, TypeError, ValueError):
                continue  # 手作業で壊れた行などは読み飛ばす
            order = orders.setdefault(row["注文ID"], {
                "id": row["注文ID"],
                "ordered_at": row["日時"],
                "lines": [],
            })
            order["lines"].append(line)
    for order in orders.values():
        order["total"] = sum(l["price"] * l["quantity"] for l in order["lines"])
    return list(orders.values())


def summarize(orders, category_of):
    """注文の集計結果を返す。category_of は品名からカテゴリ名を返す関数。"""
    by_date = {}
    by_item = {}
    by_category = {}
    for order in orders:
        date = order["ordered_at"][:10]
        day = by_date.setdefault(date, {"orders": 0, "sales": 0})
        day["orders"] += 1
        day["sales"] += order["total"]
        for line in order["lines"]:
            subtotal = line["price"] * line["quantity"]
            item = by_item.setdefault(line["name"], {"quantity": 0, "sales": 0})
            item["quantity"] += line["quantity"]
            item["sales"] += subtotal
            category = by_category.setdefault(category_of(line["name"]), {"quantity": 0, "sales": 0})
            category["quantity"] += line["quantity"]
            category["sales"] += subtotal

    total_sales = sum(order["total"] for order in orders)

    def by_sales(d):
        return sorted(d.items(), key=lambda kv: kv[1]["sales"], reverse=True)

    return {
        "order_count": len(orders),
        "total_sales": total_sales,
        "average": total_sales // len(orders) if orders else 0,
        "by_date": sorted(by_date.items()),
        "by_item": by_sales(by_item),
        "by_category": by_sales(by_category),
    }


def load_item_sales(path=ORDERS_FILE):
    """記録から品名ごとの販売数を返す。読めなければ空（人気は考慮しない）。"""
    try:
        orders = load_orders(path)
    except OSError:
        return {}
    sales = {}
    for order in orders:
        for line in order["lines"]:
            sales[line["name"]] = sales.get(line["name"], 0) + line["quantity"]
    return sales
