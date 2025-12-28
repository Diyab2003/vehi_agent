# vehi_agent/safety_rules.py
def safety_check(text: str) -> bool:
    critical_keywords = [
        "brake", "abs", "airbag", "steering",
        "fuel leak", "fire", "smoke", "suspension"
    ]

    text = text.lower()
    return any(word in text for word in critical_keywords)
