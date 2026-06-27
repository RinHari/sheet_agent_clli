# How to Setting AI Agent

## Abstract

Slack AppからBotまたはSlash Commandを作成し、そのBotにリクエストすることで、最終的に以下の操作を行えるようにしたい。

- Google Spreadsheet
- X / Twitter
- Admin画面

基本構成としては、1つの中核AI Agentに対して、Slack / Spreadsheet / X / Admin 用のToolを追加していく。

## AI Agent 構成案

```text
internal-ai-agent/
  app/
    main.py
    agent/
      planner.py
      tool_router.py
      prompts.py
    tools/
      slack_tool.py
      sheets_tool.py
      x_tool.py
      admin_tool.py
    services/
      llm_client.py
      auth.py
      audit_log.py
    config/
      settings.py
  tests/
  .env
  requirements.txt
```

ただし、現在はSlack AppとAI APIの利用が止まっているため、最初からこの構成をすべて作るのではなく、まずはSpreadsheet操作だけを検証する。

現在の最小構成は以下。

```text
sheet-agent-cli/
  .env
  .gitignore
  README.md
  requirements.txt
  client_secret.json
  test_append.py

  tools/
    __init__.py
    audit_log.py
    spreadsheet_tool.py
    policy.py

  prompts/
    base.md
    spreadsheet.md

  services/
    llm_client.py
```

現時点で実際に使うのは以下。

```text
.env
requirements.txt
client_secret.json
test_append.py
tools/__init__.py
tools/audit_log.py
tools/spreadsheet_tool.py
tools/policy.py
```

以下は、AI Agent化するときに使うため、現時点では未使用。

```text
prompts/base.md
prompts/spreadsheet.md
services/llm_client.py
```

---

# STEP BY STEP ENGINEERING

構成を以下に分ける。

1. SlackとAI Agentの連携
2. Spreadsheet操作の検証
3. AI Agent化
4. 権限の調整とAgent利用範囲の拡大

---

## 1. SlackとAI Agentの連携

AI AgentをSlackで利用するためには、基本的にSlack Appが必要。

Slack Appが必要になる主な操作は以下。

- Slash Command
- Botへのメンション
- Slackボタン
- Slackモーダル
- Slackから外部APIへのリクエスト送信

現在はSlack Appの使用上限に達しているため、Slack連携部分はいったん保留。

### 現状の切り分け

```text
Slack Appが止まっている部分：
Slack入力 → 自分のAPIへ送信

先に作れる部分：
Python CLI → Spreadsheet操作
```

Slackは入口であり、Agent本体やSpreadsheet操作は先に作れる。

---

## 2. Spreadsheet操作の検証

### 2.0 目的

本来の構成は以下。

```text
Terminal / Slack
  ↓
AI Agent
  ↓
Google Sheets API
  ↓
Edit Spreadsheet
```

ただし、OpenAI APIやClaude APIなどの外部AI APIをPythonから利用する場合は、ChatGPT PlusやClaude Proとは別にAPI利用料がかかる。

現在はOpenAI APIのクレジットを追加していないため、AI Agentによる自然文解釈は一旦停止する。

そのため、まずはAIを使わずに、PythonからGoogle Spreadsheetへ固定の1行を追加できるか確認する。

現在の検証構成は以下。

```text
Terminal
  ↓
Python CLI
  ↓
Google Sheets API
  ↓
Edit Spreadsheet
```

後でSlackやAI Agentを追加すると以下になる。

```text
Slack / Terminal
  ↓
AI Agent
  ↓
Google Sheets API
  ↓
Edit Spreadsheet
```

Google Sheets API自体は標準利用では追加料金なしで使えるため、AIなしで固定行を追加する検証は進める。

---

### 2.1 Google Cloudプロジェクトを作成する

Google Cloud Consoleで検証用プロジェクトを作成する。

```text
Google Cloud Console
↓
プロジェクト選択
↓
新しいプロジェクト作成
```

例。

```text
sheet-agent-test
```

注意点。

Google Cloudには課金対象サービスもあるが、Google Sheets APIの標準利用は追加料金なし。

今回のように、Pythonから自分のスプレッドシートへ少量の読み書きをする検証では、基本的に追加料金は発生しない。

ただし、他のGoogle Cloudサービスを有効化したり、大量処理を行う場合は別途確認が必要。

---

### 2.2 Google Sheets APIを有効化する

作成したプロジェクトでGoogle Sheets APIを有効化する。

```text
APIとサービス
↓
ライブラリ
↓
Google Sheets API
↓
有効にする
```

これをしないと、PythonからGoogle Sheets APIを呼び出せない。

---

### 2.3 認証方式を検討する

Google Sheets APIをPythonから使うには、認証方式が必要。

当初想定していた方式はサービスアカウント方式。

```text
サービスアカウント方式：
credentials.json を使う
プログラム専用のサービスアカウントとしてSpreadsheetを操作する
```

本来のサービスアカウント方式の流れは以下。

```text
1. サービスアカウントを作る
2. credentials.jsonをダウンロードする
3. スプレッドシートにサービスアカウントのメールアドレスを編集者として共有する
4. Pythonから固定行を追加する
```

