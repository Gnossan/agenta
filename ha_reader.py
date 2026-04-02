# ─────────────────────────────────────────
# Imports
# ─────────────────────────────────────────
from flask import Flask, request
from dotenv import load_dotenv
import requests
import json
import os
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

# ─────────────────────────────────────────
# Konfiguration
# ─────────────────────────────────────────
SECRET   = os.getenv("SECRET")
HA_URL   = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

HA_HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}

DEVICES_FILE = "devices.json"

client = OpenAI()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_device_state",
            "description": "Hämtar aktuell status för en enhet i hemmet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Enhetens entity_id, t.ex. light.golvlampa_i_kontoret"
                    }
                },
                "required": ["entity_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_device_state",
            "description": "Tänder eller släcker en enhet i hemmet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Enhetens entity_id, t.ex. light.golvlampa_i_kontoret"
                    },
                    "state": {
                        "type": "string",
                        "enum": ["on", "off"],
                        "description": "Önskat tillstånd, on eller off"
                    }
                },
                "required": ["entity_id", "state"]
            }
        }
    }
]
# ─────────────────────────────────────────
# HA-funktioner
# ─────────────────────────────────────────
def get_device_context():
    r = requests.get(
        f"{HA_URL}/api/states",
        headers=HA_HEADERS
    )
    all_states = r.json()

    devices = []
    for entity in all_states:
        entity_id = entity["entity_id"]
        domain = entity_id.split(".")[0]

        # Bara lampor och brytare till en början
        if domain not in ["light", "switch"]:
            continue

        devices.append({
            "name": entity["attributes"].get("friendly_name", entity_id),
            "entity_id": entity_id,
            "last_changed": entity["last_changed"]
        })

    return devices

def get_device_state(entity_id):
    r = requests.get(
        f"{HA_URL}/api/states/{entity_id}",
        headers=HA_HEADERS
    )
    data = r.json()
    return data.get("state", "okänd")

def save_device_context():
    devices = get_device_context()
    with open(DEVICES_FILE, "w", encoding="utf-8") as f:
        json.dump(devices, f, indent=2, ensure_ascii=False)
    print(f"Sparade {len(devices)} enheter till {DEVICES_FILE}")


def load_device_context():
    with open(DEVICES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    
def set_device_state(entity_id, state):
    domain = entity_id.split(".")[0]
    service = "turn_on" if state == "on" else "turn_off"
    r = requests.post(
        f"{HA_URL}/api/services/{domain}/{service}",
        headers=HA_HEADERS,
        json={"entity_id": entity_id}
    )
    return "ok" if r.status_code == 200 else "fel"

# ─────────────────────────────────────────
# AI-funktioner
# ─────────────────────────────────────────
def ask_ai(user_message, user_history=[]):
    devices = load_device_context()
    device_info = json.dumps(devices, ensure_ascii=False, indent=2)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Du är en hemassistent som känner till följande enheter:\n\n"
                    f"{device_info}\n\n"
                    "Du är en hemassistent som kan hämta status och styra enheter i hemmet. "
                    "När användaren ber dig tända eller släcka en enhet, använd set_device_state direkt utan att fråga om bekräftelse."
                )
            },
            *user_history,
            {"role": "user", "content": user_message}
        ],
        tools=TOOLS,
        temperature=0.5
    )

    message = response.choices[0].message

    if message.tool_calls:
        tool_results = []
        for tool_call in message.tool_calls:
            #print(f"Verktyg: {tool_call.function.name}, args: {tool_call.function.arguments}")
            arguments = json.loads(tool_call.function.arguments)
        
            if tool_call.function.name == "get_device_state":
                result = get_device_state(arguments["entity_id"])
            elif tool_call.function.name == "set_device_state":
                result = set_device_state(arguments["entity_id"], arguments["state"])
            else:
                result = "okänt verktyg"
        
            tool_results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            #print(f"tool_results längd: {len(tool_results)}")
        })

        second_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                *user_history,
                {"role": "user", "content": user_message},
                message,
                *tool_results
        ]
    )
        return second_response.choices[0].message.content.strip()

    return message.content.strip()
# ─────────────────────────────────────────
# Flask-routes
# ─────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    token = request.headers.get("X-Webhook-Token")
    if token != SECRET:
        return "Unauthorized", 401

    data = request.get_json()
    user_message = data.get("message", "")
    print(f"Fråga: {user_message}")

    answer = ask_ai(user_message)
    print(f"Svar: {answer}")

    return answer, 200

# ─────────────────────────────────────────
# Start
# ─────────────────────────────────────────
#if __name__ == "__main__":
    #save_device_context()
   # app.run(host="0.0.0.0", port=5001)

# ─────────────────────────────────────────
# Chat-prompt
# ─────────────────────────────────────────    
if __name__ == "__main__":
    save_device_context()
    conversation_history = []
    while True:
        user_input = input("Du: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        conversation_history.append({"role": "user", "content": user_input})
        answer = ask_ai(user_input, conversation_history)
        conversation_history.append({"role": "assistant", "content": answer})
        print(f"AI: {answer}\n")