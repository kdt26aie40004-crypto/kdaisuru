import unicodedata

# カテゴリ名 ->[(品名, 価格(円・税込))]
MENU = {
    "コーヒー": [
        ("ブレンドコーヒー", 480),
        ("アメリカーノ", 500),
        ("カフェラテ", 580),
        ("カプチーノ", 580),
        ("カフェモカ", 620),
        ("アイスコーヒー", 480),
    ],
    "ティー・ソフトドリンク": [
        ("ダージリンティー", 520),
        ("アールグレイ", 520),
        ("抹茶ラテ", 600),
        ("オレンジジュース", 450),
        ("自家製レモネード", 550),
    ],
    "フード": [
        ("ミックスサンドイッチ", 780),
        ("BLTサンド", 850),
        ("ナポリタン", 980),
        ("カルボナーラ", 1080),
        ("オムライス", 1050),
        ("本日のスープセット", 680),
    ],
    "デザート": [
        ("ベイクドチーズケーキ", 550),
        ("ガトーショコラ", 550),
        ("自家製プリン", 480),
        ("フレンチトースト", 750),
        ("バニラアイス", 380),
    ],
}


def format_price(price):
    return f"¥{price:,}"


def display_width(text):
    # 全角文字は端末上で半角2文字分の幅になる
    return sum(2 if unicodedata.east_asian_width(ch) in "FWA" else 1 for ch in text)


def pad(text, width):
    return text + " " * (width - display_width(text))


def show_categories():
    print("\n--- カテゴリ ---")
    for i, category in enumerate(MENU, start=1):
        print(f"{i}. {category}")
    print("0. 戻る")


def show_items(category):
    items = MENU[category]
    width = max(display_width(name) for name, _ in items)
    print(f"\n=== {category} ===")
    for i, (name, price) in enumerate(items, start=1):
        print(f"{i:>2}. {pad(name, width)}  {format_price(price):>7}")
    print(" 0. 戻る")
