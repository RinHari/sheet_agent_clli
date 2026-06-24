import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tools.policy import validate_append_row

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


def append_row(values: list[str]) -> dict:
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

    return result