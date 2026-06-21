import sys
from datetime import datetime
from dotenv import load_dotenv

from tools.spreadsheet_tool import append_row, update_cell


def replace_special_values(values: list[str]) -> list[str]:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return [
        current_time if value == "--now" else value
        for value in values
    ]


def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print("使い方:")
        print("  python3 main.py add \"値1\" \"値2\" \"値3\"")
        print("  python3 main.py update B2 \"更新後の値\"")
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        values = sys.argv[2:]

        if len(values) == 0:
            print("追加する値がありません。")
            print("例: python3 main.py add \"企業A\" \"確認中\" --now")
            sys.exit(1)

        values = replace_special_values(values)

        result = append_row(values)

        print("スプレッドシートに追加しました。")
        print("追加内容:")
        print(values)
        print("更新範囲:")
        print(result.get("updates", {}).get("updatedRange"))
        return

    if command == "update":
        if len(sys.argv) < 4:
            print("更新するセルと値を指定してください。")
            print("例: python3 main.py update B2 \"対応済み\"")
            sys.exit(1)

        cell = sys.argv[2]
        value = sys.argv[3]

        if value == "--now":
            value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        result = update_cell(cell, value)

        print("スプレッドシートを更新しました。")
        print("更新セル:")
        print(cell)
        print("更新内容:")
        print(value)
        print("更新範囲:")
        print(result.get("updatedRange"))
        return

    print(f"未対応のコマンドです: {command}")
    print("使えるコマンド: add, update")
    sys.exit(1)


if __name__ == "__main__":
    main()