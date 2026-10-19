"""コンソール版の画面。`python main.py --cli` で起動する。"""

from menu import ITEM_TAGS, MENU, STORE_NAME, category_of, display_width, format_price, pad, show_categories, show_items
from order import Order, OrderError
from recommend import MOODS, TEMPERATURES, recommend
from records import load_item_sales, load_orders, save_order, summarize
from validation import InputError, parse_age, parse_budget, parse_int


def show_store_name():
    print(STORE_NAME)


def ask_number(prompt, max_value):
    """0〜max_value の番号を入力させる。無効な入力なら理由を表示して None を返す。"""
    try:
        return parse_int(input(prompt), "番号", 0, max_value)
    except InputError as e:
        print(f"{e}表示されている番号を入力してください。")
        return None


def ask_until_valid(prompt, parse):
    """parse が通るまで入力を繰り返す。parse は不正な入力に InputError を送出する。"""
    while True:
        try:
            return parse(input(prompt))
        except InputError as e:
            print(e)


def ask_quantity(prompt):
    """数量（1〜上限）を入力させる。空入力なら None。"""
    return ask_until_valid(prompt, lambda text: parse_int(text, "数量", 1, Order.MAX_QUANTITY, required=False))


def show_order(order):
    if order.is_empty():
        print("\n注文はまだありません。")
        return
    width = max(display_width(line["name"]) for line in order.lines)
    print("\n=== ご注文内容 ===")
    for i, line in enumerate(order.lines, start=1):
        subtotal = line["price"] * line["quantity"]
        print(f"{i:>2}. {pad(line['name'], width)}  x{line['quantity']:<2}  {format_price(subtotal):>8}")
    print(f"    {pad('合計', width)}       {format_price(order.total()):>8}")


def order_from_category(order, category):
    items = MENU[category]
    while True:
        show_items(category)
        choice = ask_number("注文する品の番号を入力してください: ", len(items))
        if choice is None:
            continue
        if choice == 0:
            return
        name, price = items[choice - 1]
        quantity = ask_quantity(f"{name} の数量 (Enterで1): ")
        try:
            order.add(name, price, 1 if quantity is None else quantity)
        except OrderError as e:
            print(e)
            continue
        print(f"{name} を追加しました。")


def browse_menu(order):
    categories = list(MENU)
    while True:
        show_categories()
        choice = ask_number("カテゴリ番号を入力してください: ", len(categories))
        if choice is None:
            continue
        if choice == 0:
            return
        order_from_category(order, categories[choice - 1])


def manage_order(order):
    while True:
        show_order(order)
        if order.is_empty():
            return
        print(" 0. 戻る")
        choice = ask_number("取り消す注文の番号を入力してください: ", len(order.lines))
        if choice is None:
            continue
        if choice == 0:
            return
        line = order.lines[choice - 1]
        quantity = ask_quantity(f"{line['name']} を取り消す数量 (Enterですべて): ")
        name = line["name"]
        try:
            order.cancel(choice - 1, quantity)
        except OrderError as e:
            print(e)
            continue
        print(f"{name} の注文を取り消しました。")


def checkout(order):
    """会計する。会計が完了したら True を返す。"""
    if order.is_empty():
        print("\n注文がありません。")
        return False
    show_order(order)
    if input("この内容で会計しますか？ (y/n): ").strip().lower() != "y":
        print("会計を中止しました。")
        return False
    # 記録できなかった注文を会計済みにしないよう、記録を先に行う
    try:
        order_id = save_order(order)
    except OSError as e:
        print(f"注文の記録に失敗しました（{e}）。")
        print("記録ファイルを開いている場合は閉じてから、もう一度会計してください。")
        return False
    total = order.checkout()
    print(f"注文ID {order_id} として記録しました。")
    print(f"お会計は {format_price(total)} です。ありがとうございました。")
    return True


def ask_choice(title, options):
    """options: [(表示名, 値)] から選ばせる。0 は「こだわらない」で None を返す。"""
    while True:
        print(f"\n{title}")
        for i, (label, _) in enumerate(options, start=1):
            print(f"{i}. {label}")
        print("0. こだわらない")
        choice = ask_number("番号を入力してください: ", len(options))
        if choice is not None:
            return options[choice - 1][1] if choice else None


