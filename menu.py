import unicodedata

STORE_NAME = "ブルー・アルバ"

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

# 品名 -> おすすめ判定用のタグ。MENU に品を追加したらここにも追加する。
# 気分: 甘い / しっかり / 軽め / すっきり、温度: 温かい / 冷たい（どちらでもない品は付けない）
# カフェイン: カフェイン入りの品（お子さまへのおすすめから除く）
ITEM_TAGS = {
    "ブレンドコーヒー": {"カフェイン", "温かい", "すっきり"},
    "アメリカーノ": {"カフェイン", "温かい", "すっきり"},
    "カフェラテ": {"カフェイン", "温かい"},
    "カプチーノ": {"カフェイン", "温かい"},
    "カフェモカ": {"カフェイン", "温かい", "甘い"},
    "アイスコーヒー": {"カフェイン", "冷たい", "すっきり"},
    "ダージリンティー": {"カフェイン", "温かい", "すっきり"},
    "アールグレイ": {"カフェイン", "温かい", "すっきり"},
    "抹茶ラテ": {"カフェイン", "温かい", "甘い"},
    "オレンジジュース": {"冷たい", "すっきり"},
    "自家製レモネード": {"冷たい", "すっきり"},
    "ミックスサンドイッチ": {"軽め"},
    "BLTサンド": {"軽め"},
    "ナポリタン": {"温かい", "しっかり"},
    "カルボナーラ": {"温かい", "しっかり"},
    "オムライス": {"温かい", "しっかり"},
    "本日のスープセット": {"温かい", "軽め"},
    "ベイクドチーズケーキ": {"甘い"},
    "ガトーショコラ": {"甘い"},
    "自家製プリン": {"冷たい", "甘い"},
    "フレンチトースト": {"温かい", "甘い"},
    "バニラアイス": {"冷たい", "甘い", "軽め"},
}


# アレルギー表示の対象（食品表示で表示義務のある特定原材料8品目）。ボタンや表示はこの順で並べる。
ALLERGENS = ["えび", "かに", "くるみ", "小麦", "そば", "卵", "乳", "落花生"]

# 品名 -> 含まれる特定原材料。MENU に品を追加したらここにも追加する。
# ※一般的なレシピを想定した仮のデータ。実際に提供する前に、必ず店舗のレシピ・仕入れ品で確認すること。
ITEM_ALLERGENS = {
    "ブレンドコーヒー": set(),
    "アメリカーノ": set(),
    "カフェラテ": {"乳"},
    "カプチーノ": {"乳"},
    "カフェモカ": {"乳"},
    "アイスコーヒー": set(),
    "ダージリンティー": set(),
    "アールグレイ": set(),
    "抹茶ラテ": {"乳"},
    "オレンジジュース": set(),
    "自家製レモネード": set(),
    "ミックスサンドイッチ": {"小麦", "卵", "乳"},
    "BLTサンド": {"小麦", "卵"},
    "ナポリタン": {"小麦", "乳"},
    "カルボナーラ": {"小麦", "卵", "乳"},
    "オムライス": {"卵", "乳"},
    "本日のスープセット": {"小麦", "乳"},
    "ベイクドチーズケーキ": {"小麦", "卵", "乳"},
    "ガトーショコラ": {"小麦", "卵", "乳"},
    "自家製プリン": {"卵", "乳"},
    "フレンチトースト": {"小麦", "卵", "乳"},
    "バニラアイス": {"卵", "乳"},
}


def allergens_of(name):
    """品に含まれる特定原材料を ALLERGENS の順で返す。"""
    contained = ITEM_ALLERGENS.get(name, set())
    return [a for a in ALLERGENS if a in contained]


def format_allergens(name):
    if name not in ITEM_ALLERGENS:
        return "情報なし"
    return "・".join(allergens_of(name)) or "なし"


def is_hidden_by_allergens(name, excluded):
    """除外するアレルギー excluded のどれかを含む品なら True。
    アレルギー情報が登録されていない品は、安全のため絞り込み中は隠す。"""
    if not excluded:
        return False
    if name not in ITEM_ALLERGENS:
        return True
    return bool(ITEM_ALLERGENS[name] & set(excluded))


def filter_menu(menu, excluded):
    """除外するアレルギーを含む品を取り除いたメニューを返す（カテゴリは残す）。"""
    return {
        category: [(name, price) for name, price in items if not is_hidden_by_allergens(name, excluded)]
        for category, items in menu.items()
    }


def category_of(name):
    """品名のカテゴリを返す。現在のメニューにない品は「その他」。"""
    for category, items in MENU.items():
        if any(item_name == name for item_name, _ in items):
            return category
    return "その他"


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


def show_items(category, items, hidden_count=0):
    """items: 表示する [(品名, 価格)]（アレルギーで絞り込み済み）。hidden_count: 絞り込みで隠した品数。"""
    print(f"\n=== {category} ===")
    if hidden_count:
        print(f"（アレルギーの絞り込みで {hidden_count}品を非表示中）")
    if not items:
        print("このカテゴリに表示できる品はありません。")
    else:
        width = max(display_width(name) for name, _ in items)
        for i, (name, price) in enumerate(items, start=1):
            print(f"{i:>2}. {pad(name, width)}  {format_price(price):>7}  アレルギー: {format_allergens(name)}")
    print(" 0. 戻る")
