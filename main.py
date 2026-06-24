import sys
from dotenv import load_dotenv

from tools.spreadsheet_tool import append_row


def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print("使い方: python3 main.py add \"値1\" \"値2\" \"値3\"")
        sys.exit(1)

    command = sys.argv[1]

    if command != "add":
        print(f"未対応のコマンドです: {command}")
        print("使えるコマンド: add")
        sys.exit(1)

    values = sys.argv[2:]

    if len(values) == 0:
        print("追加する値がありません。")
        print("例: python3 main.py add \"企業A\" \"確認中\" \"2026-06-20\"")
        sys.exit(1)

    result = append_row(values)

    print("スプレッドシートに追加しました。")
    print("追加内容:")
    print(values)
    print("更新範囲:")
    print(result.get("updates", {}).get("updatedRange"))


if __name__ == "__main__":
    main()