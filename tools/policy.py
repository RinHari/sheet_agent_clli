ALLOWED_ACTIONS = {
    "append_row",
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