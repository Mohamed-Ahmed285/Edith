from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import requests

app = Flask(__name__)

# 🔑 Configure Gemini with your API key
genai.configure(api_key="AIzaSyCRwAmkXkmHjchS8IopRb4bTIZA5HfxH3E")
EDITH_SYSTEM = """
You are EDITH, a futuristic, confident AI assistant.
Style:
- Witty, concise, a touch of dry sarcasm when appropriate.
- Clear, structured answers. Prefer bullets and short paragraphs.
- No emoji unless the user uses them first.
Behavior:
- Be helpful and factual; admit uncertainty briefly if needed.
- If user asks for code, provide minimal, runnable snippets.
- If user asks for steps, give numbered lists.
- Keep responses under ~6 sentences unless asked for more.
U will call me:
- mido
- sir 
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=EDITH_SYSTEM
)
conversation_history = []


def format_history_for_ollama(history):
    prompt = ""
    for turn in history:
        if turn["role"] == "user":
            prompt += f"User: {turn['parts'][0]}\n"
        elif turn["role"] == "model":
            prompt += f"EDITH: {turn['parts'][0]}\n"
    prompt += "EDITH:"
    return prompt

def call_ollama(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {"model": "llama3", "prompt": prompt}
    response = requests.post(url, json=payload, timeout=10)
    data = response.json()  # Full response at once
    return data.get("response", "")



@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"reply": "I didn’t catch that. Try typing your message again."})

    conversation_history.append({"role": "user", "parts": [user_message]})

    # Skip Gemini if quota is used
    try:
        response = model.generate_content(conversation_history)
        conversation_history.append({"role": "model", "parts": [response.text]})
        return jsonify({"reply": response.text})
    except Exception as e:
        print("Gemini failed:", e)

    # Try Ollama fallback
    try:
        reply_text = call_ollama(format_history_for_ollama(conversation_history))
        conversation_history.append({"role": "model", "parts": [reply_text]})
        return jsonify({"reply": reply_text})
    except Exception as e:
        print("Ollama fallback failed:", e)
        return jsonify({"reply": "EDITH is unavailable right now."})

        
if __name__ == "__main__":
    app.run(debug=True)