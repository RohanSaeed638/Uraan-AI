import json


def parse_ai_json(text: str):

    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "")

    if text.endswith("```"):
        text = text.replace("```", "")

    return json.loads(text)