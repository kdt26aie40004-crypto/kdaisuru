class OrderError(Exception):
    pass


class Order:
    """注文の明細を保持する。会計後は変更できない。"""

    MAX_QUANTITY = 99

    def __init__(self):
        # 明細: [{"name", "price", "quantity"}]（同じ品は1行にまとめる）
        self.lines = []
        self.checked_out = False

    def _ensure_open(self):
        if self.checked_out:
            raise OrderError("会計済みの注文は変更できません。")

    def _validate_quantity(self, quantity):
        if not 1 <= quantity <= self.MAX_QUANTITY:
            raise OrderError(f"数量は1〜{self.MAX_QUANTITY}で指定してください。")

    def add(self, name, price, quantity):
        self._ensure_open()
        self._validate_quantity(quantity)
        for line in self.lines:
            if line["name"] == name:
                if line["quantity"] + quantity > self.MAX_QUANTITY:
                    raise OrderError(f"1品あたりの数量は{self.MAX_QUANTITY}までです。")
                line["quantity"] += quantity
                return
        self.lines.append({"name": name, "price": price, "quantity": quantity})

    def cancel(self, index, quantity=None):
        """明細 index を取り消す。quantity 省略時はその品をすべて取り消す。"""
        self._ensure_open()
        if not 0 <= index < len(self.lines):
            raise OrderError("指定された注文がありません。")
        line = self.lines[index]
        if quantity is None or quantity == line["quantity"]:
            del self.lines[index]
            return
        if not 1 <= quantity < line["quantity"]:
            raise OrderError(f"取り消す数量は1〜{line['quantity']}で指定してください。")
        line["quantity"] -= quantity

    def total(self):
        return sum(line["price"] * line["quantity"] for line in self.lines)

    def is_empty(self):
        return not self.lines

    def checkout(self):
        self._ensure_open()
        if self.is_empty():
            raise OrderError("注文がありません。")
        self.checked_out = True
        return self.total()
