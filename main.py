import json
import re
from llm import groq_llm
from prompt import vehicle_prompt

conversation_memory = []

# Chat states
chat_state = "NEW"            # NEW | DIY_INSPECT | DIY_FIX | DIY_VERIFY | DIY_CONTINUE
current_steps = []
step_index = 0
current_step = None
last_issue_severity = 0.0
issue_closed = False


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


def show_workshop(reason):
    global issue_closed
    issue_closed = True

    print("\nAI Assistant:")
    print(reason)
    print("I recommend getting it checked at:")
    print("- Authorized service center")
    print("- Nearest trusted multi-brand workshop")


def is_closing_intent(text):
    text = text.lower()
    return any(
        p in text for p in
        ["ok", "thanks", "thank", "alright", "got it", "understood", "fine"]
    )


def problem_found(text):
    text = text.lower()
    return any(
        p in text for p in
        ["yes", "there is", "found", "low", "block", "damage", "leak", "worn", "not working"]
    )


def problem_fixed(text):
    text = text.lower()
    return any(
        p in text for p in
        ["done", "fixed", "removed", "cleaned", "tightened", "working now"]
    )


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

    # Close politely after escalation
    if issue_closed and is_closing_intent(user_input):
        print("\nAI Assistant: You’re welcome 😊 If you have another vehicle issue, feel free to ask.")
        issue_closed = False
        chat_state = "NEW"
        continue

    # ---------- DIY INSPECT ----------
    if chat_state == "DIY_INSPECT":
        if problem_found(user_input):
            chat_state = "DIY_FIX"
            print("\nAI Assistant:")
            print(current_step["fix"])
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
                print("That covers the basic checks. Did this fix the issue? (yes / no)")
        continue

    # ---------- DIY FIX ----------
    if chat_state == "DIY_FIX":
        if problem_fixed(user_input):
            chat_state = "DIY_VERIFY"
            print("\nAI Assistant:")
            print("Does the issue seem resolved now? (yes / no)")
        else:
            print("\nAI Assistant:")
            print("Take your time and let me know once you’ve tried that.")
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
                print("Would you like to try another simple fix? (yes / no)")
            else:
                show_workshop(
                    "Since the issue is still present and could affect safety, further DIY isn’t recommended."
                )
                chat_state = "NEW"
        continue

    # ---------- DIY CONTINUE ----------
    if chat_state == "DIY_CONTINUE":
        if user_input in ["yes", "y"]:
            chat_state = "NEW"
        else:
            show_workshop(
                "Understood. A professional inspection would be the safest option now."
            )
            chat_state = "NEW"
        continue

    # ---------- NEW ISSUE ----------
    data = ask_llm(user_input)
    if not data:
        print("\nAI Assistant: Could you explain that a bit more?")
        continue

    conversation_memory.append(f"User: {user_input}")
    last_issue_severity = data.get("severity", 0.6)

    print("\nAI Assistant:")
    print(data.get("explanation", data.get("diagnosis")))
    print(f"Severity level: {last_issue_severity}")

    action = data.get("action", "ESCALATE")

    if action == "DIY" and data.get("steps"):
        # Convert plain steps to inspect–fix structure
        structured_steps = []

    for step in data["steps"]:
         structured_steps.append({
        "inspect": step,
        "fix": "Try addressing what you found and let me know once that’s done."
       })

    start_diy(structured_steps)
    continue

    if action == "ASK" and data.get("follow_up_question"):
        print("\n" + data["follow_up_question"])
        continue

    show_workshop(data.get("explanation"))
