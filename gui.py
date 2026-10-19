"""ウィンドウ版の画面（tkinter）。`python main.py` で起動する。"""

import tkinter as tk
from tkinter import messagebox, ttk

from menu import ALLERGENS, ITEM_TAGS, MENU, STORE_NAME, category_of, filter_menu, format_allergens, format_price
from order import Order, OrderError
from recommend import CHILD_AGE, MOODS, TEMPERATURES, recommend
from records import load_item_sales, load_orders, save_order, summarize
from validation import InputError, parse_age, parse_budget, parse_int

FONT_FAMILY = "Yu Gothic UI"
PRICES = {name: price for items in MENU.values() for name, price in items}


def make_tree(parent, columns, height=10, show="headings"):
    """スクロールバー付きの表を作る。columns: [(キー, 見出し, 幅, 寄せ)]。(枠, 表) を返す。"""
    frame = ttk.Frame(parent)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show=show, height=height, selectmode="browse")
    for key, heading, width, anchor in columns:
        tree.heading(key, text=heading)
        tree.column(key, width=width, anchor=anchor, stretch=anchor == "w")
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return frame, tree


def make_quantity_box(parent, variable):
    return ttk.Spinbox(parent, from_=1, to=Order.MAX_QUANTITY, width=4, textvariable=variable, justify="right")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{STORE_NAME} 注文システム")
        self.geometry("1000x640")
        self.minsize(840, 540)
        self.order = Order()
        self._setup_style()
        self._build()
        self.refresh_order()

    def _setup_style(self):
        style = ttk.Style(self)
        style.configure(".", font=(FONT_FAMILY, 11))
        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", font=(FONT_FAMILY, 11, "bold"))
        style.configure("Title.TLabel", font=(FONT_FAMILY, 24, "bold"))
        style.configure("Total.TLabel", font=(FONT_FAMILY, 18, "bold"))
        style.configure("Checkout.TButton", font=(FONT_FAMILY, 15, "bold"), padding=10)
        style.configure("Hint.TLabel", foreground="#b00020")

    # ---- レイアウト ----

    def _build(self):
        header = ttk.Frame(self, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text=STORE_NAME, style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="注文履歴・集計", command=self.open_history).pack(side="right")
        ttk.Button(header, text="おすすめを聞く", command=self.open_recommend).pack(side="right", padx=8)

        body = ttk.Frame(self, padding=(16, 0, 16, 16))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)
        self._build_menu_panel(body).grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._build_order_panel(body).grid(row=0, column=1, sticky="nsew")

    def _build_menu_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="メニュー", padding=8)
        self._build_allergen_bar(panel).pack(fill="x", pady=(0, 8))
        self.notebook = ttk.Notebook(panel)
        self.notebook.pack(fill="both", expand=True)
        self.menu_trees = []
        for category in MENU:
            frame, tree = make_tree(
                self.notebook, [("name", "品名", 200, "w"), ("allergens", "アレルギー", 140, "w"), ("price", "価格", 90, "e")]
            )
            tree.bind("<Double-1>", lambda _e: self.add_selected())
            self.notebook.add(frame, text=category)
            self.menu_trees.append(tree)
        self.refresh_menu()

        controls = ttk.Frame(panel, padding=(0, 8, 0, 0))
        controls.pack(fill="x")
        ttk.Label(controls, text="数量").pack(side="left")
        self.quantity = tk.StringVar(value="1")
        make_quantity_box(controls, self.quantity).pack(side="left", padx=6)
        ttk.Button(controls, text="注文に追加", command=self.add_selected).pack(side="left")
        ttk.Label(controls, text="（ダブルクリックでも追加できます）").pack(side="left", padx=8)
        return panel

    def _build_allergen_bar(self, parent):
        """押したアレルギーを含む料理を、メニューとおすすめから隠すトグルボタン群。"""
        bar = ttk.Frame(parent)
        ttk.Label(bar, text="アレルギーで絞り込む（押した項目を含む料理を隠す）").pack(anchor="w")
        buttons = ttk.Frame(bar)
        buttons.pack(fill="x", pady=(4, 0))
        self.allergen_vars = {}
        for allergen in ALLERGENS:
            var = tk.BooleanVar(value=False)
            ttk.Checkbutton(buttons, text=allergen, variable=var, style="Toolbutton",
                            command=self.on_allergen_change).pack(side="left", padx=(0, 4))
            self.allergen_vars[allergen] = var
        ttk.Button(buttons, text="すべて解除", command=self.clear_allergens).pack(side="left", padx=(8, 0))
        self.allergen_status = ttk.Label(bar, style="Hint.TLabel")
        self.allergen_status.pack(anchor="w", pady=(4, 0))
        return bar

    def excluded_allergens(self):
        return {allergen for allergen, var in self.allergen_vars.items() if var.get()}

    def clear_allergens(self):
        for var in self.allergen_vars.values():
            var.set(False)
        self.on_allergen_change()

    def on_allergen_change(self):
        self.refresh_menu()
        for window in self.winfo_children():
            if isinstance(window, RecommendWindow):
                window.update_results()

    def refresh_menu(self):
        excluded = self.excluded_allergens()
        visible = filter_menu(MENU, excluded)
        hidden_total = 0
        for index, (category, tree) in enumerate(zip(MENU, self.menu_trees)):
            tree.delete(*tree.get_children())
            for name, price in visible[category]:
                tree.insert("", "end", iid=name, values=(name, format_allergens(name), format_price(price)))
            hidden = len(MENU[category]) - len(visible[category])
            hidden_total += hidden
            self.notebook.tab(index, text=f"{category}（{len(visible[category])}）" if hidden else category)
        self.allergen_status.configure(
            text=f"{'・'.join(a for a in ALLERGENS if a in excluded)} を含む {hidden_total}品を非表示中" if excluded else ""
        )

    def _build_order_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="ご注文内容", padding=8)
        frame, self.order_tree = make_tree(
            panel, [("name", "品名", 180, "w"), ("qty", "数量", 60, "e"), ("subtotal", "小計", 90, "e")]
        )
        frame.pack(fill="both", expand=True)

        cancel_bar = ttk.Frame(panel, padding=(0, 8))
        cancel_bar.pack(fill="x")
        self.cancel_one_button = ttk.Button(cancel_bar, text="1個取り消す", command=lambda: self.cancel_selected(1))
        self.cancel_one_button.pack(side="left")
        self.cancel_all_button = ttk.Button(cancel_bar, text="この品を取り消す", command=lambda: self.cancel_selected(None))
        self.cancel_all_button.pack(side="left", padx=6)

        self.total_label = ttk.Label(panel, style="Total.TLabel", anchor="e")
        self.total_label.pack(fill="x", pady=(4, 8))
        self.checkout_button = ttk.Button(panel, text="会計", style="Checkout.TButton", command=self.open_checkout)
        self.checkout_button.pack(fill="x")
        return panel

    # ---- 注文 ----

    def add_item(self, name, quantity_text):
        """数量欄の文字列をチェックして注文に追加する。不正な入力はメッセージを出して False。"""
        try:
            quantity = parse_int(quantity_text, "数量", 1, Order.MAX_QUANTITY)
            self.order.add(name, PRICES[name], quantity)
        except (InputError, OrderError) as e:
            messagebox.showerror("注文できません", str(e), parent=self)
            return False
        self.refresh_order()
        return True

    def add_selected(self):
        tree = self.menu_trees[self.notebook.index("current")]
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("注文", "メニューから品を選んでください。", parent=self)
            return
        self.add_item(selection[0], self.quantity.get())

    def cancel_selected(self, quantity):
        """選択中の明細を取り消す。quantity=None ならその品をすべて取り消す。"""
        selection = self.order_tree.selection()
        if not selection:
            messagebox.showinfo("取り消し", "取り消す注文を選んでください。", parent=self)
            return
        index = int(selection[0])
        if quantity is not None and quantity >= self.order.lines[index]["quantity"]:
            quantity = None
        self.order.cancel(index, quantity)
        self.refresh_order()
        # 取り消し後も同じ位置を選択しておき、続けて操作しやすくする
        if self.order.lines:
            keep = str(min(index, len(self.order.lines) - 1))
            self.order_tree.selection_set(keep)

    def refresh_order(self):
        self.order_tree.delete(*self.order_tree.get_children())
        for i, line in enumerate(self.order.lines):
            subtotal = line["price"] * line["quantity"]
            self.order_tree.insert("", "end", iid=str(i), values=(line["name"], line["quantity"], format_price(subtotal)))
        self.total_label.configure(text=f"合計 {format_price(self.order.total())}")
        state = "disabled" if self.order.is_empty() else "normal"
        for button in (self.checkout_button, self.cancel_one_button, self.cancel_all_button):
            button.configure(state=state)

    # ---- 会計 ----

    def open_checkout(self):
        if self.order.is_empty():
            return
        CheckoutDialog(self)

    def finalize_checkout(self):
        """注文を記録して会計を確定する。成功したら新しい注文を始めて True を返す。"""
        # 記録できなかった注文を会計済みにしないよう、記録を先に行う
        try:
            order_id = save_order(self.order)
        except OSError as e:
            messagebox.showerror(
                "記録に失敗しました",
                f"注文を記録できませんでした（{e}）。\n記録ファイルを開いている場合は閉じてから、もう一度会計してください。",
                parent=self,
            )
            return False
        total = self.order.checkout()
        messagebox.showinfo(
            "会計完了", f"お会計 {format_price(total)}\n注文ID {order_id} として記録しました。\nありがとうございました。", parent=self
        )
        self.order = Order()
        self.refresh_order()
        return True

    # ---- サブ画面 ----

    def open_recommend(self):
        RecommendWindow(self)

    def open_history(self):
        try:
            orders = load_orders()
        except OSError as e:
            messagebox.showerror("注文履歴", f"注文記録を読み込めませんでした（{e}）。", parent=self)
            return
        if not orders:
            messagebox.showinfo("注文履歴", "記録された注文はまだありません。", parent=self)
            return
        HistoryWindow(self, orders)


