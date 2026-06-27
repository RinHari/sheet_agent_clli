ALLOWED_ACTIONS = {
    "append_row",
    "update_cell",
    "update_row",
}

ALLOWED_SHEET_NAMES = {
    "test_env",
}

MAX_COLUMNS_PER_ROW = 10


def validate_append_row(sheet_name: str, values: list[str]) -> None:
    if sheet_name not in ALLOWED_SHEET_NAMES:
        raise ValueError(f"このシートには書き込めません: {sheet_name}")

    if not isinstance(values, list):
        raise ValueError("values は list である必要があります。")

    if len(values) == 0:
        raise ValueError("追加する値が空です。")

    if len(values) > MAX_COLUMNS_PER_ROW:
        raise ValueError(f"一度に追加できる列数は最大 {MAX_COLUMNS_PER_ROW} です。")

    for value in values:
        if not isinstance(value, str):
            raise ValueError("追加する値はすべて文字列である必要があります。")


def validate_update_cell(sheet_name: str, cell: str, value: str) -> None:
    if sheet_name not in ALLOWED_SHEET_NAMES:
        raise ValueError(f"このシートには書き込めません: {sheet_name}")

    if not isinstance(cell, str) or not cell:
        raise ValueError("cell は空でない文字列である必要があります。")

    if not isinstance(value, str):
        raise ValueError("value は文字列である必要があります。")

    # 最低限、A1やB2のような形式だけ許可する
    # 例: A1, B2, AA10
    import re
    if not re.fullmatch(r"[A-Z]+[1-9][0-9]*", cell):
        raise ValueError(f"セル指定が不正です: {cell}")


def validate_update_row(sheet_name: str, start_cell: str, values: list[str]) -> None:
    if sheet_name not in ALLOWED_SHEET_NAMES:
        raise ValueError(f"このシートには書き込めません: {sheet_name}")

    if not isinstance(values, list):
        raise ValueError("values は list である必要があります。")

    if len(values) == 0:
        raise ValueError("更新する値が空です。")

    if len(values) > MAX_COLUMNS_PER_ROW:
        raise ValueError(f"一度に更新できる列数は最大 {MAX_COLUMNS_PER_ROW} です。")

    for value in values:
        if not isinstance(value, str):
            raise ValueError("更新する値はすべて文字列である必要があります。")

    validate_update_cell(sheet_name, start_cell, values[0])