def ask_budget():
    """1品あたりの予算を入力させる。空入力なら None（指定なし）。"""
    return ask_until_valid("\n1品あたりのご予算（円、Enterで指定なし）: ", parse_budget)


def ask_age():
    """年齢を入力させる。空入力なら None（指定なし）。"""
    return ask_until_valid("\n召し上がる方の年齢（Enterで指定なし）: ", parse_age)


def recommend_menu(order):
    mood = ask_choice("今の気分は？", MOODS)
    temperature = ask_choice("温かいもの・冷たいもの、どちらがいいですか？", TEMPERATURES)
    budget = ask_budget()
    age = ask_age()
    results = recommend(MENU, ITEM_TAGS, load_item_sales(), mood, temperature, budget, age)
    if not results:
        print("\n条件に合うおすすめが見つかりませんでした。条件を変えてお試しください。")
        return

    width = max(display_width(r["name"]) for r in results)
    while True:
        print("\n=== おすすめ ===")
        for i, r in enumerate(results, start=1):
            print(f"{i}. {pad(r['name'], width)}  {format_price(r['price']):>7}  （{r['category']}）")
            if r["reasons"]:
                print(f"     {' / '.join(r['reasons'])}")
        print("0. 戻る")
        choice = ask_number("注文する場合は番号を入力してください: ", len(results))
        if choice is None:
            continue
        if choice == 0:
            return
        item = results[choice - 1]
        quantity = ask_quantity(f"{item['name']} の数量 (Enterで1): ")
        try:
            order.add(item["name"], item["price"], 1 if quantity is None else quantity)
        except OrderError as e:
            print(e)
            continue
        print(f"{item['name']} を追加しました。")


def show_order_history(orders):
    print(f"\n=== 注文一覧（{len(orders)}件） ===")
    for order in orders:
        print(f"\n[{order['id']}] {order['ordered_at']}  合計 {format_price(order['total'])}")
        width = max(display_width(line["name"]) for line in order["lines"])
        for line in order["lines"]:
            subtotal = line["price"] * line["quantity"]
            print(f"    {pad(line['name'], width)}  x{line['quantity']:<2}  {format_price(subtotal):>8}")


def show_ranking(title, rows):
    """rows: [(名前, {"quantity", "sales"})] を売上順の表として表示する。"""
    width = max(display_width(name) for name, _ in rows)
    print(f"\n--- {title} ---")
    for rank, (name, data) in enumerate(rows, start=1):
        print(f"{rank:>2}. {pad(name, width)}  {data['quantity']:>4}個  {format_price(data['sales']):>9}")


def show_summary(orders):
    summary = summarize(orders, category_of)
    print("\n=== 売上集計 ===")
    print(f"注文件数: {summary['order_count']}件")
    print(f"売上合計: {format_price(summary['total_sales'])}")
    print(f"平均客単価: {format_price(summary['average'])}")
    print("\n--- 日別売上 ---")
    for date, data in summary["by_date"]:
        print(f"{date}  {data['orders']:>3}件  {format_price(data['sales']):>9}")
    show_ranking("カテゴリ別売上", summary["by_category"])
    show_ranking("品目別売上ランキング", summary["by_item"])


def history_menu():
    while True:
        print("\n--- 注文履歴・集計 ---")
        print("1. 注文一覧")
        print("2. 売上集計")
        print("0. 戻る")
        choice = ask_number("番号を入力してください: ", 2)
        if choice is None:
            continue
        if choice == 0:
            return
        try:
            orders = load_orders()
        except OSError as e:
            print(f"注文記録を読み込めませんでした（{e}）。")
            continue
        if not orders:
            print("\n記録された注文はまだありません。")
        elif choice == 1:
            show_order_history(orders)
        else:
            show_summary(orders)


def main():
    show_store_name()
    order = Order()
    while True:
        print("\n--- メイン ---")
        print("1. メニューを見る・注文する")
        print("2. 注文内容の確認・取り消し")
        print("3. 会計する")
        print("4. 注文履歴・集計")
        print("5. おすすめを聞く")
        print("0. 終了")
        choice = ask_number("番号を入力してください: ", 5)
        if choice == 0:
            break
        if choice == 1:
            browse_menu(order)
        elif choice == 2:
            manage_order(order)
        elif choice == 3 and checkout(order):
            break
        elif choice == 4:
            history_menu()
        elif choice == 5:
            recommend_menu(order)


def run():
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n終了します。")