class CheckoutDialog(tk.Toplevel):
    """会計ボタンで開く確認画面。注文内容と合計金額を表示する。"""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("お会計")
        self.transient(app)
        self.resizable(False, False)

        body = ttk.Frame(self, padding=20)
        body.pack(fill="both", expand=True)
        frame, tree = make_tree(
            body, [("name", "品名", 200, "w"), ("qty", "数量", 60, "e"), ("subtotal", "小計", 100, "e")],
            height=min(max(len(app.order.lines), 3), 10),
        )
        for line in app.order.lines:
            tree.insert("", "end", values=(line["name"], line["quantity"], format_price(line["price"] * line["quantity"])))
        frame.pack(fill="both", expand=True)

        ttk.Label(body, text=f"合計金額  {format_price(app.order.total())}", style="Title.TLabel").pack(pady=16)

        buttons = ttk.Frame(body)
        buttons.pack()
        ttk.Button(buttons, text="会計を確定する", style="Checkout.TButton", command=self.confirm).pack(side="left", padx=6)
        ttk.Button(buttons, text="戻る", command=self.destroy).pack(side="left", padx=6)
        self.grab_set()

    def confirm(self):
        self.grab_release()
        self.destroy()
        self.app.finalize_checkout()


class RecommendWindow(tk.Toplevel):
    """気分・温度・予算・年齢を変えるたびに、おすすめが更新される画面。"""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("おすすめ")
        self.geometry("960x560")
        self.transient(app)
        self.sales = load_item_sales()

        body = ttk.Frame(self, padding=16)
        body.pack(fill="both", expand=True)

        self.mood = tk.StringVar(value="")
        self.temperature = tk.StringVar(value="")
        self.budget = tk.StringVar(value="")
        self.age = tk.StringVar(value="")
        self._radio_row(body, "気分", MOODS, self.mood)
        self._radio_row(body, "温度", TEMPERATURES, self.temperature)
        self._entry_row(body, "1品あたりの予算", self.budget, "円（空欄で指定なし）")
        self._entry_row(body, "年齢", self.age, f"歳（空欄で指定なし・{CHILD_AGE}歳以下はカフェインなしの品をおすすめ）")
        self.hint = ttk.Label(body, style="Hint.TLabel")
        self.hint.pack(fill="x")
        self.allergen_note = ttk.Label(body)
        self.allergen_note.pack(fill="x")

        frame, self.tree = make_tree(
            body, [("name", "品名", 160, "w"), ("price", "価格", 70, "e"), ("category", "カテゴリ", 140, "w"),
                   ("allergens", "アレルギー", 110, "w"), ("reason", "おすすめの理由", 380, "w")],
            height=6,
        )
        frame.pack(fill="both", expand=True, pady=(12, 8))
        self.tree.bind("<Double-1>", lambda _e: self.add_selected())
        self.empty_label = ttk.Label(body, text="")
        self.empty_label.pack(fill="x")

        controls = ttk.Frame(body)
        controls.pack(fill="x", pady=(4, 0))
        ttk.Label(controls, text="数量").pack(side="left")
        self.quantity = tk.StringVar(value="1")
        make_quantity_box(controls, self.quantity).pack(side="left", padx=6)
        ttk.Button(controls, text="注文に追加", command=self.add_selected).pack(side="left")
        ttk.Button(controls, text="閉じる", command=self.destroy).pack(side="right")

        for variable in (self.mood, self.temperature, self.budget, self.age):
            variable.trace_add("write", lambda *_: self.update_results())
        self.update_results()

    def _radio_row(self, parent, label, options, variable):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label, width=14).pack(side="left")
        ttk.Radiobutton(row, text="こだわらない", value="", variable=variable).pack(side="left", padx=(0, 8))
        for text, tag in options:
            ttk.Radiobutton(row, text=text, value=tag, variable=variable).pack(side="left", padx=(0, 8))

    def _entry_row(self, parent, label, variable, suffix):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label, width=14).pack(side="left")
        ttk.Entry(row, textvariable=variable, width=8, justify="right").pack(side="left")
        ttk.Label(row, text=suffix).pack(side="left", padx=4)

    def update_results(self):
        self.tree.delete(*self.tree.get_children())
        errors = []
        try:
            budget = parse_budget(self.budget.get())
        except InputError as e:
            errors.append(str(e))
        try:
            age = parse_age(self.age.get())
        except InputError as e:
            errors.append(str(e))
        # 入力に誤りがある間は、おすすめを出さずに理由だけを表示する
        self.hint.configure(text="  ".join(errors))
        if errors:
            self.empty_label.configure(text="")
            return
        excluded = self.app.excluded_allergens()
        self.allergen_note.configure(
            text=f"アレルギー {'・'.join(a for a in ALLERGENS if a in excluded)} を含む料理はおすすめしません（メイン画面で変更）"
            if excluded else ""
        )
        results = recommend(
            filter_menu(MENU, excluded), ITEM_TAGS, self.sales,
            mood=self.mood.get() or None,
            temperature=self.temperature.get() or None,
            budget=budget,
            age=age,
        )
        for r in results:
            self.tree.insert("", "end", iid=r["name"], values=(
                r["name"], format_price(r["price"]), r["category"], format_allergens(r["name"]), " / ".join(r["reasons"])))
        if results:
            self.tree.selection_set(results[0]["name"])
            self.empty_label.configure(text="")
        else:
            self.empty_label.configure(text="条件に合うおすすめが見つかりませんでした。条件を変えてお試しください。")

    def add_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("おすすめ", "注文する品を選んでください。", parent=self)
            return
        if self.app.add_item(selection[0], self.quantity.get()):
            messagebox.showinfo("おすすめ", f"{selection[0]} を注文に追加しました。", parent=self)


