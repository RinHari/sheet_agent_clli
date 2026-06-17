# How to Setting AI Agent

# Abstract

Slack AppからBotまたはSlash Commandを作成し、そのBotにリクエストすることで、最終的に以下の操作を行えるようにしたい。

- Google Spreadsheet
- X / Twitter
- Admin画面

基本構成としては、1つの中核AI Agentに対して、Slack / Spreadsheet / X / Admin 用のToolを追加していく

AI Agent 構成案
```
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

# STEP BY STEP ENGINEERING

構成を以下に分ける
1. SlackとAI Agentの連携
2. AI AgentからSpreadsheetを操作
3. 権限の調整とAgent利用範囲の拡大

## 1. SlackとAI Agentの連携
- AI AgentをSlackで利用するためには、基本的にSlack Appが必要
- Slash Command、Botへのメンション、Slackボタンなどを使う場合はSlack Appが必要
- 現在はSlack Appの使用上限に達しているため、Slack連携部分はいったん保留

**現状の切り分け**
```
Slack Appが止まっている部分：
Slack入力 → 自分のAPIへ送信

先に作れる部分：
Python CLI → Spreadsheet操作
```

## 2. Spreadsheet操作の検証

本来の構成：
```
Terminal
  ↓
Python CLI
  ↓
AI Agent
  ↓
Google Sheets API
  ↓
Edit Spreadsheet
```

ただし、OpenAI APIは別課金であり、現時点ではクレジット未追加のため、AI Agent部分はいったん停止

まずはAIを使わずに、PythonからGoogle Spreadsheetへ固定の1行を追加できるか確認

一旦これができるかどうかを確認して、**最終的にターミナルからslackに変更**

**現状との切り分け**
```
現在：
Python CLI
  ↓
Google Sheets API
  ↓
Edit Spreadsheet

後で：
Python CLI / Slack
  ↓
AI Agent
  ↓
Google Sheets API
  ↓
Edit Spreadsheet
```

OpenAI APIやClaude APIなど、外部AI APIをPythonから利用する場合は、ChatGPT PlusやClaude Proとは別にAPI利用料がかかる

そのため、AI Agentによる自然文解釈はGOが出るまで一旦停止

一方で、Google Sheets API自体は標準利用では追加料金なしで使えるため、AIなしで固定行を追加する検証は進める

AI Agentを利用しない「PythonからGoogleスプレッドシートへ固定の1行を追加できるか」を確認
```
1. Google CloudでGoogle Sheets APIを有効化
2. サービスアカウントを作る
3. credentials.jsonをダウンロード
4. スプレッドシートにサービスアカウントを共有
5. Pythonから固定行を追加する
```
### 2.1  Google CloudでGoogle Sheets APIを有効化
```
Google Cloud Console
↓
プロジェクト選択
↓
新しいプロジェクト作成
```
※Google Cloudには課金対象サービスもあるが、Google Sheets APIの標準利用は追加料金なし

今回のように、Pythonから自分のスプレッドシートへ少量の読み書きをする検証では、基本的に追加料金は発生しない

ただし、他のGoogle Cloudサービスを有効化したり、大量処理を行う場合は別途確認が必要

### 2.2 Google Sheets APIを有効化
```
APIとサービス
↓
ライブラリ
↓
Google Sheets API
↓
有効にする
```

### 2.3 サービスアカウントを作成する
```
APIとサービス
↓
認証情報
↓
認証情報を作成
↓
サービスアカウント
```
サービスアカウントを作成する段階で権限についてを聞かれる

**本来であればここで設定する内容はありそう**だが、今回はスキップした

### 2.4 JSONキーを作成する
```
キー
↓
キーを追加
↓
新しい鍵を作成
↓
JSON
```

基本的にはここでサービスアカウントキーのJSONを作成できる。

しかし、今回のGoogle Cloud環境では、以下の組織ポリシーが適用

`iam.disableServiceAccountKeyCreation`

このポリシーにより、サービスアカウントキーの作成が禁止

そのため、credentials.jsonを使うサービスアカウントキー方式では進められない

### 2.4 + α
サービスアカウントキー方式が使えないため、OAuth方式に変更

サービスアカウント方式：
credentials.json を使う.
プログラム専用のサービスアカウントとしてSpreadsheetを操作する

- credentials.json

OAuth方式：
client_secret.json を使う.
初回実行時にブラウザで自分のGoogleアカウントにログインする

ログイン後、token.json が作成される.
以後は token.json を使ってSpreadsheetを操作する

- client_secret.json
- token.json

```
OAuthの概要から基本設定
↓
アプリ名やユーザーサポートメールなどを設定
↓
OAuthクライアントIDの作成
↓
アプリケーションの種類「デスクトップアプリ」に設定
↓
作成されるとJSONが作成されるのでそれを保持
```

tools 等と同じlayerに作成されるJSONを配置

.venv に
- SPRESDSHEET_ID 
- SHEET_NAME
を記入

仮想環境上で
`pip install google-auth-oauthlib google-api-python-client google-auth python-dotenv`
を実行

