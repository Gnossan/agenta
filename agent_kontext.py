import json
from datetime import datetime
from openai import OpenAI

client = OpenAI()
nu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

try:
    with open("historik.json", "r") as f:
        historik = json.load(f)
except FileNotFoundError:
    historik = []

historik.append({"role": "system", "content": f"Nu är det {nu}."})
historik.append({"role": "system", "content": "Avsluta inte alltid dina svar med en fråga om vad användaren vill göra härnäst."})

while True:
    fråga = input("Du: ")
    
    if fråga.lower() == "avsluta":
        with open("historik.json", "w") as f:
            json.dump(historik, f, ensure_ascii=False, indent=2)
        break
    
    historik.append({"role": "user", "content": fråga})
    
    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=historik
    )
    
    svar = response.choices[0].message.content
    historik.append({"role": "assistant", "content": svar})
    
    print(f"AI: {svar}\n")