サービスアカウント作成手順。

```text
APIとサービス
↓
認証情報
↓
認証情報を作成
↓
サービスアカウント
```

サービスアカウント作成時にロール設定を聞かれる。

ただし、今回のようにGoogle Spreadsheetのみを操作する検証では、Google Cloud上で強いロールを付けることよりも、対象スプレッドシートにサービスアカウントのメールアドレスを編集者として共有することが重要。

---

### 2.4 サービスアカウントキー作成でブロックされた内容

本来は以下の手順でJSONキーを作成する。

```text
サービスアカウント
↓
キー
↓
キーを追加
↓
新しい鍵を作成
↓
JSON
```

しかし、今回のGoogle Cloud環境では以下の組織ポリシーが適用されていた。

```text
iam.disableServiceAccountKeyCreation
```

このポリシーにより、サービスアカウントキーの作成が禁止されていた。

そのため、credentials.jsonを使うサービスアカウントキー方式では進められない。

また、以下のようなコマンドは組織全体のポリシーを変更する管理者向け操作であり、今回の検証目的では実行しない。

```bash
gcloud org-policies delete CONSTRAINT_NAME --organization=ORGANIZATION_ID
```

結論として、今回はサービスアカウント方式ではなくOAuth方式に変更する。

---

### 2.5 OAuth方式に変更する

OAuth方式では、サービスアカウントではなく、自分のGoogleアカウントでログインしてSpreadsheetを操作する。

```text
OAuth方式：
client_secret.json を使う
初回実行時にブラウザで自分のGoogleアカウントにログインする
ログイン後、token.json が作成される
以後は token.json を使ってSpreadsheetを操作する
```

サービスアカウント方式とOAuth方式の違い。

```text
サービスアカウント方式：
credentials.json
プログラム専用アカウントでSpreadsheetを操作

OAuth方式：
client_secret.json
自分のGoogleアカウントでログインしてSpreadsheetを操作
```

今回使うのは以下。

```text
client_secret.json
token.json
```

`client_secret.json` はGoogle Cloudからダウンロードする。  
`token.json` は初回認証後に自動生成される。

---

### 2.6 OAuth同意画面を設定する

OAuthクライアントを作る前に、Google Auth PlatformでOAuth同意画面を設定する。

入力する主な内容は以下。

```text
アプリ名：
Sheet Agent Test

ユーザーサポートメール：
自分のGoogleアカウント

対象ユーザー：
外部

デベロッパーの連絡先情報：
自分のメールアドレス
```

今回のような検証用アプリでは、アプリのロゴ、ホームページURL、プライバシーポリシーURLなどは基本的に不要。必須項目のみ入力する。

アプリがTesting状態の場合、テストユーザーに追加されたGoogleアカウントだけが利用できる。

そのため、以下のようにテストユーザーを追加する。

```text
Google Auth Platform
↓
対象 / Audience
↓
Test users
↓
Add users
↓
自分のGoogleアカウントを追加
```

注意点。

テストユーザーに追加しても、反映に時間がかかる場合がある。  
`developer-approved testers` の403が出る場合は、以下を確認する。

```text
1. client_secret.json の client_id とGoogle Cloud上のOAuthクライアントIDが一致しているか
2. テストユーザーにログイン対象のGoogleアカウントが追加されているか
3. ブラウザで別のGoogleアカウントを選んでいないか
4. token.json を削除して再認証したか
5. 反映待ちではないか
```

---

### 2.7 OAuthクライアントIDを作成する

OAuth同意画面の設定後、OAuthクライアントを作成する。

```text
Google Auth Platform
↓
クライアント
↓
クライアントを作成
```

設定内容。

```text
アプリケーションの種類：
デスクトップアプリ

名前：
Sheet Agent CLI
```

作成後、JSONファイルをダウンロードする。

ダウンロードしたJSONファイルは、プロジェクト直下に配置し、以下の名前に変更する。

```text
client_secret.json
```

配置後の構成。

```text
sheet-agent-cli/
  client_secret.json
  .env
  test_append.py
  tools/
    spreadsheet_tool.py
```

---

### 2.8 Pythonプロジェクトを設定する

現在の最小構成。

```text
sheet-agent-cli/
  .env
  .gitignore
  README.md
  requirements.txt
  client_secret.json
  test_append.py

  tools/
    __init__.py
    spreadsheet_tool.py
```

`requirements.txt`。

```txt
python-dotenv
google-api-python-client
google-auth
google-auth-oauthlib
```

インストール。

```bash
pip install -r requirements.txt
```

`.gitignore`。

```gitignore
.env
client_secret.json
token.json
.venv/
__pycache__/
*.pyc
.DS_Store
```

`.env`。

```env
SPREADSHEET_ID=スプレッドシートID
SHEET_NAME=シート名
```

スプレッドシートIDはURLの `/d/` と `/edit` の間だけを入れる。

```text
https://docs.google.com/spreadsheets/d/【ここだけ】/edit
```

例。

