import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parse_user_instruction(user_input: str) -> str:
    base_prompt = load_prompt("prompts/base.md")
    spreadsheet_prompt = load_prompt("prompts/spreadsheet.md")

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": base_prompt + "\n\n" + spreadsheet_prompt,
            },
            {
                "role": "user",
                "content": user_input,
            },
        ],
        temperature=0,
    )

    return response.choices[0].message.content