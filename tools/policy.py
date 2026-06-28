import re
from typing import Any


try:
    from config.private_policy import SHEET_ACCESS_POLICIES
except ModuleNotFoundError as exc:
    if exc.name != "config.private_policy":
        raise
    SHEET_ACCESS_POLICIES: dict[str, dict[str, dict[str, Any]]] = {}


ALLOWED_ACTIONS = {
    "append_row",
    "update_cell",
}

MAX_COLUMNS_PER_ROW = 10


def _as_set(values: Any) -> set[str]:
    if values is None:
        return set()

    if isinstance(values, set):
        return values

    if isinstance(values, (list, tuple)):
        return set(values)

    raise ValueError("allowed_actions は list / tuple / set のいずれかで設定してください。")


def _get_sheet_policy(spreadsheet_id: str, sheet_name: str) -> dict[str, Any]:
    if not SHEET_ACCESS_POLICIES:
        raise ValueError(
            "config/private_policy.py が未設定です。"
            " config/private_policy.example.py を参考に作成してください。"
        )

    spreadsheet_policy = SHEET_ACCESS_POLICIES.get(spreadsheet_id)
    if not spreadsheet_policy:
        raise ValueError("このSpreadsheetは操作できません。")

    sheet_policy = spreadsheet_policy.get(sheet_name)
    if not sheet_policy:
        raise ValueError(f"このシートには書き込めません: {sheet_name}")

    return sheet_policy


def validate_spreadsheet_access(
    spreadsheet_id: str,
    sheet_name: str,
    action: str,
) -> None:
    if not spreadsheet_id:
        raise ValueError("SPREADSHEET_ID が .env に設定されていません。")

    if not sheet_name:
        raise ValueError("SHEET_NAME が .env に設定されていません。")

    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"未許可の操作です: {action}")

    sheet_policy = _get_sheet_policy(spreadsheet_id, sheet_name)
    allowed_actions = _as_set(sheet_policy.get("allowed_actions"))

    if action not in allowed_actions:
        raise ValueError(f"このシートでは操作できません: {action}")


def validate_append_row(
    spreadsheet_id: str,
    sheet_name: str,
    values: list[str],
) -> None:
    validate_spreadsheet_access(spreadsheet_id, sheet_name, "append_row")

    if not isinstance(values, list):
        raise ValueError("values は list である必要があります。")

    if len(values) == 0:
        raise ValueError("追加する値が空です。")

    if len(values) > MAX_COLUMNS_PER_ROW:
        raise ValueError(f"一度に追加できる列数は最大 {MAX_COLUMNS_PER_ROW} です。")

    for value in values:
        if not isinstance(value, str):
            raise ValueError("追加する値はすべて文字列である必要があります。")


def validate_update_cell(
    spreadsheet_id: str,
    sheet_name: str,
    cell: str,
    value: str,
) -> None:
    validate_spreadsheet_access(spreadsheet_id, sheet_name, "update_cell")

    if not isinstance(cell, str) or not cell:
        raise ValueError("cell は空でない文字列である必要があります。")

    if not isinstance(value, str):
        raise ValueError("value は文字列である必要があります。")

    # 例: A1, B2, AA10
    if not re.fullmatch(r"[A-Z]+[1-9][0-9]*", cell):
        raise ValueError(f"セル指定が不正です: {cell}")
