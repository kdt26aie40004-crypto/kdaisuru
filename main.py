from menu import MENU, display_width, format_price, pad, show_categories, show_items
from order import Order, OrderError

STORE_NAME = "ブルー・アルバ"


def show_store_name():
    print(STORE_NAME)


def ask_number(prompt, max_value):
    """0〜max_value の番号を入力させる。無効な入力なら None を返す。"""
    choice = input(prompt).strip()
    if choice.isdigit() and 0 <= int(choice) <= max_value:
        return int(choice)
    print("無効な入力です。表示されている番号を入力してください。")
    return None


def ask_quantity(prompt):
    """数量を入力させる。空入力なら None、数字以外なら 0 を返す（0 は Order 側で弾かれる）。"""
    text = input(prompt).strip()
    if text == "":
        return None
    return int(text) if text.isdigit() else 0


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
    total = order.checkout()
    print(f"お会計は {format_price(total)} です。ありがとうございました。")
    return True


def main():
    show_store_name()
    order = Order()
    while True:
        print("\n--- メイン ---")
        print("1. メニューを見る・注文する")
        print("2. 注文内容の確認・取り消し")
        print("3. 会計する")
        print("0. 終了")
        choice = ask_number("番号を入力してください: ", 3)
        if choice == 0:
            break
        if choice == 1:
            browse_menu(order)
        elif choice == 2:
            manage_order(order)
        elif choice == 3 and checkout(order):
            break


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n終了します。")
