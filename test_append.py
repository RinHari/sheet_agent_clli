from dotenv import load_dotenv

from tools.spreadsheet_tool import append_row


def main():
    load_dotenv()

    result = append_row(["テスト企業", "確認中", "2026-06-17"])

    print("スプレッドシートに追加しました。")
    print(result)


if __name__ == "__main__":
    main()