```env
SPREADSHEET_ID=****
SHEET_NAME=****
```
---

### 2.9 Pythonコードを作成する

`tools/spreadsheet_tool.py`。

`test_append.py`。

---

### 2.10 固定行追加を実行する

実行。

```bash
python3 test_append.py
```

初回実行時はブラウザが開く。

```text
Googleログイン
↓
このアプリはGoogleで確認されていません
↓
詳細
↓
Sheet Agent Test に移動
↓
許可
↓
token.json が生成
↓
Spreadsheetに固定行が追加
```

成功すると、Spreadsheetに以下が追加される。

```text
テスト企業 | 確認中 | 2026-06-17
```

---

### 2.11 現在確認済みのエラーと対応

#### OpenAI APIの insufficient_quota

OpenAI APIキー自体は読めていたが、APIクレジットがないため実行できなかった。

```text
code: insufficient_quota
```

対応。

```text
OpenAI APIによるAI Agent化は一旦停止
Google Sheets APIの固定行追加だけを先に検証
```

#### サービスアカウントキー作成禁止

```text
iam.disableServiceAccountKeyCreation
```

対応。

```text
サービスアカウント方式をやめる
OAuth方式へ変更
```

#### OAuthの developer-approved testers エラー

```text
Error 403: access_denied
can only be accessed by developer-approved testers
```

対応。

```text
Google Auth PlatformのTest usersにログイン対象アカウントを追加
client_secret.jsonのclient_idとGoogle Cloud上のOAuthクライアントIDが一致しているか確認
token.jsonを削除して再認証
反映待ちの可能性もある
```

#### Spreadsheetの404

```text
Requested entity was not found
```

対応。

```text
SPREADSHEET_IDの末尾に / が入っていないか確認
SHEET_NAMEが実際のシートタブ名と一致しているか確認
OAuthでログインしたGoogleアカウントに対象Spreadsheetへのアクセス権限があるか確認
```

#### Python 3.9 / LibreSSLのWarning

```text
FutureWarning: You are using a Python version 3.9 past its end of life
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+
```

これは現時点の失敗原因ではない。

ただし、今後はPython 3.10以上に上げる方がよい。

---

## 3. AI Agent化

固定行追加が成功した後、AI Agent化する。

この段階で追加する主なファイル。

```text
main.py
tools/policy.py
prompts/base.md
prompts/spreadsheet.md
services/llm_client.py
```

AI Agent化後の構成。

```text
Terminal
  ↓
main.py
  ↓
LLM API
  ↓
JSON形式の操作指示
  ↓
policy.pyで検証
  ↓
spreadsheet_tool.py
  ↓
Google Sheets API
```

AIにはGoogle Sheets APIを直接操作させない。

AIは以下のようなJSONを返すだけにする。

```json
{
  "action": "append_row",
  "values": ["企業A", "面談済み", "次回連絡6/20"]
}
```

実際の操作はPython側で行う。

許可する操作は最初は `append_row` のみにする。

---

## 4. 権限の調整とAgent利用範囲の拡大

Spreadsheet操作が安定したら、以下を追加する。

```text
1. update_cell
2. read_range
3. 承認付き更新
4. 操作ログ保存
5. Slack連携
6. X / Twitter Tool
7. Admin Tool
```

安全性の考え方。

```text
プロンプト = 判断方針
policy.py = 実行制限
API権限 = 最終的な安全装置
```

危険な操作は最初からToolとして作らない。

最初に禁止する操作。

```text
delete_row
clear_sheet
delete_sheet
update_range
```

外部公開や本番データ更新を伴う操作は必ず承認制にする。

---

## 5. 操作ログ

Spreadsheetへの書き込みが成功した場合、以下のログファイルに操作内容を追記する。

```text
logs/audit_log.jsonl
```

ログは1行ごとのJSON形式で保存する。

主なログ項目。

```text
logged_at       操作ログを書き込んだUTC時刻
actor           操作ユーザ
action          append_row / update_cell
spreadsheet_id  操作対象のSpreadsheet ID
sheet_name      操作対象のシート名
target_range    実際に更新された範囲
target_cell     update_cell時の対象セル
old_value       update_cell時の更新前の値
new_value       update_cell時の更新後の値
new_values      append_row時に追加した値
result          Google Sheets APIの更新件数
```

CLI実行時のユーザは、以下の優先順で決まる。

```text
1. SHEET_AGENT_USER
2. PCの実行ユーザ名
```

例。

```bash
SHEET_AGENT_USER=slack-U123456 python3 main.py add "企業A" "確認中" --now
SHEET_AGENT_USER=slack-U123456 python3 main.py update B2 "対応済み"
```

ログファイルは書き込み後にread-onlyへ戻す。

```text
logs/audit_log.jsonl = owner read-only
```

注意点。

ローカルファイルのread-onlyは、誤編集を防ぐための最低限の保護であり、完全な改ざん防止ではない。  
本番運用で「誰も編集できないログ」にする場合は、Cloud Logging、監査ログ用DB、WORMストレージ、または追記専用権限のある外部ストレージに送る。
