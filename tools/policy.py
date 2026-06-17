ALLOWED_ACTIONS = {
    "append_row",
}


def validate_action(action_data: dict) -> None:
    action = action_data.get("action")

    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"許可されていない操作です: {action}")

    values = action_data.get("values")

    if not isinstance(values, list):
        raise ValueError("values は list である必要があります。")

    if len(values) == 0:
        raise ValueError("追加する値が空です。")

    if len(values) > 20:
        raise ValueError("一度に追加できる列数を超えています。")