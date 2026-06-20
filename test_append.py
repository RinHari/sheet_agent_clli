from dotenv import load_dotenv
from datetime import datetime
from tools.spreadsheet_tool import append_row


def main():
    load_dotenv()

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    result = append_row(["テスト", "確認中", current_time])

    print("スプレッドシートに追加しました。")
    print(result)


if __name__ == "__main__":
    main()