import sys
from datetime import datetime
from dotenv import load_dotenv

from tools.spreadsheet_tool import append_row, update_row


def replace_special_values(values: list[str]) -> list[str]:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return [
        current_time if value == "--now" else value
        for value in values
    ]


def print_usage() -> None:
    print("使い方:")
    print("  python3 main.py add \"値1\" \"値2\" \"値3\"")
    print("  python3 main.py update <開始セル> \"値1\" \"値2\" ...")
    print("")
    print("例:")
    print("  python3 main.py add \"企業A\" \"確認中\" --now")
    print("  python3 main.py update A6 \"企業A\" \"対応済み\" --now")


def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        values = sys.argv[2:]

        if len(values) == 0:
            print("追加する値がありません。")
            print_usage()
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
            print("開始セルと更新する値を指定してください。")
            print_usage()
            sys.exit(1)

        start_cell = sys.argv[2]
        values = sys.argv[3:]

        values = replace_special_values(values)

        result = update_row(start_cell, values)

        print("スプレッドシートを更新しました。")
        print("開始セル:")
        print(start_cell)
        print("更新内容:")
        print(values)
        print("更新範囲:")
        print(result.get("updatedRange"))
        return

    print(f"未対応のコマンドです: {command}")
    print("使えるコマンド: add, update")
    sys.exit(1)


if __name__ == "__main__":
    main()