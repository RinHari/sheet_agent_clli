import os
import re
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tools.audit_log import get_current_actor, write_audit_log
from tools.policy import validate_append_row, validate_update_cell, validate_update_row

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheets_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("client_secret.json"):
                raise FileNotFoundError(
                    "client_secret.json が見つかりません。"
                    "Google CloudからダウンロードしたOAuthクライアントJSONを、"
                    "プロジェクト直下に client_secret.json という名前で置いてください。"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


def append_row(values: list[str], actor: Optional[str] = None) -> dict:
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    sheet_name = os.getenv("SHEET_NAME")

    if not spreadsheet_id:
        raise ValueError("SPREADSHEET_ID が .env に設定されていません。")

    if not sheet_name:
        raise ValueError("SHEET_NAME が .env に設定されていません。")

    validate_append_row(sheet_name, values)

    service = get_sheets_service()

    body = {
        "values": [values]
    }

    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:Z",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )

    updated_range = result.get("updates", {}).get("updatedRange")
    write_audit_log(
        {
            "actor": get_current_actor(actor),
            "action": "append_row",
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name,
            "target_range": updated_range,
            "new_values": values,
            "result": {
                "updated_rows": result.get("updates", {}).get("updatedRows"),
                "updated_columns": result.get("updates", {}).get("updatedColumns"),
                "updated_cells": result.get("updates", {}).get("updatedCells"),
            },
        }
    )

    return result


def update_cell(cell: str, value: str, actor: Optional[str] = None) -> dict:
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    sheet_name = os.getenv("SHEET_NAME")

    if not spreadsheet_id:
        raise ValueError("SPREADSHEET_ID が .env に設定されていません。")

    if not sheet_name:
        raise ValueError("SHEET_NAME が .env に設定されていません。")

    validate_update_cell(sheet_name, cell, value)

    service = get_sheets_service()
    target_range = f"{sheet_name}!{cell}"
    before_result = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=target_range,
        )
        .execute()
    )
    old_values = before_result.get("values", [])
    old_value = old_values[0][0] if old_values and old_values[0] else None

    body = {
        "values": [[value]]
    }

    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=target_range,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )

    write_audit_log(
        {
            "actor": get_current_actor(actor),
            "action": "update_cell",
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name,
            "target_cell": cell,
            "target_range": result.get("updatedRange", target_range),
            "old_value": old_value,
            "new_value": value,
            "result": {
                "updated_rows": result.get("updatedRows"),
                "updated_columns": result.get("updatedColumns"),
                "updated_cells": result.get("updatedCells"),
            },
        }
    )

    return result


def _split_cell(cell: str) -> tuple[str, int]:
    match = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", cell)
    if not match:
        raise ValueError(f"セル指定が不正です: {cell}")

    return match.group(1), int(match.group(2))


def _column_to_number(column: str) -> int:
    number = 0
    for char in column:
        number = number * 26 + ord(char) - ord("A") + 1
    return number


def _number_to_column(number: int) -> str:
    column = ""
    while number > 0:
        number, remainder = divmod(number - 1, 26)
        column = chr(ord("A") + remainder) + column
    return column


def _build_row_range(sheet_name: str, start_cell: str, value_count: int) -> str:
    start_column, row_number = _split_cell(start_cell)
    end_column_number = _column_to_number(start_column) + value_count - 1
    end_column = _number_to_column(end_column_number)
    return f"{sheet_name}!{start_cell}:{end_column}{row_number}"


def update_row(start_cell: str, values: list[str], actor: Optional[str] = None) -> dict:
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    sheet_name = os.getenv("SHEET_NAME")

    if not spreadsheet_id:
        raise ValueError("SPREADSHEET_ID が .env に設定されていません。")

    if not sheet_name:
        raise ValueError("SHEET_NAME が .env に設定されていません。")

    validate_update_row(sheet_name, start_cell, values)

    service = get_sheets_service()
    target_range = _build_row_range(sheet_name, start_cell, len(values))
    before_result = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=target_range,
        )
        .execute()
    )
    old_values = before_result.get("values", [[]])

    body = {
        "values": [values]
    }

    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=target_range,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )

    write_audit_log(
        {
            "actor": get_current_actor(actor),
            "action": "update_row",
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name,
            "start_cell": start_cell,
            "target_range": result.get("updatedRange", target_range),
            "old_values": old_values[0] if old_values else [],
            "new_values": values,
            "result": {
                "updated_rows": result.get("updatedRows"),
                "updated_columns": result.get("updatedColumns"),
                "updated_cells": result.get("updatedCells"),
            },
        }
    )

    return result
