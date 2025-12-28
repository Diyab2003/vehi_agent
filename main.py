import json
import re
from llm import groq_llm
from prompt import vehicle_prompt

conversation_memory = []

# States
chat_state = "NEW"  # NEW | DIY_INSPECT | DIY_FIX | DIY_VERIFY | DIY_CONTINUE | ASK_LOCATION
current_steps = []
step_index = 0
current_step = None
last_issue_severity = 0.0
issue_closed = False
user_location = None


# ---------- Helpers ----------

def extract_json(text):
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group() if match else None


def ask_llm(user_input):
    history = "\n".join(conversation_memory)
    prompt = vehicle_prompt.format(
        user_input=user_input,
        conversation_history=history
    )
    raw = groq_llm(prompt)
    json_text = extract_json(raw)
    return json.loads(json_text) if json_text else None


def is_closing_intent(text):
    text = text.lower()
    return any(p in text for p in [
        "ok", "okay", "thanks", "thank you",
        "alright", "got it", "fine", "cool"
    ])


def problem_found(text):
    text = text.lower()
    return any(p in text for p in [
        "there is", "found", "low", "leak", "block",
        "damage", "damaged", "worn", "faulty", "not working"
    ])


def fix_attempted(text):
    text = text.lower()
    return any(p in text for p in [
        "done", "fixed", "removed", "cleaned",
        "tightened", "replaced", "adjusted",
        "it worked", "working now", "resolved",
        "problem solved", "now it's fine"
    ])


def generate_fix_guidance():
    return (
        "That confirms a likely cause of the issue. "
        "If it’s safe and simple, you can try fixing it using commonly available tools "
        "like a screwdriver, wrench, cleaning cloth, or lubricant spray. "
        "If you’re not comfortable proceeding or special tools are required, it’s best to stop and let me know."
    )


# ---------- Workshop Logic ----------

def find_workshops(location):
    mock_workshops = {
        "kochi": [
            "ABC Auto Service – MG Road",
            "QuickFix Motors – Kaloor",
            "City Car Care – Edappally"
        ],
        "bangalore": [
            "FixIt Auto Hub – Indiranagar",
            "ProDrive Garage – Whitefield",
            "Metro Car Care – Yelahanka"
        ],
        "chennai": [
            "Speed Motors – Anna Nagar",
            "Elite Auto Care – Velachery",
            "Prime Garage – T Nagar"
        ]
    }

    return mock_workshops.get(location.lower(), [
        "Authorized Service Center",
        "Nearest trusted multi-brand workshop"
    ])


def show_workshop(reason):
    global issue_closed, chat_state

    print("\nAI Assistant:")
    print(reason)

    if not user_location:
        print("To suggest nearby workshops, could you tell me your city or area?")
        chat_state = "ASK_LOCATION"
        return

    workshops = find_workshops(user_location)
    print(f"\nHere are some workshops near {user_location}:")
    for w in workshops:
        print(f"- {w}")

    issue_closed = True
    chat_state = "NEW"


# ---------- DIY Control ----------

def start_diy(steps):
    global chat_state, current_steps, step_index, current_step

    current_steps = steps
    step_index = 0
    current_step = current_steps[step_index]
    chat_state = "DIY_INSPECT"

    print("\nAI Assistant:")
    print("Let’s start with a simple check.")
    print(current_step["inspect"])


# ---------- Main Loop ----------

print("Vehicle AI Help Chatbot")
print("Type 'exit' anytime to quit.\n")

while True:
    user_input = input("You: ").strip().lower()

    if user_input == "exit":
        print("\nAI Assistant: Drive safe. I’m here if you need help again.")
        break

    # ---------- Handle Location ----------
    if chat_state == "ASK_LOCATION":
        user_location = user_input
        print("\nAI Assistant:")
        print(f"Thanks! I’ll look for workshops near {user_location}.")

        workshops = find_workshops(user_location)
        print("\nRecommended workshops:")
        for w in workshops:
            print(f"- {w}")

        print("\nIf you need help with anything else, feel free to ask.")
        issue_closed = True
        chat_state = "NEW"
        continue

    # ---------- Polite Closing ----------
    if issue_closed and is_closing_intent(user_input):
        print("\nAI Assistant: You’re welcome 😊 If you have another vehicle issue, feel free to ask.")
        issue_closed = False
        continue

    # ---------- DIY INSPECT ----------
    if chat_state == "DIY_INSPECT":
        if problem_found(user_input):
            chat_state = "DIY_FIX"
            print("\nAI Assistant:")
            print(generate_fix_guidance())
        else:
            step_index += 1
            if step_index < len(current_steps):
                current_step = current_steps[step_index]
                print("\nAI Assistant:")
                print("Alright, let’s check the next thing.")
                print(current_step["inspect"])
            else:
                chat_state = "DIY_VERIFY"
                print("\nAI Assistant:")
                print("How does it feel now — any improvement?")
        continue

    # ---------- DIY FIX ----------
    if chat_state == "DIY_FIX":
        if fix_attempted(user_input):
            chat_state = "DIY_VERIFY"
            print("\nAI Assistant:")
            print("Does the issue seem resolved now?")
        elif is_closing_intent(user_input):
            show_workshop("Understood. If the issue persists, a professional inspection is recommended.")
        else:
            print("\nAI Assistant:")
            print("Take your time. Let me know once you’ve tried what’s possible.")
        continue

    # ---------- DIY VERIFY ----------
    if chat_state == "DIY_VERIFY":
        if user_input in ["yes", "y"]:
            print("\nAI Assistant: Glad to hear that 😊 Drive safe!")
            chat_state = "NEW"
        else:
            if last_issue_severity < 0.7:
                chat_state = "DIY_CONTINUE"
                print("\nAI Assistant:")
                print("Would you like to try another simple fix?")
            else:
                show_workshop("Since this issue can affect safety, it’s best to have it checked professionally.")
        continue

    # ---------- DIY CONTINUE ----------
    if chat_state == "DIY_CONTINUE":
        if user_input in ["yes", "y"]:
            chat_state = "NEW"
        else:
            show_workshop("Understood. A professional inspection would be the safest option now.")
        continue

    # ---------- NEW ISSUE ----------
    data = ask_llm(user_input)
    if not data or not all(k in data for k in ["diagnosis", "severity", "action"]):
        print("\nAI Assistant: I’m not fully sure yet. Could you describe the issue in a bit more detail?")
        continue

    conversation_memory.append(f"User: {user_input}")
    last_issue_severity = data["severity"]

    print("\nAI Assistant:")
    print(data.get("explanation", data["diagnosis"]))

    if data["action"] == "DIY" and data.get("steps"):
        structured_steps = [{"inspect": step} for step in data["steps"]]
        start_diy(structured_steps)
    else:
        show_workshop(data.get("explanation", "This issue is best handled by a professional."))