class HistoryWindow(tk.Toplevel):
    """注文一覧と売上集計を表示する画面。"""

    def __init__(self, app, orders):
        super().__init__(app)
        self.title("注文履歴・集計")
        self.geometry("900x600")
        self.transient(app)

        notebook = ttk.Notebook(self, padding=12)
        notebook.pack(fill="both", expand=True)
        notebook.add(self._build_list(notebook, orders), text="注文一覧")
        notebook.add(self._build_summary(notebook, orders), text="売上集計")

    def _build_list(self, parent, orders):
        frame, tree = make_tree(
            parent, [("datetime", "日時", 180, "w"), ("qty", "数量", 70, "e"), ("amount", "金額", 110, "e")],
            show="tree headings",
        )
        tree.heading("#0", text=f"注文ID / 品名（{len(orders)}件）")
        tree.column("#0", width=300)
        for order in orders:
            parent_id = tree.insert("", "end", text=order["id"], open=True,
                                    values=(order["ordered_at"], "", format_price(order["total"])))
            for line in order["lines"]:
                tree.insert(parent_id, "end", text=line["name"],
                            values=("", line["quantity"], format_price(line["price"] * line["quantity"])))
        return frame

    def _build_summary(self, parent, orders):
        summary = summarize(orders, category_of)
        page = ttk.Frame(parent, padding=8)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=1)
        page.rowconfigure(2, weight=1)
        page.rowconfigure(4, weight=1)

        ttk.Label(
            page, style="Total.TLabel",
            text=f"注文件数 {summary['order_count']}件　売上合計 {format_price(summary['total_sales'])}　"
                 f"平均客単価 {format_price(summary['average'])}",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(page, text="日別売上").grid(row=1, column=0, sticky="w")
        frame, tree = make_tree(page, [("date", "日付", 120, "w"), ("orders", "件数", 60, "e"), ("sales", "売上", 100, "e")], height=5)
        for date, data in summary["by_date"]:
            tree.insert("", "end", values=(date, data["orders"], format_price(data["sales"])))
        frame.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))

        ttk.Label(page, text="カテゴリ別売上").grid(row=3, column=0, sticky="w")
        self._ranking(page, summary["by_category"], "カテゴリ").grid(row=4, column=0, sticky="nsew", padx=(0, 8))

        ttk.Label(page, text="品目別売上ランキング").grid(row=1, column=1, sticky="w")
        self._ranking(page, summary["by_item"], "品名").grid(row=2, column=1, rowspan=3, sticky="nsew")
        return page

    def _ranking(self, parent, rows, name_heading):
        frame, tree = make_tree(
            parent, [("rank", "順位", 50, "e"), ("name", name_heading, 180, "w"), ("qty", "個数", 60, "e"), ("sales", "売上", 100, "e")],
            height=5,
        )
        for rank, (name, data) in enumerate(rows, start=1):
            tree.insert("", "end", values=(rank, name, data["quantity"], format_price(data["sales"])))
        return frame


def run():
    App().mainloop()
