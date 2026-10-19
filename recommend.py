# (画面表示名, タグ)
MOODS = [
    ("甘いもの", "甘い"),
    ("しっかり食べたい", "しっかり"),
    ("軽めに", "軽め"),
    ("すっきりしたい", "すっきり"),
]
TEMPERATURES = [
    ("温かいもの", "温かい"),
    ("冷たいもの", "冷たい"),
]
OPPOSITE_TEMPERATURE = {"温かい": "冷たい", "冷たい": "温かい"}
CAFFEINE_TAG = "カフェイン"
CHILD_AGE = 12  # この年齢以下はお子さまとして扱う


def recommend(menu, item_tags, sales, mood=None, temperature=None, budget=None, age=None, limit=3):
    """条件に合う品をおすすめ順に最大 limit 件返す。

    menu: {カテゴリ: [(品名, 価格)]}、item_tags: {品名: タグ集合}、sales: {品名: 販売数}
    mood / temperature: タグ（None はこだわらない）、budget: 1品あたりの上限金額（None は指定なし）
    age: 召し上がる方の年齢（None は指定なし。値のチェックは画面側で validation.parse_age 済み）
    - 気分が指定されたら、そのタグを持つ品だけを候補にする
    - 温度が指定されたら、反対の温度の品は除き、一致する品を優先する
    - 予算を超える品は除く
    - お子さま（CHILD_AGE 以下）にはカフェイン入りの品を除く
    - 残りは「温度一致 → 販売数が多い → メニュー順」で並べる
    戻り値: [{"name", "price", "category", "reasons": [str]}]
    """
    is_child = age is not None and age <= CHILD_AGE
    candidates = []
    for category, items in menu.items():
        for name, price in items:
            tags = item_tags.get(name, set())
            if mood and mood not in tags:
                continue
            if temperature and OPPOSITE_TEMPERATURE[temperature] in tags:
                continue
            if budget is not None and price > budget:
                continue
            if is_child and CAFFEINE_TAG in tags:
                continue
            candidates.append((name, price, category, tags))

    def sort_key(candidate):
        name, _, _, tags = candidate
        return (temperature in tags, sales.get(name, 0))

    # sorted は安定ソートなので、同点ならメニュー順のまま残る
    ranked = sorted(candidates, key=sort_key, reverse=True)[:limit]

    mood_label = {tag: label for label, tag in MOODS}
    results = []
    for name, price, category, tags in ranked:
        reasons = []
        if mood:
            reasons.append(f"気分「{mood_label[mood]}」にぴったり")
        if temperature and temperature in tags:
            reasons.append(f"{temperature}品")
        if is_child:
            reasons.append("お子さまにも安心（カフェインなし）")
        if sales.get(name, 0) > 0:
            reasons.append(f"人気（これまでに{sales[name]}個）")
        results.append({"name": name, "price": price, "category": category, "reasons": reasons})
    return results
