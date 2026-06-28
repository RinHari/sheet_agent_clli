# Sheet Agent CLI

社内AI Agentのうち、Google Spreadsheetを操作するSubAgent部分を検証するためのPython CLIです。

将来的にはSlack / Web Applicationから部門Agentを呼び出し、Agentが許可されたSpreadsheetや社内ツールを操作する構成を想定しています。現時点では、LLM APIやSlack Appを使わず、まず **Python CLIからGoogle Spreadsheetを安全に操作すること** を目的にしています。

このREADMEでは、誰でもローカルで動かせるように、構成、セットアップ、実行コマンド、権限制御、ログ確認方法をまとめます。

---

## 全体構成

将来的な社内Agent構成のイメージです。

![image](https://i.gyazo.com/4854821b0e072e3eeb2584db621e5712.png)

想定している全体像。

```text
Slack / Web Application
  ↓
認証・ガードレール
  ↓
Agent実行基盤
  ↓
部門Agent
  ↓
ツール
  ├─ Webブラウザ
  ├─ API
  ├─ 社内ナレッジ
  └─ Google Spreadsheet
```

このリポジトリで現在作っている範囲。

```text
Terminal
  ↓
Python CLI
  ↓
policy.py による権限チェック
  ↓
Google Sheets API
  ↓
Spreadsheet更新
  ↓
操作ログ保存
```

---

## 現在できること

```text
Spreadsheetへの行追加
単一セル更新
操作対象Spreadsheetの制限
操作対象Sheetの制限
許可Actionの制限
入力値の基本チェック
操作成功ログの保存
ログファイルのread-only化
```

現在はLLMによる自然文解釈は使っていません。OpenAI API / Claude APIなどの利用料が発生するため、まずはAIなしでSpreadsheet操作の安全な土台を作っています。

---

## ディレクトリ構成

```text
sheet-agent-cli/
  README.md
  requirements.txt
  main.py
  test_append.py
  .gitignore

  .env                  # gitignore対象
  client_secret.json    # gitignore対象
  token.json            # gitignore対象、自動生成

  config/
    __init__.py
    private_policy.example.py
    private_policy.py   # gitignore対象

  docs/
    agent-architecture.png

  tools/
    __init__.py
    audit_log.py
    policy.py
    spreadsheet_tool.py
    Restriction.md

  prompts/
    base.md
    spreadsheet.md

  services/
    llm_client.py
```

重要なファイル。

```text
main.py
  CLI入口。

tools/spreadsheet_tool.py
  Google Sheets APIを呼び出す。

tools/policy.py
  操作前の権限チェックを行う。
  実際のSpreadsheet IDは持たない。

config/private_policy.py
  操作を許可するSpreadsheet ID / Sheet名 / Actionを管理する。
  GitHubには出さない。

tools/audit_log.py
  操作ログを保存する。

tools/Restriction.md
  権限設計の詳細メモ。
```

---

## セットアップ

### 1. Python環境を作る

Python 3.10以上を推奨します。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.9でも動く場合がありますが、Google系ライブラリから警告が出ることがあります。

---

### 2. Google Sheets APIを有効化する

Google Cloud Consoleで以下を行います。

```text
1. Google Cloudプロジェクトを作成
2. Google Sheets APIを有効化
3. OAuth同意画面を設定
4. OAuthクライアントIDを作成
5. アプリケーションの種類は「デスクトップアプリ」を選択
6. JSONをダウンロード
```

ダウンロードしたJSONを、プロジェクト直下に以下の名前で置きます。

```text
client_secret.json
```

`client_secret.json` は `.gitignore` 対象です。GitHubには出しません。

---

### 3. .envを作成する

プロジェクト直下に `.env` を作成します。

```env
SPREADSHEET_ID=****
SHEET_NAME=****
```

`SPREADSHEET_ID` はSpreadsheet URLの `/d/` と `/edit` の間の値です。

```text
https://docs.google.com/spreadsheets/d/****/edit
```

`.env` は「今回操作しようとしている対象」を指定するファイルです。  
ただし、`.env` に書いただけでは操作できません。次の `config/private_policy.py` にも許可設定が必要です。

---

### 4. private_policy.pyを作成する

見本ファイルをコピーします。

```bash
cp config/private_policy.example.py config/private_policy.py
```

`config/private_policy.py` を編集します。

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

1つ目の `****` は許可するSpreadsheet IDです。  
2つ目の `****` は許可するSheet名です。

`.env` の `SPREADSHEET_ID` / `SHEET_NAME` と、`config/private_policy.py` の設定が一致していない場合、操作は止まります。

`config/private_policy.py` は `.gitignore` 対象です。GitHubには出しません。

---

## 実行方法

初回実行時はブラウザが開き、Googleアカウント認証が求められます。認証が成功すると `token.json` が自動生成されます。

### 行を追加する

```bash
SHEET_AGENT_USER=**** python3 main.py add "****" "****" --now
```

例として、3列分の値を追加します。

```text
値1 | 値2 | 現在時刻
```

`--now` は現在日時に置き換えられます。

### セルを更新する

```bash
SHEET_AGENT_USER=**** python3 main.py update B2 "****"
```

`update` は単一セル更新です。  
`A1`、`B2`、`AA10` のようなセル指定のみ許可します。

---

## 操作ログ

Spreadsheetへの書き込みが成功すると、ログが保存されます。

```text
logs/audit_log.jsonl
```

ログ確認。

```bash
tail -n 10 logs/audit_log.jsonl
```

見やすく整形する場合。

```bash
while read line; do echo "$line" | python3 -m json.tool; done < logs/audit_log.jsonl
```

ログファイルの権限確認。

```bash
ls -l logs/audit_log.jsonl
```

`-r--------` のように表示されれば、owner read-onlyです。

ログには以下が入ります。

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

ローカルファイルのread-onlyは誤編集防止のための最低限の保護です。完全な改ざん防止ではありません。本番運用では、Cloud Logging、監査ログ用DB、WORMストレージ、追記専用ストレージなどを検討します。

---

## 権限制御

権限制御は `tools/policy.py` と `config/private_policy.py` で行います。

```text
tools/policy.py
  validateロジックだけを持つ。
  特定できるSpreadsheet IDやSheet名は書かない。

config/private_policy.py
  実際に許可するSpreadsheet ID / Sheet名 / Actionを持つ。
  gitignore対象。
```

検証の流れ。

```text
1. .env から SPREADSHEET_ID を読む
2. .env から SHEET_NAME を読む
3. config/private_policy.py を読む
4. Spreadsheet IDが許可されているか確認
5. Sheet名が許可されているか確認
6. Actionが許可されているか確認
7. 入力値の形式を確認
8. Google Sheets APIを実行
9. 成功したら操作ログを書く
```

現在許可しているAction。

```text
append_row
update_cell
```

危険な操作は現時点では作りません。

```text
delete_row
clear_sheet
delete_sheet
update_range
```

詳細は [tools/Restriction.md](tools/Restriction.md) を参照してください。

---

## GitHubに出してはいけないもの

以下は `.gitignore` 対象です。

```text
.env
client_secret.json
token.json
config/private_policy.py
logs/
.venv/
__pycache__/
*.pyc
.DS_Store
```

特に以下は絶対に公開しないでください。

```text
client_secret.json
token.json
config/private_policy.py
.env
logs/
```

---

## トラブルシューティング

### ModuleNotFoundError: No module named 'tools.audit_log'

`tools/audit_log.py` が存在するか確認します。

```bash
ls tools/audit_log.py
```

存在しない場合は、最新のコードを取得してください。

### config/private_policy.py が未設定です

`config/private_policy.py` がありません。

```bash
cp config/private_policy.example.py config/private_policy.py
```

作成後、Spreadsheet IDとSheet名を `****` から実際の値に置き換えます。

### このSpreadsheetは操作できません

`.env` の `SPREADSHEET_ID` が `config/private_policy.py` に登録されていません。

```text
.env
  SPREADSHEET_ID=****

config/private_policy.py
  SHEET_ACCESS_POLICIES のキー = ****
```

両方が一致しているか確認してください。

### このシートには書き込めません

`.env` の `SHEET_NAME` が `config/private_policy.py` に登録されていません。

### invalid_grant: Token has been expired or revoked

Google OAuthの `token.json` が期限切れ、または取り消されています。

```bash
rm token.json
SHEET_AGENT_USER=**** python3 main.py add "****" "****" --now
```

再度ブラウザ認証してください。

### Python 3.9 / LibreSSL のWarning

Python 3.9やLibreSSL環境では、Google系ライブラリからWarningが出ることがあります。

実行自体の失敗原因ではない場合がありますが、Python 3.10以上への更新を推奨します。

---

## 今後やること

優先度が高いもの。

```text
1. ユーザごとの権限制限
2. read_range の追加
3. RONLYの範囲制限
4. 拒否ログ
5. 操作確認フロー
6. 列・行単位の詳細制限
```

将来的なユーザ権限のイメージ。

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

Slack / Web Application連携後は、`SHEET_AGENT_USER` の代わりにSlack user IDやWebログインユーザIDを `actor` として渡す想定です。