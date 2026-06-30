# Spreadsheet Agent 権限設計

このドキュメントは、AI Agent が Google Spreadsheet を操作する際の権限設計をまとめたもの。

特定できる情報は記載しない。Spreadsheet ID、Sheet名、ユーザID、メールアドレス、社内固有名詞はすべて `****` として扱う。

---

## 1. 目的

AI Agent が自由に Spreadsheet を操作できるようにする一方で、以下を必ず制限する。

```text
1. 操作できるSpreadsheetを限定する
2. 操作できるSheetを限定する
3. 実行できるActionを限定する
4. 将来的に、操作できるユーザを限定する
5. 将来的に、読み取り可能範囲を権限ごとに限定する
6. 操作ログを残す
```

現時点では、まず大枠として **AIが触れるSpreadsheetを限定する** ことを最優先にする。

---

## 2. 現在の認証方式

現在は OAuth 方式で Google Sheets API を利用している。

```text
Python CLI
  ↓
OAuth token
  ↓
Google Sheets API
  ↓
Spreadsheet
```

使用しているスコープ。

```python
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
```

このスコープは、ログインしたGoogleアカウントがアクセス可能なSpreadsheetに対して読み書きできる権限を持つ。

そのため、Google側の権限だけに依存せず、Python側でも操作対象を制限する必要がある。

---

## 3. 機密情報の扱い

Spreadsheet ID や実際の Sheet名は、対象を特定できる情報である。

そのため、公開される可能性があるファイルには直書きしない。

```text
公開してよい:
  tools/policy.py
  config/private_policy.example.py

公開しない:
  .env
  client_secret.json
  token.json
  config/private_policy.py
  logs/
```

`policy.py` には検証ロジックだけを書く。  
実際の Spreadsheet ID、Sheet名、許可Actionは `config/private_policy.py` に置く。

`config/private_policy.py` は `.gitignore` 対象にする。

---

## 4. ファイル構成

現在の権限関連ファイル。

```text
tools/
  policy.py
  audit_log.py
  spreadsheet_tool.py
  Restriction.md

config/
  __init__.py
  private_policy.example.py
  private_policy.py  # gitignore対象

.env                 # gitignore対象
client_secret.json   # gitignore対象
token.json           # gitignore対象
logs/                # gitignore対象
```

役割。

```text
tools/policy.py
  権限チェックのロジック。
  実IDは持たない。

config/private_policy.example.py
  公開してよい設定見本。
  実IDは書かない。

config/private_policy.py
  実際の許可設定。
  Spreadsheet ID、Sheet名、許可Actionを持つ。
  GitHubには出さない。

tools/spreadsheet_tool.py
  Google Sheets APIを呼ぶ前にpolicy.pyでvalidateする。

tools/audit_log.py
  操作ログを書き込む。
```

---

## 5. private_policy の考え方

権限の主語はユーザではなく、Spreadsheet / Sheet に置く。

つまり以下の形にする。

```text
Spreadsheet
  ↓
Sheet
  ↓
許可Action
  ↓
将来的に許可User / 読み取りOption
```

現在の見本。

```python
SHEET_ACCESS_POLICIES = {
    "****": {
        "****": {
            "allowed_actions": {
                "append_row",
                "update_cell",
            },
        },
    },
}
```

この構成により、`.env` の `SPREADSHEET_ID` が別の値に書き換えられても、`config/private_policy.py` に登録されていないSpreadsheetは操作できない。

---

## 6. .env の役割

`.env` は「今回操作しようとしている対象」を指定する。

例。

```env
SPREADSHEET_ID=****
SHEET_NAME=****
```

`.env` の値は、実行時に読み込まれる。

ただし `.env` に書かれているだけでは操作許可にはならない。  
必ず `config/private_policy.py` に同じSpreadsheet ID / Sheet名が登録されている必要がある。

---

## 7. validate の流れ

Spreadsheet操作の前に、以下の順番で検証する。

```text
1. .env から SPREADSHEET_ID を取得
2. .env から SHEET_NAME を取得
3. policy.py が config/private_policy.py を読み込む
4. Spreadsheet ID が許可対象か確認
5. Sheet名が許可対象か確認
6. Actionが許可対象か確認
7. 入力値の形式を確認
8. Google Sheets APIを実行
9. 成功したら操作ログを書く
```

操作対象が未許可の場合は、Google Sheets APIを呼ぶ前に止める。

---

## 8. 現在許可しているAction

現在の基本Action。

```text
append_row
update_cell
```

`append_row` は行追加。  
`update_cell` は単一セル更新。

危険な操作は現時点では作らない。

```text
delete_row
clear_sheet
delete_sheet
update_range
```

`update_row` や `read_range` を追加する場合も、必ず `policy.py` のAction許可に通してから実行する。

---

## 9. append_row の制限

`append_row` では以下を検証する。

```text
Spreadsheet ID が許可されているか
Sheet名が許可されているか
append_row が許可Actionに含まれているか
values が list か
values が空ではないか
列数が上限以内か
値がすべて文字列か
```

