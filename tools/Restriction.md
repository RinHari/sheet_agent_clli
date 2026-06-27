## what should i do for Authority

### what i achieved
```
Python
  ↓
Google Sheets API
  ↓
指定したスプレッドシートに固定行を追加
```

### what should i do next
```
1. Google側の権限を最小化する

2. Pythonコード側で操作権限を制限する

3. 書き込み対象のシート・列を制限する

4. 操作ログを残す

5. ターミナルから値を指定して追加できるようにする
```

## 1. minimize google side Authority
現在使っているOAuthのスコープは

'SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]'

であり、これはGoogle sheet に対する読み書き権限である

ログインしたGoogleアカウントがアクセスできるスプレッドシートに対して、読み書きできる権限であるため、ログインしてしまえば、誰でも操作することが可能

**対策**

```
検証用Googleアカウントを使う
操作対象のスプレッドシートを限定する
本番用スプレッドシートではなく検証用コピーを使う
```

#### OAuth方式の場合、サービスアカウントのように「このファイルだけ編集者にする」という制御ではなく、ログインしたユーザーの権限で操作する

そのため、コード側で、ユーザの操作を制限する必要あり。

## 2. Restrict Authority in python side

- 許可していないシートの書き込み
- 空行の追加
- 大量の列追加操作
- 文字列以外の値の追加

を防ぐため以下のコードを追加

tools/policy.py

```
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
```

## 3. Restrict the sheets and columns that can be edited

今の append_row の中で、validate_append_row を呼ぶ

```
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
```

## 4. logging
Spreadsheetへの書き込みが成功した場合、`logs/audit_log.jsonl` に操作ログを追記する。

ログ項目は以下。

```
logged_at
actor
action
spreadsheet_id
sheet_name
target_range
target_cell
old_value
new_value
new_values
result
```

ログファイルは書き込み後に owner read-only に戻す。

```
logs/audit_log.jsonl
```

ただし、ローカルファイルのread-onlyは完全な改ざん防止ではない。
本番運用では、Cloud Logging、監査ログ用DB、WORMストレージ、追記専用権限のある外部ストレージを検討する。

## 5. Enable the addition of values specified from the terminal

`result = append_row(["テスト", "確認中", current_time])`

という固定値の挿入を任意でできるようにしたい。

理想入力

`python3 main.py add "企業A" "確認中" "2026-06-20"`

この処理を進めるため、新しいファイルmain.pyを作成

### main.py

`python3 main.py add "A" "B" "C"`

という入力によって今までと同様にspread sheetに内容が入力されるようにする

この方式では、splitよりもsys.argvを使う方が安全

["main.py", "add", "企業A", "確認中", "次回連絡 6/20"]

というような入力になり、引用符で囲まれた部分を1つの値として扱える
