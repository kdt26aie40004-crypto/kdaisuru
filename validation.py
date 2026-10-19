"""画面からの入力値のチェック。どんな文字列が来ても例外で止まらず、InputError（理由付き）にする。"""

import re
import unicodedata

AGE_MIN, AGE_MAX = 0, 120
BUDGET_MAX = 100_000


class InputError(ValueError):
    """入力が不正。メッセージはそのまま画面に表示できる文にする。"""


def parse_int(text, label, minimum=None, maximum=None, required=True):
    """入力文字列を整数に変換する。

    - 全角数字・全角マイナスも受け付ける（NFKC で半角にそろえる）
    - 空欄は required=False なら None、True なら InputError
    - 数字以外・小数・負の数・範囲外は、理由がわかるメッセージで InputError
    """
    text = unicodedata.normalize("NFKC", text or "").strip()
    if text == "":
        if required:
            raise InputError(f"{label}を入力してください。")
        return None
    if re.fullmatch(r"-?(\d+\.\d*|\.\d+)", text, re.ASCII):
        raise InputError(f"{label}は整数で入力してください。")
    if not re.fullmatch(r"-?\d+", text, re.ASCII):
        raise InputError(f"{label}は数字で入力してください。")
    value = int(text)
    if value < 0 and (minimum is None or minimum >= 0):
        raise InputError(f"{label}にマイナスの値は入力できません。")
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise InputError(f"{label}は{minimum}〜{maximum}の範囲で入力してください。")
    return value


def parse_age(text):
    """年齢（空欄は指定なしで None）。"""
    return parse_int(text, "年齢", AGE_MIN, AGE_MAX, required=False)


def parse_budget(text):
    """1品あたりの予算（空欄は指定なしで None）。"""
    return parse_int(text, "予算", 0, BUDGET_MAX, required=False)