列数の上限。

```python
MAX_COLUMNS_PER_ROW = 10
```

---

## 10. update_cell の制限

`update_cell` では以下を検証する。

```text
Spreadsheet ID が許可されているか
Sheet名が許可されているか
update_cell が許可Actionに含まれているか
cell が空でない文字列か
value が文字列か
cell が A1 / B2 / AA10 のような単一セル形式か
```

許可するセル形式。

```text
A1
B2
AA10
```

許可しないセル形式。

```text
A1:B10
A0
1A
```

現時点では、列・行単位の詳細制限は未実装。  
シート構成が固まってから追加する。

---

## 11. ユーザ権限制限

ユーザごとの権限制限は必須だが、現時点では次の段階で実装する。

設計方針は、ユーザを主語にするのではなく、Sheetを主語にする。

```text
Spreadsheet
  ↓
Sheet
  ↓
allowed_users
    ↓
    user_id
      role
      actions
      read_options
```

将来のイメージ。

```python
SHEET_ACCESS_POLICIES = {
    "****": {
        "****": {
            "allowed_users": {
                "****": {
                    "role": "executive",
                    "actions": {
                        "append_row",
                        "update_cell",
                        "read_range",
                    },
                    "read_options": {
                        "mode": "all",
                    },
                },
                "****": {
                    "role": "department_member",
                    "actions": {
                        "read_range",
                    },
                    "read_options": {
                        "mode": "limited",
                        "columns": ["A", "B", "C"],
                        "mask_columns": ["D", "E"],
                    },
                },
            },
        },
    },
}
```

実行ユーザは現在 `SHEET_AGENT_USER` で渡す想定。

```bash
SHEET_AGENT_USER=**** python3 main.py add "****" "****" --now
```

Slack連携時はSlack user ID、Web Application連携時はログインユーザIDを `actor` として渡す。

---

## 12. 読み取り権限 / RONLY

`read_range` は今後追加予定。

読み取りにも権限が必要。

例。

```text
役員:
  全範囲を閲覧可能

部門メンバー:
  自部門に必要な列だけ閲覧可能

閲覧制限対象:
  特定列をマスク
```

将来のread_options。

```text
mode: all
mode: limited
columns: ["A", "B", "C"]
mask_columns: ["D", "E"]
row_filter: ****
```

RONLY は単に「書き込み不可」ではなく、読む範囲も制限する。

```text
read-only user:
  read_range は可能
  append_row は不可
  update_cell は不可
```

---

## 13. 操作ログ

Spreadsheetへの書き込みが成功した場合、操作ログを残す。

ログファイル。

```text
logs/audit_log.jsonl
```

ログ項目。

```text
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

特定できる情報を含むため、`logs/` は `.gitignore` 対象にする。

ログファイルは書き込み後に owner read-only に戻す。

```text
mode: 0o400
```

注意点。

ローカルファイルのread-onlyは、誤編集を防ぐための最低限の保護。  
完全な改ざん防止ではない。

本番運用で「誰も編集できないログ」にする場合は、以下を検討する。

```text
Cloud Logging
監査ログ用DB
WORMストレージ
追記専用権限のある外部ストレージ
```

---

## 14. 拒否ログ

未許可操作を拒否した場合も、本来はログに残したい。

例。

```text
permission_denied
actor
spreadsheet_id
sheet_name
action
reason
```

現時点では、成功ログを優先して実装済み。  
拒否ログは次の改善候補。

---

## 15. 操作確認フロー

Slack / Web Application から操作する場合、更新前確認フローが必要になる。

理想形。

```text
ユーザ入力
  ↓
Agentが操作案を作成
  ↓
実行前に内容を返す
  ↓
ユーザが承認
  ↓
実行
  ↓
ログ保存
```

ただし、現状はCLI検証段階のため優先度は低め。

今は以下を優先する。

```text
1. Spreadsheet ID制限
2. Sheet制限
3. Action制限
4. 操作ログ
5. ユーザ制限
6. read_range / RONLY
```

---

## 16. Google側の権限

Python側の制限だけでは不十分。

Google側でも以下を確認する。

```text
Spreadsheetをリンク公開しない
操作用Googleアカウントを限定する
不要な共有権限を外す
検証用Spreadsheetと本番Spreadsheetを分ける
```

Spreadsheet IDが漏れても、Google側の共有権限が閉じていれば直接閲覧はできない。  
ただし、AgentのOAuth tokenを使える環境では操作できる可能性があるため、Python側のpolicy制限も必須。

---

## 17. 現時点の実装済み

実装済み。

```text
OAuth方式でGoogle Sheets APIを利用
append_row
update_cell
Spreadsheet ID制限
Sheet名制限
Action制限
入力値の基本チェック
操作成功ログ
ログファイルのowner read-only化
公開用exampleと非公開private_policyの分離
```

未実装 / 次にやること。

```text
ユーザごとの権限制限
read_range
RONLYの範囲制限
拒否ログ
操作確認フロー
列・行単位の詳細制限
```
